#!/usr/bin/env python3
"""What growth rate does the current share price already imply?

Most stock analysis argues about whether a company is good. The market has
usually settled that question — what it has not settled is whether the price
demands more than the business can deliver. This inverts a DCF: instead of
guessing a growth rate to produce a fair value, it takes the price as given and
solves for the growth the market is paying for. You then judge one thing, which
is a far easier judgement than a forecast: is that achievable?

Two-stage model. Free cash flow grows for an explicit forecast period, then
grows at a terminal rate forever, discounted at the cost of equity.

Standard library only.

    # what growth does the price imply?
    python3 reverse_dcf.py --price 175 --shares 15.2e9 --fcf 95e9 --discount 0.10

    # what is it worth if growth is 8%?
    python3 reverse_dcf.py --price 175 --shares 15.2e9 --fcf 95e9 --discount 0.10 --growth 0.08

    # bear / base / bull
    python3 reverse_dcf.py --price 175 --shares 15.2e9 --fcf 95e9 --discount 0.10 \
        --scenarios 0.03,0.08,0.14
"""

import argparse
import json
import sys


def project_value(fcf0, growth, years, discount, terminal, fade=False):
    """Present value of a two-stage FCF stream.

    With fade=True the growth rate declines linearly from `growth` to `terminal`
    across the explicit period, which is closer to how competitive advantage
    actually decays than a cliff-edge drop in the final year.
    """
    if discount <= terminal:
        raise ValueError("discount rate must exceed terminal growth rate")

    pv = 0.0
    fcf = fcf0
    for year in range(1, years + 1):
        if fade and years > 1:
            g = growth + (terminal - growth) * (year - 1) / (years - 1)
        else:
            g = growth
        fcf *= (1 + g)
        pv += fcf / ((1 + discount) ** year)

    terminal_value = fcf * (1 + terminal) / (discount - terminal)
    pv += terminal_value / ((1 + discount) ** years)
    return pv


def solve_implied_growth(target, fcf0, years, discount, terminal, fade=False):
    """Bisect for the growth rate whose present value equals the market cap.

    Value is monotonically increasing in growth, so bisection is safe.
    """
    low, high = -0.90, 2.00

    if project_value(fcf0, low, years, discount, terminal, fade) > target:
        return None, "below"   # even collapse implies more value than the price
    if project_value(fcf0, high, years, discount, terminal, fade) < target:
        return None, "above"   # price demands more than 200% annual growth

    for _ in range(200):
        mid = (low + high) / 2
        if project_value(fcf0, mid, years, discount, terminal, fade) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2, "ok"


def interpret(growth):
    """Plain-language read on whether an implied growth rate is demanding."""
    pct = growth * 100
    if pct < 0:
        return ("The price implies FCF DECLINE. The market expects deterioration — "
                "check whether that pessimism is justified before treating it as cheap.")
    if pct < 5:
        return ("Undemanding. The price needs little growth to be justified, so the "
                "downside case does not depend on execution.")
    if pct < 10:
        return "Moderate. Broadly in line with a healthy mature business."
    if pct < 15:
        return ("Demanding. Requires sustained above-average growth — check the base "
                "rate for companies that actually held this over a decade.")
    if pct < 25:
        return ("Very demanding. Few businesses sustain this for the full forecast "
                "period. The burden of proof is on the bull case.")
    return ("Extreme. Priced for an outcome achieved by a small minority of companies "
            "in history. Treat with real scepticism.")


