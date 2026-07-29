#!/usr/bin/env python3
"""When newly listed shares become sellable — the post-listing supply calendar.

Newly listed companies have most of their shares locked. Those locks expire on a
schedule that is known the day the stock lists, and expiries have a track record
of producing sharp falls. Anyone deciding whether to hold rather than flip needs
these dates.

The arithmetic is trivial and the details are not: base dates differ within the
same market. In India anchor and pre-IPO lock-ins run from ALLOTMENT while
promoter lock-ins run from LISTING, which is a few days later. That is exactly
the kind of distinction that gets flattened when the dates are worked out in prose.

Rules current as of July 2026 and sourced per market below. Verify against the
prospectus, which states the actual dates for the specific issue and overrides
these defaults.

Standard library only.

    python3 lockin_calendar.py --market IN --listing 2026-08-14
    python3 lockin_calendar.py --market IN --listing 2026-08-14 --allotment 2026-08-11
    python3 lockin_calendar.py --list
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta

# base: "allotment" or "listing"; days: calendar days from that base
MARKETS = {
    "IN": {
        "name": "India (NSE / BSE, SEBI ICDR)",
        "events": [
            ("allotment", 30, "Anchor investors — 50% of their allocation unlocks"),
            ("allotment", 90, "Anchor investors — remaining 50% unlocks"),
            ("allotment", 182, "Pre-IPO non-promoter shareholders (approx. 6 months)"),
            ("listing", 182, "Promoter holding above the minimum contribution (approx. 6 months)"),
            ("listing", 548, "Promoter minimum contribution, 20% of post-issue capital (18 months)"),
        ],
        "note": "Anchor split into 30/90-day tranches since April 2022; before that all anchor "
                "shares unlocked at 30 days. Promoter lock-ins were cut to 18 months / 6 months "
                "by the SEBI ICDR Second Amendment 2021.",
    },
    "US": {
        "name": "United States (NYSE / NASDAQ)",
        "events": [
            ("listing", 180, "Standard IPO lock-up expiry — insiders and pre-IPO holders"),
        ],
        "note": "The 180-day lock-up is contractual with the underwriters, not a regulatory "
                "requirement, so it varies by deal and can include early-release triggers tied "
                "to price or to the first earnings report. Read the prospectus.",
    },
    "UK": {
        "name": "United Kingdom (LSE)",
        "events": [
            ("listing", 180, "Typical director and senior manager lock-up (commonly 180 days)"),
            ("listing", 365, "Longer lock-ups, where agreed (frequently 12 months for founders)"),
        ],
        "note": "No statutory lock-up. Periods are negotiated per deal and disclosed in the "
                "prospectus — treat these as conventions, not rules.",
    },
    "HK": {
        "name": "Hong Kong (HKEX)",
        "events": [
            ("listing", 182, "Controlling shareholders may not dispose of shares (6 months)"),
            ("listing", 365, "Controlling shareholders may not cease to be controlling (12 months)"),
        ],
        "note": "Set by the HKEX Listing Rules for controlling shareholders. Other pre-IPO "
                "holders are subject to deal-specific undertakings.",
    },
}


def parse_day(value, label):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{label} must be YYYY-MM-DD, got {value!r}")


def build(market, listing, allotment):
    bases = {"listing": listing, "allotment": allotment}
    events = []
    for base, days, label in market["events"]:
        when = bases[base] + timedelta(days=days)
        events.append({
            "date": when.isoformat(),
            "days_from_listing": (when - listing).days,
            "base": base,
            "description": label,
        })
    events.sort(key=lambda e: e["date"])
    return events


def main():
    parser = argparse.ArgumentParser(description="Post-listing lock-in expiry calendar.")
    parser.add_argument("--market", "-m", help="market code, e.g. IN, US, UK, HK")
    parser.add_argument("--listing", help="listing date, YYYY-MM-DD")
    parser.add_argument("--allotment", help="allotment date, YYYY-MM-DD (defaults to listing date)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--list", action="store_true", help="list supported markets")
    args = parser.parse_args()

    if args.list or not args.market:
        if not args.list:
            print("error: --market is required\n", file=sys.stderr)
        print("Supported markets:")
        for code, market in MARKETS.items():
            print(f"  {code:3}  {market['name']}")
        print("\nFor a market not listed, read the lock-up terms out of the prospectus directly.")
        return 0 if args.list else 2

    code = args.market.upper()
    if code not in MARKETS:
        print(f"error: unknown market {code!r}. Use --list to see supported codes.", file=sys.stderr)
        return 2
    if not args.listing:
        print("error: --listing is required.", file=sys.stderr)
        return 2

    try:
        listing = parse_day(args.listing, "--listing")
        allotment = parse_day(args.allotment, "--allotment") if args.allotment else listing
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if allotment > listing:
        print("error: allotment date cannot be after the listing date.", file=sys.stderr)
        return 2

    market = MARKETS[code]
    events = build(market, listing, allotment)
    payload = {"market": market["name"], "listing": listing.isoformat(),
               "allotment": allotment.isoformat(), "events": events, "note": market["note"]}

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Market:    {market['name']}")
    print(f"Listing:   {listing.isoformat()}")
    print(f"Allotment: {allotment.isoformat()}" + ("   (assumed same as listing)" if not args.allotment else ""))
    print()
    print("Supply events — shares becoming sellable")
    print(f"  {'Date':<12} {'+days':>6}  {'from':<9} Event")
    print(f"  {'-' * 12} {'-' * 6}  {'-' * 9} {'-' * 44}")
    for event in events:
        print(f"  {event['date']:<12} {event['days_from_listing']:>+6}  "
              f"{event['base']:<9} {event['description']}")
    print()
    print(f"Note: {market['note']}")
    print()
    print("The prospectus states the actual dates for this issue and overrides these")
    print("defaults. Treat expiries as supply events, not as forecasts — a lock-in ending")
    print("means shares CAN be sold, not that they will be.")

    if not args.allotment and code == "IN":
        print()
        print("** Allotment defaulted to the listing date. In India allotment is typically a few")
        print("   days earlier, and anchor and pre-IPO lock-ins run from allotment — so those")
        print("   dates above are slightly late. Pass --allotment for accuracy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
