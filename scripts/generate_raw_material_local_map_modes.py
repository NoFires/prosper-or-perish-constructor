from __future__ import annotations

import re
import shutil
import tomllib
from pathlib import Path
from typing import Iterable

from eu5gameparser.domain.eu5 import load_eu5_data


ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG = ROOT / "constructor.toml"

MAP_MODE_REL = Path("in_game/gfx/map/map_modes/pp_local_output_modifier_map_modes.txt")
SCRIPT_VALUES_REL = Path("in_game/common/script_values/pp_local_output_modifier_map_modes.txt")
VARIABLE_HARVEST_STATIC_MODIFIERS_REL = Path(
    "in_game/common/static_modifiers/pp_variable_harvest_modifiers.txt"
)
LOCALIZATION_REL = Path("main_menu/localization/english/pp_building_adjustments_l_english.yml")
IN_GAME_ICON_REL = Path("in_game/gfx/interface/icons/map_modes")
MAIN_MENU_ICON_REL = Path("main_menu/gfx/interface/icons/map_modes")
TRADE_GOOD_ICON_REL = Path("main_menu/gfx/interface/icons/trade_goods")

LOCALIZATION_START = "  # Local output modifier map modes (pp_local_output_modifier_map_modes.txt)"
LOCALIZATION_END = "  # End generated local output modifier map modes"
WHEAT_GOOD = "wheat"
WHEAT_LOCATION_STRIPE_RGB = (246, 197, 75)
WHEAT_PRODUCTIVITY_CLASSES = [
    (
        "EXTREME_DEFICIT",
        "Extreme wheat deficit",
        "<= -1.00",
        None,
        None,
        (64, 0, 75),
        (64, 0, 75),
        (64, 0, 75),
    ),
    (
        "SEVERE_DEFICIT",
        "Severe wheat deficit",
        "< -0.75",
        "-1.00",
        "0.25",
        (75, 10, 88),
        (118, 42, 131),
        (96, 25, 109),
    ),
    (
        "DEFICIT",
        "Wheat productivity deficit",
        "< -0.50",
        "-0.75",
        "0.25",
        (130, 69, 146),
        (153, 112, 171),
        (143, 86, 157),
    ),
    (
        "WEAK",
        "Weak wheat productivity",
        "< -0.25",
        "-0.50",
        "0.25",
        (166, 129, 184),
        (194, 165, 207),
        (179, 148, 195),
    ),
    (
        "MARGINAL",
        "Marginal wheat productivity",
        "< 0",
        "-0.25",
        "0.25",
        (211, 190, 219),
        (231, 212, 232),
        (222, 202, 224),
    ),
    (
        "NEUTRAL",
        "Near neutral wheat productivity",
        "< 0.25",
        "0",
        "0.25",
        (247, 247, 247),
        (217, 240, 211),
        (235, 244, 232),
    ),
    (
        "SLIGHT_ADVANTAGE",
        "Slight wheat advantage",
        "< 0.50",
        "0.25",
        "0.25",
        (203, 233, 197),
        (166, 219, 160),
        (184, 225, 178),
    ),
    (
        "GOOD",
        "Good wheat productivity",
        "< 0.75",
        "0.50",
        "0.25",
        (139, 204, 135),
        (90, 174, 97),
        (112, 192, 119),
    ),
    (
        "STRONG",
        "Strong wheat productivity",
        "< 1.00",
        "0.75",
        "0.25",
        (62, 153, 72),
        (27, 120, 55),
        (45, 138, 64),
    ),
    (
        "VERY_STRONG",
        "Very strong wheat productivity",
        "< 1.50",
        "1.00",
        "0.50",
        (20, 110, 50),
        (8, 86, 35),
        (12, 100, 41),
    ),
    (
        "EXCELLENT",
        "Excellent wheat productivity",
        "< 2.00",
        "1.50",
        "0.50",
        (4, 77, 30),
        (0, 68, 27),
        (2, 72, 29),
    ),
    (
        "EXCEPTIONAL",
        "Exceptional wheat productivity",
        None,
        None,
        None,
        (0, 50, 20),
        (0, 50, 20),
        (0, 50, 20),
    ),
]


def main() -> None:
    project = _load_project_config(PROJECT_CONFIG)
    mod_root = _project_path(project["project"]["mod_root"])
    raw_materials = _raw_material_goods(project)

    _write_map_modes(mod_root / MAP_MODE_REL, raw_materials)
    _write_script_values(
        mod_root / SCRIPT_VALUES_REL,
        _wheat_harvest_modifier_values(mod_root / VARIABLE_HARVEST_STATIC_MODIFIERS_REL),
    )
    _upsert_localization(mod_root / LOCALIZATION_REL, raw_materials)
    _ensure_icons(mod_root, raw_materials, project)
    print(f"Generated local output modifier map modes for {len(raw_materials)} raw materials.")


