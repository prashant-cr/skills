#!/usr/bin/env python3
"""Compute trends and earnings-quality flags from reported financials.

Two reasons this is a script rather than mental arithmetic. First, CAGRs,
margin trends and ratio series are error-prone by hand and the errors are
invisible once they land in a write-up. Second, the flags below encode
divergences that are easy to miss when reading statements one year at a time —
profit rising while operating cash flow falls, receivables outgrowing sales —
and those divergences are where accounting problems announce themselves early.

This computes; it does not judge. A flag is a question to investigate, not a
verdict. Many have innocent explanations, and saying which applies is the
analyst's job.

Standard library only.

    python3 quality_check.py financials.json
    python3 quality_check.py financials.json --json
    python3 quality_check.py --example > financials.json
"""

import argparse
import json
import sys

EXAMPLE = {
    "company": "Example Ltd",
    "currency": "USD",
    "unit": "millions",
    "_comment": "Only 'year' and 'revenue' are required. Fill what the filings give you; "
                "omit the rest and those checks are skipped rather than guessed.",
    "years": [
        {"year": 2021, "revenue": 1000, "net_income": 100, "operating_cash_flow": 118,
         "capex": 40, "receivables": 150, "inventory": 90, "total_debt": 300,
         "shareholders_equity": 600, "diluted_shares": 100},
        {"year": 2022, "revenue": 1180, "net_income": 124, "operating_cash_flow": 130,
         "capex": 52, "receivables": 196, "inventory": 118, "total_debt": 340,
         "shareholders_equity": 700, "diluted_shares": 101},
        {"year": 2023, "revenue": 1370, "net_income": 152, "operating_cash_flow": 121,
         "capex": 61, "receivables": 268, "inventory": 157, "total_debt": 430,
         "shareholders_equity": 812, "diluted_shares": 103},
        {"year": 2024, "revenue": 1590, "net_income": 186, "operating_cash_flow": 112,
         "capex": 70, "receivables": 361, "inventory": 214, "total_debt": 560,
         "shareholders_equity": 940, "diluted_shares": 106},
    ],
}


def cagr(first, last, periods):
    if first is None or last is None or periods <= 0 or first <= 0 or last <= 0:
        return None
    return (last / first) ** (1.0 / periods) - 1


def get(row, key):
    value = row.get(key)
    return None if value in (None, "") else float(value)


def pct(value, digits=1):
    return "n/a" if value is None else f"{value * 100:.{digits}f}%"


def analyse(data):
    years = sorted(data.get("years", []), key=lambda r: r["year"])
    if len(years) < 2:
        raise ValueError("need at least two years of data to compute trends")

    span = len(years) - 1
    rows = []
    for row in years:
        revenue = get(row, "revenue")
        net_income = get(row, "net_income")
        cfo = get(row, "operating_cash_flow")
        capex = get(row, "capex")
        entry = {
            "year": row["year"],
            "revenue": revenue,
            "net_income": net_income,
            "operating_cash_flow": cfo,
            "capex": capex,
            "fcf": (cfo - capex) if (cfo is not None and capex is not None) else None,
            "net_margin": (net_income / revenue) if (net_income is not None and revenue) else None,
            "cfo_to_ni": (cfo / net_income) if (cfo is not None and net_income) else None,
            "receivables_pct_rev": (get(row, "receivables") / revenue)
                if (get(row, "receivables") is not None and revenue) else None,
            "inventory_pct_rev": (get(row, "inventory") / revenue)
                if (get(row, "inventory") is not None and revenue) else None,
            "debt_to_equity": (get(row, "total_debt") / get(row, "shareholders_equity"))
                if (get(row, "total_debt") is not None and get(row, "shareholders_equity")) else None,
            "roe": (net_income / get(row, "shareholders_equity"))
                if (net_income is not None and get(row, "shareholders_equity")) else None,
            "diluted_shares": get(row, "diluted_shares"),
        }
        rows.append(entry)

    first, last = rows[0], rows[-1]
    growth = {
        "revenue_cagr": cagr(first["revenue"], last["revenue"], span),
        "net_income_cagr": cagr(first["net_income"], last["net_income"], span),
        "fcf_cagr": cagr(first["fcf"], last["fcf"], span),
        "receivables_cagr": cagr(
            get(years[0], "receivables"), get(years[-1], "receivables"), span),
        "share_count_cagr": cagr(first["diluted_shares"], last["diluted_shares"], span),
    }

    flags = []

    # Cumulative cash conversion — the single most informative quality check.
    ni_total = sum(r["net_income"] for r in rows if r["net_income"] is not None)
    cfo_total = sum(r["operating_cash_flow"] for r in rows if r["operating_cash_flow"] is not None)
    if ni_total and cfo_total:
        conversion = cfo_total / ni_total
        if conversion < 0.8:
            flags.append(("HIGH", "cash conversion",
                          f"Cumulative operating cash flow is only {conversion:.2f}x cumulative net "
                          f"income. Reported profit is not turning into cash. Find out where it is "
                          f"going — working capital, or accrual-heavy revenue recognition."))
        elif conversion < 1.0:
            flags.append(("MEDIUM", "cash conversion",
                          f"Cumulative CFO/NI of {conversion:.2f}x is below 1. Worth explaining, "
                          f"though growth businesses legitimately absorb working capital."))

    # Profit rising while cash flow falls — the classic divergence.
    if (first["net_income"] and last["net_income"] and
            first["operating_cash_flow"] and last["operating_cash_flow"]):
        if last["net_income"] > first["net_income"] and last["operating_cash_flow"] < first["operating_cash_flow"]:
            flags.append(("HIGH", "profit/cash divergence",
                          "Net income rose across the period while operating cash flow fell. "
                          "This is the pattern that precedes most accounting restatements. "
                          "Reconcile it before trusting the earnings trend."))

    # Receivables outgrowing sales — collection or channel-stuffing question.
    if growth["receivables_cagr"] is not None and growth["revenue_cagr"] is not None:
        gap = growth["receivables_cagr"] - growth["revenue_cagr"]
        if gap > 0.10:
            flags.append(("HIGH", "receivables",
                          f"Receivables grew {pct(growth['receivables_cagr'])} a year against "
                          f"revenue at {pct(growth['revenue_cagr'])}. Sales are being booked "
                          f"faster than they are collected."))
        elif gap > 0.05:
            flags.append(("MEDIUM", "receivables",
                          f"Receivables growing {gap * 100:.1f}pp a year faster than revenue."))

    # Inventory build.
    inv = [r["inventory_pct_rev"] for r in rows if r["inventory_pct_rev"] is not None]
    if len(inv) >= 2 and inv[-1] > inv[0] * 1.25:
        flags.append(("MEDIUM", "inventory",
                      f"Inventory rose from {pct(inv[0])} of revenue to {pct(inv[-1])}. "
                      f"Check for obsolescence risk or slowing sell-through."))

    # Leverage trend.
    de = [r["debt_to_equity"] for r in rows if r["debt_to_equity"] is not None]
    if len(de) >= 2:
        if de[-1] > 2.0:
            flags.append(("HIGH", "leverage",
                          f"Debt/equity at {de[-1]:.2f}x. Check maturity schedule and interest cover."))
        elif de[-1] > de[0] * 1.5 and de[-1] > 0.5:
            flags.append(("MEDIUM", "leverage",
                          f"Debt/equity rose from {de[0]:.2f}x to {de[-1]:.2f}x. Ask what funded "
                          f"the growth, and whether returns justify it."))

    # Margin direction.
    margins = [r["net_margin"] for r in rows if r["net_margin"] is not None]
    if len(margins) >= 2:
        if margins[-1] < margins[0] - 0.02:
            flags.append(("MEDIUM", "margins",
                          f"Net margin compressed from {pct(margins[0])} to {pct(margins[-1])}. "
                          f"Pricing power or cost control is weakening."))

    # Dilution.
    if growth["share_count_cagr"] is not None and growth["share_count_cagr"] > 0.03:
        flags.append(("MEDIUM", "dilution",
                      f"Diluted share count growing {pct(growth['share_count_cagr'])} a year. "
                      f"Per-share growth is materially below headline growth."))

    return {"company": data.get("company"), "currency": data.get("currency"),
            "unit": data.get("unit"), "rows": rows, "growth": growth, "flags": flags}


