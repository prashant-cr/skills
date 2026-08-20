#!/usr/bin/env python3
"""Infer a company's work-email pattern and rank candidates for one person.

Every address this prints is a HYPOTHESIS. Sending to an unverified guess
bounces, and bounces damage the sending domain's reputation for every future
email -- including the ones to companies you researched correctly. Verify
before sending.

Usage:
    # Strongest: known addresses WITH the names behind them
    python3 email_pattern.py --domain acme.in \\
        --known "priya.sharma@acme.in:Priya Sharma,r.iyer@acme.in:Ravi Iyer" \\
        --name "Arjun Venkataraman"

    # Weaker: known addresses only, pattern inferred from shape
    python3 email_pattern.py --domain acme.in \\
        --known "priya.sharma@acme.in,r.iyer@acme.in" --name "Arjun Venkataraman"

    # Weakest: no samples, global frequency ordering only
    python3 email_pattern.py --domain acme.in --name "Arjun Venkataraman"

Handles the name forms that break naive first-dot-last logic: mononyms,
initial-prefixed South Indian names, and surnames long enough to be truncated.
"""

import argparse
import re
import sys

# Ordered by observed global frequency, most common first. Used to rank when
# there are no samples to infer from.
PATTERNS = [
    "first.last",
    "flast",
    "firstlast",
    "first",
    "f.last",
    "first_last",
    "firstl",
    "first-last",
    "lastfirst",
    "last.first",
    "l.first",
    "last",
    "f.l",
    "fl",
]

GENERIC_LOCALS = {
    "info", "contact", "hello", "sales", "support", "admin", "office",
    "enquiry", "enquiries", "inquiry", "team", "mail", "help", "care",
    "marketing", "hr", "careers", "jobs", "accounts", "billing", "no-reply",
    "noreply", "webmaster", "postmaster",
}


class Name:
    """A parsed personal name, tolerant of Indian forms."""

    def __init__(self, raw):
        self.raw = raw.strip()
        tokens = [t for t in re.split(r"[\s,]+", self.raw) if t]
        # Strip trailing dots from initials: "S." -> "S"
        tokens = [t.rstrip(".") for t in tokens if t.rstrip(".")]
        self.tokens = [t for t in tokens if t]
        self.initials = [t for t in self.tokens if len(t) == 1]
        self.words = [t for t in self.tokens if len(t) > 1]

        self.is_mononym = len(self.words) == 1
        # A leading single letter is an initial (father's name, village, house
        # name), not a given name -- "S. Venkatesh" means Venkatesh.
        self.leading_initial = (
            self.tokens[0] if self.tokens and len(self.tokens[0]) == 1 else None
        )

    def interpretations(self):
        """Return [(label, first, last)] -- plural, because these are ambiguous."""
        w = [x.lower() for x in self.words]
        out = []

        if not w:
            return out

        if len(w) == 1:
            # Mononym. The single word is the whole name.
            if self.leading_initial:
                # "S. Venkatesh" -- the mail system usually treats the initial
                # as the given name and the spoken name as the surname, giving
                # svenkatesh@ or s.venkatesh@. That reading comes first because
                # it is by far the most common in practice.
                ini = self.leading_initial.lower()
                out.append(("initial as given name", ini, w[0]))
                out.append(("mononym", w[0], ""))
                out.append(("initial as surname", w[0], ini))
            else:
                out.append(("mononym", w[0], ""))
            return out

        # Standard Western order.
        out.append(("given + family", w[0], w[-1]))

        # Some Indian records list family or village name first, so the
        # reverse reading is a real possibility worth generating.
        if len(w) >= 2:
            out.append(("reversed order", w[-1], w[0]))

        # Three or more words: the middle may be the operative surname.
        if len(w) >= 3:
            out.append(("given + middle as family", w[0], w[1]))

        return out


def truncations(word, lengths=(8, 6)):
    """Long surnames get cut by mail systems at whatever length someone chose."""
    return [word[:n] for n in lengths if len(word) > n]


def render(pattern, first, last):
    """Render one pattern for one (first, last) reading. '' if not applicable."""
    f = first[0] if first else ""
    l = last[0] if last else ""

    if not last:
        # Mononym: only the patterns that need no surname make sense.
        return {"first": first, "last": first, "firstlast": first}.get(pattern, "")

    return {
        "first.last": f"{first}.{last}",
        "firstlast": f"{first}{last}",
        "first_last": f"{first}_{last}",
        "first-last": f"{first}-{last}",
        "flast": f"{f}{last}",
        "f.last": f"{f}.{last}",
        "firstl": f"{first}{l}",
        "first.l": f"{first}.{l}",
        "first": first,
        "last": last,
        "lastfirst": f"{last}{first}",
        "last.first": f"{last}.{first}",
        "l.first": f"{l}.{first}",
        "f.l": f"{f}.{l}",
        "fl": f"{f}{l}",
    }.get(pattern, "")


def detect_from_pair(local, name):
    """Given a local-part and the name behind it, return matching pattern names."""
    local = local.lower()
    hits = []
    for label, first, last in Name(name).interpretations():
        for pat in PATTERNS:
            if render(pat, first, last) == local:
                hits.append(pat)
        # Also catch truncated surnames.
        if last:
            for t in truncations(last):
                for pat in ("first.last", "flast", "firstlast", "f.last"):
                    if render(pat, first, t) == local:
                        hits.append(pat + " (surname truncated)")
    return list(dict.fromkeys(hits))