def _load_project_config(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def _project_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (ROOT / path).resolve()


def _raw_material_goods(project: dict) -> list[str]:
    parser = project.get("parser", {})
    profile = str(parser.get("profile") or "constructor")
    load_order = _project_path(str(parser.get("load_order") or "constructor.load_order.toml"))
    data = load_eu5_data(profile=profile, load_order_path=load_order)
    return (
        data.goods.filter(data.goods["category"] == "raw_material")
        .select("name")
        .to_series()
        .to_list()
    )


def _vanilla_root(project: dict) -> Path:
    parser = project.get("parser", {})
    load_order = _project_path(str(parser.get("load_order") or "constructor.load_order.toml"))
    with load_order.open("rb") as stream:
        raw = tomllib.load(stream)
    paths = raw.get("paths", {})
    vanilla_root = Path(str(paths.get("vanilla_root", "")))
    if not vanilla_root.is_absolute():
        vanilla_root = (load_order.parent / vanilla_root).resolve()
    return vanilla_root


def _write_map_modes(path: Path, goods: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        "# Generated by scripts/generate_raw_material_local_map_modes.py - do not edit by hand.",
        "# Displays local_<good>_output_modifier for every parsed raw_material good.",
        "# Non-wheat: red = -50%, green = +150%. Values are additive percentages (0.1 = +10%).",
        "# Wheat uses a harvest-neutral classified diverging productivity scale plus wheat-location stripes.",
        "# Geography index = 2 keeps these in the terrain/climate bucket.",
        "",
        "@factor_add = 0.5",
        "@factor_divide = 2.0",
        "@zoom_step_near = 2",
        "@data_gradient_alpha_inside = 1",
        "@data_gradient_alpha_outside = 1",
        "@data_gradient_width = 0.25",
        "@data_gradient_color_mult = 0.9",
        "@data_edge_width = 0",
        "@data_edge_sharpness = 0.01",
        "@data_edge_alpha = 0",
        "@data_edge_color_mult = 0",
        "@data_before_lighting_blend = 0.5",
        "@data_after_lighting_blend = 0.5",
        "",
    ]
    for good in goods:
        blocks.append(_map_mode_block(good))
    _write_crlf(path, "\n".join(blocks).rstrip() + "\n")


def _map_mode_block(good: str) -> str:
    if good == WHEAT_GOOD:
        return _wheat_map_mode_block()
    return _generic_map_mode_block(good)


def _generic_map_mode_block(good: str) -> str:
    upper = good.upper()
    return f"""pp_local_{good}_output_modifier = {{
\tmap_color = {{
\t\tif = {{
\t\t\tlimit = {{ is_ownable = yes }}
\t\t\tlerp = {{
\t\t\t\tmin_color = define:NMapColors|MAP_COLOR_LOW
\t\t\t\tmax_color = define:NMapColors|MAP_COLOR_HIGH
\t\t\t\tfactor = {{
\t\t\t\t\tvalue = modifier:local_{good}_output_modifier
\t\t\t\t\tadd = @factor_add
\t\t\t\t\tdivide = @factor_divide
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t\telse = {{ value = rgb {{ 128 128 128 }} }}
\t}}
\tlegend_key = {{ desc = "MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER" color = define:NMapColors|MAP_COLOR_HIGH }}
\ttooltip_key = {{
\t\tif = {{
\t\t\tlimit = {{ is_land = yes }}
\t\t\tvalue = MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND_BREAKDOWN
\t\t}}
\t\telse = {{
\t\t\tvalue = MAPMODE_PP_LOCAL_OUTPUT_TT_WATER
\t\t}}
\t}}
\tsmall_map_names = location
\tmedium_map_names = location
\tlarge_map_names = location
\tsmall_tooltip_context = location
\tmedium_tooltip_context = location
\tlarge_tooltip_context = location
\tfill_in_impassable = yes
\tenable_snow = no
\tflatmap_behaviour = always
\tuse_fow = no
\tcategory = geography
\tindex = 2
\tallow_allocate_hotkey = no
\tmap_markers = {{ all = no }}
\tgradient_parameters = {{
\t\tzoom_step = @zoom_step_near
\t\tgradient_alpha_inside = @data_gradient_alpha_inside
\t\tgradient_alpha_outside = @data_gradient_alpha_outside
\t\tgradient_width = @data_gradient_width
\t\tgradient_color_mult = @data_gradient_color_mult
\t\tedge_width = @data_edge_width
\t\tedge_sharpness = @data_edge_sharpness
\t\tedge_alpha = @data_edge_alpha
\t\tedge_color_mult = @data_edge_color_mult
\t\tbefore_lighting_blend = @data_before_lighting_blend
\t\tafter_lighting_blend = @data_after_lighting_blend
\t}}
}}
"""


def _wheat_map_mode_block() -> str:
    upper = WHEAT_GOOD.upper()
    return f"""pp_local_{WHEAT_GOOD}_output_modifier = {{
{_wheat_map_color_block()}
\tsecondary_map_color = {{
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tis_ownable = yes
\t\t\t\traw_material = goods:wheat
\t\t\t}}
\t\t\tvalue = {_rgb(WHEAT_LOCATION_STRIPE_RGB)}
\t\t}}
\t}}
{_wheat_legend_keys(upper)}
\ttooltip_key = {{
\t\tif = {{
\t\t\tlimit = {{ is_land = yes }}
\t\t\tvalue = MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND_BREAKDOWN
\t\t}}
\t\telse = {{
\t\t\tvalue = MAPMODE_PP_LOCAL_OUTPUT_TT_WATER
\t\t}}
\t}}
\tsmall_map_names = location
\tmedium_map_names = location
\tlarge_map_names = location
\tsmall_tooltip_context = location
\tmedium_tooltip_context = location
\tlarge_tooltip_context = location
\tfill_in_impassable = yes
\tenable_snow = no
\tflatmap_behaviour = always
\tuse_fow = no
\tcategory = geography
\tindex = 2
\tallow_allocate_hotkey = no
\tmap_markers = {{ all = no }}
\tgradient_parameters = {{
\t\tzoom_step = @zoom_step_near
\t\tgradient_alpha_inside = @data_gradient_alpha_inside
\t\tgradient_alpha_outside = @data_gradient_alpha_outside
\t\tgradient_width = @data_gradient_width
\t\tgradient_color_mult = @data_gradient_color_mult
\t\tedge_width = @data_edge_width
\t\tedge_sharpness = @data_edge_sharpness
\t\tedge_alpha = @data_edge_alpha
\t\tedge_color_mult = @data_edge_color_mult
\t\tbefore_lighting_blend = @data_before_lighting_blend
\t\tafter_lighting_blend = @data_after_lighting_blend
\t}}
}}
"""


def _wheat_map_color_block() -> str:
    lines = [
        "\tmap_color = {",
        "\t\tif = {",
        "\t\t\tlimit = { is_ownable = no }",
        "\t\t\tvalue = rgb { 128 128 128 }",
        "\t\t}",
    ]
    for (
        _suffix,
        _description,
        condition,
        lower_bound,
        width,
        min_rgb,
        max_rgb,
        _legend_rgb,
    ) in WHEAT_PRODUCTIVITY_CLASSES:
        if condition is None:
            lines.append("\t\telse = {")
        else:
            lines.extend(
                [
                    "\t\telse_if = {",
                    f"\t\t\tlimit = {{ pp_wheat_productivity_map_value {condition} }}",
                ]
            )
        if width is None:
            lines.append(f"\t\t\tvalue = {_rgb(min_rgb)}")
        else:
            lines.extend(_wheat_bucket_lerp_lines(lower_bound, width, min_rgb, max_rgb))
        lines.append("\t\t}")
    lines.append("\t}")
    return "\n".join(lines)


def _wheat_bucket_lerp_lines(
    lower_bound: str | None,
    width: str,
    min_rgb: tuple[int, int, int],
    max_rgb: tuple[int, int, int],
) -> list[str]:
    if lower_bound is None:
        raise ValueError("Gradient wheat productivity buckets require a lower bound")
    lines = [
        "\t\t\tlerp = {",
        f"\t\t\t\tmin_color = {_rgb(min_rgb)}",
        f"\t\t\t\tmax_color = {_rgb(max_rgb)}",
        "\t\t\t\tfactor = {",
        "\t\t\t\t\tvalue = pp_wheat_productivity_map_value",
    ]
    if lower_bound.startswith("-"):
        lines.append(f"\t\t\t\t\tadd = {lower_bound[1:]}")
    elif lower_bound != "0":
        lines.append(f"\t\t\t\t\tsubtract = {lower_bound}")
    lines.extend(
        [
            f"\t\t\t\t\tdivide = {width}",
            "\t\t\t\t\tmax = 1",
            "\t\t\t\t\tmin = 0",
            "\t\t\t\t}",
            "\t\t\t}",
        ]
    )
    return lines


def _wheat_legend_keys(upper: str) -> str:
    lines = [
        f'\tlegend_key = {{ desc = "MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_{suffix}" color = {_rgb(legend_rgb)} }}'
        for suffix, _description, _condition, _lower_bound, _width, _min_rgb, _max_rgb, legend_rgb in WHEAT_PRODUCTIVITY_CLASSES
    ]
    lines.append(
        f'\tlegend_key = {{ desc = "MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_WHEAT_LOCATION" color = {_rgb(WHEAT_LOCATION_STRIPE_RGB)} }}'
    )
    return "\n".join(lines)


def _write_script_values(path: Path, wheat_harvest_modifiers: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        "# Generated by scripts/generate_raw_material_local_map_modes.py - do not edit by hand.",
        "# Harvest-neutral wheat productivity for the wheat local output modifier map mode.",
        "",
        "pp_wheat_productivity_map_value = {",
        "\tvalue = modifier:local_wheat_output_modifier",
    ]
    for modifier, value in wheat_harvest_modifiers:
        operation, amount = _inverse_value_operation(value)
        blocks.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ has_location_modifier = {modifier} }}",
                f"\t\t{operation} = {amount}",
                "\t}",
            ]
        )
    blocks.append("}")
    _write_crlf(path, "\n".join(blocks).rstrip() + "\n")


