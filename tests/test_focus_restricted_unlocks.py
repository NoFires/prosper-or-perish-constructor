from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

from eu5gameparser.domain.eu5 import load_eu5_data


ROOT = Path(__file__).resolve().parents[1]
FOCUS_VALUES = {"adm", "dip", "mil"}


def test_constructor_owned_unlocks_do_not_depend_on_age_focus_advances() -> None:
    data = load_eu5_data(
        profile="constructor",
        load_order_path=ROOT / "constructor.load_order.toml",
    )
    advancement_rows = data.advancements.to_dicts()
    restricted_roots_by_advance = _focus_restricted_roots_by_advance(advancement_rows)
    constructor_buildings = _constructor_owned_names(data.building_data.buildings)
    constructor_methods = _constructor_owned_names(data.building_data.production_methods)

    offenders: list[str] = []
    for row in advancement_rows:
        restricted_roots = restricted_roots_by_advance.get(row["name"])
        if restricted_roots is None:
            continue

        offenders.extend(
            _restricted_unlock_offenders(
                row,
                unlock_column="unlock_building",
                item_kind="building",
                constructor_items=constructor_buildings,
                restricted_roots=restricted_roots,
            )
        )
        offenders.extend(
            _restricted_unlock_offenders(
                row,
                unlock_column="unlock_production_method",
                item_kind="production_method",
                constructor_items=constructor_methods,
                restricted_roots=restricted_roots,
            )
        )

    assert offenders == []


def _focus_restricted_roots_by_advance(
    advancement_rows: list[dict],
) -> dict[str, set[str]]:
    children_by_requirement: dict[str, list[str]] = defaultdict(list)
    focus_roots: dict[str, str] = {}
    for row in advancement_rows:
        advance = row["name"]
        focus = row.get("focus")
        if focus in FOCUS_VALUES:
            focus_roots[advance] = focus
        for requirement in row.get("requires") or []:
            children_by_requirement[requirement].append(advance)

    restricted_roots_by_advance: dict[str, set[str]] = defaultdict(set)
    for root, focus in focus_roots.items():
        root_label = f"{root} ({focus})"
        queue: deque[str] = deque([root])
        visited: set[str] = set()
        while queue:
            advance = queue.popleft()
            if advance in visited:
                continue
            visited.add(advance)
            restricted_roots_by_advance[advance].add(root_label)
            queue.extend(children_by_requirement.get(advance, []))

    return dict(restricted_roots_by_advance)


def _constructor_owned_names(table) -> set[str]:
    return {
        row["name"]
        for row in table.select(["name", "source_layer"]).to_dicts()
        if row["source_layer"] == "constructor"
    }


def _restricted_unlock_offenders(
    row: dict,
    *,
    unlock_column: str,
    item_kind: str,
    constructor_items: set[str],
    restricted_roots: set[str],
) -> list[str]:
    source = _source_location(row)
    roots = ", ".join(sorted(restricted_roots))
    return [
        (
            f"{item_kind} {item} is unlocked by focus-restricted advance "
            f"{row['name']} under {roots} at {source}"
        )
        for item in row.get(unlock_column) or []
        if item in constructor_items
    ]


def _source_location(row: dict) -> str:
    source_file = Path(row["source_file"])
    try:
        source = source_file.relative_to(ROOT)
    except ValueError:
        source = source_file
    return f"{source}:{row['source_line']}"
