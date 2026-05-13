from pathlib import Path

from eu5_building_pipeline.template import load_template
from eu5gameparser.clausewitz.parser import parse_file, parse_text
from eu5gameparser.clausewitz.syntax import CList
from eu5gameparser.domain.availability import annotate_building_data_availability
from eu5gameparser.domain.eu5 import load_eu5_data
from eu5gameparser.load_order import LoadOrderConfig
from eu5_mod_orchestrator.blueprints import accepted_blueprint_files, validate_blueprint_file
from eu5_mod_orchestrator.config import load_project_config
from mod_injector.config import load_mod_injector_config
from prosper_or_perish_constructor import cli


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod" / "Prosper or Perish (Population Growth & Food Rework)"
ESTATE_PRIVILEGE_ADJUSTMENTS = (
    MOD_ROOT / "in_game" / "common" / "estate_privileges" / "pp_estate_privilege_adjustments.txt"
)
GOVERNMENT_REFORM_ADJUSTMENTS = (
    MOD_ROOT / "in_game" / "common" / "government_reforms" / "pp_government_reform_adjustments.txt"
)
ESTATE_ADJUSTMENTS = MOD_ROOT / "in_game" / "common" / "estates" / "pp_estate_adjustments.txt"
GOODS_DEMAND = MOD_ROOT / "in_game" / "common" / "goods_demand" / "pp_new_goods_demands.txt"
LAW_ADJUSTMENTS = MOD_ROOT / "in_game" / "common" / "laws" / "pp_law_adjustments.txt"
BUILDING_CAPS = MOD_ROOT / "in_game" / "common" / "script_values" / "pp_building_caps.txt"
BUILDING_CAPACITY_VALUES = (
    MOD_ROOT / "in_game" / "common" / "script_values" / "pp_building_capacity_values.txt"
)
AQUEDUCT_SYSTEM = MOD_ROOT / "in_game" / "common" / "building_types" / "pp_aqueduct_system.txt"
GAME_START = MOD_ROOT / "in_game" / "common" / "on_action" / "pp_game_start.txt"
BUILDING_CULLING = MOD_ROOT / "in_game" / "common" / "on_action" / "pp_building_culling.txt"
LOCATION_RANKS = MOD_ROOT / "in_game" / "common" / "location_ranks" / "pp_location_rank_adjustments.txt"
FOOD_MAP_MODES = MOD_ROOT / "in_game" / "gfx" / "map" / "map_modes" / "pp_food_map_modes.txt"
PRICE_ROOT = MOD_ROOT / "in_game" / "common" / "prices"
MODIFIER_TYPE_DEFINITIONS = MOD_ROOT / "main_menu" / "common" / "modifier_type_definitions"
MODIFIER_ICONS = MOD_ROOT / "main_menu" / "common" / "modifier_icons"
GAME_CONCEPT_ROOT = MOD_ROOT / "main_menu" / "common" / "game_concepts"
LOCALIZATION_ROOT = MOD_ROOT / "main_menu" / "localization" / "english"
CAPACITY_PRECALC = MOD_ROOT / "in_game" / "common" / "scripted_effects" / "pp_capacity_precalc.txt"
RGO_STATIC_BONUSES = MOD_ROOT / "in_game" / "common" / "static_modifiers" / "pp_rgo_static_bonuses.txt"
BUILDING_BLUEPRINT_ROOT = ROOT / "blueprints" / "accepted" / "buildings"
FARMING_VILLAGE_BLUEPRINT = BUILDING_BLUEPRINT_ROOT / "farming_village.yml"
MODEL_FARM_BLUEPRINT = BUILDING_BLUEPRINT_ROOT / "model_farm.yml"
LAND_FARM_BUILDINGS = (
    "farming_village",
    "model_farm",
    "fruit_orchard",
    "pomological_orchard",
    "sheep_farms",
    "enclosed_sheep_walks",
    "horse_breeders",
    "elephant_kraal",
    "fiber_crops_farm",
    "cotton_plantation",
    "sugar_plantation",
    "tobacco_plantation",
    "dye_plantation",
    "chili_plantation",
    "clove_grove",
    "cocoa_grove",
    "coffee_grove",
    "incense_grove",
    "pepper_garden",
    "saffron_croft",
    "sericulture_farm",
    "simplers_grove",
    "tea_garden",
    "vineyard_estate",
)
LAND_FARM_BLUEPRINTS = tuple(BUILDING_BLUEPRINT_ROOT / f"{key}.yml" for key in LAND_FARM_BUILDINGS)
FISH_CAP_BUILDINGS = (
    "fishing_village",
    "ocean_fishery",
    "offshore_fishery",
)
FOREST_CAP_BUILDINGS = (
    "forest_village",
    "managed_forest_village",
    "lumber_mill",
    "lumber_mill_improved",
)
FISH_CAP_BLUEPRINTS = tuple(BUILDING_BLUEPRINT_ROOT / f"{key}.yml" for key in FISH_CAP_BUILDINGS)
FOREST_CAP_BLUEPRINTS = tuple(BUILDING_BLUEPRINT_ROOT / f"{key}.yml" for key in FOREST_CAP_BUILDINGS)
EXCLUDED_FARM_CAP_BUILDINGS = (
    "winery",
    "winery_manufactory",
    "perfumery",
    "cookery",
    "victualling_yard",
    "saltpeter_guild",
    "saltpeter_workshop",
    "putrefaction_mill",
    "putrefaction_works",
    "fishing_village",
    "ocean_fishery",
    "offshore_fishery",
    "pearl_fishery",
    "forest_village",
    "managed_forest_village",
    "lumber_mill",
    "lumber_mill_improved",
    "charcoal_maker",
    "improved_charcoal_maker",
    "ivory_hunting_camp",
    "coastal_saltern",
    "salt_mine",
    "salt_mine_improved",
    "inland_saltworks",
    "engineered_brine_saltworks",
    "saltpeter_beds",
    "sand_pit",
    "sand_washery",
    "stone_quarry",
)


def test_constructor_config_loads() -> None:
    config = load_project_config(ROOT / "constructor.toml")

    assert config.name == "Prosper or Perish Constructor"
    assert config.mod_root == ROOT / "mod" / "Prosper or Perish (Population Growth & Food Rework)"
    if (ROOT / "constructor.local.toml").exists():
        assert config.deploy_target is not None
    else:
        assert config.deploy_target is None
    assert config.accepted_blueprints_dir == ROOT / "blueprints" / "accepted"
    assert config.profile == "constructor"
    assert config.load_order_path == ROOT / "constructor.load_order.toml"
    assert config.building_outputs.prefix == "pp_"
    assert config.building_outputs.building_types == "in_game/common/building_types/zz_{prefix}{tag}.txt"
    assert config.building_artifact_dir == ROOT / "artifacts" / "data" / "buildings"
    assert config.savegame_artifact_dir == ROOT / "artifacts" / "data" / "savegame"
    assert config.graph_dir == ROOT / "graphs"
    assert config.labeling is not None
    assert config.labeling.enabled is True
    assert config.labeling.config_path == ROOT / "labeling_output_modifiers.yaml"
    assert config.labeling.modifier_prefix == "pp"
    assert config.labeling.generated_label == "Prosper or Perish"
    assert config.labeling.managed_write_mode == "mod_root"
    assert config.population_capacity is not None
    assert config.population_capacity.enabled is True
    assert config.population_capacity.config_path == ROOT / "population_capacity.toml"
    assert config.population_capacity.generated_label == "Prosper or Perish"
    assert config.population_capacity.managed_write_mode == "mod_root"
    assert config.blueprint_evaluation.raw_input_efficiency_per_good == 0.05
    assert config.blueprint_evaluation.profit_percent_min == -0.30
    assert config.blueprint_evaluation.profit_percent_max == 0.30
    assert config.blueprint_evaluation.base_output_per_1k_min == 0.07
    assert config.blueprint_evaluation.base_output_per_1k_max == 0.15
    assert config.blueprint_evaluation.throughput_gold_per_1k["laborers"] == 1.5
    assert config.blueprint_evaluation.age_throughput_growth == 0.10
    assert config.blueprint_evaluation.throughput_tolerance == 0.30
    assert config.blueprint_evaluation.amortization_months_min == 120.0
    assert config.blueprint_evaluation.amortization_months_max == 360.0
    assert config.blueprint_evaluation.employment_size_constants == {}


