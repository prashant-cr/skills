#!/usr/bin/env python3
"""Work out what a token's supply schedule does to a holder.

Equity analysis has no real equivalent of this and it is where crypto valuations
most often quietly fail. A token can have growing users, rising fees and a falling
price at the same time, purely because supply is expanding faster than demand. The
market cap looks reasonable; the fully diluted value does not; and the gap between
them is a schedule of future selling that is already written down and public.

The number that matters to a holder is not the price target. It is how much the
price has to rise just to stand still as new supply arrives.

    python3 tokenomics_math.py --example > token.json
    python3 tokenomics_math.py token.json

Feed it the supply figures from live_data.py so nothing here comes from memory.
Standard library only.
"""

import argparse
import datetime
import json
import sys

EXAMPLE = {
    "symbol": "EXAMPLE",
    "price_usd": 0.42,
    "circulating_supply": 5_000_000_000,
    "total_supply": 10_000_000_000,
    "max_supply": 10_000_000_000,
    "volume_24h_usd": 45_000_000,
    "annual_emission_tokens": 400_000_000,
    "unlocks": [
        {"date": "2026-08-16", "tokens": 92_650_000, "note": "team and investor monthly"},
        {"date": "2026-09-16", "tokens": 92_650_000, "note": "team and investor monthly"},
        {"date": "2027-03-16", "tokens": 1_100_000_000, "note": "large investor cliff"}
    ],
    "_notes": {
        "unlocks": "from the project's published vesting schedule or a tracker. Omit "
                   "if unknown -- the script will say the schedule is unverified "
                   "rather than assume there is none.",
        "annual_emission_tokens": "new issuance per year from staking or mining, "
                                  "separate from unlocks of already-minted supply",
        "today": "optional ISO date to evaluate against; defaults to the real date"
    }
}


def pct(x):
    return f"{x * 100:.1f}%"


def analyse(t, today=None):
    warn, notes = [], []
    price = float(t["price_usd"])
    circ = float(t["circulating_supply"])
    total = float(t.get("total_supply") or 0) or None
    mx = float(t.get("max_supply") or 0) or None
    vol = float(t.get("volume_24h_usd") or 0) or None
    emission = float(t.get("annual_emission_tokens") or 0)

    if circ <= 0:
        raise SystemExit("error: circulating_supply must be positive")

    mcap = price * circ
    ultimate = mx or total
    fdv = price * ultimate if ultimate else None

    r = {"symbol": t.get("symbol", "?"), "price_usd": price,
         "market_cap_usd": mcap, "fdv_usd": fdv,
         "circulating_supply": circ, "total_supply": total, "max_supply": mx}

    if fdv:
        r["fdv_to_mcap"] = round(fdv / mcap, 2)
        r["float_pct"] = round(circ / ultimate * 100, 1)
        # The honest framing of dilution: at constant market cap, price falls by
        # exactly the share of supply not yet circulating.
        r["price_drag_to_full_float_pct"] = round((1 - circ / ultimate) * 100, 1)
        # And the inverse, which is what a holder needs: the rise required to keep
        # their money whole once every token exists.
        r["price_rise_needed_to_stand_still_pct"] = round((ultimate / circ - 1) * 100, 1)

        if r["fdv_to_mcap"] >= 3:
            warn.append(
                f"FDV is {r['fdv_to_mcap']}x market cap -- only {r['float_pct']}% of "
                f"supply is circulating. For a holder to break even by the time the "
                f"rest arrives, the price has to rise "
                f"{r['price_rise_needed_to_stand_still_pct']:.0f}% just to offset the "
                "new supply. That is the hurdle before any gain."
            )
        elif r["fdv_to_mcap"] >= 1.5:
            notes.append(
                f"FDV {r['fdv_to_mcap']}x market cap. Meaningful dilution ahead but not "
                "extreme -- treat the market cap as understating what you are paying for."
            )
        else:
            notes.append(f"FDV {r['fdv_to_mcap']}x market cap -- supply is largely issued, "
                         "so the market cap is close to the real price of the network.")
    else:
        warn.append("No total or max supply available, so dilution cannot be assessed. "
                    "Uncapped or unknown supply is itself a risk -- say so rather than "
                    "treating it as neutral.")

    if emission > 0:
        r["annual_inflation_pct"] = round(emission / circ * 100, 2)
        r["annual_emission_usd"] = emission * price
        if vol:
            r["emission_days_of_volume"] = round((emission * price) / vol, 1)
        if r["annual_inflation_pct"] >= 10:
            warn.append(
                f"Issuance runs {r['annual_inflation_pct']}% a year. Demand has to grow "
                "faster than that before the price can rise at all, which is a headwind "
                "that compounds against a holder every year they wait."
            )

    # --- unlock schedule -------------------------------------------------
    today = datetime.date.fromisoformat(today) if today else datetime.date.today()
    r["evaluated_on"] = today.isoformat()
    unlocks = t.get("unlocks")
    if not unlocks:
        warn.append("No unlock schedule supplied, so it is unverified rather than clean. "
                    "Check the project's vesting docs or a tracker before concluding "
                    "there is no cliff ahead -- an unchecked schedule has burned a lot "
                    "of otherwise sound theses.")
        r["unlocks"] = None
    else:
        rows, windows = [], {30: 0.0, 90: 0.0, 365: 0.0}
        for u in unlocks:
            try:
                d = datetime.date.fromisoformat(str(u["date"]))
            except (KeyError, ValueError):
                continue
            days = (d - today).days
            tokens = float(u.get("tokens") or 0)
            if days < 0 or tokens <= 0:
                continue
            usd = tokens * price
            row = {"date": d.isoformat(), "days_away": days, "tokens": tokens,
                   "usd": usd, "pct_of_float": round(tokens / circ * 100, 2),
                   "note": u.get("note", "")}
            if vol:
                # The most useful single number here. An unlock worth many days of
                # volume cannot be absorbed quietly even if only a fraction sells.
                row["days_of_volume"] = round(usd / vol, 1)
            rows.append(row)
            for w in windows:
                if days <= w:
                    windows[w] += tokens

        rows.sort(key=lambda x: x["days_away"])
        r["unlocks"] = rows
        r["unlock_windows"] = {
            f"next_{w}d": {"tokens": v, "pct_of_float": round(v / circ * 100, 2),
                           "usd": v * price,
                           "days_of_volume": (round(v * price / vol, 1) if vol else None)}
            for w, v in windows.items()
        }

        near = r["unlock_windows"]["next_90d"]
        if near["pct_of_float"] >= 10:
            warn.append(
                f"{near['pct_of_float']}% of the circulating float unlocks within 90 "
                f"days ({'$%.1fM' % (near['usd'] / 1e6)})"
                + (f", about {near['days_of_volume']} days of total trading volume"
                   if near["days_of_volume"] else "")
                + ". Supply of that size relative to liquidity tends to cap the price "
                "regardless of fundamentals, and waiting past the date is usually the "
                "better-odds trade than buying into it."
            )
        big = [x for x in rows if x["pct_of_float"] >= 5]
        if big:
            b = big[0]
            notes.append(f"Largest cliff ahead is {b['pct_of_float']}% of float on "
                         f"{b['date']} ({b['days_away']} days away) -- {b['note']}")

    r["warnings"], r["notes"] = warn, notes
    return r


