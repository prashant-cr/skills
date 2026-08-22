#!/usr/bin/env python3
"""Parse a messy Indian prescription into structured, comparable entries.

Indian prescriptions use dosing notation that is compact, near-universal, and
completely opaque to anything expecting "twice daily" -- OD, BD, TDS, HS, SOS,
and the 1-0-1 morning-afternoon-night grid. Normalising it by hand every time
invites transcription errors, and a mis-read frequency silently changes the
daily dose, which is the number every later check depends on.

Anything it cannot parse confidently is flagged rather than guessed, because a
wrong guess here propagates into the duplication and interaction checks.

Usage:
    python3 parse_med_list.py --file meds.txt
    printf 'Tab Augmentin 625mg BD x 5 days\\nT. Ecosprin 75 OD\\n' | python3 parse_med_list.py

It does NOT resolve brand names to molecules -- that needs a live lookup and
Indian brands are reused across different formulations. Do that step next.
"""

import argparse
import re
import sys

# Frequency notation -> (doses per day, human reading). None = not a fixed count.
FREQ = {
    "OD": (1, "once daily"), "QD": (1, "once daily"), "ONCE": (1, "once daily"),
    "BD": (2, "twice daily"), "BID": (2, "twice daily"),
    "TDS": (3, "three times daily"), "TID": (3, "three times daily"),
    "QID": (4, "four times daily"), "QDS": (4, "four times daily"),
    "HS": (1, "at night"), "NOCTE": (1, "at night"), "ON": (1, "at night"),
    "OM": (1, "in the morning"), "MANE": (1, "in the morning"),
    "Q4H": (6, "every 4 hours"), "Q6H": (4, "every 6 hours"),
    "Q8H": (3, "every 8 hours"), "Q12H": (2, "every 12 hours"),
    "Q24H": (1, "every 24 hours"),
    "SOS": (None, "as required (PRN)"), "PRN": (None, "as required (PRN)"),
    "STAT": (None, "single immediate dose"),
    "OW": (None, "once weekly"), "WEEKLY": (None, "once weekly"),
    "EOD": (None, "alternate days"), "ALT": (None, "alternate days"),
}

FORMS = {
    "TAB": "tablet", "T": "tablet", "TABS": "tablet",
    "CAP": "capsule", "C": "capsule", "CAPS": "capsule",
    "INJ": "injection", "I": "injection",
    "SYP": "syrup", "SYR": "syrup", "SUSP": "suspension",
    "OINT": "ointment", "CR": "cream", "GEL": "gel",
    "DROPS": "drops", "GTT": "drops", "NEB": "nebulisation",
    "PATCH": "patch", "SUPP": "suppository", "SPRAY": "spray",
    "PWD": "powder", "SACHET": "sachet", "MDI": "inhaler", "INH": "inhaler",
}

ROUTES = {"PO", "IV", "IM", "SC", "SL", "PR", "PV", "TOP", "OD-EYE", "NEB", "ID", "IT"}

# FDC strengths are written slash-separated with one trailing unit: "40/12.5mg".
COMBO_STRENGTH = re.compile(
    r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)(?:\s*/\s*(\d+(?:\.\d+)?))?\s*"
    r"(mg|mcg|g|ml|iu)\b", re.I)
STRENGTH = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|units?|%)\b", re.I)
# Indian prescriptions routinely omit the unit: "Ecosprin 75", "Metformin 500".
BARE_STRENGTH = re.compile(r"(?<![\d.])(\d{2,4}(?:\.\d+)?)(?![\d.])")
GRID = re.compile(r"\b([01](?:\.5)?)\s*-\s*([01](?:\.5)?)\s*-\s*([01](?:\.5)?)\b")
DURATION = re.compile(r"(?:x|for)\s*(\d+)\s*(day|days|week|weeks|month|months)\b", re.I)


