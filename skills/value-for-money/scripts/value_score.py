#!/usr/bin/env python3
"""Rank shortlisted products on cost of ownership, after adjusting ratings for evidence.

Two pieces of arithmetic decide most buying decisions and both are done badly by eye:

  * A rating means nothing without its sample size. 5.0 from 6 reviews is weaker
    evidence than 4.3 from 4,000, yet it sorts higher in every "sort by rating"
    list ever built. This uses a Wilson lower bound, which asks what the rating
    would be if the sample flattered the product as much as chance allows.
  * The sticker is not the cost. Ink, blades, pods, filters, subscriptions and
    batteries routinely cost more over three years than the device did. A printer
    at half the price with double the ink cost is not cheaper, and the gap is
    invisible at the moment of buying.

    python3 value_score.py --example > shortlist.json
    python3 value_score.py shortlist.json
    python3 value_score.py shortlist.json --years 5

Anything without source_url and fetched_at is listed but refused a ranking. Prices
move weekly and a remembered one silently decides the comparison.

Standard library only.
"""

import argparse
import json
import math
import sys

Z = 1.96          # 95% confidence
POSITIVE_STARS = (4, 5)

EXAMPLE = {
    "query": "over-ear noise cancelling headphones for daily commute",
    "currency": "INR",
    "years": 3,
    "quality_floor": 0.70,
    "quality_floor_note": "adjusted score below this fails the job regardless of price",
    "candidates": [
        {
            "name": "Brand A XM5",
            "price": 26990,
            "rating": 4.4,
            "review_count": 12038,
            "rating_histogram": {"5": 68, "4": 18, "3": 6, "2": 3, "1": 5},
            "consumable_per_year": 0,
            "subscription_per_year": 0,
            "accessories_once": 1500,
            "expected_resale": 8000,
            "warranty_years": 1,
            "source_url": "https://retailer.example/p/xm5",
            "fetched_at": "2026-08-02T09:14:00Z"
        },
        {
            "name": "Brand B Q45",
            "price": 18999,
            "rating": 4.3,
            "review_count": 3120,
            "rating_histogram": {"5": 62, "4": 21, "3": 8, "2": 4, "1": 5},
            "consumable_per_year": 0,
            "accessories_once": 0,
            "expected_resale": 4500,
            "warranty_years": 1,
            "source_url": "https://retailer.example/p/q45",
            "fetched_at": "2026-08-02T09:15:00Z"
        },
        {
            "name": "Unbranded ANC Pro",
            "price": 2499,
            "rating": 4.8,
            "review_count": 74,
            "rating_histogram": {"5": 93, "4": 3, "3": 1, "2": 1, "1": 2},
            "consumable_per_year": 0,
            "warranty_years": 0,
            "source_url": "https://marketplace.example/p/ancpro",
            "fetched_at": "2026-08-02T09:16:00Z"
        },
        {
            "name": "Brand C (price not readable)",
            "price": None,
            "rating": 4.5,
            "review_count": 900,
            "note": "listing rendered client-side, price not fetchable"
        }
    ],
    "_notes": {
        "rating_histogram": "percent or count per star. Optional but strongly "
                            "preferred -- the shape says more than the mean.",
        "consumable_per_year": "ink, pods, blades, filters, batteries",
        "expected_resale": "what it is worth at the end of the horizon, if you would sell",
        "provenance": "source_url + fetched_at are required to be ranked"
    }
}


def wilson_lower(pos, n, z=Z):
    """Lower bound of the 95% CI on the positive share.

    Sorting by raw average puts a 5.0-from-3-reviews above a 4.5-from-5,000, which
    is exactly backwards as evidence. This penalises small samples in proportion to
    how little they tell you.
    """
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, (centre - margin) / denom)


