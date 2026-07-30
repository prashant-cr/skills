#!/usr/bin/env python3
"""Verify a drafted week of meals against its own targets.

Summing calories and protein across 28 meals by eye is exactly the task that
produces confident wrong totals, and the failure is invisible: the plan looks
careful, the person follows it precisely, and the protein floor that was meant
to protect their muscle was never actually met. So write the week out as data
and let this add it up.

    python3 plan_check.py --example > week.json    # structure to fill in
    python3 plan_check.py week.json
    python3 plan_check.py week.json --json

Exits non-zero if any day fails, so it can gate a plan before it is shown.
Dependency-free, standard library only.
"""

import argparse
import json
import sys
from collections import Counter

KCAL_TOLERANCE = 0.10        # a day may land within +/-10% of target
PROTEIN_SHORTFALL_OK = 0.03  # protein is a floor; allow only rounding slack
MIN_MEALS_AT_THRESHOLD = 3   # meals that should clear the per-meal protein mark
PER_MEAL_PROTEIN_G = 20      # roughly the per-meal threshold worth hitting
MAX_DISTINCT_DISHES = 22     # past this the week stops being shoppable

EXAMPLE = {
    "targets": {"kcal": 1514, "protein_g": 130, "fibre_g": 21},
    "diet_pattern": "vegetarian",
    "days": [
        {
            "day": "Monday",
            "meals": [
                {
                    "name": "Breakfast",
                    "items": [
                        {"food": "Greek yogurt 0%, 300 g", "kcal": 178, "protein_g": 30, "fibre_g": 0},
                        {"food": "Rolled oats, 35 g", "kcal": 136, "protein_g": 5, "fibre_g": 4},
                        {"food": "Blueberries, 80 g", "kcal": 46, "protein_g": 1, "fibre_g": 2},
                    ],
                },
                {
                    "name": "Lunch",
                    "items": [
                        {"food": "Low-fat paneer, 120 g", "kcal": 200, "protein_g": 22, "fibre_g": 0},
                        {"food": "Roti, 2", "kcal": 220, "protein_g": 6, "fibre_g": 4},
                        {"food": "Mixed salad, large", "kcal": 60, "protein_g": 2, "fibre_g": 5},
                    ],
                },
                {
                    "name": "Snack",
                    "items": [
                        {"food": "Whey protein, 1 scoop", "kcal": 120, "protein_g": 24, "fibre_g": 0},
                        {"food": "Apple, 1 medium", "kcal": 95, "protein_g": 0, "fibre_g": 4},
                    ],
                },
                {
                    "name": "Dinner",
                    "items": [
                        {"food": "Firm tofu, 220 g", "kcal": 320, "protein_g": 34, "fibre_g": 2},
                        {"food": "Brown rice, 45 g dry", "kcal": 162, "protein_g": 3, "fibre_g": 2},
                        {"food": "Stir-fried vegetables", "kcal": 90, "protein_g": 4, "fibre_g": 6},
                    ],
                },
            ],
        }
    ],
    "_notes": "Repeat the day objects for all seven days. fibre_g is optional per item.",
}


def sum_day(day):
    totals = Counter()
    per_meal = []
    for meal in day.get("meals", []):
        m = Counter()
        for item in meal.get("items", []):
            for key in ("kcal", "protein_g", "fibre_g", "fat_g", "carb_g"):
                if item.get(key) is not None:
                    m[key] += float(item[key])
        per_meal.append((meal.get("name", "?"), m))
        totals.update(m)
    return totals, per_meal


def check_day(day, targets):
    totals, per_meal = sum_day(day)
    name = day.get("day", "?")
    failures, notices = [], []

    kcal_t = targets.get("kcal")
    if kcal_t:
        lo, hi = kcal_t * (1 - KCAL_TOLERANCE), kcal_t * (1 + KCAL_TOLERANCE)
        if not lo <= totals["kcal"] <= hi:
            direction = "under" if totals["kcal"] < lo else "over"
            failures.append(
                f"{totals['kcal']:.0f} kcal is {direction} target "
                f"{kcal_t:.0f} (allowed {lo:.0f}-{hi:.0f})"
            )

    prot_t = targets.get("protein_g")
    if prot_t:
        if totals["protein_g"] < prot_t * (1 - PROTEIN_SHORTFALL_OK):
            failures.append(
                f"protein {totals['protein_g']:.0f} g is under the {prot_t:.0f} g "
                f"floor by {prot_t - totals['protein_g']:.0f} g"
            )
        strong = sum(1 for _, m in per_meal if m["protein_g"] >= PER_MEAL_PROTEIN_G)
        if strong < MIN_MEALS_AT_THRESHOLD:
            biggest = max((m["protein_g"] for _, m in per_meal), default=0)
            notices.append(
                f"protein is bunched — only {strong} meal(s) clear "
                f"{PER_MEAL_PROTEIN_G} g (largest is {biggest:.0f} g). Spreading it "
                "across the day does more for muscle retention and satiety."
            )

    fib_t = targets.get("fibre_g")
    if fib_t and totals["fibre_g"]:
        if totals["fibre_g"] < fib_t * 0.8:
            notices.append(
                f"fibre {totals['fibre_g']:.0f} g against a {fib_t:.0f} g target — "
                "this day will be hungrier than it needs to be"
            )

    if len(per_meal) < 3:
        notices.append(f"only {len(per_meal)} eating occasions")

    return {
        "day": name,
        "kcal": round(totals["kcal"]),
        "protein_g": round(totals["protein_g"]),
        "fibre_g": round(totals["fibre_g"]),
        "meals": [(n, round(m["protein_g"])) for n, m in per_meal],
        "failures": failures,
        "notices": notices,
    }