def test_accepted_blueprints_validate() -> None:
    for blueprint in accepted_blueprint_files(ROOT / "blueprints" / "accepted"):
        validate_blueprint_file(blueprint)


def test_farm_gross_capacity_uses_live_rgo_population_inputs_only() -> None:
    parsed = parse_file(BUILDING_CAPS)
    entries = {entry.key: entry.value for entry in parsed.entries}
    assert "farm_rgo_capacity_bonus" in entries
    assert "farm_gross_capacity" in entries
    assert "farm_max_level" in entries
    assert "farm_capacity_remaining" in entries
    assert "farm_capacity_available" in entries
    assert "land_farm_building_levels" in entries
    assert "non_farm_building_levels" in entries
    assert "farming_capacity" not in entries
    assert "farming_village_max_level" not in entries

    text = BUILDING_CAPS.read_text(encoding="utf-8-sig")
    bonus_block = _text_block_between(
        text,
        "farm_rgo_capacity_bonus = {",
        "\nfarm_gross_capacity = {",
    )
    block = _text_block_between(
        text,
        "farm_gross_capacity = {",
        "\nland_farm_building_levels = {",
    )

    required_bonus_snippets = (
        "limit = { has_variable = pp_farm_base_capacity }",
        'desc = "BUILDING_LEVEL_RGO_SIZE_FARMING"\n\t\t\tvalue = var:pp_farm_base_capacity\n\t\t\tmultiply = max_rgo_workers\n\t\t\tmultiply = 0.125',
    )
    missing_bonus = [snippet for snippet in required_bonus_snippets if snippet not in bonus_block]
    assert not missing_bonus

    required_snippets = (
        'desc = "BUILDING_LEVEL_BASE_FARM_RGO"\n\t\tif = {\n\t\t\tlimit = { has_variable = pp_farm_base_capacity }\n\t\t\tvalue = var:pp_farm_base_capacity',
        "add = farm_rgo_capacity_bonus",
        'desc = "BUILDING_LEVEL_POPULATION_CAPACITY_FARMING"\n\t\tvalue = modifier:local_population_capacity\n\t\tmultiply = 0.08',
        'desc = "BUILDING_LEVEL_FROM_LOCATION_RANK_FARMING"\n\t\tvalue = modifier:farm_rank_capacity_modifier',
        'desc = "BUILDING_LEVEL_FARM_CAPACITY_IMPROVEMENTS"\n\t\tvalue = modifier:farm_max_level_modifier',
    )
    missing = [snippet for snippet in required_snippets if snippet not in block]
    assert not missing

    forbidden_snippets = (
        "total_building_levels",
        "modifier:farm_space_used",
        "location_building_level(",
        "farm_capacity_remaining",
        "pp_farming_village_fixed_env_bonus",
        "pp_farming_village_capacity_value",
        "BUILDING_LEVEL_FROM_ENVIRONMENT_FARMING",
        "value = development",
        "value = population",
        "value = max_rgo_workers\n\t\tmultiply = 0.75",
    )
    offenders = [snippet for snippet in forbidden_snippets if snippet in block + bonus_block]
    assert not offenders


def test_farm_capacity_remaining_tracks_urbanization_and_farm_space() -> None:
    text = BUILDING_CAPS.read_text(encoding="utf-8-sig")

    non_farm_block = _text_block_between(
        text,
        "non_farm_building_levels = {",
        "\nfarm_capacity_remaining = {",
    )
    remaining_block = _text_block_between(
        text,
        "farm_capacity_remaining = {",
        "\nfarm_max_level = {",
    )
    max_level_block = _text_block_between(
        text,
        "farm_max_level = {",
        "\nfarm_capacity_available = {",
    )
    available_block = _text_block_between(
        text,
        "farm_capacity_available = {",
        "\nfish_building_levels = {",
    )

    assert "add = total_building_levels" in non_farm_block
    assert "value = land_farm_building_levels\n\t\tmultiply = -1" in non_farm_block
    assert "min = 0" in non_farm_block

    required_remaining = (
        "add = farm_gross_capacity",
        'desc = "BUILDING_LEVEL_AVAILABLE_SPACE"\n\t\tvalue = non_farm_building_levels\n\t\tmultiply = -0.05',
        'desc = "BUILDING_LEVEL_FARM_SPACE_USED"\n\t\tvalue = land_farm_building_levels\n\t\tmultiply = -1',
    )
    missing = [snippet for snippet in required_remaining if snippet not in remaining_block]
    assert not missing
    assert "location_building_level(" not in remaining_block
    assert "modifier:farm_space_used" not in remaining_block
    assert "add = farm_capacity_remaining" in max_level_block
    assert "min = 0" in max_level_block
    assert "add = farm_max_level" in available_block


def test_granary_cap_and_storage_are_startup_compatible() -> None:
    text = BUILDING_CAPS.read_text(encoding="utf-8-sig")
    block = text.split("pp_granary_cap = {", 1)[1]

    required_snippets = (
        'desc = "BUILDING_LEVEL_BASE"\n\t\tvalue = 2.25',
        'desc = "BUILDING_LEVEL_DEVELOPMENT"\n\t\tvalue = development\n\t\tmultiply = 0.05',
        'desc = "BUILDING_LEVEL_POPULATION"\n\t\tvalue = population\n\t\tmultiply = 0.01',
        'location_rank = location_rank:town\n\t\t}\n\t\tadd = {\n\t\t\tdesc = "BUILDING_LEVEL_IS_TOWN"\n\t\t\tvalue = 0.5',
        'location_rank = location_rank:city\n\t\t}\n\t\tadd = {\n\t\t\tdesc = "BUILDING_LEVEL_IS_CITY"\n\t\t\tvalue = 1.0',
        "max = 6",
    )
    missing = [snippet for snippet in required_snippets if snippet not in block]
    assert not missing

    granary_text = (BUILDING_BLUEPRINT_ROOT / "granary.yml").read_text(encoding="utf-8-sig")
    assert "local_food_capacity = 1000" in granary_text
    assert "local_food_capacity = 1200" not in granary_text


