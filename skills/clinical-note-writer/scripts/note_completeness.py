#!/usr/bin/env python3
"""Check a drafted clinical document for sections the type requires.

This is a backstop against omission, not a check on truth. It reports whether a
section is present, and cannot tell you whether what is in it is correct or
whether it was invented -- only a clinician reading the source can do that.

Sections are graded by consequence, because "no discharge diagnosis" and "no
occupation recorded" are not the same problem and a flat checklist hides that.

Usage:
    python3 note_completeness.py --type discharge --file draft.md
    python3 note_completeness.py --list
"""

import argparse
import re
import sys

# grade: "blocks"  -- cannot be signed without it
#        "clinical" -- omission can cause harm downstream
#        "complete" -- worth having
REQUIREMENTS = {
    "discharge": [
        ("blocks", "Discharge diagnosis", ["discharge diagnosis", "final diagnosis", "diagnosis"]),
        ("blocks", "Discharge medications", ["discharge medic", "medications on discharge",
                                             "treatment on discharge", "rx on discharge", "advice on discharge"]),
        ("blocks", "Follow-up plan", ["follow.?up", "review in", "opd after", "next appointment"]),
        ("blocks", "Admission and discharge dates", ["date of admission", "doa", "date of discharge", "dod"]),
        ("clinical", "Reason for admission", ["presenting complaint", "reason for admission",
                                              "chief complaint", "c/o", "admitted with"]),
        ("clinical", "Hospital course", ["hospital course", "course in hospital",
                                         "clinical course", "progress"]),
        ("clinical", "Key investigations with values", ["investigation", "lab", "imaging", "reports"]),
        ("clinical", "Allergy status", ["allerg", "nkda", "no known drug"]),
        ("clinical", "Medication changes explained", ["stopped", "discontinued", "changed", "new medic"]),
        ("clinical", "Safety netting / return advice", ["return if", "report immediately",
                                                        "red flag", "seek medical", "come back if",
                                                        "emergency if", "warning sign"]),
        ("clinical", "Pending results to chase", ["pending", "awaited", "to follow", "result awaited"]),
        ("complete", "Procedures performed", ["procedure", "surgery", "operation", "intervention"]),
        ("complete", "Condition at discharge", ["condition at discharge", "status at discharge",
                                                "discharged in", "vitals at discharge"]),
        ("complete", "Diet and activity advice", ["diet", "activity", "lifestyle", "restrictions"]),
    ],
    "referral": [
        ("blocks", "Reason for referral", ["reason for referral", "referred for",
                                           "question", "seeking opinion", "kindly see"]),
        ("blocks", "Urgency", ["urgent", "routine", "soon", "priority", "within"]),
        ("blocks", "Current medications", ["medic", "drug", "treatment", "rx"]),
        ("clinical", "Relevant history", ["history", "h/o", "presenting", "background"]),
        ("clinical", "Examination findings", ["examination", "o/e", "on examination", "findings"]),
        ("clinical", "Investigations already done", ["investigation", "lab", "imaging", "already"]),
        ("clinical", "Allergy status", ["allerg", "nkda", "no known drug"]),
        ("complete", "What has already been tried", ["tried", "trialled", "failed", "previous treatment"]),
        ("complete", "Referrer contact", ["contact", "reachable", "phone", "email", "queries"]),
    ],
    "operative": [
        ("blocks", "Pre-operative diagnosis", ["pre.?op(?:erative)? diagnosis", "preop diagnosis"]),
        ("blocks", "Post-operative diagnosis", ["post.?op(?:erative)? diagnosis", "postop diagnosis"]),
        ("blocks", "Procedure performed", ["procedure", "operation performed", "surgery performed"]),
        ("blocks", "Surgeon", ["surgeon", "operated by", "primary surgeon"]),
        ("blocks", "Anaesthesia", ["anaesthe", "anesthe", "ga ", "spinal", "sedation"]),
        ("clinical", "Findings", ["finding", "intra.?op", "noted"]),
        ("clinical", "Procedure steps", ["steps", "technique", "incision", "approach"]),
        ("clinical", "Estimated blood loss", ["blood loss", "ebl"]),
        ("clinical", "Specimens sent", ["specimen", "histopath", "biopsy", "sent for"]),
        ("clinical", "Complications", ["complication", "uneventful", "no immediate"]),
        ("clinical", "Post-operative instructions", ["post.?op(?:erative)? (?:instruction|plan|care)",
                                                     "post.?op advice"]),
        ("complete", "Counts correct", ["count", "swab", "instrument"]),
        ("complete", "Implants or devices used", ["implant", "prosthes", "mesh", "device", "graft"]),
    ],
    "death": [
        ("blocks", "Immediate cause of death", ["immediate cause", "cause of death", "cod"]),
        ("blocks", "Antecedent and underlying cause", ["antecedent", "underlying", "due to"]),
        ("blocks", "Date and time of death", ["time of death", "date of death", "declared"]),
        ("blocks", "Admission date", ["date of admission", "doa", "admitted on"]),
        ("clinical", "Clinical course", ["course", "progress", "deteriorat"]),
        ("clinical", "Resuscitation attempted or DNR", ["resuscitat", "cpr", "dnr", "dnar", "not for"]),
        ("clinical", "Who was informed", ["informed", "relatives", "next of kin", "family"]),
        ("complete", "Post-mortem status", ["post.?mortem", "autopsy", "pm "]),
        ("complete", "Medico-legal case status", ["medico.?legal", "mlc", "police"]),
    ],
}