def detect_from_shape(local):
    """No name available -- infer what we can from the local-part's shape."""
    local = local.lower()
    if "." in local:
        head, _, tail = local.partition(".")
        if len(head) == 1:
            return ["f.last", "f.l"]
        if len(tail) == 1:
            return ["first.l"]
        return ["first.last", "last.first"]
    if "_" in local:
        return ["first_last"]
    if "-" in local:
        return ["first-last"]
    if len(local) <= 6:
        return ["first", "flast"]
    return ["flast", "firstlast", "first"]


def main():
    p = argparse.ArgumentParser(description="Infer a work-email pattern and rank candidates.")
    p.add_argument("--domain", required=True, help="Company mail domain, e.g. acme.in")
    p.add_argument("--name", required=True, help="Target person's full name")
    p.add_argument("--known", default="",
                   help="Comma-separated known addresses. Use 'email:Full Name' where "
                        "the name is known -- that is much stronger evidence.")
    p.add_argument("--top", type=int, default=8, help="How many candidates to print")
    args = p.parse_args()

    domain = args.domain.strip().lower().lstrip("@")
    target = Name(args.name)

    if not target.words:
        print("Could not parse a name from --name.", file=sys.stderr)
        sys.exit(1)

    # --- Infer the pattern from samples -------------------------------------
    votes = {}
    samples_used = 0
    skipped_generic = []

    for entry in [e.strip() for e in args.known.split(",") if e.strip()]:
        if ":" in entry:
            addr, _, who = entry.partition(":")
        else:
            addr, who = entry, ""
        addr = addr.strip().lower()
        local = addr.split("@")[0]
        if not local:
            continue
        if local in GENERIC_LOCALS:
            skipped_generic.append(addr)
            continue

        found = detect_from_pair(local, who) if who.strip() else detect_from_shape(local)
        if found:
            samples_used += 1
            weight = 3 if who.strip() else 1
            for pat in found:
                votes[pat] = votes.get(pat, 0) + weight

    named_samples = sum(1 for e in args.known.split(",") if ":" in e)

    if votes:
        ranked = sorted(votes.items(), key=lambda kv: (-kv[1], PATTERNS.index(kv[0]) if kv[0] in PATTERNS else 99))
        best = [pat for pat, _ in ranked]
        if named_samples >= 2 and len(set(best[:1])) == 1 and ranked[0][1] >= 6:
            confidence = "high"
        elif named_samples >= 1:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        best = list(PATTERNS)
        confidence = "none"

    # Once the pattern is actually established, extra candidates are noise --
    # they invite the user to try alternatives that the evidence rules out.
    if confidence == "high":
        best = best[:1]
    elif confidence == "medium":
        best = best[:3]

    # --- Generate candidates -------------------------------------------------
    seen, candidates = set(), []
    for pat in best:
        base_pat = pat.replace(" (surname truncated)", "")
        for label, first, last in target.interpretations():
            variants = [(first, last, "")]
            if last:
                for t in truncations(last):
                    variants.append((first, t, "surname truncated"))
            for f_, l_, extra in variants:
                local = render(base_pat, f_, l_)
                if not local or local in seen:
                    continue
                seen.add(local)
                note = label if label != "given + family" else ""
                if extra:
                    note = f"{note}, {extra}".strip(", ")
                shown_pat = "mononym" if not l_ else base_pat
                candidates.append((f"{local}@{domain}", shown_pat, note))

    # --- Report --------------------------------------------------------------
    print("EMAIL PATTERN")
    print(f"  Domain           {domain}")
    print(f"  Target           {target.raw}")
    if target.is_mononym:
        print("                   (mononym -- no surname; common in South India)")
    if target.leading_initial:
        print(f"                   (leading initial '{target.leading_initial}' treated as an initial,")
        print("                    not a given name -- both readings generated)")
    print(f"  Samples used     {samples_used}"
          f"{f' ({named_samples} with names attached)' if named_samples else ''}")
    if skipped_generic:
        print(f"  Skipped          {', '.join(skipped_generic)} (role alias, not a person)")
    print(f"  Pattern          {best[0] if votes else 'unknown'}   confidence: {confidence}")
    print()

    if confidence == "none":
        print("  No usable samples. The ranking below is global frequency only, which")
        print("  is a weak prior. Find two or three known-good addresses at this domain")
        print("  first -- press releases, careers pages, conference speaker listings,")
        print("  open-source commits, PDF document metadata, WHOIS.")
        print()
    elif confidence == "low":
        print("  Samples had no names attached, so the pattern was inferred from the")
        print("  shape of the local-part alone. Treat the top candidate as a guess.")
        print()

    print(f"  {'#':<3} {'Candidate':<42} {'Pattern':<18} Note")
    print(f"  {'-' * 3} {'-' * 42} {'-' * 18} {'-' * 20}")
    for i, (addr, pat, note) in enumerate(candidates[: args.top], 1):
        print(f"  {i:<3} {addr:<42} {pat:<18} {note}")
    print()

    print("  VERIFY BEFORE SENDING. These are hypotheses, not findings.")
    print("  Treat an accept-all domain as unverified -- it answers yes to everything.")
    if target.is_mononym or target.leading_initial:
        print("  Indian name forms are the most error-prone case: collect three or four")
        print("  samples for this domain rather than two before trusting a pattern.")


if __name__ == "__main__":
    main()
