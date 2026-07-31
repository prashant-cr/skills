#!/usr/bin/env python3
"""Normalise proxy and scraping-API offerings to one monthly number for one job.

Sticker prices are not comparable. One vendor charges per gigabyte, another per IP
per month, a scraping API per successful request, and a data vendor a flat fee. The
only way to choose is to price the *same job* through each, which is arithmetic
nobody enjoys doing by hand and which is therefore usually skipped -- so people buy
on headline rate and are surprised by the invoice.

Two things this deliberately includes, because leaving them out is how the wrong
option wins on paper:

  * Retries. A blocked request still costs bandwidth on per-GB pricing. A 40% block
    rate is a 67% surcharge, and it is invisible in the rate card.
  * Engineering time. A cheap proxy that needs two weeks of fingerprint work is not
    cheap. Priced at your own hourly rate, the ranking often inverts.

    python3 cost_model.py --example > job.json
    python3 cost_model.py job.json
    python3 cost_model.py job.json --months 6

Every offering must carry source_url and fetched_at. Anything without them is listed
but refused a ranking, because a remembered price silently decides the comparison.

Standard library only.
"""

import argparse
import json
import sys

UNVIABLE_BLOCK_RATE = 0.50   # above this it is not an option, it is a failure mode

UNITS = {
    "per_gb": "per GB of traffic",
    "per_request": "per request made",
    "per_1k_requests": "per 1,000 requests made",
    "per_success": "per successful response only",
    "per_ip_month": "per IP per month",
    "flat_month": "flat monthly fee",
}

EXAMPLE = {
    "job": {
        "pages_per_month": 120000,
        "bytes_per_page": 59000,
        "block_rate": 0.15,
        "block_rate_note": "share of attempts that fail and must be retried",
        "hourly_rate_usd": 60,
        "notes": "bytes_per_page comes from site_probe.py full_page_bytes"
    },
    "offerings": [
        {
            "name": "Datacenter proxies (example vendor)",
            "kind": "datacenter",
            "price": 0.60, "unit": "per_gb",
            "min_monthly_usd": 50,
            "setup_hours": 4, "maintenance_hours_month": 2,
            "expected_block_rate": 0.85,
            "source_url": "https://vendor.example/pricing",
            "fetched_at": "2026-07-31T09:00:00Z"
        },
        {
            "name": "Residential proxies (example vendor)",
            "kind": "residential",
            "price": 3.50, "unit": "per_gb",
            "min_monthly_usd": 0,
            "setup_hours": 24, "maintenance_hours_month": 6,
            "expected_block_rate": 0.15,
            "source_url": "https://vendor.example/residential",
            "fetched_at": "2026-07-31T09:00:00Z"
        },
        {
            "name": "Scraping API (example vendor)",
            "kind": "scraping_api",
            "price": 0.0012, "unit": "per_success",
            "setup_hours": 3, "maintenance_hours_month": 0.5,
            "expected_block_rate": 0.02,
            "source_url": "https://vendor.example/api-pricing",
            "fetched_at": "2026-07-31T09:00:00Z"
        },
        {
            "name": "Official API",
            "kind": "official_api",
            "price": 0, "unit": "flat_month",
            "setup_hours": 6, "maintenance_hours_month": 0.5,
            "expected_block_rate": 0.0,
            "coverage_note": "check it exposes the fields you actually need",
            "source_url": "https://site.example/developers",
            "fetched_at": "2026-07-31T09:00:00Z"
        }
    ],
    "_notes": {
        "expected_block_rate": "per-offering override of job.block_rate. A datacenter "
                               "IP on a protected site is mostly blocked, which is the "
                               "whole reason it looks cheap.",
        "ip_count": "required for per_ip_month pricing",
        "provenance": "source_url and fetched_at are required to be ranked."
    }
}


