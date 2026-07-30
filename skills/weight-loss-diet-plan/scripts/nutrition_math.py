#!/usr/bin/env python3
"""Turn an intake into calorie, protein, fat, carb and fibre targets for fat loss.

The arithmetic here is not hard, but every mistake in it is silent: a protein
target scaled to the wrong bodyweight or a deficit that lands under someone's
basal requirement both look entirely reasonable written down. So compute it
rather than estimating, and read the warnings — they are the point.

    python3 nutrition_math.py --example > intake.json
    python3 nutrition_math.py intake.json
    python3 nutrition_math.py intake.json --json

Dependency-free, standard library only.
"""

import argparse
import json
import sys

KCAL_PER_KG_FAT = 7700.0

# Standard Harris-Benedict style multipliers. People consistently place
# themselves one notch high, so when the intake is vague, round down.
ACTIVITY = {
    "sedentary": (1.20, "desk job, little deliberate exercise, under ~5k steps"),
    "lightly_active": (1.375, "light exercise 1-3 days/week, or an active-ish job"),
    "moderately_active": (1.55, "moderate exercise 3-5 days/week"),
    "very_active": (1.725, "hard exercise 6-7 days/week, or a physical job"),
    "extra_active": (1.90, "physical job plus daily training, or an athlete"),
}

# Below these, a plan stops being a diet and starts being a deficiency risk.
ABSOLUTE_FLOOR = {"female": 1200, "male": 1500}

# Fat loss dominates in this band. Past the top of it, a rising share of the
# loss is muscle and adherence falls apart.
RATE_MIN_PCT, RATE_DEFAULT_PCT, RATE_MAX_PCT = 0.005, 0.0075, 0.010

EXAMPLE = {
    "age": 34,
    "sex": "female",
    "height_cm": 163,
    "weight_kg": 78,
    "body_fat_pct": None,
    "activity": "lightly_active",
    "goal_weight_kg": 65,
    "diet_pattern": "vegetarian",
    "conditions": [],
    "_notes": {
        "sex": "'male' or 'female' — Mifflin-St Jeor is defined this way. If the "
               "person is intersex or transgender, ask which figure to use or "
               "supply body_fat_pct so the sex-neutral equation applies instead.",
        "body_fat_pct": "optional; if known, a better protein target is derived",
        "activity": "one of " + ", ".join(ACTIVITY),
        "conditions": "free text, e.g. ['type 2 diabetes on metformin', 'hypothyroid']",
    },
}


def bmr_mifflin(weight_kg, height_cm, age, sex):
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def bmr_katch(lean_mass_kg):
    """Sex-neutral, and more accurate than Mifflin when body fat is known."""
    return 370 + 21.6 * lean_mass_kg