def _wheat_harvest_modifier_values(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    values: list[tuple[str, str]] = []
    pattern = re.compile(r"^(pp_harvest_[a-z0-9_]+)\s*=\s*\{(?P<body>.*?)^\}", re.DOTALL | re.MULTILINE)
    for match in pattern.finditer(text):
        value_match = re.search(
            r"^\s*local_wheat_output_modifier\s*=\s*([-+]?\d+(?:\.\d+)?)\s*$",
            match.group("body"),
            flags=re.MULTILINE,
        )
        if value_match is not None:
            values.append((match.group(1), value_match.group(1)))
    if not values:
        raise ValueError(f"Could not find wheat harvest modifiers in {path}")
    return values


def _inverse_value_operation(value: str) -> tuple[str, str]:
    if value.startswith("-"):
        return "add", value[1:]
    return "subtract", value.removeprefix("+")


def _upsert_localization(path: Path, goods: Iterable[str]) -> None:
    existing = path.read_text(encoding="utf-8-sig")
    generated = _localization_block(goods)
    if LOCALIZATION_START in existing:
        if LOCALIZATION_END in existing:
            pattern = re.compile(
                rf"{re.escape(LOCALIZATION_START)}.*?{re.escape(LOCALIZATION_END)}\n?",
                re.DOTALL,
            )
            updated = pattern.sub(lambda _match: generated, existing)
        else:
            legacy_end = re.compile(
                rf"{re.escape(LOCALIZATION_START)}.*?"
                r'  MAPMODE_PP_LOCAL_OUTPUT_TT_WATER: "[^"]*"\n?',
                re.DOTALL,
            )
            updated = legacy_end.sub(lambda _match: generated, existing)
    else:
        anchor = "  # Unemployed Peasants (Unemployment) map mode - absolute numbers, cap 0-50k"
        if anchor not in existing:
            raise ValueError(f"Could not find localization insertion point in {path}")
        updated = existing.replace(anchor, generated + "\n" + anchor)
    _write_crlf(path, updated.rstrip() + "\n")


def _localization_block(goods: Iterable[str]) -> str:
    lines = [
        LOCALIZATION_START,
        "  # Generated by scripts/generate_raw_material_local_map_modes.py - do not edit by hand.",
        '  PP_LOCAL_OUTPUT_MAPMODE_RANGE: "Red=-50%, Green=150%"',
    ]
    goods = list(goods)
    for good in goods:
        name = "Wheat Productivity" if good == WHEAT_GOOD else f"Local {_display_name(good)} Output"
        lines.append(f'  mapmode_pp_local_{good}_output_modifier_name: "{name}"')
    lines.append("")
    for good in goods:
        upper = good.upper()
        if good == WHEAT_GOOD:
            lines.extend(_wheat_legend_localization_lines())
        else:
            name_key = f"mapmode_pp_local_{good}_output_modifier_name"
            lines.append(
                f'  MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER: "#T ${name_key}$#!\\n'
                f'This colors [locations|e] by the local {_display_name(good).lower()} output modifier in the [location|e]."'
            )
    lines.append("")
    for good in goods:
        upper = good.upper()
        display = _display_name(good).lower()
        if good == WHEAT_GOOD:
            lines.append(
                f'  MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND: '
                '"[ROOT.GetLocation.GetName] has harvest-neutral wheat productivity of '
                "[ROOT.GetLocation.MakeScope.ScriptValue('pp_wheat_productivity_map_value')|2].\""
            )
        else:
            lines.append(
                f'  MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND: '
                f'"[ROOT.GetLocation.GetName] has a local {display} output modifier of '
                f"[ROOT.GetLocation.GetModifierValue('local_{good}_output_modifier')|Y].\""
            )
    lines.append("")
    for good in goods:
        upper = good.upper()
        display = _display_name(good).lower()
        if good == WHEAT_GOOD:
            lines.append(
                f'  MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND_BREAKDOWN: '
                '"[ROOT.GetLocation.GetName] harvest-neutral wheat productivity: '
                "[ROOT.GetLocation.MakeScope.ScriptValue('pp_wheat_productivity_map_value')|2].\\n"
                "Live local wheat output modifier: [ROOT.GetLocation.GetModifierValue('local_wheat_output_modifier')|Y].\\n"
                'Active variable harvest effects are excluded from the map color. Purple-to-green diverging bands make similar productive areas easier to compare, with subtle shading inside each band; stripes mark locations where wheat is the raw material."'
            )
        else:
            lines.append(
                f'  MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND_BREAKDOWN: '
                f'"[ROOT.GetLocation.GetName] has a local {display} output modifier of '
                f"[ROOT.GetLocation.GetModifierValue('local_{good}_output_modifier')|Y].\\n"
                'Aggregated from vegetation, topography, climate, water, and labeling sources."'
            )
    lines.extend(
        [
            "",
            '  MAPMODE_PP_LOCAL_OUTPUT_TT_WATER: "[ROOT.GetLocation.GetName] is not a land [location|e] so it does not have production modifiers."',
            LOCALIZATION_END,
        ]
    )
    return "\n".join(lines) + "\n"


def _wheat_legend_localization_lines() -> list[str]:
    name_key = "mapmode_pp_local_wheat_output_modifier_name"
    lines = [
        f'  MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER: "#T ${name_key}$#!\\n'
        'This colors [locations|e] by harvest-neutral wheat productivity. '
        'Purple-to-green diverging bands separate modest, strong, and exceptional productivity, with subtle shading inside each band; '
        'temporary harvest effects do not change the color. Stripes mark locations where wheat is the raw material."',
    ]
    lines.extend(
        f'  MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER_{suffix}: "{description}"'
        for suffix, description, _condition, _lower_bound, _width, _min_rgb, _max_rgb, _legend_rgb in WHEAT_PRODUCTIVITY_CLASSES
    )
    lines.append('  MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER_WHEAT_LOCATION: "Wheat raw material"')
    return lines


def _display_name(good: str) -> str:
    return good.replace("_", " ").title()


def _rgb(value: tuple[int, int, int]) -> str:
    red, green, blue = value
    return f"rgb {{ {red} {green} {blue} }}"


def _write_crlf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="\r\n") as stream:
        stream.write(text)