def test_land_farm_building_levels_count_all_shared_pool_buildings() -> None:
    text = BUILDING_CAPS.read_text(encoding="utf-8-sig")
    parsed = parse_file(BUILDING_CAPS)
    entries = {entry.key: entry.value for entry in parsed.entries}
    assert not any(key.endswith("_farm_max_level") for key in entries)

    block = _text_block_between(
        text,
        "land_farm_building_levels = {",
        "\nnon_farm_building_levels = {",
    )
    for building in LAND_FARM_BUILDINGS:
        assert f'value = "location_building_level(building_type:{building})"' in block


def test_farm_space_used_modifier_path_is_removed() -> None:
    roots = (
        BUILDING_BLUEPRINT_ROOT,
        MOD_ROOT / "in_game" / "common" / "building_types",
        MODIFIER_TYPE_DEFINITIONS,
        MODIFIER_ICONS,
        LOCALIZATION_ROOT,
    )
    offenders: list[str] = []

    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".txt", ".yml"}:
                continue
            if "farm_space_used" in path.read_text(encoding="utf-8-sig", errors="replace"):
                offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_farming_capacity_old_fixed_environment_path_is_removed() -> None:
    tokens = (
        "pp_farming_village_fixed_env_bonus",
        "pp_farming_village_capacity_value",
        "pp_farming_village_global_",
    )
    roots = (
        MOD_ROOT / "in_game" / "common" / "script_values",
        MOD_ROOT / "in_game" / "common" / "on_action",
        MOD_ROOT / "in_game" / "common" / "scripted_effects",
        MOD_ROOT / "in_game" / "common" / "customizable_localization",
        MOD_ROOT / "in_game" / "common" / "building_types",
        MOD_ROOT / "in_game" / "gfx" / "map" / "map_modes",
        LOCALIZATION_ROOT,
        ROOT / "blueprints" / "accepted" / "buildings",
    )
    offenders: list[str] = []

    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".txt", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            for token in tokens:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {token}")

    assert offenders == []


def test_obsolete_fruit_sheep_capacity_systems_are_removed() -> None:
    tokens = (
        "fruit_orchard_max_level",
        "sheep_farms_max_level",
        "farming_village_max_level_modifier",
        "pp_fruit_orchard_fixed_env_bonus",
        "pp_sheep_farms_fixed_env_bonus",
        "pp_fruit_orchard_global_",
        "pp_sheep_farms_global_",
        "pp_fruit_orchard_capacity_value",
        "pp_sheep_farms_capacity_value",
        "MAPMODE_PP_FRUIT_ORCHARD_CAPACITY",
        "MAPMODE_PP_SHEEP_FARMS_CAPACITY",
        "mapmode_pp_fruit_orchard_capacity_name",
        "mapmode_pp_sheep_farms_capacity_name",
    )
    roots = (
        MOD_ROOT / "in_game" / "common" / "script_values",
        MOD_ROOT / "in_game" / "common" / "on_action",
        MOD_ROOT / "in_game" / "common" / "scripted_effects",
        MOD_ROOT / "in_game" / "common" / "customizable_localization",
        MOD_ROOT / "in_game" / "common" / "building_types",
        MOD_ROOT / "in_game" / "gfx" / "map" / "map_modes",
        MODIFIER_TYPE_DEFINITIONS,
        MODIFIER_ICONS,
        LOCALIZATION_ROOT,
        BUILDING_BLUEPRINT_ROOT,
    )
    offenders: list[str] = []

    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".txt", ".yml", ".md"}:
                continue
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            for token in tokens:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {token}")

    obsolete_icons = (
        MOD_ROOT / "main_menu" / "gfx" / "interface" / "icons" / "map_modes" / "pp_fruit_orchard_capacity.dds",
        MOD_ROOT / "main_menu" / "gfx" / "interface" / "icons" / "map_modes" / "pp_sheep_farms_capacity.dds",
        MOD_ROOT
        / "main_menu"
        / "gfx"
        / "interface"
        / "icons"
        / "modifier_types"
        / "fruit_orchard_max_level_modifier.dds",
        MOD_ROOT
        / "main_menu"
        / "gfx"
        / "interface"
        / "icons"
        / "modifier_types"
        / "sheep_farms_max_level_modifier.dds",
        MOD_ROOT
        / "main_menu"
        / "gfx"
        / "interface"
        / "icons"
        / "modifier_types"
        / "farming_village_max_level_modifier.dds",
    )
    offenders.extend(str(path.relative_to(ROOT)) for path in obsolete_icons if path.exists())

    farm_icon = (
        MOD_ROOT
        / "main_menu"
        / "gfx"
        / "interface"
        / "icons"
        / "modifier_types"
        / "farm_max_level_modifier.dds"
    )
    if not farm_icon.exists():
        offenders.append(f"{farm_icon.relative_to(ROOT)} missing")

    assert offenders == []


def test_fish_and_forest_fixed_environment_paths_are_removed() -> None:
    cap_values = BUILDING_CAPACITY_VALUES.read_text(encoding="utf-8-sig")
    cap_text = BUILDING_CAPS.read_text(encoding="utf-8-sig")
    game_start = GAME_START.read_text(encoding="utf-8-sig")
    map_text = FOOD_MAP_MODES.read_text(encoding="utf-8-sig")
    localization_text = (LOCALIZATION_ROOT / "pp_building_adjustments_l_english.yml").read_text(
        encoding="utf-8-sig"
    )

    required = (
        "pp_farm_base_capacity_value",
        "pp_fish_base_capacity_value",
        "pp_forest_base_capacity_value",
        "fish_gross_capacity",
        "fish_capacity_remaining",
        "fish_capacity_available",
        "fish_max_level",
        "forest_gross_capacity",
        "forest_capacity_remaining",
        "forest_capacity_available",
        "forest_max_level",
    )
    combined = "\n".join((cap_values, cap_text, game_start, map_text, localization_text))
    missing = [token for token in required if token not in combined]
    assert not missing

    obsolete = (
        "pp_fishing_village_fixed_env_bonus",
        "pp_forest_village_fixed_env_bonus",
        "pp_fishing_village_capacity_value",
        "pp_forest_village_capacity_value",
        "pp_fishing_village_global_",
        "pp_forest_village_global_",
        "fishing_village_max_level",
        "forest_village_max_level",
        "fishing_village_max_level_modifier",
        "forest_village_max_level_modifier",
    )
    offenders = [token for token in obsolete if token in combined]
    assert offenders == []


def test_fish_capacity_uses_water_rgo_size_and_used_fish_levels_only() -> None:
    text = BUILDING_CAPS.read_text(encoding="utf-8-sig")
    cap_values = BUILDING_CAPACITY_VALUES.read_text(encoding="utf-8-sig")
    entries = {entry.key for entry in parse_file(BUILDING_CAPS).entries}
    assert "fish_rgo_capacity_bonus" in entries

    base_block = _text_block_between(
        cap_values,
        "pp_fish_base_capacity_value = {",
        "\npp_forest_base_capacity_value = {",
    )
    bonus_block = _text_block_between(
        text,
        "fish_rgo_capacity_bonus = {",
        "\nfish_gross_capacity = {",
    )
    gross_block = _text_block_between(
        text,
        "fish_gross_capacity = {",
        "\nfish_capacity_remaining = {",
    )
    remaining_block = _text_block_between(
        text,
        "fish_capacity_remaining = {",
        "\nfish_max_level = {",
    )

    for snippet in (
        "raw_material = goods:fish",
        "add = 3.00",
        "is_coastal = yes",
        "add = 4.50",
        "is_adjacent_to_lake = yes",
        "has_river = yes",
        "add = 2.25",
        "topography = wetlands",
        "add = 1.50",
    ):
        assert snippet in base_block

    assert "limit = { has_variable = pp_fish_base_capacity }" in bonus_block
    assert (
        'desc = "BUILDING_LEVEL_RGO_SIZE_FISHING"\n\t\t\tvalue = var:pp_fish_base_capacity\n\t\t\tmultiply = max_rgo_workers\n\t\t\tmultiply = 0.030'
        in bonus_block
    )
    assert "add = fish_rgo_capacity_bonus" in gross_block
    assert "value = modifier:fish_max_level_modifier" in gross_block
    assert "max = 20" not in gross_block
    assert "value = fish_building_levels\n\t\tmultiply = -1" in remaining_block

    forbidden = ("value = population", "value = development", "local_population_capacity", "total_building_levels", "rank_capacity")
    assert not [token for token in forbidden if token in gross_block + remaining_block]
    assert "value = max_rgo_workers\n\t\tmultiply = 0.40" not in gross_block + bonus_block
    assert "multiply = 1.12" not in gross_block + bonus_block


