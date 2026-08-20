#!/usr/bin/env python3
"""Map deal size, category and company size onto the likely buying committee.

The seniority that can approve a purchase is a function of what it costs and
how big the company is -- not a fixed title. This encodes that mapping so the
answer is consistent rather than re-derived (differently) on every run.

Usage:
    python3 buying_committee.py --category saas --acv 1200000 --currency INR \
        --headcount 400

    python3 buying_committee.py --category marketing --acv 25000 \
        --currency USD --headcount 60 --founder-run yes

Output is a committee map: who owns the budget, who champions it, who can veto
it, and which seat to approach first.
"""

import argparse
import sys

# Static, approximate. Only used to place a deal in a tier, where being 15%
# off does not change the answer. Never present these as live rates.
FX_TO_USD = {
    "USD": 1.0,
    "INR": 1.0 / 88.0,
    "EUR": 1.10,
    "GBP": 1.28,
    "AED": 1.0 / 3.67,
    "SGD": 1.0 / 1.35,
    "AUD": 1.0 / 1.52,
    "CAD": 1.0 / 1.37,
}

# (upper bound in USD ACV, tier name, approving seniority)
TIERS = [
    (5_000, "team", "Team manager / first-line lead"),
    (30_000, "department", "Department head / Senior Manager or Director"),
    (120_000, "function", "Functional head (VP or CXO of that function)"),
    (500_000, "executive", "CXO of the function, co-signed by the CFO"),
    (float("inf"), "board", "CXO plus CFO, with board or promoter sign-off"),
]

# category -> (owning function, champion seat, typical user)
CATEGORIES = {
    "saas": ("IT / Engineering", "Engineering or Ops lead using the tool", "Individual engineers or operators"),
    "software": ("IT / Engineering", "Engineering or Ops lead using the tool", "Individual engineers or operators"),
    "security": ("Information Security / IT", "Security lead or SRE", "Security and platform teams"),
    "infrastructure": ("Engineering / Platform", "Platform or DevOps lead", "Engineering teams"),
    "data": ("Data / Analytics", "Head of Data or Analytics lead", "Analysts and data scientists"),
    "marketing": ("Marketing", "Head of Growth / Demand Gen lead", "Marketing team"),
    "sales": ("Sales / Revenue", "Sales Ops or a frontline sales leader", "Account executives"),
    "hr": ("HR / People", "HR Business Partner or Talent lead", "HR team and all employees"),
    "finance": ("Finance", "Financial Controller or FP&A lead", "Finance and accounting team"),
    "legal": ("Legal / Compliance", "In-house counsel or Compliance lead", "Legal team"),
    "logistics": ("Supply Chain / Operations", "Logistics or Warehouse manager", "Operations staff"),
    "manufacturing": ("Operations / Plant", "Plant Head or Production manager", "Plant and production staff"),
    "consulting": ("The function being served", "The manager who owns the problem", "That function's team"),
    "services": ("The function being served", "The manager who owns the problem", "That function's team"),
    "hardware": ("IT / Admin / Operations", "IT manager or Facilities lead", "Whoever uses the equipment"),
    "other": ("The function that owns the problem", "The manager who feels the pain", "That function's team"),
}