def _ensure_icons(mod_root: Path, goods: Iterable[str], project: dict) -> None:
    vanilla_root = _vanilla_root(project)
    targets = [mod_root / IN_GAME_ICON_REL, mod_root / MAIN_MENU_ICON_REL]
    for target in targets:
        target.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    for good in goods:
        source = _icon_source(mod_root, vanilla_root, good)
        if source is None:
            missing.append(good)
            continue
        for target_dir in targets:
            destination = target_dir / f"pp_local_{good}_output_modifier.dds"
            if not destination.exists():
                shutil.copy2(source, destination)
    if missing:
        raise FileNotFoundError("Missing icon source for raw material goods: " + ", ".join(missing))


def _icon_source(mod_root: Path, vanilla_root: Path, good: str) -> Path | None:
    candidates = [
        mod_root / IN_GAME_ICON_REL / f"pp_local_{good}_output_modifier.dds",
        mod_root / MAIN_MENU_ICON_REL / f"pp_local_{good}_output_modifier.dds",
        mod_root / IN_GAME_ICON_REL / f"pp_{good}_output.dds",
        mod_root / MAIN_MENU_ICON_REL / f"pp_{good}_output.dds",
        vanilla_root / "game" / TRADE_GOOD_ICON_REL / f"icon_goods_{good}.dds",
        mod_root / TRADE_GOOD_ICON_REL / f"icon_goods_{good}.dds",
        mod_root / "in_game" / "gfx" / "interface" / "icons" / "trade_goods" / f"icon_goods_{good}.dds",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


if __name__ == "__main__":
    main()