def test_forest_capacity_uses_forest_rgo_rank_urbanization_and_used_levels() -> None:
    text = BUILDING_CAPS.read_text(encoding="utf-8-sig")
    cap_values = BUILDING_CAPACITY_VALUES.read_text(encoding="utf-8-sig")
    entries = {entry.key for entry in parse_file(BUILDING_CAPS).entries}
    assert "forest_rgo_capacity_bonus" in entries

    base_block = "pp_forest_base_capacity_value = {" + cap_values.split(
        "pp_forest_base_capacity_value = {",
        1,
    )[1]
    bonus_block = _text_block_between(
        text,
        "forest_rgo_capacity_bonus = {",
        "\nforest_gross_capacity = {",
    )
    gross_block = _text_block_between(
        text,
        "forest_gross_capacity = {",
        "\nforest_capacity_remaining = {",
    )
    remaining_block = _text_block_between(
        text,
        "forest_capacity_remaining = {",
        "\nforest_max_level = {",
    )

    for snippet in (
        "raw_material = goods:lumber",
        "raw_material = goods:fur",
        "raw_material = goods:wild_game",
        "vegetation = forest",
        "add = 6",
        "vegetation = woods",
        "add = 4",
        "vegetation = jungle",
        "add = 3",
    ):
        assert snippet in base_block

    assert "limit = { has_variable = pp_forest_base_capacity }" in bonus_block
    assert (
        'desc = "BUILDING_LEVEL_RGO_SIZE_FOREST"\n\t\t\tvalue = var:pp_forest_base_capacity\n\t\t\tmultiply = max_rgo_workers\n\t\t\tmultiply = 0.030'
        in bonus_block
    )
    assert "add = forest_rgo_capacity_bonus" in gross_block
    assert "value = modifier:forest_max_level_modifier" in gross_block
    assert "max = 20" not in gross_block
    assert "value = modifier:forest_rank_capacity_modifier" in remaining_block
    assert "value = non_forest_building_levels\n\t\tmultiply = -0.1" in remaining_block
    assert "value = forest_building_levels\n\t\tmultiply = -1" in remaining_block
    assert not [token for token in ("value = population", "value = development", "local_population_capacity") if token in gross_block + remaining_block]
    assert "value = max_rgo_workers\n\t\tmultiply = 0.50" not in gross_block + bonus_block
    assert "multiply = 1.25" not in gross_block + bonus_block


def test_land_farm_blueprints_use_shared_capacity_pool() -> None:
    missing_paths = [path for path in LAND_FARM_BLUEPRINTS if not path.exists()]
    assert missing_paths == []

    for blueprint in LAND_FARM_BLUEPRINTS:
        text = blueprint.read_text(encoding="utf-8-sig")

        assert "max_levels = farm_max_level" in text
        assert "_farm_max_level" not in text
        assert "farm_space_used" not in text
        assert "farm_capacity_available > 0" in text
        assert "max_levels = farming_capacity" not in text
        assert "max_levels = farming_village_max_level" not in text
        assert "location_potential = {" in text
        assert "pp_farming_village_fixed_env_bonus" not in text

    for blueprint in (FARMING_VILLAGE_BLUEPRINT, MODEL_FARM_BLUEPRINT):
        text = blueprint.read_text(encoding="utf-8-sig")

        assert "pp_general_farmable_food_location > 0" in text
        assert "max_rgo_workers > 0" not in text
        assert "modifier:local_population_capacity > 0" not in text


def test_general_farm_eligibility_script_values_are_conservative() -> None:
    text = BUILDING_CAPACITY_VALUES.read_text(encoding="utf-8-sig")
    general_block = _text_block_between(
        text,
        "pp_general_farmable_food_location = {",
        "\npp_orchard_friendly_location = {",
    )
    orchard_block = _text_block_between(
        text,
        "pp_orchard_friendly_location = {",
        "\npp_pasture_friendly_location = {",
    )
    pasture_block = _text_block_between(
        text,
        "pp_pasture_friendly_location = {",
        "\npp_fish_base_capacity_value = {",
    )

    expected_allowed = {
        general_block: (
            "wheat",
            "maize",
            "rice",
            "millet",
            "legumes",
            "potato",
            "livestock",
            "olives",
            "fruit",
            "wool",
        ),
        orchard_block: (
            "fruit",
            "olives",
            "wine",
            "wheat",
            "maize",
            "rice",
            "millet",
            "legumes",
            "potato",
            "livestock",
            "beeswax",
            "silk",
            "tea",
        ),
        pasture_block: ("wool", "livestock", "horses"),
    }
    forbidden = ("fish", "clay", "lumber", "stone", "tin", "silver", "gold", "goods_gold", "gems", "saltpeter", "amber")

    for block, goods in expected_allowed.items():
        for good in goods:
            assert f"raw_material = goods:{good}" in block
        for good in forbidden:
            assert f"raw_material = goods:{good}" not in block

    for accepted_old_warning_good in ("wheat", "rice", "legumes", "livestock", "silk", "beeswax", "wine"):
        assert f"raw_material = goods:{accepted_old_warning_good}" in orchard_block
    for rejected_old_warning_good in ("clay", "fish", "tin", "silver", "goods_gold", "gems", "saltpeter", "amber"):
        assert f"raw_material = goods:{rejected_old_warning_good}" not in orchard_block


def test_fruit_and_sheep_families_use_shared_eligibility_gates() -> None:
    gates = {
        "fruit_orchard": "pp_orchard_friendly_location",
        "pomological_orchard": "pp_orchard_friendly_location",
        "sheep_farms": "pp_pasture_friendly_location",
        "enclosed_sheep_walks": "pp_pasture_friendly_location",
    }

    for building, gate in gates.items():
        text = (BUILDING_BLUEPRINT_ROOT / f"{building}.yml").read_text(encoding="utf-8-sig")
        assert f"{gate} > 0" in text
        assert "farm_capacity_available > 0" in text
        assert "pp_fruit_orchard_fixed_env_bonus" not in text
        assert "pp_sheep_farms_fixed_env_bonus" not in text

    game_start = GAME_START.read_text(encoding="utf-8-sig")
    assert "NOT = { pp_general_farmable_food_location > 0 }" in game_start
    assert "NOT = { pp_orchard_friendly_location > 0 }" in game_start
    assert "NOT = { pp_pasture_friendly_location > 0 }" in game_start
    assert "NOT = { raw_material = goods:fruit }" not in game_start
    assert "NOT = { raw_material = goods:wool }" not in game_start
    assert "raw_material = goods:fruit" in game_start
    assert "raw_material = goods:wool" in game_start


