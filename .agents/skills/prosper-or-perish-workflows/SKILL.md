---
name: prosper-or-perish-workflows
description: Use for Prosper or Perish Constructor repo workflows, including setup, tests, parser inspection, static analysis, savegame export, docs publishing, blueprint list/parity/evaluate/good/build, and guarded live sync/deploy commands.
---

# Prosper Or Perish Workflows

Use the repo command surface before reaching for raw commands:

```bash
uv run ppc --help
```

Default to the constructor workspace:

```bash
cd /mnt/c/Development/ProsperOrPerishConstructor
```

When running from another folder, pass the repo explicitly:

```bash
uv run --project /mnt/c/Development/ProsperOrPerishConstructor ppc --repo /mnt/c/Development/ProsperOrPerishConstructor --help
```

## Command Index

- `uv run ppc setup`: install dev dependencies and inspect the project.
- `uv run ppc inspect`: inspect the configured constructor project.
- `uv run ppc test`: run pytest; pass file names or pytest args after the command.
- `uv run ppc analyze`: export static parser tables and refresh the goods-flow docs example.
- `uv run ppc savegame`: export latest savegame facts and the savegame explorer.
- `uv run ppc publish-docs`: copy generated graph outputs into `docs/examples`.
- STATIC_HTML_GRAPH_UPDATE: run `uv run ppc analyze` for `graphs/goods_flow_explorer.html` and `docs/examples/goods_flow_explorer.html`.
- STATIC_HTML_GRAPH_UPDATE: run `uv run ppc savegame` for `graphs/savegame_explorer.html` and `docs/examples/savegame_explorer.html`.
- `uv run ppc dashboard`: serve the current population-capacity dashboard at `http://127.0.0.1:8000/`.
- `uv run ppc blueprint list`: list accepted blueprints.
- `uv run ppc blueprint parity`: compare accepted blueprints with generated mod output.
- `uv run ppc blueprint evaluate`: evaluate blueprint economics and balance rules.
- `uv run ppc blueprint good <good>`: compare methods that produce one trade good.
- `uv run ppc blueprint build`: build accepted blueprints into the constructor mod copy.
- `uv run ppc build`: same build workflow as `blueprint build`.
- `uv run ppc sync --yes`: guarded live mirror into the configured Paradox mod folder.

## Safety Rules

- Do not run `sync --yes` unless the user explicitly asks to update the live Paradox mod folder.
- If `sync` is requested, confirm `constructor.local.toml` exists and contains the intended deploy target.
- If dashboard output is missing, generate or refresh the population-capacity artifacts before serving it.
- Prefer `test`, `inspect`, `blueprint evaluate`, and `blueprint parity` before changes that affect accepted blueprints or generated output.
- Use parser/evaluator command output as source of truth for game-data answers; do not infer economics from raw text search.

## Building Override Pattern

- For existing vanilla buildings, use a top-level `REPLACE:<building>` blueprint render.
- If replacing inline `unique_production_methods`, never reuse the vanilla method key. Add a mod-owned `pp_*` method key, reference that same key in `production_method_slots`, define it in `unique_production_methods`, and localize it.
- Do not put `TRY_REPLACE`, `REPLACE`, or `INJECT` inside `unique_production_methods`; those modes only apply to top-level common database entries.
- After changing a building override, run `uv run eu5-orchestrator validate --project constructor.toml` and `uv run ppc test tests/test_project_config.py::test_replaced_buildings_do_not_reuse_vanilla_unique_method_names tests/test_project_config.py::test_constructor_building_methods_are_resolved_and_unique`.

## Output Style

When reporting results, mention the exact `ppc` command used and summarize the important pass/fail lines. If a command writes a graph or dashboard, report the path under `graphs/`, `docs/examples/`, or `artifacts/data/population_capacity/current_capacity_map/`.

## Localization Style

- Treat localization as player-facing in-game text, not developer notes or a restatement of requested implementation details.
- Do not hardcode balance values in localization when a modifier, scripted value, building tooltip, or generated modifier effect can show the current value.
- Write localization around what the player sees, what it means, and where to inspect the effects; let modifiers carry exact changing numbers.
- Use plain text in situation panes and generated static-modifier descriptions unless that target UI is verified to support inline concept links; unsupported formatter tags spam `error.log`.
- Use mod-owned plain localization keys for situation map legends rather than inherited or generic `LEGEND_KEY_*` keys; the legend UI is sensitive to formatter syntax.
- In GUI files, do not prefix `default_format` style names with `#`; use the raw style key such as `yellow_titles` so the text formatter does not parse it as an inline tag.
