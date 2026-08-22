#!/usr/bin/env python3
"""Compute kidney function both ways, because drug labels and labs disagree.

The lab reports CKD-EPI eGFR, normalised to body surface area, for staging CKD.
Most drug labels define their dose adjustments against Cockcroft-Gault
creatinine clearance, which is not normalised and needs actual body weight.

These are different numbers. They diverge most in exactly the patients where
dosing errors matter -- the elderly, the very light, and the obese -- so using
the lab's eGFR to make a drug-dosing decision the label defined in CrCl terms
is a real and common error. This prints both and says which the label means.

Usage:
    python3 kidney_function.py --creatinine 1.4 --age 74 --sex F --weight 58
    python3 kidney_function.py --creatinine 1.4 --age 74 --sex F   # no weight
    python3 kidney_function.py --creatinine 0.6 --age 7 --sex M --height 122

Units: creatinine in mg/dL (pass --umol for micromol/L), weight kg, height cm.
"""

import argparse
import sys

CKD_STAGES = [
    (90, "G1", "Normal or high"),
    (60, "G2", "Mildly decreased"),
    (45, "G3a", "Mild to moderately decreased"),
    (30, "G3b", "Moderately to severely decreased"),
    (15, "G4", "Severely decreased"),
    (0, "G5", "Kidney failure"),
]


def ckd_epi_2021(scr, age, sex):
    """CKD-EPI 2021 creatinine equation, race-free. Returns mL/min/1.73m2."""
    female = sex == "F"
    k = 0.7 if female else 0.9
    a = -0.241 if female else -0.302
    egfr = 142 * min(scr / k, 1) ** a * max(scr / k, 1) ** -1.200 * 0.9938 ** age
    return egfr * 1.012 if female else egfr


def cockcroft_gault(scr, age, sex, weight):
    """Cockcroft-Gault creatinine clearance in mL/min. Needs actual weight."""
    crcl = ((140 - age) * weight) / (72 * scr)
    return crcl * 0.85 if sex == "F" else crcl


def schwartz(scr, height_cm):
    """Bedside Schwartz (2009) for children. Returns mL/min/1.73m2."""
    return 0.413 * height_cm / scr


def stage_for(egfr):
    for cutoff, stage, label in CKD_STAGES:
        if egfr >= cutoff:
            return stage, label
    return "G5", "Kidney failure"


def main():
    p = argparse.ArgumentParser(description="Kidney function for drug dosing.")
    p.add_argument("--creatinine", type=float, required=True, help="Serum creatinine, mg/dL")
    p.add_argument("--umol", action="store_true", help="Creatinine is in micromol/L")
    p.add_argument("--age", type=float, required=True, help="Age in years")
    p.add_argument("--sex", required=True, choices=["M", "F", "m", "f"])
    p.add_argument("--weight", type=float, help="Actual body weight, kg (Cockcroft-Gault needs it)")
    p.add_argument("--height", type=float, help="Height in cm (needed for children)")
    args = p.parse_args()

    scr = args.creatinine / 88.4 if args.umol else args.creatinine
    sex = args.sex.upper()
    age = args.age

    if scr <= 0:
        print("Creatinine must be positive.", file=sys.stderr)
        sys.exit(1)

    print("KIDNEY FUNCTION")
    print(f"  Creatinine    {scr:.2f} mg/dL"
          f"{f'  ({args.creatinine:.0f} umol/L)' if args.umol else ''}")
    print(f"  Patient       {age:.0f}y {sex}"
          f"{f', {args.weight:.0f} kg' if args.weight else ''}")
    print()

    if age < 18:
        print("  PAEDIATRIC")
        if args.height:
            e = schwartz(scr, args.height)
            print(f"    Bedside Schwartz   {e:.0f} mL/min/1.73m2")
        else:
            print("    Bedside Schwartz   needs --height; not computed")
        print()
        print("    Adult equations are not valid under 18. Paediatric dosing is")
        print("    per kilogram against a current measured weight, with a ceiling")
        print("    at the adult dose -- do not scale an adult dose down by eye.")
        print()
        return

    egfr = ckd_epi_2021(scr, age, sex)
    stage, label = stage_for(egfr)

    print(f"  CKD-EPI 2021 eGFR      {egfr:5.0f} mL/min/1.73m2   -> {stage}, {label}")
    if args.weight:
        crcl = cockcroft_gault(scr, age, sex, args.weight)
        print(f"  Cockcroft-Gault CrCl   {crcl:5.0f} mL/min          <- use for drug dosing")
        print()
        # An absolute gap matters less than whether the two land in different
        # dosing bands -- that is when the choice of equation changes the dose.
        THRESHOLDS = [60, 50, 30, 15]
        straddled = [t for t in THRESHOLDS if min(crcl, egfr) < t <= max(crcl, egfr)]
        diff = abs(crcl - egfr)

        if straddled:
            lower = "CrCl" if crcl < egfr else "eGFR"
            bands = ", ".join(str(t) for t in straddled)
            print(f"  ** These fall either side of {bands} mL/min -- a threshold drug")
            print("     labels commonly use. Which equation you pick changes the dose")
            print(f"     for some drugs here. The {lower} is the lower figure, so dosing")
            print("     off the other one would overdose this patient. Check each label.")
            print()
        elif diff >= 10:
            lower = "CrCl" if crcl < egfr else "eGFR"
            print(f"  ** These differ by {diff:.0f} mL/min. The {lower} is lower, and dosing")
            print("     off the higher number would overdose this patient. Check which")
            print("     measure the product label actually specifies before adjusting.")
            print()
    else:
        print(f"  Cockcroft-Gault CrCl      --  needs actual body weight")
        print()
        print("  ** No weight supplied, so the number most drug labels actually use")
        print("     could not be computed. Do not substitute the eGFR above for it:")
        print("     in a light or elderly patient it reads meaningfully higher, and")
        print("     dosing off it overdoses. Get the weight.")
        print()

    print("  Which to use")
    print("    Drug dosing        Cockcroft-Gault CrCl, unless the label says otherwise")
    print("    CKD staging        CKD-EPI eGFR")
    print("    Chemotherapy       per the specific protocol -- it will name the method")
    print()

    if egfr < 30:
        print("  At this level many drugs are contraindicated rather than reduced.")
        print("  Treat 'contraindicated below a threshold' and 'needs a lower dose'")
        print("  as different actions -- check each drug against its own label.")
        print()

    print("  A single creatinine is a snapshot. In acute illness it lags behind real")
    print("  function, so a rising creatinine means the true clearance is already")
    print("  lower than any of these numbers suggest.")


if __name__ == "__main__":
    main()