def test_fish_blueprints_use_shared_capacity_pool_and_keep_distinctions() -> None:
    missing_paths = [path for path in FISH_CAP_BLUEPRINTS if not path.exists()]
    assert missing_paths == []

    for blueprint in FISH_CAP_BLUEPRINTS:
        text = blueprint.read_text(encoding="utf-8-sig")
        assert "max_levels = fish_max_level" in text
        assert "fish_capacity_available > 0" in text
        assert "fishing_village_max_level" not in text
        assert "pp_fishing_village_fixed_env_bonus" not in text

    fishing_village = (BUILDING_BLUEPRINT_ROOT / "fishing_village.yml").read_text(encoding="utf-8-sig")
    for gate in ("has_river = yes", "is_adjacent_to_lake = yes", "topography = wetlands", "raw_material = goods:fish"):
        assert gate in fishing_village
    assert "is_coastal = yes" not in _text_block_between(
        fishing_village,
        "location_potential = {",
        "\n        allow = {",
    )

    for blueprint in ("ocean_fishery", "offshore_fishery"):
        text = (BUILDING_BLUEPRINT_ROOT / f"{blueprint}.yml").read_text(encoding="utf-8-sig")
        location_potential = _text_block_between(text, "location_potential = {", "\n    allow = {")
        assert "is_coastal = yes" in location_potential
        assert "has_river = yes" not in location_potential
        assert "is_adjacent_to_lake = yes" not in location_potential

    pearl = (BUILDING_BLUEPRINT_ROOT / "pearl_fishery.yml").read_text(encoding="utf-8-sig")
    assert "fish_max_level" not in pearl
    assert "fish_capacity_available" not in pearl


def test_forest_blueprints_use_shared_capacity_pool() -> None:
    missing_paths = [path for path in FOREST_CAP_BLUEPRINTS if not path.exists()]
    assert missing_paths == []

    for blueprint in FOREST_CAP_BLUEPRINTS:
        text = blueprint.read_text(encoding="utf-8-sig")
        assert "max_levels = forest_max_level" in text
        assert "forest_capacity_available > 0" in text
        assert "forest_village_max_level" not in text
        assert "pp_forest_village_fixed_env_bonus" not in text
        for gate in (
            "vegetation = woods",
            "vegetation = forest",
            "vegetation = jungle",
            "raw_material = goods:lumber",
            "raw_material = goods:fur",
            "raw_material = goods:wild_game",
        ):
            assert gate in text

    for excluded in ("charcoal_maker", "improved_charcoal_maker", "ivory_hunting_camp", "pearl_fishery"):
        text = (BUILDING_BLUEPRINT_ROOT / f"{excluded}.yml").read_text(encoding="utf-8-sig")
        assert "forest_max_level" not in text
        assert "forest_capacity_available" not in text


def test_location_rank_farming_capacity_modifiers_are_canonical() -> None:
    parsed = parse_file(LOCATION_RANKS)
    entries = {entry.key: entry.value for entry in parsed.entries}
    expected = {
        "TRY_INJECT:megalopolis": -20,
        "TRY_REPLACE:city": -5,
        "TRY_REPLACE:town": -1,
        "TRY_REPLACE:rural_settlement": 0,
    }

    for rank_key, value in expected.items():
        rank = entries[rank_key]
        assert isinstance(rank, CList)
        rank_modifier = _entry_values(rank)["rank_modifier"]
        assert isinstance(rank_modifier, CList)
        modifiers = _entry_values(rank_modifier)
        assert modifiers["farm_rank_capacity_modifier"] == value
        assert modifiers["forest_rank_capacity_modifier"] == value
        assert "farm_max_level_modifier" not in modifiers
        assert "fruit_orchard_max_level_modifier" not in modifiers
        assert "sheep_farms_max_level_modifier" not in modifiers
        assert "farming_village_max_level_modifier" not in modifiers
        assert "fishing_village_max_level_modifier" not in modifiers
        assert "forest_village_max_level_modifier" not in modifiers
        assert "fish_max_level_modifier" not in modifiers
        assert "forest_max_level_modifier" not in modifiers


def test_farm_capacity_rank_and_improvement_modifiers_are_separate() -> None:
    modifier_types = _database_keys(MODIFIER_TYPE_DEFINITIONS)
    modifier_icons = _database_keys(MODIFIER_ICONS)
    localization_text = (LOCALIZATION_ROOT / "pp_building_adjustments_l_english.yml").read_text(
        encoding="utf-8-sig"
    )

    assert "farm_rank_capacity_modifier" in modifier_types
    assert "farm_rank_capacity_modifier" in modifier_icons
    assert "fish_max_level_modifier" in modifier_types
    assert "fish_max_level_modifier" in modifier_icons
    assert "forest_max_level_modifier" in modifier_types
    assert "forest_max_level_modifier" in modifier_icons
    assert "forest_rank_capacity_modifier" in modifier_types
    assert "forest_rank_capacity_modifier" in modifier_icons
    assert "MODIFIER_TYPE_NAME_farm_rank_capacity_modifier:" in localization_text
    assert "MODIFIER_TYPE_NAME_fish_max_level_modifier:" in localization_text
    assert "MODIFIER_TYPE_NAME_forest_max_level_modifier:" in localization_text
    assert "MODIFIER_TYPE_NAME_forest_rank_capacity_modifier:" in localization_text
    assert "BUILDING_LEVEL_FARM_CAPACITY_IMPROVEMENTS:" in localization_text
    assert "BUILDING_LEVEL_FISH_CAPACITY_IMPROVEMENTS:" in localization_text
    assert "BUILDING_LEVEL_FOREST_CAPACITY_IMPROVEMENTS:" in localization_text

    expected_blueprint_modifiers = {
        "irrigation_systems": 1,
        "bund": 1,
        "terraces": 2,
        "polders": 2,
        "khmer_baray": 2,
    }
    for blueprint, modifier in expected_blueprint_modifiers.items():
        text = (BUILDING_BLUEPRINT_ROOT / f"{blueprint}.yml").read_text(encoding="utf-8-sig")
        assert f"farm_max_level_modifier = {modifier}" in text
        assert "farm_rank_capacity_modifier" not in text

    aqueduct_text = AQUEDUCT_SYSTEM.read_text(encoding="utf-8-sig")
    assert "farm_max_level_modifier = 2" in aqueduct_text
    assert "farm_rank_capacity_modifier" not in aqueduct_text


def test_water_control_capacity_buildings_use_scaled_gold_prices() -> None:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    buildings = {row["name"]: row for row in data.building_data.buildings.to_dicts()}
    expected_prices = {
        "bund": ("pp_bund_price", 400.0),
        "irrigation_systems": ("pp_irrigation_systems_price", 600.0),
        "terraces": ("pp_terraces_price", 800.0),
        "polders": ("pp_polders_price", 800.0),
        "khmer_baray": ("pp_khmer_baray_price", 1000.0),
        "aqueduct_system": ("expand_aqueduct_system", 1000.0),
    }

    for building, (price_key, gold) in expected_prices.items():
        assert buildings[building]["price"] == price_key
        assert buildings[building]["price_gold"] == gold


