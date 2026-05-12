from __future__ import annotations

import json
from pathlib import Path
import re

import polars as pl
import yaml

from eu5gameparser.domain.eu5 import load_eu5_data
from eu5_mod_orchestrator.config import load_project_config


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_ROOT = ROOT / "blueprints" / "accepted"
MANIFEST_PATH = ROOT / "blueprints" / "buildings.manifest.yml"
LABELING_BASELINE = (
    ROOT.parent / "ProsperOrPerishLabelingPipeline" / "base_data" / "locations_with_raw_material.parquet"
)
ADVANCES_PATH = (
    ROOT
    / "mod"
    / "Prosper or Perish (Population Growth & Food Rework)"
    / "in_game"
    / "common"
    / "advances"
    / "pp_local_resource_productivity_advances.txt"
)
PROSPERITY_ADVANCES_PATH = (
    ROOT
    / "mod"
    / "Prosper or Perish (Population Growth & Food Rework)"
    / "in_game"
    / "common"
    / "advances"
    / "pp_prosperity_advances_adjustments.txt"
)
FISHING_ADVANCES_PATH = (
    ROOT
    / "mod"
    / "Prosper or Perish (Population Growth & Food Rework)"
    / "in_game"
    / "common"
    / "advances"
    / "pp_fishing_village.txt"
)
GAME_START_PATH = (
    ROOT
    / "mod"
    / "Prosper or Perish (Population Growth & Food Rework)"
    / "in_game"
    / "common"
    / "on_action"
    / "pp_game_start.txt"
)
BUILDING_TYPES_ROOT = (
    ROOT
    / "mod"
    / "Prosper or Perish (Population Growth & Food Rework)"
    / "in_game"
    / "common"
    / "building_types"
)
LOCALIZATION_ROOT = (
    ROOT
    / "mod"
    / "Prosper or Perish (Population Growth & Food Rework)"
    / "main_menu"
    / "localization"
    / "english"
)
LOCATION_MODIFIER_ADJUSTMENTS_PATH = (
    ROOT
    / "mod"
    / "Prosper or Perish (Population Growth & Food Rework)"
    / "main_menu"
    / "common"
    / "static_modifiers"
    / "pp_location_modifier_adjustments.txt"
)
RAW_MATERIAL_OUTPUT_TO_RGO_ADVANCES = {
    "arabia_felix": 0.10,
    "otm_lord_of_bungo": 0.10,
    "sba_multiple_shugo": 0.10,
    "cultivate_the_land": 0.05,
    "llama_michis": 0.10,
    "por_estimulate_rural_areas": 0.10,
    "hyanyak_system": 0.10,
    "wealth_of_mesoamerica": 0.10,
    "free_subjects": 0.10,
    "gra_modernized_economy": 0.20,
    "bur_rich_soil_of_burgundy": 0.20,
    "neapolitan_industrialization": 0.10,
    "produktplakatet": 0.10,
    "tre_trapezuntine_endurance": 0.10,
}

EXPECTED_CHAINS = {
    "alum_quarry": [
        ("alum_quarry", "advanced_mining"),
        ("alum_works", "green_vitriol"),
    ],
    "coal_mine": [
        ("coal_mine", None),
        ("coal_mine_improved", "coal_improvements_absolutism"),
        ("coal_mine_revolutions", "coal_improvements_revolutions"),
    ],
    "mercury_mine": [
        ("cinnabar_pit", None),
        ("quicksilver_retort", "pan_amalgamation_advance"),
    ],
    "copper_mine": [
        ("copper_mine", None),
        ("copper_mine_adit", "new_currency_demands"),
    ],
    "silver_mine": [
        ("silver_mine", None),
        ("silver_mine_improved", "saiger_process_discovery"),
    ],
    "lead_mine": [
        ("lead_mine", None),
        ("lead_mine_bole_smelting", "bole_smelting"),
        ("lead_mine_improved", "lead_ore_dressing"),
        ("lead_mine_cupola_smelting", "cupola_smelting"),
    ],
    "marble_quarry": [
        ("marble_quarry", None),
        ("marble_saw_yard", "renaissance_sculptures"),
    ],
    "tin_mine": [
        ("tin_streamworks", None),
        ("tin_stamping_mill", "new_currency_demands"),
    ],
    "gold_mine": [
        ("gold_diggings", None),
        ("gold_stamp_mill", "pan_amalgamation_advance"),
    ],
    "gem_mine": [
        ("gem_gravel_pit", None),
        ("gem_sluice", "foreign_mining_techniques"),
    ],
    "iron_mine": [
        ("iron_mine", None),
        ("iron_mine_improved", "efficient_mining"),
        ("iron_mine_deep", "slitting_mills"),
    ],
    "bog_iron_smelter": [
        ("bog_iron_smelter", None),
        ("bog_iron_smelter_blast_furnace", "blast_furnace"),
        ("bog_iron_smelter_coke_blast_furnace", "coke_blast_furnace"),
    ],
    "cookery": [
        ("cookery", None),
        ("victualling_yard", "food_advance_absolutism"),
    ],
}

