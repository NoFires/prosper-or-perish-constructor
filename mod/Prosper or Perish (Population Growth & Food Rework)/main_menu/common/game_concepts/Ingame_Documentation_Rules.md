# In-game Documentation Rules

Instructions for Cursor when editing game concept definitions or the Europedia.
# Prosper or Perish (Population Growth & Food Rework)\in_game\gui\encyclopedia_lateralview.gui
# Localization is usually here main_menu/localization/english/pp_europedia_l_english.yml
## Concept display order

When editing the Europedia GUI or concept definitions, preserve this order:

1. All (done)
2. F.A.Q.
3. Update 0.8: Foundations
4. Overview (done)
5. Urbanisation (done)
6. Food Production (done)
7. Food Consumption
8. New Buildings (done)
9. New Trade Goods (done)
10. Building Capacity (done)
11. Building Output (done)
12. Variable Harvests (done)
13. Population Capacity
14. Population Growth
15. Population Distribution
16. Other Changes

More concepts may be added later.

## File naming

Each Europedia card has exactly one game concept file. Filename = card name (snake_case, pp_ prefix):

| # | Card | File |
|---|------|------|
| 1 | All | (filter only) |
| 2 | F.A.Q. | pp_faq.txt |
| 3 | Update 0.8: Foundations | pp_update_0_8_foundations.txt |
| 4 | Overview | pp_overview.txt |
| 5 | Urbanisation | pp_urbanisation.txt |
| 6 | Food Production | pp_food_production.txt |
| 7 | Food Consumption | pp_food_consumption.txt |
| 8 | New Buildings | pp_new_buildings.txt |
| 9 | New Trade Goods | pp_new_trade_goods.txt |
| 10 | Building Capacity | pp_farm_capacity.txt |
| 11 | Building Output | pp_farm_output.txt |
| 12 | Variable Harvests | pp_variable_harvests.txt |
| 13 | Population Capacity | pp_population_capacity.txt |
| 14 | Population Growth | pp_population_growth.txt |
| 15 | Population Distribution | pp_population_distribution.txt |
| 16 | Other Changes | other_changes_pp_buildings_in_location.txt, other_changes_pp_prosperity.txt, other_changes_pp_devastation.txt, other_changes_pp_cheap_food.txt, other_changes_pp_expensive_food.txt, other_changes_pp_province_current_food_storage.txt, other_changes_pp_starvation.txt |

Other Changes sub-cards use the `other_changes_` prefix so they group together when browsing the folder.

Linked support concepts without top-level Europedia cards:

| Concept | File |
|---|---|
| Fishing Capacity | pp_fish_capacity.txt |
| Forest Capacity | pp_forest_capacity.txt |