def histogram_flags(c):
    """Shape checks that a confidence interval cannot make.

    Wilson only asks 'how sure are we of this average'. It is perfectly happy with
    74 reviews at 93% five-star, because the sample is consistent -- consistency is
    exactly what manufactured reviews have. The tell is the shape: genuine products
    accumulate a middle. People who are mildly disappointed leave three stars, and
    shipping damage and duds leave ones. A distribution with almost nothing between
    the extremes has usually been helped.
    """
    hist = c.get("rating_histogram")
    n = c.get("review_count") or 0
    rating = c.get("rating")
    if not hist:
        # An absent histogram is missing evidence, not clean evidence. Without this
        # the shape checks simply never run, positive_share falls back to a crude
        # mean approximation, and Wilson barely penalises a small n -- so the exact
        # profile these checks exist to catch (high average, thin sample, no
        # breakdown) sails through and ranks FIRST on price. Observed: a 4.8 from
        # 91 reviews was returned as "best value" over two far better-evidenced
        # options.
        if rating is not None and n and n < 500 and rating >= 4.6:
            return ([f"rating shape unknown -- {rating} from only {n:,} reviews with no "
                     "star breakdown supplied. That average on that sample is the "
                     "profile manufactured reviews have, and without the histogram it "
                     "cannot be checked. Read the breakdown on the listing before "
                     "treating this rating as evidence."], None)
        return [], None
    vals = {int(k): float(v) for k, v in hist.items()}
    total = sum(vals.values())
    if total <= 0:
        return [], None
    share = {k: v / total for k, v in vals.items()}
    top = share.get(5, 0.0)
    middle = share.get(2, 0.0) + share.get(3, 0.0) + share.get(4, 0.0)
    bottom = share.get(1, 0.0)

    flags = []
    if top > 0.85 and middle < 0.12:
        flags.append(f"missing middle -- {top:.0%} five-star with only {middle:.0%} "
                     "spread across two, three and four. Real products collect a middle.")
    if top > 0.92:
        flags.append(f"{top:.0%} five-star is higher than well-reviewed flagship "
                     "products achieve, which is not a good sign.")
    if n >= 200 and bottom < 0.01:
        flags.append(f"almost no one-star reviews across {n:,} -- at that volume, "
                     "courier damage alone normally produces some.")
    if n and n < 100 and top > 0.85:
        flags.append(f"only {n} reviews and {top:.0%} of them perfect. Too few to "
                     "trust and too clean to be typical.")
    return flags, round(middle, 4)


def positive_share(c):
    """Share of reviews that are 4-5 star, from the histogram if present."""
    hist = c.get("rating_histogram")
    n = c.get("review_count") or 0
    if hist:
        vals = {int(k): float(v) for k, v in hist.items()}
        total = sum(vals.values())
        if total > 0:
            pos = sum(v for k, v in vals.items() if k in POSITIVE_STARS)
            return pos / total, n
    # No histogram: approximate from the mean. Crude, and flagged as such.
    r = c.get("rating")
    if r is None or n <= 0:
        return None, n
    return max(0.0, min(1.0, (r - 1.0) / 4.0)), n


def total_cost(c, years):
    price = c.get("price")
    if price is None:
        return None
    cost = float(price)
    cost += float(c.get("consumable_per_year") or 0) * years
    cost += float(c.get("subscription_per_year") or 0) * years
    cost += float(c.get("accessories_once") or 0)
    cost += float(c.get("shipping") or 0)
    # Warranty running out inside the horizon is a real expected cost, not a vibe.
    w = c.get("warranty_years")
    if w is not None and w < years:
        cost += float(c.get("out_of_warranty_risk") or 0)
    cost -= float(c.get("expected_resale") or 0)
    return cost


def evaluate(spec):
    years = float(spec.get("years") or 3)
    floor = float(spec.get("quality_floor") or 0.0)
    rows = []

    for c in spec["candidates"]:
        r = {"name": c.get("name", "?"), "price": c.get("price"),
             "rating": c.get("rating"), "review_count": c.get("review_count"),
             "sourced": bool(c.get("source_url") and c.get("fetched_at")),
             "source_url": c.get("source_url"), "fetched_at": c.get("fetched_at"),
             "note": c.get("note"), "warranty_years": c.get("warranty_years"),
             "errors": []}

        r["review_flags"], r["middle_share"] = histogram_flags(c)
        share, n = positive_share(c)
        if share is None:
            r["errors"].append("no rating or review count")
            r["adjusted"] = None
        else:
            r["adjusted"] = round(wilson_lower(share * n, n), 4)
            r["raw_positive_share"] = round(share, 4)
            r["histogram_used"] = bool(c.get("rating_histogram"))

        r["total_cost"] = total_cost(c, years)
        if r["total_cost"] is None:
            r["errors"].append("no price")

        if r["adjusted"] is not None and r["total_cost"] not in (None, 0):
            # Quality per unit of money. Only meaningful among options that already
            # clear the floor -- otherwise the cheapest inadequate thing always wins.
            r["value_per_1k"] = round(r["adjusted"] / (r["total_cost"] / 1000.0), 4)
        else:
            r["value_per_1k"] = None

        rows.append(r)

    rankable = [r for r in rows if r["sourced"] and not r["errors"]]
    unranked = [r for r in rows if r not in rankable]
    # Ratings that look manufactured are not a cheap option, they are an unknown
    # one. Leaving them in the price ranking lets the least trustworthy listing win
    # on the strength of the number that is least likely to be real.
    suspect = [r for r in rankable if r["review_flags"]]
    rankable = [r for r in rankable if not r["review_flags"]]
    meets = [r for r in rankable if r["adjusted"] >= floor]
    below = [r for r in rankable if r["adjusted"] < floor]
    meets.sort(key=lambda r: r["total_cost"])
    below.sort(key=lambda r: -r["adjusted"])

    return {"years": years, "quality_floor": floor, "currency": spec.get("currency", ""),
            "query": spec.get("query", ""), "meets": meets, "below_floor": below,
            "unranked": unranked, "suspect_reviews": suspect, "all": rows}