def price_offering(off, job, months=1):
    """Return a costing dict for one offering over `months`."""
    pages = float(job["pages_per_month"])
    bpp = float(job.get("bytes_per_page") or 0)
    rate = float(job.get("hourly_rate_usd") or 0)

    block = off.get("expected_block_rate")
    block = float(job.get("block_rate", 0) if block is None else block)
    block = min(max(block, 0.0), 0.99)

    # Attempts needed to land `pages` successes. At a 50% block rate you make twice
    # the requests, and on per-GB pricing you pay for every one of them.
    attempts = pages / (1.0 - block)
    gb = attempts * bpp / 1e9

    unit = off["unit"]
    p = float(off.get("price") or 0)
    if unit == "per_gb":
        infra = gb * p
    elif unit == "per_request":
        infra = attempts * p
    elif unit == "per_1k_requests":
        infra = attempts / 1000.0 * p
    elif unit == "per_success":
        # Only successes billed, so the vendor carries the block risk. This is why a
        # per-success rate that looks expensive can win at a high block rate.
        infra = pages * p
    elif unit == "per_ip_month":
        n = float(off.get("ip_count") or 0)
        if not n:
            return {"name": off["name"], "error": "per_ip_month pricing needs ip_count"}
        infra = n * p
    elif unit == "flat_month":
        infra = p
    else:
        return {"name": off["name"], "error": f"unknown unit {unit!r}"}

    infra = max(infra, float(off.get("min_monthly_usd") or 0))

    setup = float(off.get("setup_hours") or 0) * rate
    upkeep = float(off.get("maintenance_hours_month") or 0) * rate

    infra_total = infra * months
    eng_total = setup + upkeep * months
    return {
        "name": off["name"],
        "kind": off.get("kind", "?"),
        "unit": unit,
        "price": p,
        "block_rate": round(block, 3),
        "attempts": round(attempts),
        "gb_per_month": round(gb, 2),
        "infra_month": round(infra, 2),
        "infra_total": round(infra_total, 2),
        "eng_setup": round(setup, 2),
        "eng_upkeep_month": round(upkeep, 2),
        "eng_total": round(eng_total, 2),
        "total": round(infra_total + eng_total, 2),
        "sourced": bool(off.get("source_url") and off.get("fetched_at")),
        "source_url": off.get("source_url"),
        "fetched_at": off.get("fetched_at"),
        "coverage_note": off.get("coverage_note"),
        "error": None,
    }


def bandwidth_variants(job, offerings, months):
    """What does dropping images and fonts save? Usually more than switching vendor."""
    bpp = float(job.get("bytes_per_page") or 0)
    html_share = float(job.get("html_only_share") or 0)
    if not bpp or not html_share or html_share >= 0.99:
        return None
    lean = dict(job)
    lean["bytes_per_page"] = bpp * html_share
    out = []
    for off in offerings:
        if off.get("unit") != "per_gb":
            continue
        full = price_offering(off, job, months)
        thin = price_offering(off, lean, months)
        if full.get("error") or thin.get("error"):
            continue
        out.append({"name": off["name"],
                    "full_month": full["infra_month"],
                    "html_only_month": thin["infra_month"],
                    "saving_month": round(full["infra_month"] - thin["infra_month"], 2)})
    return out or None


