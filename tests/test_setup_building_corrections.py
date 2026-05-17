from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from scripts.generate_setup_building_corrections import (
    LOCATION_TEMPLATES_RELATIVE_PATH,
    SETUP_RELATIVE_PATH,
    TOWN_SETUPS_RELATIVE_PATH,
    SetupCorrectionError,
    build_correction_plan,
    expand_town_setup,
    parse_setup_errors,
    parse_town_setups,
    render_sanitized_town_setups,
    render_setup_override,
    write_generated_files,
)


def test_parse_setup_errors_groups_current_patterns() -> None:
    text = """
[20:01:00][building.cpp:123]: Location leuven has an invalid building granary
[20:01:01][building.cpp:456]: farming_village in London (london) is above max level! Current level is 2 (Max is 0)
"""

    errors = parse_setup_errors(text)

    assert [(error.kind, error.location, error.building) for error in errors] == [
        ("invalid", "leuven", "granary"),
        ("above_max", "london", "farming_village"),
    ]
    assert errors[1].current_level == 2
    assert errors[1].max_level == 0


def test_expand_town_setup_copy_from_adds_parent_levels() -> None:
    definitions = parse_town_setups(
        """
base_town = {
    granary = 1
    marketplace = 1
}
lowlands_town = {
    copy_from = base_town
    marketplace = 1
    cloth_guild = 2
}
"""
    )

    assert expand_town_setup("lowlands_town", definitions) == {
        "granary": 1,
        "marketplace": 2,
        "cloth_guild": 2,
    }


def test_generated_setup_sanitizes_direct_town_and_implicit_startup_sources() -> None:
    setup_text = """
locations={
    leuven = { rank = town town_setup = lowlands_town }
    london = { rank = city town_setup = british_town }
    lindi = { rank = rural_settlement town_setup = kilwan_merchant_settlement }
}

building_manager = {
    farming_village = { tag = ENG level = 2 location = london }
    fruit_orchard = { tag = CHI level = 4 location = zigui }
    marketplace = { tag = ENG level = 1 location = london }
}
"""
    town_setups_text = """
base_town = {
    granary = 1
    marketplace = 1
}
lowlands_town = {
    copy_from = base_town
    cloth_guild = 2
}
british_town = {
    marketplace = 1
    granary = 1
}
kilwan_merchant_settlement = {
    market_village = 3
    charcoal_maker = 1
}
"""
    location_templates_text = """
hunfeld = { topography = hills vegetation = forest climate = continental raw_material = beeswax }
"""
    log_text = """
[20:01:00][building.cpp:123]: Location leuven has an invalid building granary
[20:01:01][building.cpp:456]: farming_village in London (london) is above max level! Current level is 2 (Max is 0)
[20:01:02][building.cpp:456]: market_village in Lindi (lindi) is above max level! Current level is 3 (Max is 2)
[20:01:03][building.cpp:123]: Location hunfeld has an invalid building farming_village
[20:01:04][building.cpp:456]: fruit_orchard in Zigui (zigui) is above max level! Current level is 4 (Max is 3)
"""

    plan = build_correction_plan(
        setup_text=setup_text,
        town_setups_text=town_setups_text,
        location_templates_text=location_templates_text,
        log_text=log_text,
    )
    setup_output = render_setup_override(plan, source_label="error.log")
    town_output = render_sanitized_town_setups(plan, source_label="error.log")
    combined = setup_output + town_output

    assert not plan.unresolved
    assert plan.implicit_startup_corrections == 1
    assert plan.direct_clamped_count == 1
    assert "farming_village = { tag = ENG" not in setup_output
    assert "fruit_orchard = { tag = CHI level = 3 location = zigui }" in setup_output
    assert "marketplace = { tag = ENG level = 1 location = london }" in setup_output
    assert "hunfeld = { town_setup = pp_setup_sanitized_hunfeld }" in setup_output
    assert _block(town_output, "pp_setup_sanitized_leuven") == {
        "marketplace = 1",
        "cloth_guild = 2",
    }
    assert _block(town_output, "pp_setup_sanitized_lindi") == {
        "market_village = 2",
        "charcoal_maker = 1",
    }
    assert "farming_village" not in _block_text(town_output, "pp_setup_sanitized_hunfeld")
    assert "on_action" not in combined
    assert "on_game_start" not in combined
    assert "construct_building" not in combined
    assert "scripted_effect" not in combined