DEACTIVATED_MINING_VILLAGE_BLUEPRINTS = {
    "buildings/mining_village.yml",
    "buildings/mining_village_blast_furnace.yml",
    "buildings/mining_village_slitting_mills.yml",
    "buildings/mining_village_coke_blast_furnace.yml",
    "buildings/mining_village_hot_blast_furnace.yml",
}
GAME_START_DIRECT_RGO_BUILDINGS = {
    "alum_quarry",
    "coal_mine",
    "copper_mine",
    "gem_gravel_pit",
    "gold_diggings",
    "iron_mine",
    "lead_mine",
    "marble_quarry",
    "cinnabar_pit",
    "salt_collector",
    "salt_mine",
    "inland_saltworks",
    "silver_mine",
    "saltpeter_beds",
    "tin_streamworks",
}
RAW_MATERIAL_BASE_PRODUCERS = {
    "horse_breeders": ("horses", "pp_horse_breeders_base_horses"),
    "sand_pit": ("sand", "pp_sand_pit_base_sand"),
    "stone_quarry": ("stone", "pp_stone_quarry_base_stone"),
    "incense_grove": ("incense", "pp_incense_grove_base_incense"),
    "fiber_crops_farm": ("fiber_crops", "pp_fiber_crops_farm_base_fiber_crops"),
    "ivory_hunting_camp": ("ivory", "pp_ivory_hunting_camp_base_ivory"),
    "salt_collector": ("salt", "pp_coastal_saltern_base_salt"),
    "salt_mine": ("salt", "pp_salt_mine_base_salt"),
    "inland_saltworks": ("salt", "pp_inland_saltworks_base_salt"),
    "saltpeter_beds": ("saltpeter", "pp_saltpeter_beds_base_saltpeter"),
    "vineyard_estate": ("wine", "pp_vineyard_estate_base_wine"),
    "cotton_plantation": ("cotton", "pp_cotton_plantation_base_cotton"),
    "sugar_plantation": ("sugar", "pp_sugar_plantation_base_sugar"),
    "tobacco_plantation": ("tobacco", "pp_tobacco_plantation_base_tobacco"),
}
RAW_PROCESSOR_EXCLUSIONS = {
    "perfumery": "incense",
    "winery": "wine",
    "winery_manufactory": "wine",
    "saltpeter_guild": "saltpeter",
    "saltpeter_workshop": "saltpeter",
    "putrefaction_works": "saltpeter",
    "putrefaction_mill": "saltpeter",
}
PM_PRECISION_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z][A-Za-z0-9_]*)\s*=\s*(?P<value>-?\d+\.\d{4,})\b"
)
PM_PRECISION_SKIP_KEYS = {"debug_max_profit"}

DEACTIVATED_BOG_IRON_BLUEPRINTS = {
    "buildings/bog_iron_smelter_slitting_mills.yml",
    "buildings/bog_iron_smelter_hot_blast_furnace.yml",
}
SALT_MINE_TOPOGRAPHIES = {"hills", "mountains", "plateau"}
SALT_MINE_MODIFIERS = {"sahara_salt_mines_base", "turda_salt_mines_base"}


def _load_blueprint(key: str) -> dict:
    with (BLUEPRINT_ROOT / "buildings" / f"{key}.yml").open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    assert isinstance(raw, dict)
    return raw


def _has_salt_mine_marker(row: dict) -> bool:
    modifier = str(row.get("modifier") or "")
    return row.get("topography") in SALT_MINE_TOPOGRAPHIES or any(
        marker in modifier for marker in SALT_MINE_MODIFIERS
    )


def _salt_location_families(row: dict) -> list[str]:
    raw_salt = row.get("raw_material") == "salt"
    coastal = row.get("is_coastal") is True
    salt_pan = row.get("topography") == "salt_pans"
    mine_marker = _has_salt_mine_marker(row)

    families: list[str] = []
    if raw_salt and coastal:
        families.append("coastal_saltern")
    if raw_salt and not coastal and mine_marker:
        families.append("salt_mine")
    if not coastal and (raw_salt or salt_pan) and not mine_marker:
        families.append("inland_saltworks")
    return families


def _advance_block(advance: str, text: str) -> str:
    match = re.search(
        rf"(?:(?:REPLACE|TRY_INJECT):)?{re.escape(advance)}\s*=\s*\{{(?P<body>.*?)\n\}}",
        text,
        flags=re.S,
    )
    assert match is not None, f"{advance} block missing"
    return match.group("body")


def _active_advancement_modifiers() -> dict[str, dict[str, float]]:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    rows = data.advancements.to_dicts()
    return {row["name"]: json.loads(row.get("modifiers") or "{}") for row in rows}