# A heading with nothing under it is not a completed section. Detecting this
# matters because the honest way to draft from thin notes is to leave labelled
# blanks -- so a heading-only check reports a skeleton as fully complete, which
# is the opposite of the signal the clinician needs.
PLACEHOLDER = re.compile(
    r"\[\s*(?:\]|_+\]|\.{2,}\]|[^\]]{0,40}(?:not recorded|not documented|not stated|"
    r"unknown|tbc|to be|blank|fill|insert|pending|\?{2,})[^\]]{0,40}\])"
    r"|_{3,}|\.{4,}|\bnot recorded\b|\bnot documented\b|\bnot stated\b"
    r"|\bnot in (?:the )?(?:source|notes)\b|\bno record\b", re.I)


def _section_is_empty(text, pos, window=260):
    """Is the text following a matched section heading only placeholders?"""
    chunk = text[pos:pos + window]
    # Judge only this section: stop at the next heading OR the next field label,
    # since most clinical documents are written as "Label: value" lines rather
    # than as markdown sections.
    nxt = re.search(r"\n\s*(?:#{1,6}\s|\*\*[A-Z]|[A-Z][A-Za-z ()/-]{2,40}\s*:)", chunk)
    if nxt:
        chunk = chunk[:nxt.start()]
    stripped = PLACEHOLDER.sub(" ", chunk)
    # Strip the heading punctuation and any label text that came with it.
    stripped = re.sub(r"[^A-Za-z0-9]+", " ", stripped).strip()
    return len(stripped) < 12


def check(doc_type, text):
    reqs = REQUIREMENTS[doc_type]
    low = text.lower()
    results = []
    for grade, label, patterns in reqs:
        found, empty = False, False
        for pat in patterns:
            m = re.search(pat, low)
            if m:
                found = True
                empty = _section_is_empty(text, m.end())
                break
        results.append((grade, label, found, empty))
    return results


def main():
    p = argparse.ArgumentParser(description="Check a clinical document for required sections.")
    p.add_argument("--type", choices=sorted(REQUIREMENTS), help="Document type")
    p.add_argument("--file", help="Draft file (default: stdin)")
    p.add_argument("--list", action="store_true", help="List supported document types")
    args = p.parse_args()

    if args.list:
        for t, reqs in sorted(REQUIREMENTS.items()):
            blocks = sum(1 for r in reqs if r[0] == "blocks")
            print(f"  {t:<12} {len(reqs)} checks, {blocks} blocking")
        return

    if not args.type:
        p.error("--type is required (or use --list)")

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    results = check(args.type, text)

    missing = [r for r in results if not r[2]]
    unfilled = [r for r in results if r[2] and r[3]]
    blocking = [r for r in missing if r[0] == "blocks"] + [r for r in unfilled if r[0] == "blocks"]

    print(f"COMPLETENESS -- {args.type}")
    print(f"  Checks     {len(results)}")
    print(f"  Present    {len(results) - len(missing)}")
    print(f"  Missing    {len(missing)}")
    print(f"  Unfilled   {len(unfilled)}  (heading present, no content)")
    print(f"  Blocking   {len(blocking)}")
    print()

    labels = {"blocks": "BLOCKS SIGN-OFF", "clinical": "Clinically important", "complete": "Completeness"}
    for grade in ("blocks", "clinical", "complete"):
        group = [r for r in missing if r[0] == grade]
        if not group:
            continue
        print(f"  {labels[grade]} -- absent")
        for r in group:
            print(f"    - {r[1]}")
        print()

    if unfilled:
        print("  PRESENT BUT UNFILLED -- heading only, nothing under it")
        for r in unfilled:
            tag = " (blocking)" if r[0] == "blocks" else ""
            print(f"    - {r[1]}{tag}")
        print()
        print("    Labelled blanks are the honest way to draft from thin notes, so")
        print("    this is not an error -- but they are gaps, not completed sections,")
        print("    and they belong in the gap report the clinician reads first.")
        print()

    if not missing and not unfilled:
        print("  Every checked section is present and has content.")
        print()

    print("  Presence only. This cannot tell you whether a section is accurate, or")
    print("  whether it was written from the source rather than composed to fill a")
    print("  gap -- which is the failure that matters. Read it against the notes.")

    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