def test_direct_building_manager_filter_only_clamps_matching_direct_entries() -> None:
    setup_text = """
locations={
    london = { rank = city town_setup = british_town }
    lindi = { rank = rural_settlement town_setup = kilwan_merchant_settlement }
}

building_manager = {
    fruit_orchard = { tag = CHI level = 4 location = zigui }
    marketplace = { tag = ENG level = 1 location = london }
}
"""
    town_setups_text = """
british_town = {
    marketplace = 1
}
kilwan_merchant_settlement = {
    market_village = 3
}
"""
    location_templates_text = """
hunfeld = { topography = hills vegetation = forest climate = continental raw_material = beeswax }
"""
    log_text = """
[20:01:01][building.cpp:456]: market_village in Lindi (lindi) is above max level! Current level is 3 (Max is 2)
[20:01:02][building.cpp:456]: fruit_orchard in Zigui (zigui) is above max level! Current level is 4 (Max is 3)
[20:01:03][building.cpp:456]: fruit_orchard in Hunfeld (hunfeld) is above max level! Current level is 1 (Max is 0)
"""

    plan = build_correction_plan(
        setup_text=setup_text,
        town_setups_text=town_setups_text,
        location_templates_text=location_templates_text,
        log_text=log_text,
        buildings=("fruit_orchard",),
        direct_building_manager_only=True,
    )
    setup_output = render_setup_override(plan, source_label="error.log")

    assert not plan.unresolved
    assert not plan.sanitized_town_setups
    assert plan.implicit_startup_corrections == 0
    assert plan.direct_clamped_count == 1
    assert "fruit_orchard = { tag = CHI level = 3 location = zigui }" in setup_output
    assert "market_village = 3" not in setup_output


def test_existing_generated_override_detects_vanilla_setup_drift(tmp_path: Path) -> None:
    setup_text = "locations={\n}\n\nbuilding_manager = {\n}\n"
    town_setups_text = ""
    plan = build_correction_plan(
        setup_text=setup_text,
        town_setups_text=town_setups_text,
        location_templates_text="",
        log_text="",
    )
    output = tmp_path / SETUP_RELATIVE_PATH
    output.parent.mkdir(parents=True)
    output.write_text(
        "# Generated by scripts/generate_setup_building_corrections.py; do not edit by hand.\n"
        f"# Vanilla setup sha256: {'0' * 64}\n",
        encoding="utf-8",
    )

    with pytest.raises(SetupCorrectionError, match="upstream setup drift"):
        write_generated_files(plan=plan, mod_root=tmp_path, source_label="error.log")


def test_current_error_log_counts_resolve_to_setup_sources() -> None:
    vanilla_root = Path("/mnt/c/Games/steamapps/common/Europa Universalis V/game")
    log_path = Path(
        "/mnt/c/Users/Anwender/Documents/Paradox Interactive/Europa Universalis V/logs/error.log"
    )
    required_paths = [
        vanilla_root / SETUP_RELATIVE_PATH,
        vanilla_root / TOWN_SETUPS_RELATIVE_PATH,
        vanilla_root / LOCATION_TEMPLATES_RELATIVE_PATH,
        log_path,
    ]
    if not all(path.exists() for path in required_paths):
        pytest.skip("local EU5 install or current error.log is not available")

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    counts = Counter(error.kind for error in parse_setup_errors(log_text))
    if not counts:
        pytest.skip("local error.log has no setup building errors")

    plan = build_correction_plan(
        setup_text=(vanilla_root / SETUP_RELATIVE_PATH).read_text(encoding="utf-8-sig"),
        town_setups_text=(vanilla_root / TOWN_SETUPS_RELATIVE_PATH).read_text(
            encoding="utf-8-sig"
        ),
        location_templates_text=(vanilla_root / LOCATION_TEMPLATES_RELATIVE_PATH).read_text(
            encoding="utf-8-sig"
        ),
        log_text=log_text,
    )

    assert not plan.unresolved
    assert plan.parsed_error_count == sum(counts.values())
    assert plan.invalid_error_count == counts["invalid"]
    assert plan.above_max_error_count == counts["above_max"]


def _block(text: str, key: str) -> set[str]:
    return {
        line.strip()
        for line in _block_text(text, key).splitlines()
        if line.strip() and not line.strip().endswith("{") and line.strip() != "}"
    }


def _block_text(text: str, key: str) -> str:
    start = text.index(f"{key} = {{")
    next_start = text.find("\npp_setup_sanitized_", start + 1)
    if next_start == -1:
        return text[start:]
    return text[start:next_start]