def _production_method_precision_offenders(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    depth = 0
    production_method_depths: list[int] = []
    offenders: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\bunique_production_methods\s*=\s*\{", line):
            production_method_depths.append(depth + line.count("{") - line.count("}"))
        if production_method_depths:
            match = PM_PRECISION_RE.match(line)
            if match and match.group("key") not in PM_PRECISION_SKIP_KEYS:
                relative = path.relative_to(ROOT)
                offenders.append(f"{relative}:{line_number}: {line.strip()}")
        depth += line.count("{") - line.count("}")
        while production_method_depths and depth < production_method_depths[-1]:
            production_method_depths.pop()

    return offenders


def _base_production_method_input_offenders(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    offenders: list[str] = []

    for index, line in enumerate(lines):
        match = re.match(
            r"\s*(?P<method>pp_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*_base_[A-Za-z0-9_]+)\s*=\s*\{\s*$",
            line,
        )
        if match is None:
            continue
        method = match.group("method")
        if method.endswith("_base_maintenance"):
            continue
        block_lines: list[str] = []
        depth = line.count("{") - line.count("}")
        for block_line in lines[index + 1 :]:
            depth += block_line.count("{") - block_line.count("}")
            if depth < 1:
                break
            block_lines.append(block_line)
        for block_line in block_lines:
            key_match = re.match(r"\s*(?P<key>[A-Za-z][A-Za-z0-9_]*)\s*=", block_line)
            if key_match and key_match.group("key") not in {"produced", "output", "category"}:
                relative = path.relative_to(ROOT)
                offenders.append(f"{relative}:{index + 1}: {method} has input {key_match.group('key')}")

    return offenders


def test_metal_building_upgrade_chains_are_explicit_and_unlockable() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])
    advances = "\n".join(
        (
            ADVANCES_PATH.read_text(encoding="utf-8"),
            PROSPERITY_ADVANCES_PATH.read_text(encoding="utf-8"),
        )
    )

    for family, chain in EXPECTED_CHAINS.items():
        for tier, (key, unlock_advance) in enumerate(chain):
            raw = _load_blueprint(key)

            assert f"buildings/{key}.yml" in enabled
            assert raw["tag"] == key
            assert raw["building"]["key"] == key

            upgrade_chain = raw.get("upgrade_chain")
            assert upgrade_chain == {
                "family": family,
                "tier": tier,
                "previous": chain[tier - 1][0] if tier > 0 else None,
                "next": chain[tier + 1][0] if tier + 1 < len(chain) else None,
                "unlock_advance": unlock_advance,
            }

            body = raw["building"]["body"]
            if tier == 0:
                assert "obsolete =" not in body
            else:
                previous = chain[tier - 1][0]
                assert re.search(rf"^\s*obsolete\s*=\s*{re.escape(previous)}\s*$", body, flags=re.M)
                assert "icon" in raw, f"{key} must provide its own icon"
                assert raw["icon"]["output_dds"] == f"{key}.dds"

            if unlock_advance is not None:
                block = _advance_block(unlock_advance, advances)
                assert re.search(rf"^\s*unlock_building\s*=\s*{re.escape(key)}\s*$", block, flags=re.M)


def test_ocean_fishery_upgrade_chain_is_explicit_and_globally_unlockable() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])
    advances = FISHING_ADVANCES_PATH.read_text(encoding="utf-8")

    chain = [
        ("ocean_fishery", None),
        ("offshore_fishery", "pp_herring_buss"),
    ]
    for tier, (key, unlock_advance) in enumerate(chain):
        raw = _load_blueprint(key)

        assert f"buildings/{key}.yml" in enabled
        assert raw["tag"] == key
        assert raw["building"]["key"] == key
        assert raw.get("upgrade_chain") == {
            "family": "ocean_fishery",
            "tier": tier,
            "previous": chain[tier - 1][0] if tier > 0 else None,
            "next": chain[tier + 1][0] if tier + 1 < len(chain) else None,
            "unlock_advance": unlock_advance,
        }

    offshore_body = _load_blueprint("offshore_fishery")["building"]["body"]
    assert re.search(r"^\s*obsolete\s*=\s*ocean_fishery\s*$", offshore_body, flags=re.M)
    assert re.search(r"location_potential\s*=\s*\{\s*is_coastal\s*=\s*yes\s*\}", offshore_body)

    herring_block = _advance_block("pp_herring_buss", advances)
    assert re.search(r"^\s*unlock_building\s*=\s*offshore_fishery\s*$", herring_block, flags=re.M)
    assert "potential =" not in herring_block

    distant_water_block = _advance_block("pp_distant_water_fishing", advances)
    assert re.search(
        r"^\s*unlock_production_method\s*=\s*pp_offshore_fishery_distant_water_schooners\s*$",
        distant_water_block,
        flags=re.M,
    )
    assert "potential =" not in distant_water_block

    steam_block = _advance_block("pp_steam_trawling", advances)
    assert re.search(
        r"^\s*unlock_production_method\s*=\s*pp_offshore_fishery_steam_trawlers\s*$",
        steam_block,
        flags=re.M,
    )
    assert "potential =" not in steam_block


