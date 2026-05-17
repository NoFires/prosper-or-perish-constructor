from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from eu5gameparser.domain.eu5 import load_eu5_data


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod" / "Prosper or Perish (Population Growth & Food Rework)"
MAP_MODES = MOD_ROOT / "in_game" / "gfx" / "map" / "map_modes" / "pp_local_output_modifier_map_modes.txt"
SCRIPT_VALUES = MOD_ROOT / "in_game" / "common" / "script_values" / "pp_local_output_modifier_map_modes.txt"
HARVEST_MODIFIERS = MOD_ROOT / "in_game" / "common" / "static_modifiers" / "pp_variable_harvest_modifiers.txt"
LOCALIZATION = MOD_ROOT / "main_menu" / "localization" / "english" / "pp_building_adjustments_l_english.yml"
ICON_DIRS = (
    MOD_ROOT / "in_game" / "gfx" / "interface" / "icons" / "map_modes",
    MOD_ROOT / "main_menu" / "gfx" / "interface" / "icons" / "map_modes",
)


def _raw_material_goods() -> list[str]:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    return (
        data.goods.filter(data.goods["category"] == "raw_material")
        .select("name")
        .to_series()
        .to_list()
    )


def _all_goods() -> set[str]:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    return set(data.goods.select("name").to_series().to_list())


def _map_mode_goods(text: str) -> list[str]:
    return re.findall(r"^pp_local_(.+?)_output_modifier\s*=\s*\{", text, flags=re.MULTILINE)


def _map_mode_blocks(text: str) -> dict[str, str]:
    starts = list(re.finditer(r"^pp_local_(.+?)_output_modifier\s*=\s*\{", text, flags=re.MULTILINE))
    blocks: dict[str, str] = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        blocks[match.group(1)] = text[match.start() : end]
    return blocks


def _wheat_harvest_modifier_values() -> dict[str, str]:
    text = HARVEST_MODIFIERS.read_text(encoding="utf-8-sig")
    values: dict[str, str] = {}
    pattern = re.compile(r"^(pp_harvest_[a-z0-9_]+)\s*=\s*\{(?P<body>.*?)^\}", re.DOTALL | re.MULTILINE)
    for match in pattern.finditer(text):
        value_match = re.search(
            r"^\s*local_wheat_output_modifier\s*=\s*([-+]?\d+(?:\.\d+)?)\s*$",
            match.group("body"),
            flags=re.MULTILINE,
        )
        if value_match is not None:
            values[match.group(1)] = value_match.group(1)
    return values


def test_local_output_map_modes_match_parser_raw_materials() -> None:
    raw_materials = _raw_material_goods()
    found = _map_mode_goods(MAP_MODES.read_text(encoding="utf-8-sig"))
    counts = Counter(found)

    assert found == raw_materials
    assert not [good for good, count in counts.items() if count != 1]
    assert set(found).issubset(_all_goods())


def test_local_output_map_modes_have_no_non_raw_material_goods() -> None:
    raw_materials = set(_raw_material_goods())
    found = set(_map_mode_goods(MAP_MODES.read_text(encoding="utf-8-sig")))

    assert found == raw_materials


def test_local_output_map_modes_have_required_localization() -> None:
    loc = LOCALIZATION.read_text(encoding="utf-8-sig")

    missing: list[str] = []
    for good in _raw_material_goods():
        upper = good.upper()
        keys = [
            f"mapmode_pp_local_{good}_output_modifier_name",
            f"MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER",
            f"MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND",
            f"MAPMODE_PP_LOCAL_{upper}_OUTPUT_MODIFIER_TT_LAND_BREAKDOWN",
        ]
        missing.extend(key for key in keys if key not in loc)

    assert not missing


def test_wheat_output_map_mode_uses_harvest_neutral_script_value_only_for_wheat() -> None:
    blocks = _map_mode_blocks(MAP_MODES.read_text(encoding="utf-8-sig"))

    assert "pp_wheat_productivity_map_value" in blocks["wheat"]
    assert "value = modifier:local_wheat_output_modifier" not in blocks["wheat"]

    bad = [
        good
        for good, block in blocks.items()
        if good != "wheat" and "pp_wheat_productivity_map_value" in block
    ]
    assert not bad


def test_non_wheat_output_map_modes_keep_generic_modifier_ramp() -> None:
    blocks = _map_mode_blocks(MAP_MODES.read_text(encoding="utf-8-sig"))

    bad: list[str] = []
    for good, block in blocks.items():
        if good == "wheat":
            continue
        if f"value = modifier:local_{good}_output_modifier" not in block:
            bad.append(f"{good}: missing direct modifier value")
        if "add = @factor_add" not in block:
            bad.append(f"{good}: missing generic factor add")
        if "divide = @factor_divide" not in block:
            bad.append(f"{good}: missing generic factor divide")
        if "secondary_map_color" in block:
            bad.append(f"{good}: unexpected secondary map color")

    assert not bad


def test_wheat_output_map_mode_has_multi_stop_colors_and_raw_material_stripes() -> None:
    block = _map_mode_blocks(MAP_MODES.read_text(encoding="utf-8-sig"))["wheat"]

    assert len(re.findall(r"rgb \{", block)) >= 34
    assert block.count("legend_key =") >= 13
    assert block.count("lerp = {") >= 10
    assert "secondary_map_color = {" in block
    assert "raw_material = goods:wheat" in block
    assert "MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER_WHEAT_LOCATION" in block