def check_week(plan):
    targets = plan.get("targets", {})
    days = plan.get("days", [])
    results = [check_day(d, targets) for d in days]

    week = {"days": results, "failures": [], "notices": []}

    if len(days) != 7:
        week["notices"].append(
            f"{len(days)} day{'' if len(days) == 1 else 's'} in the plan, expected 7"
        )

    dishes = Counter()
    for d in days:
        for meal in d.get("meals", []):
            for item in meal.get("items", []):
                dishes[str(item.get("food", "")).split(",")[0].strip().lower()] += 1
    distinct = len(dishes)
    if distinct > MAX_DISTINCT_DISHES:
        week["notices"].append(
            f"{distinct} distinct foods across the week. Past roughly "
            f"{MAX_DISTINCT_DISHES} the shopping and prep load is what breaks "
            "adherence — lean harder on batch cooking and repeats."
        )
    elif distinct and distinct < 8:
        week["notices"].append(
            f"only {distinct} distinct foods — this will be boring by Thursday, "
            "and monotony is a top reason plans get abandoned."
        )

    week["distinct_foods"] = distinct
    week["failures"] = [f"{r['day']}: {f}" for r in results for f in r["failures"]]
    return week


def render(week, plan):
    out = []
    t = plan.get("targets", {})
    out.append(f"Targets: {t.get('kcal', '?')} kcal, {t.get('protein_g', '?')} g protein, "
               f"{t.get('fibre_g', '?')} g fibre")
    if plan.get("diet_pattern"):
        out.append(f"Diet pattern: {plan['diet_pattern']} "
                   "(check every item against this by eye — the script cannot)")
    out.append("")
    out.append(f"{'Day':<12}{'kcal':>7}{'protein':>9}{'fibre':>7}   protein by meal")
    out.append("-" * 68)
    for r in week["days"]:
        spread = "  ".join(f"{n[:5]} {p}g" for n, p in r["meals"])
        flag = "FAIL" if r["failures"] else ("~" if r["notices"] else "ok")
        out.append(f"{r['day'][:11]:<12}{r['kcal']:>7}{r['protein_g']:>9}"
                   f"{r['fibre_g']:>7}   {spread}   {flag}")

    if week["failures"]:
        out.append("")
        out.append("FAILURES — fix the day, do not move the target")
        for f in week["failures"]:
            out.append(f"  x {f}")

    notices = [f"{r['day']}: {n}" for r in week["days"] for n in r["notices"]] + week["notices"]
    if notices:
        out.append("")
        out.append("WORTH A LOOK")
        for n in notices:
            out.append(f"  - {n}")

    out.append("")
    out.append(f"{week['distinct_foods']} distinct foods across the week.")
    out.append("PASS — every day is within tolerance." if not week["failures"]
               else "NOT READY — days above are outside tolerance.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plan", nargs="?", help="path to week plan JSON")
    ap.add_argument("--example", action="store_true", help="print a template week file")
    ap.add_argument("--targets", help="optional JSON with targets, overriding the plan's")
    ap.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.plan:
        ap.error("give a week plan JSON file, or --example to get a template")

    with open(args.plan) as fh:
        plan = json.load(fh)
    plan.pop("_notes", None)

    if args.targets:
        with open(args.targets) as fh:
            supplied = json.load(fh)
        plan["targets"] = {k: supplied[k] for k in ("kcal", "protein_g", "fibre_g")
                           if k in supplied}
    if not plan.get("targets"):
        raise SystemExit("error: no targets in the plan and none supplied via --targets")
    if not plan.get("days"):
        raise SystemExit("error: plan has no days")

    week = check_week(plan)
    print(json.dumps(week, indent=2) if args.json else render(week, plan))
    return 1 if week["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