def test_salt_production_families_are_explicit_and_unlockable() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])
    advances = ADVANCES_PATH.read_text(encoding="utf-8")

    assert "buildings/salt_collector.yml" not in enabled
    coastal = _load_blueprint("coastal_saltern")
    assert coastal["building"]["key"] == "salt_collector"
    assert coastal["building"]["mode"] == "REPLACE"

    expected_chains = {
        "salt_mine": [
            ("salt_mine", None),
            ("salt_mine_improved", "efficient_mining"),
        ],
        "inland_saltworks": [
            ("inland_saltworks", None),
            ("engineered_brine_saltworks", "pp_engineered_brine_saltworks"),
        ],
    }
    for family, chain in expected_chains.items():
        for tier, (key, unlock_advance) in enumerate(chain):
            raw = _load_blueprint(key)
            assert f"buildings/{key}.yml" in enabled
            assert raw["tag"] == key
            assert raw["building"]["key"] == key
            assert raw.get("upgrade_chain") == {
                "family": family,
                "tier": tier,
                "previous": chain[tier - 1][0] if tier > 0 else None,
                "next": chain[tier + 1][0] if tier + 1 < len(chain) else None,
                "unlock_advance": unlock_advance,
            }

            body = raw["building"]["body"]
            if tier == 0:
                assert "obsolete =" not in body
            else:
                previous = chain[tier - 1][0]
                assert re.search(rf"^\s*obsolete\s*=\s*{re.escape(previous)}\s*$", body, flags=re.M)
                assert raw["icon"]["output_dds"] == f"{key}.dds"

    efficient_mining = _advance_block("efficient_mining", advances)
    assert re.search(r"^\s*unlock_building\s*=\s*salt_mine_improved\s*$", efficient_mining, flags=re.M)

    engineered = _load_blueprint("engineered_brine_saltworks")
    advancements = engineered.get("advancements")
    assert isinstance(advancements, list)
    advancement = next(item for item in advancements if item["key"] == "pp_engineered_brine_saltworks")
    assert re.search(r"^\s*requires\s*=\s*manufactories_advance\s*$", advancement["body"], flags=re.M)
    assert re.search(r"^\s*unlock_building\s*=\s*engineered_brine_saltworks\s*$", advancement["body"], flags=re.M)

    coal = _advance_block("coal_improvements_absolutism", advances)
    assert re.search(
        r"^\s*unlock_production_method\s*=\s*pp_engineered_brine_saltworks_mineral_fired_pans\s*$",
        coal,
        flags=re.M,
    )


def test_salt_building_location_potentials_are_mutually_exclusive() -> None:
    bodies = {
        key: _load_blueprint(key)["building"]["body"]
        for key in (
            "coastal_saltern",
            "salt_mine",
            "salt_mine_improved",
            "inland_saltworks",
            "engineered_brine_saltworks",
        )
    }
    combined = "\n".join(bodies.values())

    assert "vegetation = desert" not in combined
    assert re.search(
        r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:salt\s*is_coastal\s*=\s*yes\s*\}",
        bodies["coastal_saltern"],
    )
    for key in ("salt_mine", "salt_mine_improved"):
        body = bodies[key]
        assert "raw_material = goods:salt" in body
        assert "NOT = { is_coastal = yes }" in body
        assert "topography = salt_pans" not in body
        for topography in SALT_MINE_TOPOGRAPHIES:
            assert f"topography = {topography}" in body
        for modifier in SALT_MINE_MODIFIERS:
            assert f"has_location_modifier = {modifier}" in body

    for key in ("inland_saltworks", "engineered_brine_saltworks"):
        body = bodies[key]
        assert "NOT = { is_coastal = yes }" in body
        assert "raw_material = goods:salt" in body
        assert "topography = salt_pans" in body
        for modifier in SALT_MINE_MODIFIERS:
            assert f"has_location_modifier = {modifier}" in body


def test_salt_location_split_matches_current_location_data() -> None:
    baseline = pl.read_parquet(LABELING_BASELINE).select(
        ["location_tag", "is_coastal", "topography", "vegetation", "raw_material", "modifier"]
    )
    salt_rows = baseline.filter(pl.col("raw_material") == "salt").to_dicts()

    counts = {"coastal_saltern": 0, "salt_mine": 0, "inland_saltworks": 0}
    offenders: list[str] = []
    for row in salt_rows:
        families = _salt_location_families(row)
        if len(families) != 1:
            offenders.append(f"{row['location_tag']}: {families}")
            continue
        counts[families[0]] += 1

    assert offenders == []
    assert counts == {"coastal_saltern": 233, "salt_mine": 93, "inland_saltworks": 86}

    generic_coastal = baseline.filter(
        (pl.col("raw_material").fill_null("") != "salt")
        & pl.col("is_coastal")
        & (pl.col("topography").fill_null("") != "salt_pans")
    ).head(500)
    generic_desert = baseline.filter(
        (pl.col("raw_material").fill_null("") != "salt")
        & (pl.col("vegetation") == "desert")
        & (pl.col("topography").fill_null("") != "salt_pans")
    ).head(500)
    assert all(_salt_location_families(row) == [] for row in generic_coastal.to_dicts())
    assert all(_salt_location_families(row) == [] for row in generic_desert.to_dicts())
    assert _salt_location_families(
        {
            "raw_material": None,
            "is_coastal": False,
            "topography": "salt_pans",
            "modifier": None,
        }
    ) == ["inland_saltworks"]