def fmt_money(amount, currency):
    if currency == "INR":
        if amount >= 10_000_000:
            return f"Rs {amount / 10_000_000:.2f} Cr"
        if amount >= 100_000:
            return f"Rs {amount / 100_000:.2f} L"
        return f"Rs {amount:,.0f}"
    symbol = {"USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency + " ")
    return f"{symbol}{amount:,.0f}"


def tier_for(acv_usd):
    for bound, name, approver in TIERS:
        if acv_usd < bound:
            return name, approver
    return TIERS[-1][1], TIERS[-1][2]


def size_band(headcount):
    if headcount < 50:
        return "micro"
    if headcount < 200:
        return "small"
    if headcount < 1000:
        return "mid"
    return "large"


def build(category, acv, currency, headcount, founder_run):
    rate = FX_TO_USD.get(currency.upper())
    if rate is None:
        print(f"Unknown currency '{currency}'. Known: {', '.join(sorted(FX_TO_USD))}", file=sys.stderr)
        sys.exit(1)

    acv_usd = acv * rate
    tier, approver = tier_for(acv_usd)
    band = size_band(headcount)
    owning, champion_seat, user_seat = CATEGORIES.get(category.lower(), CATEGORIES["other"])

    if founder_run == "auto":
        founder_run = "yes" if headcount < 200 else "no"
    founder_led = founder_run == "yes"

    rows = []
    notes = []

    # Micro companies do not have a committee. Saying so is more useful than
    # inventing an org chart.
    if band == "micro" or (founder_led and band == "small" and tier in ("function", "executive", "board")):
        rows.append(("Economic buyer", "Founder / CEO", "Approves everything at this size", True, "decide"))
        rows.append(("Champion", f"Founder, or the one person running {owning.lower()}", "Same person, or their only hire in the function", False, "persuade"))
        rows.append(("Technical / security", "Usually nobody formally", "No dedicated reviewer exists yet", False, "none"))
        rows.append(("Procurement / finance", "Founder, or an external CA / bookkeeper", "No procurement function", False, "none"))
        rows.append(("End user", user_seat, "Often the founder too", False, "persuade"))
        notes.append(
            "Under ~50 people the committee collapses into one person. Do not "
            "construct an org chart that does not exist -- write to the founder."
        )
        entry_note = (
            "The founder is the buyer, the champion and often the user. There is no "
            "committee to navigate and no one to be referred down to -- write to "
            "them directly, and keep it short."
        )
        return rows, notes, tier, approver, band, acv_usd, owning, entry_note

    # Economic buyer, adjusted for company size.
    buyer = approver
    if band == "small":
        notes.append(
            "At 50-200 people real delegation is partial. Expect the founder or "
            "CEO to be consulted even where the title suggests otherwise."
        )
        if tier in ("function", "executive", "board"):
            buyer = f"{approver} -- in practice the founder/CEO signs"
    elif band == "large":
        if tier == "team":
            buyer = "Department head -- process pushes even small spend up a level"
        if tier in ("team", "department"):
            notes.append(
                "Small deal, large company. One operator decides this -- do not "
                "build a five-person selling campaign for it. Procurement and "
                "security are process gates to schedule around, not stakeholders "
                "to persuade, and treating them as stakeholders is how a "
                "three-week deal becomes a three-month one."
            )

    rows.append(("Economic buyer", f"{owning} -- {buyer}", "Controls budget; can say yes", tier in ("executive", "board"), "decide"))
    rows.append(("Champion", champion_seat, "Feels the pain; sells it internally", tier in ("team", "department", "function"), "persuade"))

    # Security / technical reviewer only exists above a certain size, and its
    # presence depends heavily on category.
    tech_categories = {"saas", "software", "security", "infrastructure", "data", "hardware"}
    if category.lower() in tech_categories:
        if band in ("mid", "large"):
            tech = "CISO / Head of InfoSec, plus IT for access and SSO"
        else:
            tech = "Senior-most engineer or the IT generalist"
        rows.append(("Technical / security", tech, "Can say no on architecture, data handling or access", False, "gate"))
        if band in ("mid", "large"):
            notes.append(
                "Security review is where technical deals stall silently. Find "
                "this person before the first call, not at week six. The trust "
                "or security page on the company site often names them."
            )
    elif category.lower() in {"hr", "finance", "legal"}:
        rows.append(("Technical / security", "Legal or Compliance, and the DPO where personal data is involved", "Can say no on data protection and contract terms", False, "gate"))
    else:
        rows.append(("Technical / security", "Usually none for this category", "No formal reviewer expected", False, "none"))

    # Procurement appears as a real gate at size and at deal value.
    if band == "large" or tier in ("executive", "board"):
        rows.append(("Procurement / finance", "Procurement, with CFO or Financial Controller", "Owns contract, terms and timing; can stall a quarter", False, "gate"))
        notes.append(
            "Procurement is involved at this size and value. Ask about their "
            "vendor onboarding and security questionnaire early -- it is "
            "usually the longest pole and it is entirely predictable."
        )
    elif tier in ("department", "function") and band == "mid":
        rows.append(("Procurement / finance", "Financial Controller or Finance Manager", "Reviews spend; not usually a blocker at this value", False, "gate"))
    else:
        rows.append(("Procurement / finance", "Finance reviews the invoice, no formal gate", "Low friction at this value", False, "none"))

    rows.append(("End user", user_seat, "Determines whether it is actually adopted", False, "persuade"))

    if tier in ("team", "department", "function"):
        entry_note = (
            "Start here. The champion has the problem, and they will tell you who "
            "actually holds the budget -- which beats external research, because "
            "an insider's answer is current and yours is inferred."
        )
    else:
        entry_note = (
            "At this value the buyer is senior enough that starting with a champion "
            "risks stalling below the budget line. Lead with the buyer, but ask to "
            "be pointed down to whoever owns the problem rather than pitching."
        )
    return rows, notes, tier, approver, band, acv_usd, owning, entry_note


def main():
    p = argparse.ArgumentParser(description="Map a deal onto its likely buying committee.")
    p.add_argument("--category", default="other", help="What is being sold: " + ", ".join(sorted(CATEGORIES)))
    p.add_argument("--acv", type=float, required=True, help="Annual contract value, in --currency")
    p.add_argument("--currency", default="USD", help="Currency of --acv (default USD)")
    p.add_argument("--headcount", type=int, required=True, help="Approximate company headcount")
    p.add_argument("--founder-run", choices=["yes", "no", "auto"], default="auto",
                   help="Is the founder still running it? (default: auto from headcount)")
    args = p.parse_args()

    currency = args.currency.upper()
    rows, notes, tier, approver, band, acv_usd, owning, entry_note = build(
        args.category, args.acv, currency, args.headcount, args.founder_run
    )

    band_label = {"micro": "under 50", "small": "50-200", "mid": "200-1000", "large": "1000+"}[band]

    print("BUYING COMMITTEE")
    print(f"  Selling          {args.category} into {owning}")
    print(f"  Deal value       {fmt_money(args.acv, currency)} ACV", end="")
    if currency != "USD":
        print(f"   (~${acv_usd:,.0f} at an approximate static rate)")
    else:
        print()
    print(f"  Company size     {args.headcount:,} people  ({band_label})")
    print(f"  Approval tier    {tier}  ->  {approver}")
    print()

    seat_w = max(len(seat) for _r, seat, _w, _e, _k in rows)
    kind_label = {"decide": "DECIDES", "persuade": "persuade", "gate": "gate", "none": "-"}
    print(f"  {'Role':<22} {'Likely seat':<{seat_w}} {'Treat as':<9}")
    print(f"  {'-' * 22} {'-' * seat_w} {'-' * 9}")
    for role, seat, _why, is_entry, kind in rows:
        marker = "  <-- start here" if is_entry else ""
        print(f"  {role:<22} {seat:<{seat_w}} {kind_label[kind]:<9}{marker}")
    print()

    # The distinction that stops a small deal being over-engineered: the people
    # you must convince are not the same as the checkpoints you must clear.
    persuade = [r[0] for r in rows if r[4] in ("decide", "persuade")]
    gates = [r[0] for r in rows if r[4] == "gate"]
    print(f"  Convince {len(persuade)}: {', '.join(persuade)}")
    if gates:
        print(f"  Clear {len(gates)}: {', '.join(gates)}  -- schedule these, do not sell to them")
    else:
        print("  No formal gates expected at this size and value.")
    print()

    print("  What each seat does")
    for role, _seat, why, _entry, _kind in rows:
        print(f"    {role:<22} {why}")
    print()

    entry = next((r for r in rows if r[3]), None)
    if entry:
        print(f"  ENTRY POINT: {entry[0]} -- {entry[1]}")
        for line in _wrap(entry_note, 70):
            print(f"    {line}")
        print()

    if notes:
        print("  Notes")
        for n in notes:
            for line in _wrap(n, 72):
                print(f"    {line}")
            print()

    print("  This is a prior, not a finding. Confirm each seat against a live source")
    print("  and grade it Confirmed / Probable / Inferred before the user acts on it.")


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


if __name__ == "__main__":
    main()
