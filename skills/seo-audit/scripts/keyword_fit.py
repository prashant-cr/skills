#!/usr/bin/env python3
"""Rank keyword candidates by whether THIS site can actually rank for them.

The failure mode this exists to stop: a keyword list chosen on search volume.
Volume tells you what a term is worth if you win it, and nothing at all about
whether you can. A six-month-old site handed "project management software" gets
a year of work and no traffic, while the terms it could have owned went to
somebody else.

Winnability is mostly decided by one thing that is free to check: who currently
ranks. A top ten of strong, on-intent pages from established domains is closed
for now regardless of any difficulty score. A top ten containing forum threads,
outdated posts, or pages that miss the intent has a door in it -- those are the
terms where a small site beats a big one, and they are invisible to volume-first
research.

    python3 keyword_fit.py --example > keywords.json   # documented input
    python3 keyword_fit.py keywords.json
    python3 keyword_fit.py keywords.json --json scored.json

Candidates without SERP evidence are listed but refused a score. A guess about
who ranks is the one input that cannot be reconstructed later, and scoring one
produces a confident number resting on nothing.

Standard library only.
"""

import argparse
import json
import sys

# Authority proxies. Real link metrics need a paid index; these tiers are what
# can honestly be judged from age, brand recognition and existing footprint.
AUTHORITY = {"new": 5, "low": 20, "medium": 45, "high": 70, "very_high": 85}

# Result types that represent an opening. A forum thread ranking on page one
# means Google could not find a good page -- the clearest buy signal in search.
WEAK_TYPES = {"forum", "ugc", "thin", "off_intent", "outdated", "aggregator",
              "social", "unrelated"}
STRONG_TYPES = {"brand", "publisher", "competitor", "marketplace", "gov", "edu"}

INTENTS = {"informational", "commercial", "transactional", "navigational", "local"}

# Roughly what share of clicks organic position 1 keeps once the SERP furniture
# is in place. These are directional, not measured for your market -- they exist
# so a term that cannot deliver clicks even at #1 stops outranking one that can.
FEATURE_COST = {
    "ai_overview": 0.30,
    "ads_top": 0.15,
    "shopping_pack": 0.15,
    "local_pack": 0.20,
    "video_pack": 0.10,
    "featured_snippet_other": 0.15,   # someone else holds it
    "people_also_ask": 0.05,
    "sitelinks_competitor": 0.05,
}

TIERS = [
    (65, "NOW", "0-3 months", "Start here. The gap is small or the SERP has an opening."),
    (45, "NEXT", "3-6 months", "Reachable after the Now tier lands and links accrue."),
    (30, "LATER", "6-12 months", "Needs authority the site does not have yet."),
    (0, "SKIP", "not on this horizon",
        "The incumbents are strong and on-intent. Effort is better spent elsewhere."),
]