def test_clay_sand_and_stone_quarry_upgrade_chains_are_explicit_and_unlockable() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])
    expected_chains = {
        "clay_pit": [
            ("clay_pit", None),
            ("clay_washmill", "pp_clay_washmill"),
        ],
        "sand_pit": [
            ("sand_pit", None),
            ("sand_washery", "pp_sand_washery"),
        ],
        "stone_quarry": [
            ("stone_quarry", None),
            ("stone_quarry_improved", "pp_stone_quarry_improvements"),
        ],
    }

    for family, chain in expected_chains.items():
        for tier, (key, unlock_advance) in enumerate(chain):
            raw = _load_blueprint(key)

            assert f"buildings/{key}.yml" in enabled
            assert raw["tag"] == key
            assert raw["building"]["key"] == key
            assert raw.get("upgrade_chain") == {
                "family": family,
                "tier": tier,
                "previous": chain[tier - 1][0] if tier > 0 else None,
                "next": chain[tier + 1][0] if tier + 1 < len(chain) else None,
                "unlock_advance": unlock_advance,
            }

            body = raw["building"]["body"]
            if tier == 0:
                assert "obsolete =" not in body
            else:
                previous = chain[tier - 1][0]
                assert re.search(rf"^\s*obsolete\s*=\s*{re.escape(previous)}\s*$", body, flags=re.M)
                assert raw["icon"]["output_dds"] == f"{key}.dds"
                advancements = raw.get("advancements")
                assert isinstance(advancements, list)
                advancement = next(item for item in advancements if item["key"] == unlock_advance)
                assert re.search(rf"^\s*unlock_building\s*=\s*{re.escape(key)}\s*$", advancement["body"], flags=re.M)


def test_rural_food_building_upgrade_chains_are_explicit() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])
    assert _load_blueprint("fishing_village").get("upgrade_chain") is None
    expected_chains = {
        "sheep_farms": [
            ("sheep_farms", None),
            ("enclosed_sheep_walks", "pp_enclosed_sheep_walks"),
        ],
        "farming_village": [
            ("farming_village", None),
            ("model_farm", "pp_model_farm"),
        ],
        "forest_village": [
            ("forest_village", None),
            ("managed_forest_village", "pp_managed_forest_village"),
        ],
        "fruit_orchard": [
            ("fruit_orchard", None),
            ("pomological_orchard", "pp_pomological_orchard"),
        ],
    }

    for family, chain in expected_chains.items():
        for tier, (key, unlock_advance) in enumerate(chain):
            raw = _load_blueprint(key)

            assert f"buildings/{key}.yml" in enabled
            assert raw["tag"] == key
            assert raw["building"]["key"] == key
            assert raw.get("upgrade_chain") == {
                "family": family,
                "tier": tier,
                "previous": chain[tier - 1][0] if tier > 0 else None,
                "next": chain[tier + 1][0] if tier + 1 < len(chain) else None,
                "unlock_advance": unlock_advance,
            }

            body = raw["building"]["body"]
            if tier == 0:
                assert "obsolete =" not in body
            else:
                previous = chain[tier - 1][0]
                assert re.search(rf"^\s*obsolete\s*=\s*{re.escape(previous)}\s*$", body, flags=re.M)


def test_blueprint_upgrade_successors_load_after_obsolete_predecessors() -> None:
    config = load_project_config(ROOT / "constructor.toml")
    blueprints = {
        path.stem: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted((BLUEPRINT_ROOT / "buildings").glob("*.yml"))
    }
    generated_building_paths = {
        key: config.building_outputs.building_types.format(
            prefix=config.building_outputs.prefix,
            tag=raw.get("output_tag", raw["tag"]),
            key=raw["building"]["key"],
        )
        for key, raw in blueprints.items()
    }

    offenders: list[str] = []
    for key, raw in blueprints.items():
        upgrade_chain = raw.get("upgrade_chain")
        if not upgrade_chain or upgrade_chain.get("previous") is None:
            continue

        previous = upgrade_chain["previous"]
        if previous not in generated_building_paths:
            continue

        previous_path = generated_building_paths[previous]
        current_path = generated_building_paths[key]
        if previous_path >= current_path:
            offenders.append(f"{key}: {current_path} loads before {previous}: {previous_path}")

    assert not offenders


def test_enabled_blueprint_upgrade_successors_declare_obsolete_predecessors() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = {Path(entry).stem for entry in manifest["enabled"]}

    offenders: list[str] = []
    for key in sorted(enabled):
        raw = _load_blueprint(key)
        upgrade_chain = raw.get("upgrade_chain")
        if not upgrade_chain:
            continue

        body = raw["building"]["body"]
        previous = upgrade_chain.get("previous")
        obsolete_match = re.search(r"^\s*obsolete\s*=\s*(?P<previous>[A-Za-z0-9_]+)\s*$", body, flags=re.M)
        if previous is None:
            if obsolete_match:
                offenders.append(f"{key}: base tier declares obsolete = {obsolete_match.group('previous')}")
            continue

        if not re.search(rf"^\s*obsolete\s*=\s*{re.escape(previous)}\s*$", body, flags=re.M):
            offenders.append(f"{key}: missing obsolete = {previous}")

    assert not offenders