def main():
    parser = argparse.ArgumentParser(description="Reverse DCF: solve for the growth the price implies.")
    parser.add_argument("--price", type=float, required=True, help="current share price")
    parser.add_argument("--shares", type=float, required=True, help="diluted shares outstanding")
    parser.add_argument("--fcf", type=float, required=True,
                        help="starting annual free cash flow (or owner earnings), total not per share")
    parser.add_argument("--discount", type=float, default=0.10,
                        help="discount rate / cost of equity (default 0.10)")
    parser.add_argument("--terminal", type=float, default=0.025,
                        help="perpetual growth after the forecast period (default 0.025)")
    parser.add_argument("--years", type=int, default=10, help="explicit forecast years (default 10)")
    parser.add_argument("--fade", action="store_true",
                        help="fade growth linearly toward the terminal rate over the period")
    parser.add_argument("--growth", type=float, help="value the business at this growth rate instead")
    parser.add_argument("--scenarios", help="comma-separated growth rates, e.g. 0.03,0.08,0.14")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    if args.shares <= 0 or args.fcf == 0:
        print("error: --shares must be positive and --fcf non-zero.", file=sys.stderr)
        return 2
    if args.fcf < 0:
        print("note: negative starting FCF makes a DCF meaningless. Value the business on a",
              file=sys.stderr)
        print("      normalised or forward FCF instead, and say which you used.", file=sys.stderr)
        return 2

    market_cap = args.price * args.shares
    result = {
        "price": args.price,
        "shares": args.shares,
        "market_cap": market_cap,
        "starting_fcf": args.fcf,
        "discount_rate": args.discount,
        "terminal_growth": args.terminal,
        "forecast_years": args.years,
        "fade": args.fade,
    }

    lines = []
    lines.append(f"Market cap:      {market_cap:,.0f}")
    lines.append(f"Starting FCF:    {args.fcf:,.0f}   ({market_cap / args.fcf:.1f}x)")
    lines.append(f"Discount rate:   {args.discount:.1%}    Terminal: {args.terminal:.1%}"
                 f"    Horizon: {args.years}y{'  (fading)' if args.fade else ''}")
    lines.append("")

    try:
        if args.growth is not None:
            value = project_value(args.fcf, args.growth, args.years, args.discount,
                                  args.terminal, args.fade)
            per_share = value / args.shares
            upside = (per_share / args.price - 1) * 100
            result["scenario_growth"] = args.growth
            result["fair_value_per_share"] = per_share
            result["upside_pct"] = upside
            lines.append(f"At {args.growth:.1%} FCF growth:")
            lines.append(f"  intrinsic value:  {per_share:,.2f} per share")
            lines.append(f"  vs price {args.price:,.2f}:  {upside:+.1f}%")

        elif args.scenarios:
            rates = [float(r) for r in args.scenarios.split(",")]
            result["scenarios"] = []
            lines.append(f"{'Growth':>8}  {'Value/share':>13}  {'vs price':>10}")
            lines.append(f"{'-' * 8}  {'-' * 13}  {'-' * 10}")
            for rate in rates:
                value = project_value(args.fcf, rate, args.years, args.discount,
                                      args.terminal, args.fade)
                per_share = value / args.shares
                upside = (per_share / args.price - 1) * 100
                result["scenarios"].append(
                    {"growth": rate, "value_per_share": per_share, "upside_pct": upside})
                lines.append(f"{rate:>7.1%}  {per_share:>13,.2f}  {upside:>+9.1f}%")

        else:
            implied, status = solve_implied_growth(market_cap, args.fcf, args.years,
                                                   args.discount, args.terminal, args.fade)
            if status == "below":
                lines.append("The price is below the value of even a collapsing business.")
                lines.append("Either the market expects something this model cannot express")
                lines.append("(fraud, terminal decline, a broken balance sheet), or the FCF")
                lines.append("figure is unrepresentative. Investigate before calling it cheap.")
                result["implied_growth"] = None
            elif status == "above":
                lines.append("The price implies growth above 200% a year — the model cannot")
                lines.append("bracket it. The starting FCF is almost certainly depressed or")
                lines.append("unrepresentative; use normalised earnings instead.")
                result["implied_growth"] = None
            else:
                result["implied_growth"] = implied
                result["interpretation"] = interpret(implied)
                lines.append(f"IMPLIED FCF GROWTH: {implied:.2%} a year for {args.years} years")
                lines.append("")
                lines.append(interpret(implied))
                lines.append("")
                lines.append("This is what you now have to judge: can the business deliver that?")
                lines.append("That is a far more tractable question than forecasting a price.")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    lines.append("")
    lines.append("Sensitivity matters more than the point estimate — rerun with a discount rate")
    lines.append("1-2 points either side. If the conclusion flips, say so rather than quoting")
    lines.append("a single number with false confidence.")

    print(json.dumps(result, indent=2) if args.json else "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
