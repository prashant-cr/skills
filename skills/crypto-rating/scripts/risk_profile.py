#!/usr/bin/env python3
"""Turn someone's capacity for loss into a maximum position size, and show what that
position does in a crash.

The rating tells you whether an asset is worth owning. It cannot tell you whether
*this person* should own it, and in an asset class where 80% drawdowns happen to
the majors -- not the failures, the majors -- the size is the decision that
actually determines the outcome. Somebody who buys the best asset at a size they
cannot hold will sell it at the bottom and take the loss anyway.

So size is derived from the drawdown the asset can plausibly deliver, not from
conviction. A position is acceptable only if the person can still function after
it falls by the historical worst case for its tier.

    python3 risk_profile.py --example > profile.json
    python3 risk_profile.py profile.json --tier major
    python3 risk_profile.py profile.json --rank 98 --market-cap 1900000000

Standard library only. This is arithmetic on stated constraints, not advice.
"""

import argparse
import json
import sys

# Assumed peak-to-trough drawdown by tier, from what this asset class has actually
# done rather than what feels reasonable. Bitcoin fell 84% in 2018 and 77% in 2022;
# treating -80% as the majors' worst case is history, not pessimism. Anything small
# or new is sized on the assumption it goes to zero, because most of them do.
TIERS = {
    "major":     (0.80, "BTC or ETH -- multi-cycle history, deepest liquidity"),
    "large":     (0.90, "top ~20, survived at least one full cycle"),
    "mid":       (0.95, "roughly top 100, one cycle or less"),
    "small":     (1.00, "outside top 100, or under two years old"),
    "micro":     (1.00, "thin liquidity, very new, or unlisted on major venues"),
}

# Ceiling on total crypto as a share of net worth, by how much shock the person's
# situation can absorb. Deliberately conservative: this is the allocation someone
# can hold through a two-year drawdown without it changing their life.
ALLOC_CAP = {"fragile": 0.02, "moderate": 0.10, "resilient": 0.20}

# How much of the crypto allocation any single asset may occupy, by tier. Without
# this, a total-exposure cap alone lets one micro-cap take the entire sleeve and
# get sized identically to Bitcoin -- which is the opposite of what the tiers mean.
# Concentration is the risk that actually ruins people here: the tail is not that a
# small token falls, it is that it was the whole position when it did.
PER_ASSET_CAP = {"major": 1.00, "large": 0.40, "mid": 0.20, "small": 0.10, "micro": 0.05}

EXAMPLE = {
    "portfolio_usd": 40000,
    "max_loss_usd": 4000,
    "max_loss_pct": None,
    "horizon_months": 24,
    "emergency_fund_months": 6,
    "income_stability": "stable",
    "existing_crypto_usd": 4800,
    "uses_leverage": False,
    "money_needed_within_months": None,
    "has_held_through_a_crash": True,
    "_notes": {
        "portfolio_usd": "total investable net worth, excluding the home they live in",
        "max_loss_usd": "the loss they say they could absorb without it changing "
                        "their plans. Use max_loss_pct instead if they think in percent.",
        "income_stability": "stable | variable | none",
        "emergency_fund_months": "months of expenses in cash, outside investments",
        "money_needed_within_months": "null, or when they need this money back",
    },
}