def test_manpower_building_blueprints_do_not_copy_invalid_owner_culture_gate() -> None:
    for key in ("armory", "training_fields", "barracks", "regimental_camp", "conscription_center"):
        body = _load_blueprint(key)["building"]["body"]

        assert "has_primary_or_accepted_culture" not in body
        assert "prev.dominant_culture" not in body
        assert "prev.location.dominant_culture" not in body


def test_game_start_never_places_offshore_fishery_directly_and_culls_invalid_locations() -> None:
    text = GAME_START_PATH.read_text(encoding="utf-8-sig")

    assert "construct_building = {\n\t\t\t\t\t\tbuilding_type = building_type:offshore_fishery" not in text
    assert re.search(
        r"building_type\s*=\s*building_type:offshore_fishery.*?NOT\s*=\s*\{\s*is_coastal\s*=\s*yes\s*\}.*?"
        r"building\s*=\s*building_type:offshore_fishery",
        text,
        flags=re.S,
    )


def test_game_start_restores_lake_adjacency_modifier() -> None:
    text = GAME_START_PATH.read_text(encoding="utf-8-sig")
    modifier_text = LOCATION_MODIFIER_ADJUSTMENTS_PATH.read_text(encoding="utf-8-sig")
    localization_text = (LOCALIZATION_ROOT / "pp_building_adjustments_l_english.yml").read_text(
        encoding="utf-8-sig"
    )

    assert re.search(r"on_game_start\s*=\s*\{.*?pp_apply_adjacent_to_lake_modifier", text, flags=re.S)
    assert "pp_apply_adjacent_to_lake_modifier = {" in text
    assert "limit = { is_adjacent_to_lake = yes }" in text
    assert "modifier = is_adjacent_to_lake" in text
    assert "has_location_modifier = is_adjacent_to_lake" in text
    assert "remove_location_modifier = is_adjacent_to_lake" in text
    assert "modifier = adjacent_to_lake" not in text
    assert "has_location_modifier = adjacent_to_lake" not in text
    assert "remove_location_modifier = adjacent_to_lake" not in text
    assert re.search(r"^is_adjacent_to_lake\s*=\s*\{.*?category\s*=\s*location", modifier_text, flags=re.S | re.M)
    assert "STATIC_MODIFIER_NAME_is_adjacent_to_lake" in localization_text


def test_game_start_direct_rgo_construction_checks_buildability() -> None:
    lines = GAME_START_PATH.read_text(encoding="utf-8-sig").splitlines()
    offenders: list[str] = []

    for index, line in enumerate(lines):
        match = re.match(r"\s*building_type\s*=\s*building_type:([A-Za-z0-9_]+)\s*$", line)
        if not match or match.group(1) not in GAME_START_DIRECT_RGO_BUILDINGS:
            continue
        if index == 0 or not re.match(r"\s*construct_building\s*=\s*\{\s*$", lines[index - 1]):
            continue
        building = match.group(1)
        guard = f"can_build_building = building_type:{building}"
        if guard not in "\n".join(lines[max(0, index - 24) : index]):
            offenders.append(f"{building} near line {index + 1}")

    assert not offenders


def test_building_production_method_quantities_use_at_most_three_decimals() -> None:
    offenders: list[str] = []
    paths = sorted((BLUEPRINT_ROOT / "buildings").glob("*.yml")) + sorted(BUILDING_TYPES_ROOT.glob("*.txt"))
    for path in paths:
        offenders.extend(_production_method_precision_offenders(path))

    assert not offenders


def test_base_production_methods_are_output_only() -> None:
    offenders: list[str] = []
    paths = sorted((BLUEPRINT_ROOT / "buildings").glob("*.yml")) + sorted(BUILDING_TYPES_ROOT.glob("*.txt"))
    for path in paths:
        offenders.extend(_base_production_method_input_offenders(path))

    assert not offenders


def test_target_raw_material_producers_have_no_input_base_methods() -> None:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    methods = {
        row["name"]: row
        for row in data.building_data.production_methods.select(
            ["name", "building", "produced", "input_goods"]
        ).to_dicts()
    }

    for building, (good, method) in RAW_MATERIAL_BASE_PRODUCERS.items():
        assert method in methods
        row = methods[method]
        assert row["building"] == building
        assert row["produced"] == good
        assert row["input_goods"] == []


def test_raw_processor_replacements_exclude_matching_raw_materials() -> None:
    for building, good in RAW_PROCESSOR_EXCLUSIONS.items():
        body = _load_blueprint(building)["building"]["body"]
        assert "location_potential = {" in body
        assert f"raw_material = goods:{good}" in body
        assert re.search(rf"NOT\s*=\s*\{{\s*raw_material\s*=\s*goods:{good}\s*\}}", body)


def test_game_start_routes_raw_saltpeter_to_niter_beds() -> None:
    text = GAME_START_PATH.read_text(encoding="utf-8-sig")
    saltpeter_windows = []
    for match in re.finditer(r"raw_material\s*=\s*goods:saltpeter", text):
        window = text[match.start() : match.start() + 600]
        if "construct_building" in window:
            saltpeter_windows.append(window)

    assert saltpeter_windows
    assert all("building_type = building_type:saltpeter_beds" in window for window in saltpeter_windows)
    assert all("building_type = building_type:saltpeter_guild" not in window for window in saltpeter_windows)
    assert "unlock_building = saltpeter_beds" in ADVANCES_PATH.read_text(encoding="utf-8-sig")