EXAMPLE = {
    "site": {
        "domain": "example-crm.com",
        "authority": "low",
        "authority_basis": "18 months old, ~40 referring domains (Search Console + "
                           "free backlink checker), ranks top-20 for 6 long-tail terms",
        "topical_depth": {"crm": "medium", "invoicing": "none"}
    },
    "candidates": [
        {
            "term": "crm for freelance designers",
            "intent": "commercial",
            "volume_band": "long",
            "business_value": 5,
            "cluster": "crm",
            "have_page": None,
            "current_position": None,
            "serp": {
                "results": [
                    {"type": "publisher", "authority": "high"},
                    {"type": "forum", "authority": "high"},
                    {"type": "competitor", "authority": "medium"},
                    {"type": "off_intent", "authority": "high"},
                    {"type": "thin", "authority": "low"},
                    {"type": "competitor", "authority": "medium"},
                    {"type": "ugc", "authority": "medium"},
                    {"type": "publisher", "authority": "medium"},
                    {"type": "outdated", "authority": "medium"},
                    {"type": "competitor", "authority": "low"}
                ],
                "features": ["people_also_ask"],
                "checked_on": "2026-08-15"
            }
        },
        {
            "term": "best crm software",
            "intent": "commercial",
            "volume_band": "head",
            "business_value": 4,
            "cluster": "crm",
            "have_page": None,
            "current_position": None,
            "serp": {
                "results": [{"type": "publisher", "authority": "very_high"}] * 4
                           + [{"type": "competitor", "authority": "very_high"}] * 4
                           + [{"type": "publisher", "authority": "high"}] * 2,
                "features": ["ai_overview", "ads_top", "people_also_ask"],
                "checked_on": "2026-08-15"
            }
        },
        {
            "term": "how to track client invoices spreadsheet",
            "intent": "informational",
            "volume_band": "mid",
            "business_value": 2,
            "cluster": "invoicing",
            "have_page": "https://example-crm.com/blog/invoice-tracking",
            "current_position": 14,
            "serp": {
                "results": [
                    {"type": "publisher", "authority": "medium"},
                    {"type": "thin", "authority": "low"},
                    {"type": "ugc", "authority": "high"},
                    {"type": "publisher", "authority": "medium"},
                    {"type": "outdated", "authority": "medium"},
                    {"type": "forum", "authority": "high"},
                    {"type": "publisher", "authority": "low"},
                    {"type": "thin", "authority": "low"},
                    {"type": "competitor", "authority": "medium"},
                    {"type": "publisher", "authority": "medium"}
                ],
                "features": ["featured_snippet_other", "people_also_ask"],
                "checked_on": "2026-08-15"
            }
        },
        {
            "term": "crm pricing comparison 2026",
            "intent": "commercial",
            "volume_band": "mid",
            "business_value": 4,
            "cluster": "crm",
            "have_page": None,
            "serp": None
        }
    ],
    "_notes": {
        "authority": "new | low | medium | high | very_high -- your honest read of "
                     "the site's standing, with the basis stated",
        "type": "brand, publisher, competitor, marketplace, gov, edu (strong) | "
                "forum, ugc, thin, off_intent, outdated, aggregator, social, "
                "unrelated (an opening)",
        "current_position": "from Search Console. Positions 5-20 are the cheapest "
                            "wins on the whole list",
        "business_value": "1-5, how close this searcher is to paying you",
        "volume_band": "head | mid | long. Use a band unless you have a sourced "
                       "number -- an invented volume figure gets budgeted against",
        "serp": "null means unchecked. Unchecked candidates are not scored."
    }
}


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def score_candidate(c, site_auth, site):
    """Return a 0-100 winnability score with its reasoning exposed.

    Every component is returned rather than folded away, because the number is
    only useful if someone can see which input drove it and argue with that.
    """
    serp = c.get("serp")
    results = (serp or {}).get("results") or []
    if not results:
        return None

    auths = [AUTHORITY.get(r.get("authority", "medium"), 45) for r in results]
    auths.sort()
    median_auth = auths[len(auths) // 2]
    weak = [r for r in results if r.get("type") in WEAK_TYPES]
    strong_on_intent = [r for r in results
                        if r.get("type") in STRONG_TYPES
                        and r.get("type") != "off_intent"]
    top5_weak = sum(1 for r in results[:5] if r.get("type") in WEAK_TYPES)

    # 1. Authority fit (40). The gap to the typical incumbent, softened by any
    #    opening -- a weak result on page one is a seat that is already empty,
    #    which is why small sites win these and lose the clean ones.
    gap = site_auth - median_auth
    fit = clamp((gap + 45) / 90.0)
    opening_bonus = clamp(len(weak) / 5.0) * 0.35 + clamp(top5_weak / 3.0) * 0.15
    authority_fit = clamp(fit + opening_bonus) * 40

    # 2. Existing asset (20). A page sitting at 5-20 is already most of the way
    #    there; nudging it beats writing something new by a wide margin, and it
    #    is the single most under-used lever in most audits.
    pos = c.get("current_position")
    if pos and 4 <= pos <= 20:
        existing = 20
    elif pos and pos <= 3:
        existing = 6          # already won; defend, do not re-invest
    elif pos and pos <= 50:
        existing = 12
    elif c.get("have_page"):
        existing = 8
    else:
        existing = 0

    # 3. Competition density (15).
    density = clamp(1 - (len(strong_on_intent) / 10.0)) * 15

    # 4. Topical depth (15). Google trusts a site on subjects it has covered;
    #    an isolated page on an unrelated topic starts from further back.
    depth_map = {"strong": 1.0, "medium": 0.65, "weak": 0.35, "none": 0.15}
    depth = depth_map.get(
        (site.get("topical_depth") or {}).get(c.get("cluster", ""), "none"), 0.15) * 15

    # 5. Click availability (10). Winning a SERP whose clicks are already spent
    #    on ads and an AI overview is a ranking, not traffic.
    features = (serp or {}).get("features") or []
    remaining = 1.0
    for f in features:
        remaining -= FEATURE_COST.get(f, 0.0)
    remaining = clamp(remaining, 0.15, 1.0)
    capture = remaining * 10

    total = authority_fit + existing + density + depth + capture

    # Head terms are structurally harder than any component captures: they
    # attract every competitor's best effort and the strongest links.
    band = c.get("volume_band", "mid")
    if band == "head":
        total *= 0.75
    elif band == "long":
        total *= 1.05

    total = round(clamp(total, 0, 100), 1)

    return {
        "score": total,
        "components": {
            "authority_fit": round(authority_fit, 1),
            "existing_asset": existing,
            "competition_density": round(density, 1),
            "topical_depth": round(depth, 1),
            "click_availability": round(capture, 1),
        },
        "median_incumbent_authority": median_auth,
        "authority_gap": gap,
        "weak_results": len(weak),
        "weak_in_top5": top5_weak,
        "strong_on_intent": len(strong_on_intent),
        "clicks_remaining": round(remaining, 2),
        "serp_checked_on": (serp or {}).get("checked_on"),
    }


def tier_for(score, business_value):
    for cutoff, name, horizon, why in TIERS:
        if score >= cutoff:
            # A term you can win that nobody who buys is searching is not a win.
            if business_value <= 1 and name in ("NOW", "NEXT"):
                return "LATER", "3-6 months", ("Winnable, but the searcher is far "
                                               "from buying -- low priority.")
            return name, horizon, why
    return "SKIP", "not on this horizon", ""


def reason_for(c, s, tier):
    """One line a human can check, not a restatement of the score."""
    bits = []
    if s["weak_in_top5"]:
        bits.append(f"{s['weak_in_top5']} weak result(s) in the top 5 -- "
                    "there is a seat open")
    elif s["weak_results"] >= 3:
        bits.append(f"{s['weak_results']} weak results on page one")
    if s["strong_on_intent"] >= 7:
        bits.append(f"{s['strong_on_intent']}/10 strong on-intent incumbents")
    if s["authority_gap"] < -30:
        bits.append(f"authority gap of {s['authority_gap']} points to the "
                    "typical incumbent")
    pos = c.get("current_position")
    if pos and 4 <= pos <= 20:
        bits.append(f"already at position {pos} -- striking distance")
    if s["clicks_remaining"] <= 0.6:
        bits.append(f"only ~{int(s['clicks_remaining'] * 100)}% of clicks left "
                    "after SERP features")
    if c.get("volume_band") == "head":
        bits.append("head term: every competitor is trying")
    return "; ".join(bits) or "no distinguishing signal either way"


def run(data):
    site = data.get("site", {})
    site_auth = AUTHORITY.get(site.get("authority", "low"), 20)
    scored, unscored = [], []

    for c in data.get("candidates", []):
        s = score_candidate(c, site_auth, site)
        if s is None:
            unscored.append(c)
            continue
        tier, horizon, why = tier_for(s["score"], c.get("business_value", 3))
        scored.append({**c, "scoring": s, "tier": tier, "horizon": horizon,
                       "tier_rationale": why, "reason": reason_for(c, s, tier)})

    scored.sort(key=lambda x: (-x["scoring"]["score"],
                               -x.get("business_value", 3)))
    return scored, unscored, site, site_auth


def render(scored, unscored, site, site_auth):
    L = []
    w = L.append
    w(f"KEYWORD WINNABILITY: {site.get('domain', '(site)')}")
    w("=" * 74)
    w(f"Site authority: {site.get('authority', 'low')} ({site_auth}/100)")
    if site.get("authority_basis"):
        w(f"  basis: {site['authority_basis']}")
    w("")

    by_tier = {}
    for c in scored:
        by_tier.setdefault(c["tier"], []).append(c)

    for _, name, horizon, why in TIERS:
        group = by_tier.get(name)
        if not group:
            continue
        w(f"{name}  ({horizon})  -- {why}")
        w("-" * 74)
        for c in group:
            s = c["scoring"]
            w(f"  {c['term']}")
            w(f"    score {s['score']}/100   intent {c.get('intent', '?')}   "
              f"volume {c.get('volume_band', '?')}   value {c.get('business_value', '?')}/5")
            w(f"    why: {c['reason']}")
            comp = s["components"]
            w(f"    components: authority {comp['authority_fit']} | "
              f"existing {comp['existing_asset']} | density {comp['competition_density']} "
              f"| depth {comp['topical_depth']} | clicks {comp['click_availability']}")
            if c.get("have_page"):
                w(f"    existing page: {c['have_page']}"
                  + (f" (position {c['current_position']})" if c.get("current_position") else ""))
            w("")

    if unscored:
        w("NOT SCORED -- no SERP evidence supplied")
        w("-" * 74)
        for c in unscored:
            w(f"  {c['term']}")
        w("  Search each term, record the top ten result types and authority, and")
        w("  re-run. Guessing this input is what produces confident wrong answers.")
        w("")

    now = by_tier.get("NOW", [])
    nxt = by_tier.get("NEXT", [])
    w("PORTFOLIO CHECK")
    w("-" * 74)
    if not now and not nxt:
        w("  Nothing is winnable inside six months. That is a real finding: the")
        w("  constraint is authority, not keyword choice. Either go further down")
        w("  the long tail than this list goes, or accept a longer horizon and")
        w("  invest in links and depth first.")
    elif not now:
        w("  Nothing in the Now tier -- there is no traffic in the first quarter to")
        w("  show for the work. Look for longer-tail variants of the Next terms.")
    else:
        hv = [c for c in now + nxt if c.get("business_value", 3) >= 4]
        w(f"  {len(now)} to start now, {len(nxt)} to follow.")
        if not hv:
            w("  None of them are close to revenue. Winnable and worthless is still")
            w("  worthless -- add commercial-intent terms even if they score lower.")
        else:
            # Winnability and business value are separate axes on purpose;
            # collapsing them into one number hides the trade the user has to
            # make. This names the intersection, which is what to work on.
            w(f"  Highest value among the winnable, work these first:")
            for c in sorted(hv, key=lambda x: (-x.get("business_value", 3),
                                               -x["scoring"]["score"]))[:5]:
                w(f"    - {c['term']}  (value {c['business_value']}/5, "
                  f"score {c['scoring']['score']}, {c['tier']})")
    w("")
    w("Scores rank candidates against each other for this site. They are not a")
    w("difficulty metric and do not transfer to another domain.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", nargs="?", help="JSON file of candidates")
    ap.add_argument("--example", action="store_true",
                    help="print a documented example input and exit")
    ap.add_argument("--json", metavar="PATH", help="write scored output as JSON")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.input:
        ap.error("give an input file, or --example to see the format")

    with open(args.input) as f:
        data = json.load(f)

    scored, unscored, site, site_auth = run(data)
    print(render(scored, unscored, site, site_auth))

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"site": site, "scored": scored,
                       "unscored": [c["term"] for c in unscored]}, f, indent=2)
        print(f"\nWritten to {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
