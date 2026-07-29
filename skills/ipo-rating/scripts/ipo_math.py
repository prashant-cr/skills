#!/usr/bin/env python3
"""IPO arithmetic: issue structure, valuation against peers, and what you stand to win or lose.

Three calculations that decide most IPO questions and are all easy to get slightly
wrong by hand:

  --fresh / --ofs        how much of the money actually reaches the company
  --eps / --peer-pe      what the band implies versus comparable listed companies
  --gmp / --lot          the grey-market-implied listing outcome, shown alongside
                         the flat and down cases

That last one is deliberate. Grey market premium gets quoted as though it were the
only possible outcome. Printing the downside next to it, in the same units and on
the same screen, is the honest way to present an unregulated sentiment reading.

Standard library only.

    python3 ipo_math.py --fresh 500 --ofs 4500
    python3 ipo_math.py --band 100-105 --eps 4.2 --peer-pe 21
    python3 ipo_math.py --band 100-105 --gmp 31 --lot 142
"""

import argparse
import json
import sys


def parse_band(text):
    """Accept '100-105' or a single '105'. Returns (low, high)."""
    if "-" in text:
        low, high = text.split("-", 1)
        return float(low), float(high)
    price = float(text)
    return price, price


def main():
    parser = argparse.ArgumentParser(description="IPO structure, valuation and outcome arithmetic.")
    parser.add_argument("--band", help="price band, e.g. 100-105 (or a single price)")
    parser.add_argument("--gmp", type=float, help="grey market premium per share, in currency units")
    parser.add_argument("--lot", type=float, help="shares per lot / minimum application")
    parser.add_argument("--fresh", type=float, help="fresh issue size")
    parser.add_argument("--ofs", type=float, help="offer for sale size")
    parser.add_argument("--eps", type=float, help="earnings per share (state which year)")
    parser.add_argument("--peer-pe", type=float, dest="peer_pe", help="peer group P/E to compare against")
    parser.add_argument("--currency", default="", help="label for output, e.g. INR or $")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    if not any([args.band, args.fresh, args.ofs]):
        parser.error("give at least --band, or --fresh/--ofs")

    cur = f"{args.currency} " if args.currency else ""
    result = {}
    out = []

    # ---- issue structure -------------------------------------------------
    if args.fresh is not None or args.ofs is not None:
        fresh = args.fresh or 0.0
        ofs = args.ofs or 0.0
        total = fresh + ofs
        if total <= 0:
            print("error: fresh + ofs must be positive.", file=sys.stderr)
            return 2
        fresh_pct = fresh / total * 100
        result["issue"] = {"fresh": fresh, "ofs": ofs, "total": total, "fresh_pct": fresh_pct}

        out.append("ISSUE STRUCTURE")
        out.append(f"  Total issue      {cur}{total:,.0f}")
        out.append(f"  Fresh issue      {cur}{fresh:,.0f}   ({fresh_pct:.1f}%)  -> reaches the company")
        out.append(f"  Offer for sale   {cur}{ofs:,.0f}   ({100 - fresh_pct:.1f}%)  -> goes to selling shareholders")
        out.append("")
        if fresh_pct < 25:
            out.append("  ** Overwhelmingly an exit. Most of what you pay goes to existing holders,")
            out.append("     not into the business. Ask why they are selling, and why now.")
        elif fresh_pct < 60:
            out.append("  ** Mixed. A meaningful share is a shareholder exit — worth asking who is")
            out.append("     selling and how much of their stake goes.")
        else:
            out.append("  Predominantly a fundraising. Check use of proceeds: growth capex, debt")
            out.append("  repayment and 'general corporate purposes' are three different things.")
        out.append("")

    # ---- valuation against peers ----------------------------------------
    if args.band and args.eps is not None:
        low, high = parse_band(args.band)
        if args.eps <= 0:
            out.append("VALUATION")
            out.append("  EPS is zero or negative — no meaningful P/E exists. Value on revenue or")
            out.append("  gross profit against peers, and say the valuation rests on assumptions")
            out.append("  rather than earnings.")
            out.append("")
        else:
            pe_low, pe_high = low / args.eps, high / args.eps
            result["valuation"] = {"pe_at_low": pe_low, "pe_at_high": pe_high}
            out.append("VALUATION")
            out.append(f"  Issue P/E        {pe_low:.1f}x at {cur}{low:,.2f}   ->   {pe_high:.1f}x at {cur}{high:,.2f}")
            if args.peer_pe:
                premium = (pe_high / args.peer_pe - 1) * 100
                fair = args.peer_pe * args.eps
                result["valuation"].update({"peer_pe": args.peer_pe, "premium_pct": premium,
                                            "price_at_peer_pe": fair})
                out.append(f"  Peer group P/E   {args.peer_pe:.1f}x")
                out.append(f"  At upper band    {premium:+.1f}% vs peers")
                out.append(f"  Peer multiple implies {cur}{fair:,.2f} per share")
                out.append("")
                if premium > 25:
                    out.append("  ** Priced at a clear premium to listed peers. The report needs to say")
                    out.append("     what justifies it — and 'faster growth' needs evidence that the")
                    out.append("     growth is durable, not just recent.")
                elif premium < -15:
                    out.append("  Priced below peers. Check whether that is an opportunity or whether")
                    out.append("  the peers are not truly comparable.")
                else:
                    out.append("  Broadly in line with peers — little valuation cushion either way.")
            out.append("")

    # ---- listing outcomes ------------------------------------------------
    if args.band and args.gmp is not None:
        low, high = parse_band(args.band)
        implied = high + args.gmp
        gain_pct = (implied / high - 1) * 100
        result["listing"] = {"upper_band": high, "gmp": args.gmp,
                             "implied_price": implied, "implied_gain_pct": gain_pct}

        out.append("LISTING OUTCOMES  (applying at the upper band)")
        out.append(f"  Upper band       {cur}{high:,.2f}")
        out.append(f"  Grey market      {cur}{args.gmp:,.2f} per share")
        out.append(f"  Implied listing  {cur}{implied:,.2f}   ({gain_pct:+.1f}%)")
        out.append("")

        scenarios = [
            ("grey market holds", implied),
            ("lists flat", high),
            ("lists 10% below", high * 0.90),
            ("lists 20% below", high * 0.80),
        ]
        if args.lot:
            invested = high * args.lot
            result["lot"] = {"shares": args.lot, "invested": invested, "scenarios": []}
            out.append(f"  One lot = {args.lot:,.0f} shares = {cur}{invested:,.0f} invested")
            out.append("")
            unit = f" ({args.currency})" if args.currency else ""
            out.append(f"  {'Scenario':<20} {'Price':>10} {'Value':>12} {'P/L':>12}{unit}")
            out.append(f"  {'-' * 20} {'-' * 10} {'-' * 12} {'-' * 12}")
            for label, price in scenarios:
                value = price * args.lot
                pnl = value - invested
                result["lot"]["scenarios"].append(
                    {"scenario": label, "price": price, "value": value, "pnl": pnl})
                out.append(f"  {label:<20} {price:>10,.2f} {value:>12,.0f} {pnl:>+12,.0f}")
        else:
            out.append(f"  {'Scenario':<20} {'Price':>12} {'Return':>10}")
            out.append(f"  {'-' * 20} {'-' * 12} {'-' * 10}")
            for label, price in scenarios:
                out.append(f"  {label:<20} {cur}{price:>10,.2f} {(price / high - 1) * 100:>9.1f}%")

        out.append("")
        out.append("  Grey market premium is an unofficial, unregulated quote on thin volume. It")
        out.append("  can be moved by a small number of operators with an interest in the issue")
        out.append("  looking hot, it is least reliable on the most hyped issues, and it says")
        out.append("  nothing about where the stock trades a month later. Read it as sentiment,")
        out.append("  never as a forecast — the downside rows above are not decoration.")

    print(json.dumps(result, indent=2) if args.json else "\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
