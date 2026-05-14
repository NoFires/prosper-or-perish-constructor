from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from eu5gameparser.domain.eu5 import load_eu5_data


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod" / "Prosper or Perish (Population Growth & Food Rework)"
MAP_MODES = MOD_ROOT / "in_game" / "gfx" / "map" / "map_modes" / "pp_goods_output_map_modes_generated.txt"
SCRIPT_VALUES = MOD_ROOT / "in_game" / "common" / "script_values" / "pp_goods_output_map_modes_generated.txt"
LOCALIZATION = MOD_ROOT / "main_menu" / "localization" / "english" / "pp_goods_output_map_modes_l_english.yml"
ICON_DIR = MOD_ROOT / "in_game" / "gfx" / "interface" / "icons" / "map_modes"


def _all_goods() -> set[str]:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    return set(data.goods.select("name").to_series().to_list())


def _assert_exact_goods(label: str, found: list[str], expected: set[str]) -> None:
    counts = Counter(found)
    duplicates = sorted(good for good, count in counts.items() if count != 1)
    missing = sorted(expected - set(found))
    extra = sorted(set(found) - expected)

    assert not duplicates, f"{label} duplicates: {duplicates}"
    assert not missing, f"{label} missing goods: {missing}"
    assert not extra, f"{label} extra goods: {extra}"


def test_goods_output_map_modes_cover_all_goods_and_no_more() -> None:
    expected = _all_goods()

    map_mode_goods = re.findall(
        r"^pp_(.+?)_output\s*=\s*\{",
        MAP_MODES.read_text(encoding="utf-8-sig"),
        flags=re.MULTILINE,
    )
    script_value_goods = re.findall(
        r"^pp_(.+?)_output_raw\s*=\s*\{",
        SCRIPT_VALUES.read_text(encoding="utf-8-sig"),
        flags=re.MULTILINE,
    )
    localization_goods = re.findall(
        r"^\s*mapmode_pp_(.+?)_output_name:",
        LOCALIZATION.read_text(encoding="utf-8-sig"),
        flags=re.MULTILINE,
    )
    icon_goods = [
        match.group(1)
        for path in sorted(ICON_DIR.glob("pp_*_output.dds"))
        if (match := re.match(r"pp_(.+?)_output\.dds$", path.name))
    ]

    _assert_exact_goods("map modes", map_mode_goods, expected)
    _assert_exact_goods("script values", script_value_goods, expected)
    _assert_exact_goods("localization", localization_goods, expected)
    _assert_exact_goods("icons", icon_goods, expected)