def assess(p, tier):
    warnings, gates, notes = [], [], []

    portfolio = float(p["portfolio_usd"])
    if p.get("max_loss_usd") is not None:
        max_loss = float(p["max_loss_usd"])
    elif p.get("max_loss_pct") is not None:
        max_loss = portfolio * float(p["max_loss_pct"]) / 100.0
    else:
        raise SystemExit("error: give max_loss_usd or max_loss_pct")

    horizon = p.get("horizon_months")
    ef_months = p.get("emergency_fund_months")
    income = str(p.get("income_stability", "stable")).lower()
    existing = float(p.get("existing_crypto_usd") or 0)
    leverage = bool(p.get("uses_leverage"))
    need_by = p.get("money_needed_within_months")
    veteran = bool(p.get("has_held_through_a_crash"))

    dd, tier_desc = TIERS[tier]

    # --- gates: reasons not to buy at any size ---------------------------
    if ef_months is not None and float(ef_months) < 3:
        gates.append(
            f"Emergency fund is {ef_months} months. Below about three months, a job "
            "loss or a repair forces a sale at whatever price happens to exist that "
            "week, which is how a temporary drawdown becomes a permanent loss. Cash "
            "buffer first -- that is the higher-return decision here."
        )
    if need_by is not None and horizon and float(need_by) <= float(horizon):
        gates.append(
            f"This money is needed in {need_by} months. Crypto drawdowns have lasted "
            "two to three years, so capital with a deadline inside that window is not "
            "investable capital regardless of how good the asset is."
        )
    if need_by is not None and float(need_by) <= 12:
        gates.append(f"Needed within {need_by} months -- too soon for an asset that can "
                     "halve and stay there for a year.")
    if max_loss > portfolio * 0.5:
        warnings.append(
            f"A stated loss tolerance of {max_loss / portfolio:.0%} of net worth is "
            "unusually high. Worth testing before relying on it -- ask what would "
            "actually change in their life at that loss. People reliably overstate "
            "this in a calm market and discover the real number in a crash."
        )
    if leverage:
        warnings.append(
            "Leverage is in use. Position sizing below assumes spot holding. With "
            "leverage the relevant number is not the drawdown but the liquidation "
            "distance, and a -80% move liquidates any leveraged long long before the "
            "bottom. The sizing here does not apply."
        )
    if income == "none":
        warnings.append("No stable income, so there is no ability to replenish a loss "
                        "from earnings. Treat the allocation cap as a hard ceiling.")
    if not veteran:
        notes.append(
            "Has not held through a crash. The most common failure is not picking the "
            "wrong asset, it is selling the right one at the bottom. Sizing small "
            "enough that the position is boring is what makes holding possible."
        )

    # --- resilience -> allocation ceiling --------------------------------
    score = 0
    if ef_months is not None and float(ef_months) >= 6:
        score += 1
    if income == "stable":
        score += 1
    elif income == "none":
        score -= 1
    if horizon and float(horizon) >= 24:
        score += 1
    if veteran:
        score += 1
    if leverage:
        score -= 1
    band = "resilient" if score >= 3 else ("moderate" if score >= 1 else "fragile")
    alloc_cap_pct = ALLOC_CAP[band]

    # --- two independent caps, the tighter one wins ----------------------
    # From the loss budget: a position whose worst-case fall equals what they can lose.
    size_from_loss = max_loss / dd if dd else 0.0
    # From total exposure: everything already held counts against the ceiling.
    total_cap = portfolio * alloc_cap_pct
    size_from_alloc = max(0.0, total_cap - existing)

    # From concentration: no single asset should be the whole crypto sleeve unless
    # it is BTC or ETH.
    size_from_concentration = total_cap * PER_ASSET_CAP[tier]

    candidates = {
        "loss tolerance": size_from_loss,
        "total crypto exposure": size_from_alloc,
        f"single-asset concentration ({PER_ASSET_CAP[tier]:.0%} of the crypto sleeve)":
            size_from_concentration,
    }
    binding = min(candidates, key=candidates.get)
    max_position = max(0.0, candidates[binding])

    if gates:
        max_position = 0.0

    scenarios = []
    for pct in (0.30, 0.50, 0.80, 1.00):
        loss = max_position * pct
        scenarios.append({
            "drawdown_pct": int(pct * 100),
            "loss_usd": round(loss),
            "pct_of_portfolio": round(loss / portfolio * 100, 2),
            "within_budget": loss <= max_loss + 1e-9,
        })

    return {
        "tier": tier, "tier_desc": tier_desc, "assumed_drawdown_pct": int(dd * 100),
        "portfolio_usd": portfolio, "max_loss_usd": round(max_loss),
        "max_loss_pct_of_portfolio": round(max_loss / portfolio * 100, 2),
        "resilience_band": band, "alloc_cap_pct": round(alloc_cap_pct * 100, 1),
        "total_crypto_cap_usd": round(total_cap),
        "existing_crypto_usd": round(existing),
        "existing_crypto_pct": round(existing / portfolio * 100, 2),
        "size_from_loss_budget_usd": round(size_from_loss),
        "size_from_alloc_cap_usd": round(size_from_alloc),
        "size_from_concentration_usd": round(size_from_concentration),
        "per_asset_cap_pct": round(PER_ASSET_CAP[tier] * 100),
        "max_position_usd": round(max_position),
        "max_position_pct": round(max_position / portfolio * 100, 2),
        "binding_constraint": binding,
        "scenarios": scenarios,
        "gates": gates, "warnings": warnings, "notes": notes,
    }


