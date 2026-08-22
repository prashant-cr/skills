#!/usr/bin/env python3
"""Find and optionally redact patient identifiers, tuned for Indian records.

Identifiers leaking into a shared context are a privacy problem and a safety
one -- a name carried into working text is how a note gets filed against the
wrong patient. Under India's DPDP Act 2023 health data is personal data with a
consent regime, and the treating institution is the data fiduciary.

This flags rather than silently deletes, because a clinician needs to know what
was removed in order to re-insert it into their own system at the end.

Usage:
    python3 deidentify.py --file notes.txt
    python3 deidentify.py --file notes.txt --redact > safe_notes.txt
    echo "Mr Ramesh Kumar, UHID 4471223" | python3 deidentify.py

Deliberately conservative about clinical numbers: a 3-digit dose or a lab value
must never be mistaken for an identifier, so patterns that could collide with
clinical data require nearby context words to fire.
"""

import argparse
import re
import sys

# Each rule: (label, compiled pattern, needs_context)
# Patterns that could collide with clinical values require a context word.
RULES = [
    ("AADHAAR", re.compile(r"\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b"), False),
    ("ABHA_HEALTH_ID", re.compile(r"\b\d{2}-\d{4}-\d{4}-\d{4}\b"), False),
    ("MOBILE", re.compile(r"(?:\+?91[\s-]?)?\b[6-9]\d{9}\b"), False),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b"), False),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), False),
    ("DATE", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-](?:19|20)\d{2}\b"), False),
    ("NAME_AFTER_TITLE", re.compile(
        r"\b(?:Mr|Mrs|Ms|Miss|Dr|Prof|Master|Baby|Smt|Shri|Sri)\.?\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"), False),
    # Context-dependent: these shapes are common in clinical data too.
    ("HOSPITAL_ID", re.compile(
        r"\b(?:UHID|MRN|MR\s?No|IP\s?No|OP\s?No|IPD|OPD|Reg(?:n|istration)?\s?No|"
        r"Patient\s?ID|Hosp(?:ital)?\s?No|Bed\s?No|CR\s?No)"
        r"\.?\s*[:\-]?\s*([A-Za-z0-9/-]{3,20})", re.I), False),
    ("PIN_CODE", re.compile(
        r"\b(?:PIN|Pincode|Pin\s?Code|Postal\s?Code)\.?\s*[:\-]?\s*(\d{6})\b", re.I), False),
    ("DOCTOR_REG", re.compile(
        r"\b(?:Reg|Registration|MCI|NMC|SMC)\.?\s?(?:No|Number)?\.?\s*[:\-]?\s*"
        r"([A-Z]{0,4}[\s/-]?\d{4,12})", re.I), False),
]

# Lines that look like an address block are worth flagging wholesale.
ADDRESS_HINT = re.compile(
    r"\b(?:address|resident of|r/o|s/o|w/o|d/o|village|taluka|tehsil|district)\b", re.I)


def scan(text):
    """Return (findings, redacted_text). findings = [(label, matched, line_no)]."""
    findings = []
    spans = []  # (start, end, label)

    for label, pattern, _ctx in RULES:
        for m in pattern.finditer(text):
            # For patterns with a capture group, redact only the identifier part,
            # keeping the label ("UHID:") so the clinician sees what was there.
            if m.groups():
                start, end = m.span(1)
            else:
                start, end = m.span(0)
            if not text[start:end].strip():
                continue
            spans.append((start, end, label))

    # Drop spans fully contained in an earlier, longer span (avoids a mobile
    # number inside an Aadhaar match being reported twice).
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    kept = []
    for s in spans:
        if any(s[0] >= k[0] and s[1] <= k[1] for k in kept):
            continue
        kept.append(s)

    for start, end, label in kept:
        line_no = text.count("\n", 0, start) + 1
        findings.append((label, text[start:end].strip(), line_no))

    for line_no, line in enumerate(text.split("\n"), 1):
        if ADDRESS_HINT.search(line):
            findings.append(("POSSIBLE_ADDRESS", line.strip()[:60], line_no))

    # Build redacted text back-to-front so offsets stay valid.
    redacted = text
    for start, end, label in sorted(kept, key=lambda s: -s[0]):
        redacted = redacted[:start] + f"[{label}]" + redacted[end:]

    findings.sort(key=lambda f: (f[2], f[0]))
    return findings, redacted


def main():
    p = argparse.ArgumentParser(description="Flag patient identifiers in clinical text.")
    p.add_argument("--file", help="File to scan (default: stdin)")
    p.add_argument("--redact", action="store_true",
                   help="Print the redacted text to stdout instead of the report")
    args = p.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    findings, redacted = scan(text)

    if args.redact:
        print(redacted, end="")
        print(f"\n[{len(findings)} identifier(s) redacted]", file=sys.stderr)
        return

    print("IDENTIFIER SCAN")
    print(f"  Source     {args.file or 'stdin'}")
    print(f"  Found      {len(findings)}")
    print()

    if not findings:
        print("  No identifiers matched. This is not proof the text is clean --")
        print("  a bare name with no title, or a local ID format not covered here,")
        print("  will not match. Read it before sharing.")
        return

    width = max(len(f[0]) for f in findings)
    print(f"  {'Line':<6} {'Type':<{width}}  Matched")
    print(f"  {'-' * 6} {'-' * width}  {'-' * 30}")
    for label, matched, line_no in findings:
        print(f"  {line_no:<6} {label:<{width}}  {matched}")
    print()
    print("  Remove these before drafting, and refer to the patient by age and sex.")
    print("  Re-insert them into the hospital system at the end -- they should not")
    print("  travel back through the draft.")
    print()
    print("  Pattern matching is a backstop, not a guarantee. Names without titles,")
    print("  employer names and rare local ID formats will slip through, so read the")
    print("  text yourself before it leaves the institution.")


if __name__ == "__main__":
    main()
