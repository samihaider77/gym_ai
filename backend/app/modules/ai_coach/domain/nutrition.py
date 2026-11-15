"""Daily calorie and protein targets, and the one-line coaching tip. Pure functions, no framework code.

Calories: Mifflin-St Jeor resting energy x an activity factor, adjusted for the goal.
Protein: grams per kg of body weight by goal (1.4-2.0 g/kg, the range sports-nutrition guidance recommends
for people who train).
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

ACTIVITY = {"sedentary": 1.2, "lightly_active": 1.375, "moderately_active": 1.55, "very_active": 1.725}
GOAL_KCAL = {"fat_loss": -500, "muscle_gain": 300, "strength": 200}
PROTEIN_PER_KG = {"fat_loss": 2.0, "muscle_gain": 1.8, "strength": 1.8, "endurance": 1.4, "general_fitness": 1.4}

# High-protein foods from the table to suggest, with their default unit: (food key, label EN, label Roman Urdu).
PROTEIN_IDEAS: List[Tuple[str, str, str]] = [
    ("egg_boiled", "boiled eggs", "ublay anday"),
    ("chicken_tikka", "a piece of chicken tikka", "chicken tikka ka ek piece"),
    ("dahi", "a katori of dahi", "ek katori dahi"),
    ("milk", "a glass of milk", "ek glass doodh"),
    ("daal", "a katori of daal", "ek katori daal"),
]


@dataclass
class Targets:
    kcal: int
    protein_g: int


def age_on(dob: Optional[date], today: date) -> Optional[int]:
    if not dob:
        return None
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def daily_targets(weight_kg: Optional[float], height_cm: Optional[float], age: Optional[int],
                  gender: Optional[str], activity: Optional[str], goal: Optional[str]) -> Optional[Targets]:
    """None when weight, height or age is missing: the tip then asks the user to complete the profile."""
    if not weight_kg or not height_cm or not age:
        return None
    sex = {"male": 5, "female": -161}.get((gender or "").lower(), -78)
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + sex
    kcal = bmr * ACTIVITY.get(activity or "", 1.375) + GOAL_KCAL.get(goal or "", 0)
    protein = weight_kg * PROTEIN_PER_KG.get(goal or "", 1.6)
    return Targets(kcal=int(round(kcal / 10) * 10), protein_g=int(round(protein)))


def coaching_tip(totals: Dict[str, float], targets: Optional[Targets], meals_logged: int,
                 protein_per_unit: Dict[str, float]) -> Dict[str, str]:
    """One short line in English and Roman Urdu, chosen from today's totals against the targets."""
    if targets is None:
        return {
            "en": "Add your weight, height and date of birth in Profile to get daily calorie and protein targets.",
            "ur": "Profile mein apna wazan, qad aur date of birth daalein, phir rozana calories aur protein ka target milega.",
        }
    if meals_logged == 0:
        return {
            "en": f"Today's target: {targets.kcal} kcal and {targets.protein_g} g protein. Snap your first meal.",
            "ur": f"Aaj ka target: {targets.kcal} kcal aur {targets.protein_g} g protein. Pehle khane ki photo lein.",
        }
    protein_left = targets.protein_g - totals["protein_g"]
    kcal_left = targets.kcal - totals["kcal"]
    if kcal_left < -150:
        over = int(round(-kcal_left))
        return {
            "en": f"You're {over} kcal over today. Keep the next meal light: daal or sabzi with one roti.",
            "ur": f"Aaj aap {over} kcal zyada kha chuke hain. Agla khana halka rakhein: daal ya sabzi ke saath ek roti.",
        }
    if protein_left >= 15:
        need = int(round(protein_left))
        key, en, ur = PROTEIN_IDEAS[0]
        per_egg = protein_per_unit.get(key, 6.0)
        eggs = max(1, min(4, int(round(protein_left / per_egg)))) if protein_left < 30 else None
        if eggs:
            return {
                "en": f"{need} g protein to go today. {eggs} {en} would cover most of it.",
                "ur": f"Aaj {need} g protein baqi hai. {eggs} {ur} se zyada tar poora ho jayega.",
            }
        _, en2, ur2 = PROTEIN_IDEAS[1]
        _, en3, ur3 = PROTEIN_IDEAS[2]
        return {
            "en": f"{need} g protein to go today. Try {en2} with {en3}.",
            "ur": f"Aaj {need} g protein baqi hai. {ur2} aur {ur3} le lein.",
        }
    if kcal_left > 400:
        left = int(round(kcal_left))
        return {
            "en": f"Protein is on track. You still have about {left} kcal left for today.",
            "ur": f"Protein theek hai. Aaj ke liye abhi takreeban {left} kcal baqi hain.",
        }
    return {
        "en": "Protein and calories are on track today. Nice work.",
        "ur": "Aaj protein aur calories dono target par hain. Shabash.",
    }