def test_mining_village_chain_is_deactivated() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])
    advances = ADVANCES_PATH.read_text(encoding="utf-8")

    assert DEACTIVATED_MINING_VILLAGE_BLUEPRINTS.isdisjoint(enabled)
    assert "unlock_building = mining_village" not in advances


def test_old_bog_iron_extra_tiers_are_deactivated() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])
    advances = ADVANCES_PATH.read_text(encoding="utf-8")

    assert DEACTIVATED_BOG_IRON_BLUEPRINTS.isdisjoint(enabled)
    assert "unlock_building = bog_iron_smelter_slitting_mills" not in advances
    assert "unlock_building = bog_iron_smelter_hot_blast_furnace" not in advances


def test_coal_mine_tiers_are_coal_deposit_only() -> None:
    for key in ("coal_mine", "coal_mine_improved", "coal_mine_revolutions"):
        body = _load_blueprint(key)["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:coal\s*\}", body)


def test_alum_quarry_tiers_are_alum_deposit_only() -> None:
    for key in ("alum_quarry", "alum_works"):
        body = _load_blueprint(key)["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:alum\s*\}", body)


def test_mercury_mine_tiers_are_mercury_deposit_only() -> None:
    for key in ("cinnabar_pit", "quicksilver_retort"):
        body = _load_blueprint(key)["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:mercury\s*\}", body)


def test_later_alum_modifier_advances_do_not_unlock_alum_buildings() -> None:
    advances = ADVANCES_PATH.read_text(encoding="utf-8")
    for advance in ("shared_products_procedures", "ostentatious_clothing"):
        assert f"REPLACE:{advance}" not in advances


def test_raw_material_output_advances_convert_to_rgo_size() -> None:
    modifiers_by_advance = _active_advancement_modifiers()
    positive_raw_material_output = {
        advance: modifiers["global_raw_material_output"]
        for advance, modifiers in modifiers_by_advance.items()
        if modifiers.get("global_raw_material_output", 0.0) > 0.0
    }

    assert positive_raw_material_output == {}

    for advance, expected_value in RAW_MATERIAL_OUTPUT_TO_RGO_ADVANCES.items():
        modifiers = modifiers_by_advance[advance]
        assert abs(modifiers.get("global_raw_material_output", 0.0)) < 0.000000001
        assert modifiers.get("global_max_rgo_size_modifier") == expected_value


def test_iron_mine_tiers_are_iron_deposit_only() -> None:
    for key in ("iron_mine", "iron_mine_improved", "iron_mine_deep"):
        body = _load_blueprint(key)["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:iron\s*\}", body)


def test_silver_mine_tiers_are_silver_deposit_only_and_have_unique_icons() -> None:
    for key in ("silver_mine", "silver_mine_improved"):
        raw = _load_blueprint(key)
        body = raw["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:silver\s*\}", body)
        assert raw["icon"]["output_dds"] == f"{key}.dds"


def test_lead_mine_tiers_are_lead_deposit_only_and_have_unique_icons() -> None:
    for key in ("lead_mine", "lead_mine_bole_smelting", "lead_mine_improved", "lead_mine_cupola_smelting"):
        raw = _load_blueprint(key)
        body = raw["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:lead\s*\}", body)
        assert raw["icon"]["output_dds"] == f"{key}.dds"


def test_lead_and_coal_late_modifier_advances_unlock_buildings_instead_of_global_output() -> None:
    advances = ADVANCES_PATH.read_text(encoding="utf-8")
    expected_unlocks = {
        "bole_smelting": "lead_mine_bole_smelting",
        "cupola_smelting": "lead_mine_cupola_smelting",
        "coal_improvements_revolutions": "coal_mine_revolutions",
    }

    for advance, building in expected_unlocks.items():
        block = _advance_block(advance, advances)
        assert re.search(rf"^\s*unlock_building\s*=\s*{building}\s*$", block, flags=re.M)
        assert not re.search(r"global_(lead|coal)_output_modifier\s*=", block)


def test_tin_mine_tiers_are_tin_deposit_only_and_have_unique_icons() -> None:
    for key in ("tin_streamworks", "tin_stamping_mill"):
        raw = _load_blueprint(key)
        body = raw["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:tin\s*\}", body)
        assert raw["icon"]["output_dds"] == f"{key}.dds"


def test_copper_mine_tiers_are_copper_deposit_only() -> None:
    for key in ("copper_mine", "copper_mine_adit"):
        body = _load_blueprint(key)["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:copper\s*\}", body)


def test_gold_mine_tiers_are_gold_deposit_only() -> None:
    for key in ("gold_diggings", "gold_stamp_mill"):
        body = _load_blueprint(key)["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:goods_gold\s*\}", body)


def test_gem_mine_tiers_are_gem_deposit_only_and_have_unique_icons() -> None:
    for key in ("gem_gravel_pit", "gem_sluice"):
        raw = _load_blueprint(key)
        body = raw["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:gems\s*\}", body)
        assert raw["icon"]["output_dds"] == f"{key}.dds"