def render(r):
    o = []
    if r["gates"]:
        o.append("=" * 70)
        o.append("DO NOT BUY AT ANY SIZE")
        o.append("=" * 70)
        for g in r["gates"]:
            o.append(f"  x {g}")
        o.append("")
        o.append("The asset may be excellent. This is about the circumstances, not the")
        o.append("asset, so say which and revisit once the blocker is cleared.")
        return "\n".join(o)

    o.append(f"  Tier assumed      {r['tier']} -- {r['tier_desc']}")
    o.append(f"  Worst case used   -{r['assumed_drawdown_pct']}%  (what this tier has "
             "actually done, not a guess)")
    o.append("")
    o.append(f"  Net worth         ${r['portfolio_usd']:,.0f}")
    o.append(f"  Can lose          ${r['max_loss_usd']:,.0f} "
             f"({r['max_loss_pct_of_portfolio']}% of net worth)")
    o.append(f"  Resilience        {r['resilience_band']} -> total crypto capped at "
             f"{r['alloc_cap_pct']}% (${r['total_crypto_cap_usd']:,.0f})")
    o.append(f"  Already in crypto ${r['existing_crypto_usd']:,.0f} "
             f"({r['existing_crypto_pct']}%)")
    o.append("")
    o.append(f"  Loss budget allows      ${r['size_from_loss_budget_usd']:,.0f}")
    o.append(f"  Exposure cap allows     ${r['size_from_alloc_cap_usd']:,.0f}")
    o.append(f"  Concentration allows    ${r['size_from_concentration_usd']:,.0f}"
             f"   (max {r['per_asset_cap_pct']}% of the crypto sleeve in one {r['tier']})")
    o.append(f"  MAX POSITION            ${r['max_position_usd']:,.0f} "
             f"({r['max_position_pct']}% of net worth)")
    o.append(f"  Bound by                {r['binding_constraint']}")
    o.append("")
    o.append("  If it falls:")
    for s in r["scenarios"]:
        mark = "ok" if s["within_budget"] else "EXCEEDS BUDGET"
        o.append(f"    -{s['drawdown_pct']:>3}%   -${s['loss_usd']:>10,}   "
                 f"{s['pct_of_portfolio']:>5}% of net worth   {mark}")
    o.append("")
    o.append("  Size it so the -100% row is survivable. In this asset class total loss")
    o.append("  is not a tail scenario for anything outside the majors -- it is the base")
    o.append("  rate, and most tokens ever launched are already there.")

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


def infer_tier(rank, market_cap):
    if rank and rank <= 2:
        return "major"
    if rank and rank <= 20:
        return "large"
    if rank and rank <= 100:
        return "mid"
    if market_cap is not None and market_cap < 50_000_000:
        return "micro"
    return "small"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("profile", nargs="?", help="path to profile JSON")
    ap.add_argument("--example", action="store_true", help="print a template profile")
    ap.add_argument("--tier", choices=sorted(TIERS), help="asset tier")
    ap.add_argument("--rank", type=int, help="market cap rank, to infer the tier")
    ap.add_argument("--market-cap", type=float, help="market cap in USD, to infer the tier")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.profile:
        ap.error("give a profile JSON, or --example for a template")

    with open(args.profile) as fh:
        p = json.load(fh)
    p.pop("_notes", None)

    tier = args.tier or infer_tier(args.rank, args.market_cap)
    if not args.tier and not args.rank and args.market_cap is None:
        print("note: no tier given, assuming 'small'. Pass --tier, or --rank/--market-cap "
              "from live_data.py so the drawdown assumption matches the asset.\n",
              file=sys.stderr)

    r = assess(p, tier)
    print(json.dumps(r, indent=2) if args.json else render(r))
    return 1 if r["gates"] else 0


if __name__ == "__main__":
    sys.exit(main())
