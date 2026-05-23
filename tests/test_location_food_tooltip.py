from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod" / "Prosper or Perish (Population Growth & Food Rework)"
LOCATION_FOOD_TOOLTIP = (
    MOD_ROOT / "in_game" / "gui" / "shared" / "zz_pp_location_food_tooltip_absolute_sources.gui"
)


def test_location_food_tooltip_shows_absolute_local_food_sources() -> None:
    assert LOCATION_FOOD_TOOLTIP.exists()

    text = LOCATION_FOOD_TOOLTIP.read_text(encoding="utf-8-sig")

    assert "template location_food_tooltip" in text
    assert "Location.GetFoodSources" in text
    assert "Location.GetModifierValue('local_monthly_food')" in text
    assert "MODIFIER_TYPE_NAME_local_monthly_food" in text
    assert (
        "Not(EqualTo_CFixedPoint(Location.GetModifierValueFixed('local_monthly_food'), "
        "'(CFixedPoint)0'))"
    ) in text
    assert text.index("Location.GetFoodSources") < text.index(
        "Location.GetModifierValue('local_monthly_food')"
    )
    assert "Location.GetFoodsOutputModifiersTooltip" not in text
    assert "FOOD_PRODUCTIVITY_LIST_TITLE" not in text