def compute(intake):
    warnings, notes = [], []

    weight = float(intake["weight_kg"])
    height = float(intake["height_cm"])
    age = int(intake["age"])
    sex = str(intake.get("sex", "")).lower()
    bf = intake.get("body_fat_pct")
    goal = intake.get("goal_weight_kg")
    conditions = " ".join(intake.get("conditions") or []).lower()

    if sex not in ("male", "female") and bf is None:
        raise SystemExit(
            "error: sex must be 'male' or 'female', or supply body_fat_pct so the "
            "sex-neutral equation can be used instead"
        )

    activity_key = str(intake.get("activity", "sedentary")).lower()
    if activity_key not in ACTIVITY:
        raise SystemExit(
            f"error: activity must be one of {', '.join(ACTIVITY)}"
        )
    multiplier, activity_desc = ACTIVITY[activity_key]

    height_m = height / 100.0
    bmi = weight / (height_m ** 2)
    healthy_max = 25.0 * height_m ** 2

    # --- Should this person be in a deficit at all? -----------------------
    stop = None
    if age < 18:
        stop = ("Under 18 — do not set a calorie deficit here. Growth and puberty "
                "change the requirements entirely. Refer to a paediatrician.")
    elif bmi < 18.5:
        stop = (f"BMI is {bmi:.1f}, which is underweight. Fat loss is not "
                "indicated. Offer maintenance or muscle gain instead.")
    elif bmi < 20:
        warnings.append(
            f"BMI is {bmi:.1f} — already at the lean end of healthy. Ask what the "
            "goal actually is before planning a deficit. Recomposition (training "
            "plus adequate protein at maintenance) is usually the better answer, "
            "and is what people at this BMI are normally describing."
        )
    if any(w in conditions for w in ("pregnan", "breastfeed", "lactating", "nursing")):
        stop = ("Pregnant or breastfeeding — a weight-loss deficit is not "
                "appropriate. Refer to their doctor or midwife.")

    # --- Energy ------------------------------------------------------------
    if bf is not None:
        lean = weight * (1 - float(bf) / 100.0)
        bmr = bmr_katch(lean)
        notes.append(f"BMR from Katch-McArdle using {lean:.1f} kg lean mass.")
    else:
        lean = None
        bmr = bmr_mifflin(weight, height, age, sex)
        notes.append("BMR from Mifflin-St Jeor.")

    tdee = bmr * multiplier

    # --- Deficit, capped by rate of loss rather than a fixed number --------
    rate_pct = RATE_DEFAULT_PCT
    if bmi < 22:
        # Less fat to draw on, so a gentler rate keeps the loss from coming
        # out of muscle.
        rate_pct = RATE_MIN_PCT
        notes.append("BMI under 22, so the rate is set at the gentle end.")

    target_rate_kg = weight * rate_pct
    deficit = target_rate_kg * KCAL_PER_KG_FAT / 7.0
    deficit = min(deficit, 0.25 * tdee)          # never more than a 25% cut
    target = tdee - deficit

    floor = ABSOLUTE_FLOOR.get(sex, 1200)
    if target < floor:
        warnings.append(
            f"Deficit clamped: the rate-based target was {target:.0f} kcal, below "
            f"the {floor} kcal floor for adequate micronutrients. Using {floor}. "
            "Losing faster than this needs more activity, not less food."
        )
        target = floor
    elif target < bmr:
        # Not a hard floor — for a sedentary person TDEE is only 1.2x BMR, so
        # any real deficit lands under it. Worth saying, not worth clamping.
        notes.append(
            f"Target sits below BMR ({bmr:.0f} kcal). That is expected for a "
            "sedentary person in a deficit, but it leaves no room to cut further "
            "later — added activity is the lever from here, not less food."
        )

    actual_deficit = tdee - target
    actual_rate_kg = actual_deficit * 7.0 / KCAL_PER_KG_FAT

    # --- Protein -----------------------------------------------------------
    renal = any(w in conditions for w in ("kidney", "renal", "ckd", "dialysis", "nephro"))
    if lean is not None:
        protein_ref, protein_basis = lean, "lean body mass"
        protein_g = 2.2 * lean
    elif bmi >= 27:
        # Fat mass has no protein requirement, so scaling to a high bodyweight
        # gives a number that is both unnecessary and unable to be eaten.
        ref = goal if goal and goal >= healthy_max * 0.9 else healthy_max
        protein_ref, protein_basis = ref, "target weight (not current)"
        protein_g = 2.0 * ref
    else:
        protein_ref, protein_basis = weight, "current bodyweight"
        protein_g = 1.8 * weight

    if renal:
        warnings.append(
            "Kidney condition mentioned. The usual 1.6-2.2 g/kg advice does NOT "
            "apply — protein must be set by their nephrologist. The figure below "
            "is a placeholder, not a recommendation."
        )

    protein_g = round(protein_g)
    if protein_g * 4 > 0.45 * target:
        capped = round(0.45 * target / 4)
        warnings.append(
            f"Protein target of {protein_g} g would be {protein_g * 4 / target:.0%} "
            f"of intake, leaving too little room for fat and carbohydrate. "
            f"Reduced to {capped} g."
        )
        protein_g = capped

    # --- Fat and carbs -----------------------------------------------------
    fat_g = max(0.6 * (lean or protein_ref), 0.20 * target / 9)
    fat_g = round(fat_g)
    carb_kcal = target - protein_g * 4 - fat_g * 9
    carb_g = round(carb_kcal / 4)
    if carb_g < 50:
        warnings.append(
            f"Only {carb_g} g of carbohydrate left after protein and fat. That is "
            "workable but restrictive — consider easing the deficit, or say "
            "explicitly that this is a low-carb plan so it isn't a surprise."
        )

    fibre_g = min(round(14 * target / 1000), 40)

    # --- Timeline ----------------------------------------------------------
    timeline = None
    if goal:
        goal = float(goal)
        if goal < 18.5 * height_m ** 2:
            # A stop, not a warning. Targets computed here would be a deficit
            # aimed at an underweight endpoint, and half-meeting an unsafe goal
            # ratifies it — see the "do not negotiate" note in SKILL.md.
            stop = (
                f"Goal weight of {goal:.0f} kg is a BMI of "
                f"{goal / height_m ** 2:.1f} for this height, which is underweight. "
                "Do not build a deficit toward it, and do not counter-offer a "
                "slightly higher but still underweight figure. Say plainly that a "
                f"goal at or above {18.5 * height_m ** 2:.0f} kg is the lowest "
                "sensible one, and ask what they are actually trying to change — "
                "it is usually body composition, which maintenance plus resistance "
                "training serves better than any deficit."
            )
        to_lose = weight - goal
        if to_lose > 0 and actual_rate_kg > 0:
            weeks = to_lose / actual_rate_kg
            timeline = {"to_lose_kg": round(to_lose, 1), "weeks": round(weeks)}
        elif to_lose <= 0:
            warnings.append("Goal weight is at or above current weight — confirm the goal.")

    if any(w in conditions for w in ("insulin", "sulfonylurea", "gliclazide", "glipizide")):
        warnings.append(
            "On insulin or a sulfonylurea. Cutting carbohydrate while doses stay "
            "the same risks hypoglycaemia — their prescriber should review doses "
            "before the plan starts."
        )

    return {
        "stop": stop,
        "bmi": round(bmi, 1),
        "bmr": round(bmr),
        "tdee": round(tdee),
        "activity": {"key": activity_key, "multiplier": multiplier, "means": activity_desc},
        "target_kcal": round(target),
        "deficit_kcal": round(actual_deficit),
        "deficit_pct": round(100 * actual_deficit / tdee),
        "rate_kg_per_week": round(actual_rate_kg, 2),
        "protein_g": protein_g,
        "protein_basis": f"{protein_basis} ({protein_ref:.0f} kg)",
        "fat_g": fat_g,
        "carb_g": carb_g,
        "fibre_g": fibre_g,
        "water_ml": round(35 * weight / 100) * 100,
        "healthy_weight_range_kg": [round(18.5 * height_m ** 2), round(healthy_max)],
        "timeline": timeline,
        "warnings": warnings,
        "notes": notes,
    }