def money(v):
    if v is None:
        return "n/a"
    for u, d in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= d:
            return f"${v / d:,.2f}{u}"
    return f"${v:,.0f}"


def render(r):
    o = [f"{r['symbol']} tokenomics   evaluated {r['evaluated_on']}", ""]
    o.append(f"  Price          ${r['price_usd']:,.6f}".rstrip("0").rstrip("."))
    o.append(f"  Market cap     {money(r['market_cap_usd'])}"
             + (f"      FDV {money(r['fdv_usd'])}   {r['fdv_to_mcap']}x"
                if r.get("fdv_to_mcap") else ""))
    if r.get("float_pct") is not None:
        o.append(f"  Float          {r['float_pct']}% of ultimate supply circulating")
        o.append(f"  Dilution       price falls {r['price_drag_to_full_float_pct']}% at "
                 "constant market cap once fully diluted")
        o.append(f"                 needs +{r['price_rise_needed_to_stand_still_pct']}% "
                 "just to stand still")
    if r.get("annual_inflation_pct") is not None:
        line = f"  Issuance       {r['annual_inflation_pct']}% a year"
        if r.get("emission_days_of_volume"):
            line += f"   ({r['emission_days_of_volume']} days of volume)"
        o.append(line)

    if r.get("unlocks"):
        o.append("")
        o.append("  Unlocks ahead")
        for w in ("next_30d", "next_90d", "next_365d"):
            u = r["unlock_windows"][w]
            dv = f"   {u['days_of_volume']} days of volume" if u["days_of_volume"] else ""
            o.append(f"    {w.replace('next_', '').replace('d', ' days'):>9}   "
                     f"{u['pct_of_float']:>6}% of float   {money(u['usd']):>10}{dv}")
        o.append("")
        for row in r["unlocks"][:8]:
            dv = f"  {row.get('days_of_volume', '')}d vol" if row.get("days_of_volume") else ""
            o.append(f"    {row['date']}  (+{row['days_away']:>4}d)  "
                     f"{row['pct_of_float']:>6}% float  {money(row['usd']):>10}{dv}"
                     f"   {row['note']}")

    if r["warnings"]:
        o.append("")
        o.append("  WARNINGS")
        for w in r["warnings"]:
            o.append(f"    ! {w}")
    if r["notes"]:
        o.append("")
        for n in r["notes"]:
            o.append(f"    - {n}")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("token", nargs="?")
    ap.add_argument("--example", action="store_true")
    ap.add_argument("--today", help="ISO date to evaluate against")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.token:
        ap.error("give a token JSON, or --example for a template")

    with open(args.token) as fh:
        t = json.load(fh)
    t.pop("_notes", None)
    r = analyse(t, args.today or t.get("today"))
    print(json.dumps(r, indent=2) if args.json else render(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