def parse_line(raw):
    """Return a dict for one prescription line, with a `flags` list for anything unclear."""
    line = raw.strip().rstrip(".")
    out = {"raw": raw.strip(), "form": None, "name": None, "strengths": [],
           "freq": None, "per_day": None, "duration": None, "route": None, "flags": []}
    if not line:
        return None

    work = line

    # Duration, then remove so it cannot be mistaken for a strength.
    m = DURATION.search(work)
    if m:
        out["duration"] = f"{m.group(1)} {m.group(2).lower()}"
        work = work[:m.start()] + " " + work[m.end():]

    # Dosage form prefix.
    m = re.match(r"^\s*([A-Za-z]{1,6})\.?\s+", work)
    if m and m.group(1).upper() in FORMS:
        out["form"] = FORMS[m.group(1).upper()]
        work = work[m.end():]

    # Strengths. Slash-separated FDC form first, then remove it so the single
    # pattern cannot re-match the trailing component on its own.
    cm = COMBO_STRENGTH.search(work)
    if cm:
        unit = cm.group(4).lower()
        for g in (cm.group(1), cm.group(2), cm.group(3)):
            if g:
                out["strengths"].append(f"{g}{unit}")
        work = work[:cm.start()] + " " + work[cm.end():]
        out["flags"].append("slash-separated strengths -- this is an FDC, resolve each molecule")

    for sm in STRENGTH.finditer(work):
        out["strengths"].append(f"{sm.group(1)}{sm.group(2).lower()}")

    # Frequency: the 1-0-1 grid first, since it is unambiguous.
    g = GRID.search(work)
    if g:
        parts = [float(x) for x in g.groups()]
        n = sum(1 for x in parts if x > 0)
        out["freq"] = g.group(0)
        out["per_day"] = n
        work = work[:g.start()] + " " + work[g.end():]
    else:
        for token in re.findall(r"\b[A-Za-z]{1,5}\b", work):
            t = token.upper()
            if t in FREQ:
                per_day, human = FREQ[t]
                out["freq"] = t
                out["per_day"] = per_day
                if per_day is None:
                    out["flags"].append(f"{t} = {human}; no fixed daily total")
                work = re.sub(rf"\b{re.escape(token)}\b", " ", work, count=1)
                break

    # Route.
    for token in re.findall(r"\b[A-Za-z]{2,3}\b", work):
        if token.upper() in ROUTES:
            out["route"] = token.upper()
            work = re.sub(rf"\b{re.escape(token)}\b", " ", work, count=1)
            break

    # Whatever survives, minus strengths and noise, is the drug name.
    name = STRENGTH.sub(" ", work)
    name = re.sub(r"\b(?:before|after|with|food|meals?|empty|stomach|daily|"
                  r"tablet|tablets|cap|caps|dose|doses|po)\b", " ", name, flags=re.I)
    name = re.sub(r"[^\w\s+/-]", " ", name)

    # A bare number left in the name is almost always an unlabelled strength.
    if not out["strengths"]:
        bm = BARE_STRENGTH.search(name)
        if bm:
            out["strengths"].append(f"{bm.group(1)} (unit not stated)")
            name = name[:bm.start()] + " " + name[bm.end():]
            out["flags"].append(
                f"strength '{bm.group(1)}' has no unit -- confirm mg vs mcg before dosing")

    name = re.sub(r"\s+", " ", name).strip(" -/+")
    out["name"] = name or None

    if not out["name"]:
        out["flags"].append("could not identify a drug name")
    if not out["strengths"]:
        out["flags"].append("no strength stated")
    if out["freq"] is None:
        out["flags"].append("no frequency stated")
    if len(out["strengths"]) > 1:
        out["flags"].append(f"{len(out['strengths'])} strengths -- likely an FDC; resolve each molecule")
    if out["name"] and len(out["name"].split()) > 4:
        out["flags"].append("name is long; check the parse split dose from name correctly")

    return out


def main():
    p = argparse.ArgumentParser(description="Parse an Indian prescription list.")
    p.add_argument("--file", help="File with one medication per line (default: stdin)")
    args = p.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    entries = [e for e in (parse_line(l) for l in text.split("\n")) if e]

    if not entries:
        print("No medication lines found.", file=sys.stderr)
        sys.exit(1)

    print("PARSED MEDICATION LIST")
    print(f"  Lines      {len(entries)}")
    flagged = [e for e in entries if e["flags"]]
    print(f"  Flagged    {len(flagged)}  (resolve these before checking interactions)")
    print()

    nw = max(max(len(e["name"] or "?") for e in entries), 12)
    sw = max(max(len(" + ".join(e["strengths"]) or "-") for e in entries), 8)
    print(f"  {'#':<3} {'Drug':<{nw}} {'Strength':<{sw}} {'Freq':<8} {'/day':<5} {'Duration':<10}")
    print(f"  {'-'*3} {'-'*nw} {'-'*sw} {'-'*8} {'-'*5} {'-'*10}")
    for i, e in enumerate(entries, 1):
        strengths = " + ".join(e["strengths"]) or "-"
        if e["per_day"] is not None:
            per_day = str(e["per_day"])
        elif e["freq"] is not None:
            per_day = "prn"
        else:
            per_day = "-"
        print(f"  {i:<3} {(e['name'] or '?'):<{nw}} {strengths:<{sw}} "
              f"{(e['freq'] or '-'):<8} {per_day:<5} {(e['duration'] or '-'):<10}")
    print()

    if flagged:
        print("  NEEDS RESOLVING")
        for i, e in enumerate(entries, 1):
            for f in e["flags"]:
                print(f"    {i}. {e['name'] or e['raw'][:30]}: {f}")
        print()

    print("  Next step: resolve every brand to its molecules before checking anything.")
    print("  A brand list cannot show duplication, and duplication across two FDCs is")
    print("  the commonest real finding in an Indian medication review.")
    print()
    print("  Frequencies are normalised, not verified. Where the prescription itself")
    print("  was ambiguous this reproduces the ambiguity -- it does not resolve it.")


if __name__ == "__main__":
    main()