def test_excluded_buildings_do_not_use_land_farm_capacity_pool() -> None:
    explicit_missing = [
        key for key in EXCLUDED_FARM_CAP_BUILDINGS if not (BUILDING_BLUEPRINT_ROOT / f"{key}.yml").exists()
    ]
    assert explicit_missing == []

    excluded_blueprints = _farm_cap_excluded_blueprints()
    assert excluded_blueprints

    offenders: list[str] = []
    for blueprint in excluded_blueprints:
        text = blueprint.read_text(encoding="utf-8-sig")
        if "max_levels = farm_max_level" in text:
            offenders.append(f"{blueprint.relative_to(ROOT)}: farm_max_level")
        if "_farm_max_level" in text:
            offenders.append(f"{blueprint.relative_to(ROOT)}: per-building farm max level")
        if "farm_space_used" in text:
            offenders.append(f"{blueprint.relative_to(ROOT)}: farm_space_used")
        if "farm_capacity_available > 0" in text:
            offenders.append(f"{blueprint.relative_to(ROOT)}: farm_capacity_available")

    assert offenders == []


def test_farming_capacity_map_uses_available_capacity_and_tooltip_shows_maximum() -> None:
    map_text = FOOD_MAP_MODES.read_text(encoding="utf-8-sig")
    localization_text = (LOCALIZATION_ROOT / "pp_building_adjustments_l_english.yml").read_text(
        encoding="utf-8-sig"
    )

    assert "value = farm_capacity_available" in map_text
    assert "value = farm_max_level" not in map_text
    assert "ScriptValue('farm_capacity_available')" in localization_text
    assert "ScriptValue('farm_gross_capacity')" in localization_text
    assert "ScriptValue('farm_max_level')" not in localization_text
    assert "Farming Villages and Model Farms" not in localization_text


def test_fish_and_forest_capacity_maps_use_available_capacity_and_tooltips_show_maximum() -> None:
    map_text = FOOD_MAP_MODES.read_text(encoding="utf-8-sig")
    localization_text = (LOCALIZATION_ROOT / "pp_building_adjustments_l_english.yml").read_text(
        encoding="utf-8-sig"
    )

    assert "value = fish_capacity_available" in map_text
    assert "value = forest_capacity_available" in map_text
    assert "var:pp_fishing_village_fixed_env_bonus" not in map_text
    assert "var:pp_forest_village_fixed_env_bonus" not in map_text
    assert "global_var:pp_fishing_village_global_" not in map_text
    assert "global_var:pp_forest_village_global_" not in map_text

    assert "ScriptValue('fish_capacity_available')" in localization_text
    assert "ScriptValue('fish_gross_capacity')" in localization_text
    assert "ScriptValue('forest_capacity_available')" in localization_text
    assert "ScriptValue('forest_gross_capacity')" in localization_text
    assert "GetVariable('pp_fishing_village_fixed_env_bonus')" not in localization_text
    assert "GetVariable('pp_forest_village_fixed_env_bonus')" not in localization_text


def test_capacity_map_mode_europedia_links_have_game_concepts() -> None:
    expected_concepts = (
        "pp_fish_capacity",
        "pp_farm_capacity",
        "pp_forest_capacity",
    )
    localization_text = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in (
            LOCALIZATION_ROOT / "pp_building_adjustments_l_english.yml",
            LOCALIZATION_ROOT / "pp_europedia_l_english.yml",
        )
    )

    for concept in expected_concepts:
        concept_path = GAME_CONCEPT_ROOT / f"{concept}.txt"
        assert concept_path.exists()
        assert f"{concept} = {{" in concept_path.read_text(encoding="utf-8-sig")
        assert f"[{concept}|e]" in localization_text


def test_capacity_error_files_are_finalized_with_utf8_bom() -> None:
    expected_paths = (
        GAME_CONCEPT_ROOT / "pp_fish_capacity.txt",
        GAME_CONCEPT_ROOT / "pp_forest_capacity.txt",
        BUILDING_CAPACITY_VALUES,
        CAPACITY_PRECALC,
    )
    configured_paths = {MOD_ROOT / path for path in cli.BOM_TEXT_RELATIVE_PATHS}

    for path in expected_paths:
        assert path in configured_paths
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_land_farm_culling_uses_shared_capacity_remaining() -> None:
    text = BUILDING_CULLING.read_text(encoding="utf-8-sig")

    for building in LAND_FARM_BUILDINGS:
        building_ref = f"building_type = building_type:{building}"
        idx = text.index(building_ref)
        block_start = text.rfind("\n\t\t\tif = {", 0, idx)
        change_ref = f"building = building_type:{building}"
        block_end = text.index(change_ref, idx) + len(change_ref)
        block = text[block_start:block_end]
        assert "farm_capacity_remaining < 0" in block
        assert "value > 0" in block
        assert building_ref in block
        assert change_ref in block


    assert "value > farm_max_level" not in text
    assert "value > fruit_orchard_max_level" not in text
    assert "value > sheep_farms_max_level" not in text
    assert "value > fishing_village_max_level" not in text
    assert "value > forest_village_max_level" not in text


def test_fish_and_forest_culling_use_shared_capacity_remaining() -> None:
    text = BUILDING_CULLING.read_text(encoding="utf-8-sig")

    for building in FISH_CAP_BUILDINGS:
        building_ref = f"building_type = building_type:{building}"
        idx = text.index(building_ref)
        block_start = text.rfind("\n\t\t\tif = {", 0, idx)
        change_ref = f"building = building_type:{building}"
        block_end = text.index(change_ref, idx) + len(change_ref)
        block = text[block_start:block_end]
        assert "fish_capacity_remaining < 0" in block
        assert "value > 0" in block
        assert building_ref in block
        assert change_ref in block

    for building in FOREST_CAP_BUILDINGS:
        building_ref = f"building_type = building_type:{building}"
        idx = text.index(building_ref)
        block_start = text.rfind("\n\t\t\tif = {", 0, idx)
        change_ref = f"building = building_type:{building}"
        block_end = text.index(change_ref, idx) + len(change_ref)
        block = text[block_start:block_end]
        assert "forest_capacity_remaining < 0" in block
        assert "value > 0" in block
        assert building_ref in block
        assert change_ref in block


def test_replaced_buildings_do_not_reuse_vanilla_unique_method_names() -> None:
    vanilla_methods_by_building = _vanilla_unique_methods_by_building()
    offenders = []

    for blueprint in accepted_blueprint_files(ROOT / "blueprints" / "accepted"):
        template = load_template(blueprint)
        if template.mode != "REPLACE":
            continue
        vanilla_methods = vanilla_methods_by_building.get(template.key)
        if not vanilla_methods:
            continue
        rendered = parse_text(
            f"{template.key} = {{\n{template.building_body}\n}}\n",
            path=blueprint,
        )
        unique_methods = _unique_production_method_names(rendered.entries[0].value)
        reused = sorted(unique_methods & vanilla_methods)
        if reused:
            offenders.append(f"{blueprint.relative_to(ROOT)}: {', '.join(reused)}")
        non_pp = sorted(method for method in unique_methods if not method.startswith("pp_"))
        if non_pp:
            offenders.append(f"{blueprint.relative_to(ROOT)} non-pp methods: {', '.join(non_pp)}")

    assert not offenders