def money(v, cur):
    if v is None:
        return "n/a"
    sym = {"INR": "Rs ", "USD": "$", "GBP": "GBP ", "EUR": "EUR "}.get(cur, "")
    return f"{sym}{v:,.0f}"


def render(res):
    cur = res["currency"]
    o = []
    if res["query"]:
        o.append(f"  {res['query']}")
    o.append(f"  Horizon {res['years']:.0f} years   quality floor "
             f"{res['quality_floor']:.2f} adjusted")
    o.append("")
    o.append(f"  {'option':<26}{'price':>11}{'3yr cost':>11}{'rating':>9}{'adj':>7}{'n':>8}")
    o.append("  " + "-" * 72)
    for r in res["meets"]:
        o.append(f"  {r['name'][:25]:<26}{money(r['price'], cur):>11}"
                 f"{money(r['total_cost'], cur):>11}"
                 f"{(str(r['rating']) if r['rating'] else '-'):>9}"
                 f"{r['adjusted']:>7.2f}{(r['review_count'] or 0):>8,}")
    if res["meets"]:
        best = res["meets"][0]
        o.append("")
        o.append(f"  Best value: {best['name']} at {money(best['total_cost'], cur)} "
                 f"over {res['years']:.0f} years.")
        if len(res["meets"]) > 1:
            nxt = res["meets"][1]
            gap = nxt["total_cost"] - best["total_cost"]
            if nxt["adjusted"] > best["adjusted"]:
                # Paying more buys a better-evidenced product: a real trade-up.
                o.append(f"  The runner-up costs {money(gap, cur)} more and scores "
                         f"{nxt['adjusted']:.2f} against {best['adjusted']:.2f} -- worth it "
                         "only if that gap matters for your use.")
            else:
                # Costs more AND scores lower. Saying "worth it if the difference
                # matters" here would imply the extra money buys something.
                o.append(f"  Everything else costs more and scores no better -- "
                         f"the runner-up is {money(gap, cur)} more at "
                         f"{nxt['adjusted']:.2f} against {best['adjusted']:.2f}. "
                         "There is no trade-up here, just a worse deal.")
    else:
        o.append("  Nothing on this shortlist clears the quality floor.")

    if res["below_floor"]:
        o.append("")
        o.append("  BELOW THE QUALITY BAR -- not ranked on price")
        for r in res["below_floor"]:
            why = (f"{r['review_count']:,} reviews" if r.get("review_count")
                   else "too few reviews")
            o.append(f"    x {r['name'][:24]:<26}{money(r['price'], cur):>11}   "
                     f"adjusted {r['adjusted']:.2f} from {why}")
        o.append("    A high average on a thin sample is not evidence. Buying the")
        o.append("    cheapest thing that cannot do the job wastes all of the money,")
        o.append("    not some of it.")

    if res["suspect_reviews"]:
        o.append("")
        o.append("  RATINGS NOT CREDIBLE -- excluded from the ranking")
        for r in res["suspect_reviews"]:
            o.append(f"    x {r['name'][:24]:<26}{money(r['price'], cur):>11}   "
                     f"{r['rating']} from {(r['review_count'] or 0):,}")
            for f in r["review_flags"]:
                o.append(f"        - {f}")
        o.append("    Not a claim that the product is bad -- a claim that the rating")
        o.append("    is not evidence about it. Judge these on the seller, the")
        o.append("    warranty and a returns policy you can actually use.")

    if res["unranked"]:
        o.append("")
        o.append("  NOT RANKED")
        for r in res["unranked"]:
            why = ", ".join(r["errors"]) or "price or rating not verified with a source"
            if not r["sourced"] and "no price" not in why:
                why += " (no source_url + fetched_at)"
            o.append(f"    ? {r['name'][:30]:<32} {why}")
            if r.get("note"):
                o.append(f"      {r['note']}")
        o.append("    Get these from the live listing before deciding. A price you")
        o.append("    cannot point at is one that quietly decides the comparison.")

    o.append("")
    o.append("  'adj' is a 95% lower bound on the share of positive reviews, so a")
    o.append("  small sample scores below its average on purpose. Compare adj, not stars.")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--example", action="store_true")
    ap.add_argument("--years", type=float)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.spec:
        ap.error("give a shortlist JSON, or --example for a template")

    with open(args.spec) as fh:
        spec = json.load(fh)
    spec.pop("_notes", None)
    if args.years:
        spec["years"] = args.years
    if not spec.get("candidates"):
        raise SystemExit("error: no candidates to compare")

    res = evaluate(spec)
    print(json.dumps(res, indent=2) if args.json else render(res))
    return 0 if res["meets"] else 2


if __name__ == "__main__":
    sys.exit(main())