def render(r):
    out = []
    if r["stop"]:
        # Deliberately withhold the numbers. Printing a calorie target under a
        # "do not use this" banner just supplies the thing that shouldn't be used.
        out.append("=" * 68)
        out.append("DO NOT BUILD A DEFICIT PLAN FOR THIS PERSON")
        out.append("=" * 68)
        out.append(r["stop"])
        out.append("")
        out.append(f"BMI {r['bmi']}   healthy range for this height: "
                   f"{r['healthy_weight_range_kg'][0]}-{r['healthy_weight_range_kg'][1]} kg")
        out.append(f"Maintenance is roughly {r['tdee']:,} kcal — use it for maintenance "
                   "guidance only.")
        out.append("")
        out.append("Targets are withheld on purpose. Explain why, kindly, and refer on.")
        return "\n".join(out)

    out.append(f"BMI {r['bmi']}   healthy range for this height: "
               f"{r['healthy_weight_range_kg'][0]}-{r['healthy_weight_range_kg'][1]} kg")
    out.append("")
    out.append(f"  Maintenance (TDEE)   {r['tdee']:>6,} kcal   "
               f"(BMR {r['bmr']:,} x {r['activity']['multiplier']})")
    out.append(f"  Target intake        {r['target_kcal']:>6,} kcal   "
               f"(-{r['deficit_kcal']:,}, a {r['deficit_pct']}% deficit)")
    out.append(f"  Expected loss        {r['rate_kg_per_week']:>6} kg/week")
    out.append("")
    out.append(f"  Protein   {r['protein_g']:>4} g   floor, not a target to stay under")
    out.append(f"            {'':>4}     scaled to {r['protein_basis']}")
    out.append(f"  Fat       {r['fat_g']:>4} g   minimum, for hormonal health")
    out.append(f"  Carbs     {r['carb_g']:>4} g   the flexible remainder")
    out.append(f"  Fibre     {r['fibre_g']:>4} g   satiety per calorie")
    out.append(f"  Water     {r['water_ml']:>4} ml  plus more around training")

    if r["timeline"]:
        t = r["timeline"]
        out.append("")
        out.append(f"  {t['to_lose_kg']} kg to lose at this rate: about {t['weeks']} weeks "
                   f"({t['weeks'] / 4.35:.1f} months).")

    if r["warnings"]:
        out.append("")
        out.append("WARNINGS")
        for w in r["warnings"]:
            out.append(f"  ! {w}")

    out.append("")
    out.append(f"Activity taken as '{r['activity']['key']}' = {r['activity']['means']}.")
    out.append("People place themselves a notch high more often than a notch low; if "
               "the answer was vague, rerun one level down and use that.")
    for n in r["notes"]:
        out.append(n)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("intake", nargs="?", help="path to intake JSON")
    ap.add_argument("--example", action="store_true", help="print a template intake file")
    ap.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.intake:
        ap.error("give an intake JSON file, or --example to get a template")

    with open(args.intake) as fh:
        intake = json.load(fh)
    intake.pop("_notes", None)

    missing = [k for k in ("age", "height_cm", "weight_kg") if intake.get(k) is None]
    if missing:
        raise SystemExit(f"error: intake is missing {', '.join(missing)}")

    result = compute(intake)
    if result["stop"]:
        # Same reasoning as render(): don't hand back a target that must not be used.
        for key in ("target_kcal", "deficit_kcal", "deficit_pct", "rate_kg_per_week",
                    "protein_g", "fat_g", "carb_g", "fibre_g", "timeline"):
            result[key] = None
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