def render(result):
    out = []
    header = f"{result.get('company') or 'Company'}"
    if result.get("unit") or result.get("currency"):
        header += f"   ({result.get('currency') or ''} {result.get('unit') or ''})".rstrip()
    out.append(header)
    out.append("=" * max(len(header), 60))
    out.append("")

    cols = ["year", "revenue", "net_income", "operating_cash_flow", "fcf"]
    heads = ["Year", "Revenue", "Net income", "CFO", "FCF"]
    out.append("  ".join(h.rjust(12) for h in heads))
    for row in result["rows"]:
        cells = []
        for col in cols:
            value = row.get(col)
            if value is None:
                text = "n/a"
            elif col == "year":
                text = str(int(value))
            else:
                text = f"{value:,.0f}"
            cells.append(text.rjust(12))
        out.append("  ".join(cells))
    out.append("")

    out.append("Ratios")
    out.append(f"  {'Year':>6}  {'Net margin':>11}  {'CFO/NI':>8}  {'Recv/Rev':>9}  {'D/E':>6}  {'ROE':>7}")
    for row in result["rows"]:
        conversion = row["cfo_to_ni"]
        leverage = row["debt_to_equity"]
        conversion_text = "n/a" if conversion is None else f"{conversion:.2f}x"
        leverage_text = "n/a" if leverage is None else f"{leverage:.2f}x"
        out.append(
            f"  {row['year']:>6}  {pct(row['net_margin']):>11}  "
            f"{conversion_text:>8}  "
            f"{pct(row['receivables_pct_rev']):>9}  "
            f"{leverage_text:>6}  "
            f"{pct(row['roe']):>7}")
    out.append("")

    growth = result["growth"]
    out.append("Growth (CAGR over the period)")
    for label, key in [("revenue", "revenue_cagr"), ("net income", "net_income_cagr"),
                       ("free cash flow", "fcf_cagr"), ("receivables", "receivables_cagr"),
                       ("share count", "share_count_cagr")]:
        out.append(f"  {label:<16} {pct(growth[key]):>8}")
    out.append("")

    if result["flags"]:
        out.append(f"Flags ({len(result['flags'])}) — questions to investigate, not conclusions")
        for severity, name, message in result["flags"]:
            out.append(f"  [{severity:<6}] {name}")
            for line in _wrap(message, 72):
                out.append(f"            {line}")
    else:
        out.append("No flags raised by these checks.")
        out.append("That is not a clean bill of health — it means these particular")
        out.append("divergences are absent. Read the notes to the accounts regardless.")
    return "\n".join(out)


def _wrap(text, width):
    words, line, lines = text.split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


def main():
    parser = argparse.ArgumentParser(description="Trend and earnings-quality checks from reported financials.")
    parser.add_argument("path", nargs="?", help="JSON file of yearly financials")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--example", action="store_true", help="print a template input file")
    args = parser.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.path:
        parser.error("path is required (or use --example)")

    try:
        with open(args.path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: could not read {args.path}: {exc}", file=sys.stderr)
        return 2

    try:
        result = analyse(data)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