def test_wheat_output_map_mode_separates_mid_and_high_positive_productivity() -> None:
    block = _map_mode_blocks(MAP_MODES.read_text(encoding="utf-8-sig"))["wheat"]

    assert "pp_wheat_productivity_map_value < 0.75" in block
    assert "pp_wheat_productivity_map_value < 1.00" in block
    assert "pp_wheat_productivity_map_value < 1.50" in block
    assert "pp_wheat_productivity_map_value < 2.00" in block
    assert "rgb { 112 192 119 }" in block
    assert "rgb { 45 138 64 }" in block
    assert "rgb { 0 50 20 }" in block
    assert "MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER_STRONG" in block
    assert "MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER_VERY_STRONG" in block
    assert "MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER_EXCELLENT" in block
    assert "MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER_EXCEPTIONAL" in block


def test_wheat_output_map_mode_shades_inside_each_productivity_bucket() -> None:
    block = _map_mode_blocks(MAP_MODES.read_text(encoding="utf-8-sig"))["wheat"]

    assert "min_color = rgb { 139 204 135 }" in block
    assert "max_color = rgb { 90 174 97 }" in block
    assert "subtract = 0.50" in block
    assert "divide = 0.25" in block
    assert "min_color = rgb { 20 110 50 }" in block
    assert "max_color = rgb { 8 86 35 }" in block
    assert "subtract = 1.00" in block
    assert "divide = 0.50" in block
    assert "max = 1" in block
    assert "min = 0" in block


def test_wheat_output_map_mode_clamps_extreme_productivity_without_gradient() -> None:
    block = _map_mode_blocks(MAP_MODES.read_text(encoding="utf-8-sig"))["wheat"]

    assert re.search(
        r"limit = \{ pp_wheat_productivity_map_value <= -1\.00 \}\s+value = rgb \{ 64 0 75 \}",
        block,
    )
    assert re.search(r"else = \{\s+value = rgb \{ 0 50 20 \}", block)


def test_wheat_productivity_script_value_neutralizes_all_variable_harvests() -> None:
    script_values = SCRIPT_VALUES.read_text(encoding="utf-8-sig")
    harvest_values = _wheat_harvest_modifier_values()
    assert harvest_values

    found = set(re.findall(r"has_location_modifier = (pp_harvest_[a-z0-9_]+)", script_values))
    assert found == set(harvest_values)

    for modifier, value in harvest_values.items():
        operation = "add" if value.startswith("-") else "subtract"
        amount = value.removeprefix("-").removeprefix("+")
        pattern = (
            rf"has_location_modifier = {re.escape(modifier)} \}}\n"
            rf"\t\t{operation} = {re.escape(amount)}"
        )
        assert re.search(pattern, script_values), modifier


def test_wheat_map_mode_localization_explains_harvest_neutral_value_without_balance_numbers() -> None:
    loc = LOCALIZATION.read_text(encoding="utf-8-sig")
    wheat_keys = re.findall(
        r"^\s+MAPMODE_PP_LOCAL_WHEAT_OUTPUT_MODIFIER[^:]*: \"(.*)\"$",
        loc,
        flags=re.MULTILINE,
    )
    assert wheat_keys
    wheat_text = "\n".join(wheat_keys)

    assert "harvest-neutral wheat productivity" in wheat_text
    assert "Active variable harvest effects are excluded from the map color" in wheat_text
    assert "wheat is the raw material" in wheat_text

    text_without_format_precision = wheat_text.replace("|2", "")
    assert not re.search(r"[-+]?\d+(?:\.\d+)?%?", text_without_format_precision)


def test_local_output_map_mode_localization_uses_literal_newlines() -> None:
    loc = LOCALIZATION.read_text(encoding="utf-8-sig")
    block_match = re.search(
        r"  # Local output modifier map modes \(pp_local_output_modifier_map_modes\.txt\).*?"
        r"  # End generated local output modifier map modes",
        loc,
        flags=re.DOTALL,
    )
    assert block_match is not None
    block = block_match.group(0)
    bad_lines = [
        line
        for line in block.splitlines()
        if line.strip()
        and not line.startswith("  #")
        and not re.match(r'^\s+[A-Za-z0-9_]+:\s*".*"$', line)
    ]

    assert "\\n" in block
    assert "\nThis colors " not in block
    assert "\nAggregated from " not in block
    assert not bad_lines


def test_local_output_map_modes_have_icons_in_both_contexts() -> None:
    missing: list[str] = []
    for good in _raw_material_goods():
        filename = f"pp_local_{good}_output_modifier.dds"
        for icon_dir in ICON_DIRS:
            if not (icon_dir / filename).is_file():
                missing.append(str(icon_dir / filename))

    assert not missing


def test_local_output_map_modes_are_geography_index_two() -> None:
    blocks = _map_mode_blocks(MAP_MODES.read_text(encoding="utf-8-sig"))

    bad: list[str] = []
    for good, block in blocks.items():
        if not re.search(r"^\s*category\s*=\s*geography\s*$", block, flags=re.MULTILINE):
            bad.append(f"{good}: missing category = geography")
        if not re.search(r"^\s*index\s*=\s*2\s*$", block, flags=re.MULTILINE):
            bad.append(f"{good}: missing index = 2")

    assert not bad