def test_land_owning_farmers_is_a_full_privilege_replacement() -> None:
    parsed = parse_file(ESTATE_PRIVILEGE_ADJUSTMENTS)
    entries = {entry.key: entry.value for entry in parsed.entries}

    assert "TRY_REPLACE:land_owning_farmers" in entries
    assert "TRY_INJECT:land_owning_farmers" not in entries
    privilege = entries["TRY_REPLACE:land_owning_farmers"]
    assert isinstance(privilege, CList)

    privilege_values = _entry_values(privilege)
    assert privilege_values["estate"] == "peasants_estate"
    assert privilege_values["content_priority"] == 200
    assert "potential" in privilege_values
    assert "can_revoke" in privilege_values

    country_modifier = privilege_values["country_modifier"]
    assert isinstance(country_modifier, CList)
    modifier_values = _entry_values(country_modifier)
    assert "global_monthly_food_modifier" not in modifier_values
    assert modifier_values["levy_combat_efficiency_modifier"] == 0.05
    assert modifier_values["global_population_capacity_modifier"] == 0.05
    assert modifier_values["global_wheat_output_modifier"] == 0.05
    assert modifier_values["global_fish_output_modifier"] == 0.05
    assert modifier_values["global_millet_output_modifier"] == 0.05
    assert modifier_values["global_peasants_estate_power"] == 0.5


def test_powerful_magnates_food_modifier_is_zeroed_by_replacement() -> None:
    parsed = parse_file(GOVERNMENT_REFORM_ADJUSTMENTS)
    entries = {entry.key: entry.value for entry in parsed.entries}

    assert "REPLACE:hun_power_to_magnates" in entries
    assert "TRY_INJECT:hun_power_to_magnates" not in entries
    reform = entries["REPLACE:hun_power_to_magnates"]
    assert isinstance(reform, CList)

    reform_values = _entry_values(reform)
    assert reform_values["age"] == "age_2_renaissance"
    assert reform_values["unique"] is True
    assert reform_values["content_priority"] == 600
    assert "potential" in reform_values
    assert reform_values["years"] == 2

    country_modifier = reform_values["country_modifier"]
    assert isinstance(country_modifier, CList)
    modifier_values = _entry_values(country_modifier)
    assert modifier_values["global_nobles_estate_power"] == 1.0
    assert modifier_values["global_estate_target_satisfaction"] == "medium_permanent_target_satisfaction"
    assert modifier_values["global_monthly_food_modifier"] == 0


def test_dhimmi_satisfaction_uses_small_regional_staple_output_package() -> None:
    parsed = parse_file(ESTATE_ADJUSTMENTS)
    entries = {entry.key: entry.value for entry in parsed.entries}

    assert "TRY_INJECT:dhimmi_estate" in entries
    estate = entries["TRY_INJECT:dhimmi_estate"]
    assert isinstance(estate, CList)

    satisfaction = _entry_values(estate)["satisfaction"]
    assert isinstance(satisfaction, CList)
    modifier_values = _entry_values(satisfaction)

    assert "global_monthly_food_modifier" not in modifier_values
    assert modifier_values == {
        "global_wheat_output_modifier": 0.05,
        "global_rice_output_modifier": 0.05,
        "global_millet_output_modifier": 0.05,
        "global_legumes_output_modifier": 0.05,
        "global_fruit_output_modifier": 0.05,
        "global_olives_output_modifier": 0.05,
    }


def test_inject_targets_exist_in_constructor_load_order() -> None:
    load_order = LoadOrderConfig.load(ROOT / "constructor.load_order.toml")
    vanilla_root = load_order.vanilla_root
    offenders: list[str] = []

    for relative_common, vanilla_common in (
        (Path("in_game") / "common", vanilla_root / "game" / "in_game" / "common"),
        (Path("main_menu") / "common", vanilla_root / "game" / "main_menu" / "common"),
    ):
        mod_common = MOD_ROOT / relative_common
        for collection_dir in sorted(path for path in mod_common.iterdir() if path.is_dir()):
            collection = collection_dir.relative_to(mod_common)
            existing = _database_keys(vanilla_common / collection)
            if collection == Path("static_modifiers"):
                existing |= _database_keys(vanilla_root / "game" / "main_menu" / "common" / collection)

            for path in sorted(collection_dir.rglob("*.txt")):
                for entry in parse_file(path).entries:
                    if not isinstance(entry.value, CList):
                        continue
                    mode, key = _entry_mode(entry.key)
                    if mode in {"INJECT", "TRY_INJECT"} and key not in existing:
                        offenders.append(
                            f"{path.relative_to(ROOT)}:{entry.location.line} {mode}:{key}"
                        )
                    if mode in {"CREATE", "REPLACE", "REPLACE_OR_CREATE", "INJECT_OR_CREATE"}:
                        existing.add(key)
                    elif mode in {"TRY_REPLACE", "INJECT", "TRY_INJECT"} and key in existing:
                        existing.add(key)

    assert not offenders


def test_constructor_building_methods_are_resolved_and_unique() -> None:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")

    assert data.building_data.duplicate_production_methods.is_empty()
    assert data.building_data.unresolved_production_methods.is_empty()
    assert data.building_data.warnings == []


def test_cookery_building_line_has_resolved_prices() -> None:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    buildings = {row["name"]: row for row in data.building_data.buildings.to_dicts()}

    assert buildings["cookery"]["price"] == "pp_cookery_price"
    assert buildings["cookery"]["price_gold"] == 150.0
    assert buildings["victualling_yard"]["price"] == "pp_victualling_yard_price"
    assert buildings["victualling_yard"]["price_gold"] == 225.0


def test_victuals_pop_demand_uses_scalar_database_value() -> None:
    entries = {entry.key: entry.value for entry in parse_file(GOODS_DEMAND).entries}
    pop_demand = entries["INJECT:pop_demand"]
    assert isinstance(pop_demand, CList)

    values = _entry_values(pop_demand)
    assert values["victuals"] == 1


def test_pp_law_adjustments_use_existing_modifier_types() -> None:
    text = LAW_ADJUSTMENTS.read_text(encoding="utf-8-sig")

    assert "army_infantry_maintenance_cost_modifier" not in text
    assert "trade_efficiency =" not in text
    assert "army_light_infantry_maintenance_cost_modifier = -0.1" in text
    assert "army_heavy_infantry_maintenance_cost_modifier = -0.1" in text
    assert "trade_land_efficiency = small_trade_efficiency_bonus" in text
    assert "trade_sea_efficiency = small_trade_efficiency_bonus" in text


def test_pp_building_prices_have_modifier_type_assets_and_localization() -> None:
    price_keys = {
        key
        for key in _database_keys(PRICE_ROOT)
        if key.startswith("pp_") and key.endswith("_price")
    }
    expected = {f"{price_key}_cost_modifier" for price_key in price_keys}

    modifier_types = _database_keys(MODIFIER_TYPE_DEFINITIONS)
    modifier_icons = _database_keys(MODIFIER_ICONS)
    localization_text = "\n".join(
        path.read_text(encoding="utf-8-sig") for path in sorted(LOCALIZATION_ROOT.glob("*.yml"))
    )

    assert expected
    assert not (expected - modifier_types)
    assert not (expected - modifier_icons)
    assert not [
        key
        for key in sorted(expected)
        if f"MODIFIER_TYPE_DESC_{key}:" not in localization_text
        or f"MODIFIER_TYPE_NAME_{key}:" not in localization_text
    ]
    assert not [key for key in sorted(price_keys) if f"{key}:" not in localization_text]