def test_marble_quarry_tiers_are_marble_deposit_only_and_have_unique_icons() -> None:
    for key in ("marble_quarry", "marble_saw_yard"):
        raw = _load_blueprint(key)
        body = raw["building"]["body"]
        assert re.search(r"location_potential\s*=\s*\{\s*raw_material\s*=\s*goods:marble\s*\}", body)
        assert raw["icon"]["output_dds"] == f"{key}.dds"


def test_manifest_uses_dedicated_gold_mines_not_mining_village() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])

    assert "buildings/gold_diggings.yml" in enabled
    assert "buildings/gold_stamp_mill.yml" in enabled
    assert all("mining_village" not in entry for entry in enabled)


def test_manifest_uses_dedicated_tin_mines_not_mining_village() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    enabled = set(manifest["enabled"])

    assert "buildings/tin_streamworks.yml" in enabled
    assert "buildings/tin_stamping_mill.yml" in enabled
    assert all("mining_village" not in entry for entry in enabled)


def test_bog_iron_smelters_exclude_true_metal_and_coal_deposits() -> None:
    for key, _unlock_advance in EXPECTED_CHAINS["bog_iron_smelter"]:
        body = _load_blueprint(key)["building"]["body"]
        nor_match = re.search(r"NOR\s*=\s*\{(?P<body>.*?)\n\s*\}", body, flags=re.S)
        assert nor_match is not None
        nor_body = nor_match.group("body")
        assert re.search(r"raw_material\s*=\s*goods:iron", nor_body)
        assert re.search(r"raw_material\s*=\s*goods:coal", nor_body)
        assert re.search(r"raw_material\s*=\s*goods:copper", nor_body)
        assert re.search(r"raw_material\s*=\s*goods:gems", nor_body)
        assert re.search(r"raw_material\s*=\s*goods:mercury", nor_body)
        assert re.search(r"raw_material\s*=\s*goods:marble", nor_body)


def test_pan_amalgamation_unlocks_gold_and_mercury_upgrades() -> None:
    advances = ADVANCES_PATH.read_text(encoding="utf-8")
    block = _advance_block("pan_amalgamation_advance", advances)
    assert re.search(r"^\s*unlock_building\s*=\s*gold_stamp_mill\s*$", block, flags=re.M)
    assert re.search(r"^\s*unlock_building\s*=\s*quicksilver_retort\s*$", block, flags=re.M)


def test_smelting_advances_do_not_unlock_iron_mines() -> None:
    advances = ADVANCES_PATH.read_text(encoding="utf-8")
    for advance in ("blast_furnace", "coke_blast_furnace", "hot_blast_furnace"):
        block = _advance_block(advance, advances)
        assert "unlock_building = iron_mine" not in block
        assert "unlock_building = iron_mine_improved" not in block


def test_slitting_mills_advances_iron_methods_and_deep_mine() -> None:
    advances = ADVANCES_PATH.read_text(encoding="utf-8")
    block = _advance_block("slitting_mills", advances)

    assert re.search(r"^\s*unlock_building\s*=\s*iron_mine_deep\s*$", block, flags=re.M)
    assert re.search(
        r"^\s*unlock_production_method\s*=\s*pp_iron_mine_improved_slitting_dressed_ore\s*$",
        block,
        flags=re.M,
    )
    assert re.search(
        r"^\s*unlock_production_method\s*=\s*pp_bog_iron_smelter_blast_furnace_finery\s*$",
        block,
        flags=re.M,
    )
    assert "unlock_building = bog_iron_smelter" not in block


def test_hot_blast_unlocks_final_bog_iron_method_not_building() -> None:
    advances = ADVANCES_PATH.read_text(encoding="utf-8")
    block = _advance_block("hot_blast_furnace", advances)

    assert re.search(
        r"^\s*unlock_production_method\s*=\s*pp_bog_iron_smelter_hot_blast_refining_maintenance\s*$",
        block,
        flags=re.M,
    )
    assert "unlock_building = bog_iron_smelter_hot_blast_furnace" not in block


def test_charcoal_buildings_exclude_coal_deposits() -> None:
    for key in ("charcoal_maker", "improved_charcoal_maker"):
        body = _load_blueprint(key)["building"]["body"]
        assert re.search(
            r"location_potential\s*=\s*\{\s*NOT\s*=\s*\{\s*raw_material\s*=\s*goods:coal\s*\}\s*\}",
            body,
        )


def test_marble_output_localization_uses_dedicated_quarry_chain() -> None:
    text = (
        (LOCALIZATION_ROOT / "pp_goods_output_map_modes_l_english.yml").read_text(encoding="utf-8")
        + "\n"
        + (LOCALIZATION_ROOT / "pp_rgo_modifiers_l_english.yml").read_text(encoding="utf-8")
    )

    marble_lines = [line for line in text.splitlines() if "marble" in line.lower()]
    assert any("marble_quarry" in line for line in marble_lines)
    assert any("marble_saw_yard" in line for line in marble_lines)
    assert not any("mining_village" in line for line in marble_lines)
