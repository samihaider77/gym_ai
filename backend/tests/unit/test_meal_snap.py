"""Meal Snap: food table, macro maths, targets and tips (no database, no network)."""
from datetime import date

import pytest
from fastapi import HTTPException

from app.modules.ai_coach.application.dtos import MealItemIn
from app.modules.ai_coach.application.services import MealSnapService
from app.modules.ai_coach.domain.nutrition import Targets, age_on, coaching_tip, daily_targets
from app.modules.ai_coach.infrastructure import foods


def test_food_table_loads_with_units_and_sources():
    table = foods.all_foods()
    assert len(table) >= 30
    for food in table:
        assert food.units and all(u.grams > 0 for u in food.units), food.key
        assert food.kcal > 0, food.key


def test_roti_macros_come_from_the_table():
    roti = foods.get_food("roti")
    item = MealSnapService.build_items([MealItemIn(food_key="roti", quantity=2)])[0]
    assert item.unit == "roti"
    assert item.grams == 2 * roti.units[0].grams
    assert item.kcal == round(roti.kcal * item.grams / 100)


def test_second_unit_is_used_when_named():
    item = MealSnapService.build_items([MealItemIn(food_key="rice", quantity=1, unit="katori")])[0]
    assert item.unit == "katori"
    assert item.grams == foods.get_food("rice").unit("katori").grams


def test_unknown_food_is_rejected():
    with pytest.raises(HTTPException) as error:
        MealSnapService.build_items([MealItemIn(food_key="pizza", quantity=1)])
    assert error.value.status_code == 400


def test_targets_need_weight_height_and_age():
    assert daily_targets(80, None, 30, "male", "sedentary", "fat_loss") is None
    t = daily_targets(80, 178, 30, "male", "moderately_active", "muscle_gain")
    # Mifflin-St Jeor: 10*80 + 6.25*178 - 5*30 + 5 = 1767.5; x1.55 = 2739.6; +300 = 3039.6
    assert t.kcal == 3040
    assert t.protein_g == 144  # 1.8 g/kg


def test_age_on_birthday_boundary():
    assert age_on(date(2000, 11, 16), date(2026, 11, 15)) == 25
    assert age_on(date(2000, 11, 15), date(2026, 11, 15)) == 26


def test_tip_suggests_protein_when_short():
    tip = coaching_tip({"kcal": 900, "protein_g": 60, "carbs_g": 0, "fat_g": 0}, Targets(2500, 80), 2, {"egg_boiled": 6.2})
    assert "20 g protein" in tip["en"] and "baqi" in tip["ur"]


def test_tip_warns_when_over_calories():
    tip = coaching_tip({"kcal": 2900, "protein_g": 150, "carbs_g": 0, "fat_g": 0}, Targets(2500, 140), 4, {})
    assert "over" in tip["en"]


def test_tip_asks_for_profile_without_targets():
    assert "Profile" in coaching_tip({"kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}, None, 0, {})["en"]


def test_usda_match_finds_common_foods_and_skips_alcohol():
    assert foods.match("Cucumber, raw").name == "Cucumber, raw"
    assert foods.match("cola").name == "Soft drink, cola"
    assert foods.match("tomatoes").name == "Tomatoes, raw"
    assert foods.match("gulab jamun") is None  # not in USDA: the AI's estimate is used instead


def test_serving_unit_uses_the_photo_weight():
    cucumber = foods.match("cucumber raw")
    item = MealSnapService.build_items(
        [MealItemIn(food_key=cucumber.key, quantity=1, unit="serving", unit_grams=80, name="Kheera")])[0]
    assert item.grams == 80 and item.name == "Kheera"
    assert item.kcal == round(cucumber.kcal * 0.8)


def test_estimated_item_needs_values_and_is_flagged():
    from app.modules.ai_coach.application.dtos import Per100g
    item = MealSnapService.build_items([MealItemIn(
        food_key="est:gulab-jamun", quantity=1, unit="100 g", name="Gulab jamun",
        per_100g=Per100g(kcal=320, protein_g=5, carbs_g=50, fat_g=12))])[0]
    assert item.estimated and item.kcal == 320
    with pytest.raises(HTTPException):
        MealSnapService.build_items([MealItemIn(food_key="est:x", quantity=1, name="X")])


def test_search_puts_desi_foods_first():
    names = [f.name for f in foods.search("chicken")]
    assert names[0].startswith("Chicken") and "Chicken curry / karahi" in names[:4]