def render(job, rows, months, variants):
    o = []
    pages = job["pages_per_month"]
    o.append(f"  Job          {pages:,} successful pages/month"
             f"   {job.get('bytes_per_page', 0) / 1000:,.0f} KB/page"
             f"   over {months} month(s)")
    if job.get("hourly_rate_usd"):
        o.append(f"  Your time    ${job['hourly_rate_usd']}/hour "
                 "(engineering is priced in below, because a cheap proxy that needs "
                 "two weeks of work is not cheap)")
    o.append("")

    usable = [r for r in rows if not r.get("error") and r["sourced"]]
    unranked = [r for r in rows if r.get("error") or not r["sourced"]]
    # An option that fails most requests is not a cheap option, it is a broken one.
    # Left in the main table it looks attractive precisely because failure is cheap
    # on per-GB pricing -- fewer bytes delivered. Rank only what actually works.
    ranked = [r for r in usable if r["block_rate"] < UNVIABLE_BLOCK_RATE]
    unviable = [r for r in usable if r["block_rate"] >= UNVIABLE_BLOCK_RATE]
    ranked.sort(key=lambda r: r["total"])
    unviable.sort(key=lambda r: -r["block_rate"])

    o.append(f"  {'option':<34}{'blk':>5}{'infra':>11}{'eng':>10}{'TOTAL':>11}")
    o.append("  " + "-" * 69)
    for r in ranked:
        o.append(f"  {r['name'][:33]:<34}{r['block_rate']:>5.0%}"
                 f"{'$' + format(r['infra_total'], ',.0f'):>11}"
                 f"{'$' + format(r['eng_total'], ',.0f'):>10}"
                 f"{'$' + format(r['total'], ',.0f'):>11}")
    if ranked:
        best = ranked[0]
        o.append("")
        o.append(f"  Cheapest that works: {best['name']} at ${best['total']:,.0f} "
                 f"over {months} month(s).")
        if len(ranked) > 1:
            second = ranked[1]
            gap = second["total"] - best["total"]
            o.append(f"  Next option costs ${gap:,.0f} more. If that gap is small, "
                     "prefer the one with less operational risk rather than the "
                     "cheaper sticker.")

    if unviable:
        o.append("")
        o.append("  DOES NOT WORK -- excluded from the ranking above")
        for r in unviable:
            o.append(f"    x {r['name'][:33]:<35}{r['block_rate']:>5.0%} blocked"
                     f"   {r['attempts']:,} attempts for {pages:,} pages")
        o.append("    These look cheap on per-GB pricing precisely because they fail:")
        o.append("    a blocked response is a small response. Do not buy on that number.")

    if unranked:
        o.append("")
        o.append("  NOT RANKED")
        for r in unranked:
            why = r.get("error") or "no source_url + fetched_at, so the price is unverified"
            o.append(f"    ? {r['name'][:40]:<42} {why}")
        o.append("    A price you cannot point at is a price that silently decides this")
        o.append("    comparison. Fetch it or get a written quote, then re-run.")

    if variants:
        o.append("")
        o.append("  Bandwidth lever (per-GB options only)")
        for v in variants:
            o.append(f"    {v['name'][:36]:<38} full ${v['full_month']:>8,.0f}"
                     f"   HTML-only ${v['html_only_month']:>8,.0f}"
                     f"   saves ${v['saving_month']:>8,.0f}/mo")
        o.append("    Blocking images, fonts and CSS is usually a bigger saving than")
        o.append("    any vendor discount, and it costs one line of config.")

    covered = [r for r in ranked if r.get("coverage_note")]
    if covered:
        o.append("")
        for r in covered:
            o.append(f"  ! {r['name']}: {r['coverage_note']}")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec", nargs="?", help="job + offerings JSON")
    ap.add_argument("--example", action="store_true")
    ap.add_argument("--months", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.spec:
        ap.error("give a spec JSON, or --example for a template")

    with open(args.spec) as fh:
        spec = json.load(fh)
    spec.pop("_notes", None)
    job = spec["job"]
    offerings = spec["offerings"]
    if not offerings:
        raise SystemExit("error: no offerings to compare")

    rows = [price_offering(o, job, args.months) for o in offerings]
    variants = bandwidth_variants(job, offerings, args.months)

    if args.json:
        print(json.dumps({"job": job, "months": args.months, "rows": rows,
                          "bandwidth_variants": variants}, indent=2))
    else:
        print(render(job, rows, args.months, variants))

    return 0 if any(not r.get("error") and r["sourced"] for r in rows) else 2


if __name__ == "__main__":
    sys.exit(main())