def test_victuals_pop_demand_modifier_type_is_registered() -> None:
    modifier_types = _database_keys(MODIFIER_TYPE_DEFINITIONS)
    modifier_icons = _database_keys(MODIFIER_ICONS)
    localization_text = "\n".join(
        path.read_text(encoding="utf-8-sig") for path in sorted(LOCALIZATION_ROOT.glob("*.yml"))
    )

    assert "global_victuals_pop_demand" in modifier_types
    assert "global_victuals_pop_demand" in modifier_icons
    assert "MODIFIER_TYPE_NAME_global_victuals_pop_demand:" in localization_text
    assert "MODIFIER_TYPE_DESC_global_victuals_pop_demand:" in localization_text


def test_current_megalopolis_buildings_allow_megalopolis() -> None:
    for blueprint_name in ("dock", "fruit_orchard", "irrigation_systems"):
        template = load_template(ROOT / "blueprints" / "accepted" / "buildings" / f"{blueprint_name}.yml")
        rendered = parse_text(
            f"{template.key} = {{\n{template.building_body}\n}}\n",
            path=Path(f"{blueprint_name}.yml"),
        )
        values = _entry_values(rendered.entries[0].value)
        assert values["megalopolis"] is True


def test_victuals_market_construction_and_coastal_saltern_debug_keys_are_localized() -> None:
    victuals_market = load_template(ROOT / "blueprints" / "accepted" / "buildings" / "victuals_market.yml")
    coastal_saltern = load_template(ROOT / "blueprints" / "accepted" / "buildings" / "coastal_saltern.yml")

    assert victuals_market.localization["victuals_market_construction"] == "Victuals Market Construction"

    rendered = parse_text(
        f"{coastal_saltern.key} = {{\n{coastal_saltern.building_body}\n}}\n",
        path=Path("coastal_saltern.yml"),
    )
    body = rendered.entries[0].value
    assert isinstance(body, CList)
    methods = body.values("unique_production_methods")[0]
    assert isinstance(methods, CList)
    base = _entry_values(methods)["pp_coastal_saltern_base_salt"]
    assert isinstance(base, CList)
    base_values = _entry_values(base)
    assert base_values["output"] == 0.24

    worked_methods = body.values("unique_production_methods")[1]
    assert isinstance(worked_methods, CList)
    lined_pans = _entry_values(worked_methods)["pp_coastal_saltern_lined_evaporation_pans"]
    assert isinstance(lined_pans, CList)
    values = _entry_values(lined_pans)
    assert values["output"] == 0.72
    assert values["clay"] == 4.0
    assert values["pottery"] == 1.15


def test_salt_rgo_bonus_reduces_food_decay_without_affecting_saltpeter() -> None:
    bonuses = {entry.key: entry.value for entry in parse_file(RGO_STATIC_BONUSES).entries}

    salt = bonuses["pp_rgo_bonus_salt"]
    saltpeter = bonuses["pp_rgo_bonus_saltpeter"]
    assert isinstance(salt, CList)
    assert isinstance(saltpeter, CList)

    assert _entry_values(salt)["local_food_decay_modifier"] == -0.00070
    assert "local_food_decay_modifier" not in _entry_values(saltpeter)


def test_farming_village_uses_baseline_building_price() -> None:
    data = load_eu5_data(profile="constructor", load_order_path=ROOT / "constructor.load_order.toml")
    annotated = annotate_building_data_availability(data.building_data, data.advancements)
    buildings = {row["name"]: row for row in annotated.buildings.to_dicts()}

    farming_village = buildings["farming_village"]
    assert farming_village["price"] is None
    assert farming_village["effective_price"] == "p_building_age_1_traditions"
    assert farming_village["effective_price_gold"] == 50.0
    assert farming_village["price_kind"] == "baseline_age"


def test_labeling_output_modifier_config_loads_explicit_goods() -> None:
    cfg = load_mod_injector_config(ROOT / "labeling_output_modifiers.yaml")

    assert cfg.defaults["null_productivity"] == -0.6
    assert cfg.defaults["scale_args"] == {"output_min": -0.6, "output_max": 0.4}
    assert [g.trade_good for g in cfg.goods] == [
        "beeswax",
        "chili",
        "cloves",
        "cocoa",
        "coffee",
        "cotton",
        "dyes",
        "elephants",
        "fiber_crops",
        "fish",
        "fruit",
        "fur",
        "horses",
        "incense",
        "ivory",
        "legumes",
        "livestock",
        "lumber",
        "maize",
        "medicaments",
        "millet",
        "olives",
        "pepper",
        "potato",
        "rice",
        "saffron",
        "silk",
        "sugar",
        "tea",
        "tobacco",
        "wheat",
        "wild_game",
        "wine",
        "wool",
    ]
    assert all(g.enabled for g in cfg.goods)


def _vanilla_unique_methods_by_building() -> dict[str, set[str]]:
    load_order = LoadOrderConfig.load(ROOT / "constructor.load_order.toml")
    building_dir = load_order.vanilla_root / "game" / "in_game" / "common" / "building_types"
    result: dict[str, set[str]] = {}
    for path in sorted(building_dir.glob("*.txt")):
        for entry in parse_file(path).entries:
            if isinstance(entry.value, CList):
                methods = _unique_production_method_names(entry.value)
                if methods:
                    result[entry.key] = methods
    return result


def _entry_values(block: CList) -> dict[str, object]:
    return {entry.key: entry.value for entry in block.entries}


def _database_keys(root: Path) -> set[str]:
    if not root.exists():
        return set()
    keys: set[str] = set()
    for path in sorted(root.rglob("*.txt")):
        for entry in parse_file(path).entries:
            if isinstance(entry.value, CList):
                keys.add(_entry_mode(entry.key)[1])
    return keys


def _entry_mode(raw_key: str) -> tuple[str, str]:
    if ":" not in raw_key:
        return "CREATE", raw_key
    mode, key = raw_key.split(":", 1)
    return mode.strip().upper(), key


def _text_block_between(text: str, start: str, end: str) -> str:
    _, tail = text.split(start, 1)
    block, _ = tail.split(end, 1)
    return start + block


def _farm_cap_excluded_blueprints() -> tuple[Path, ...]:
    excluded = set(EXCLUDED_FARM_CAP_BUILDINGS)
    extractive_markers = (
        "_mine",
        "_quarry",
        "_pit",
        "_washmill",
        "_collector",
        "_smelter",
        "_diggings",
        "_sluice",
        "_beds",
        "_washery",
    )

    for path in BUILDING_BLUEPRINT_ROOT.glob("*.yml"):
        key = path.stem
        if key in LAND_FARM_BUILDINGS:
            continue
        if any(marker in key for marker in extractive_markers):
            excluded.add(key)
        if "smelter" in key:
            excluded.add(key)

    return tuple(sorted(BUILDING_BLUEPRINT_ROOT / f"{key}.yml" for key in excluded))


def _unique_production_method_names(block: CList) -> set[str]:
    names: set[str] = set()
    for value in block.values("unique_production_methods"):
        if isinstance(value, CList):
            names.update(entry.key for entry in value.entries)
    return names
