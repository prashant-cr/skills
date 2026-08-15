#!/usr/bin/env python3
"""Find the cheapest ranking wins in a Google Search Console export.

Search Console is the only free source of what a site *actually* ranks for, and
most audits ignore it in favour of guessing. Three things hide in it, all of
them worth more than any new content plan:

  * Striking distance. Queries sitting at positions 4-20 already have relevance
    and impressions; they need a nudge, not a new page. Moving one of these
    beats writing something from scratch by an order of magnitude in effort.
  * A click problem wearing a ranking problem's clothes. A query at position 3
    taking 1% of clicks does not need links -- it needs a title someone wants
    to click. Buying links to fix that is the most expensive way to not solve it.
  * Cannibalisation. Two URLs alternating on one query split the signal and
    neither wins. It is invisible unless you group the export by query.

    python3 gsc_opportunities.py Queries.csv
    python3 gsc_opportunities.py performance.csv --compare last-quarter.csv
    python3 gsc_opportunities.py Queries.csv --min-impressions 50 --json out.json

Export from Search Console > Performance > Export > CSV. The query-and-page
export ("Pages" plus "Queries", or the combined table) enables cannibalisation
detection; a queries-only export still gives you the first two.

Standard library only.
"""

import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict

# Approximate organic CTR by position, desktop+mobile blended. Every published
# study disagrees with every other because CTR depends on intent, brand and
# what else is on the page -- these are here to spot an order-of-magnitude gap,
# not to hit a target. Treat a page at half its expected CTR as interesting and
# anything closer than that as noise.
CTR_CURVE = {1: 0.28, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05, 6: 0.04,
             7: 0.033, 8: 0.028, 9: 0.024, 10: 0.021}
TAIL_CTR = 0.01

STRIKING_LO, STRIKING_HI = 3.5, 20.0

ALIASES = {
    "query": {"query", "queries", "search query", "top queries", "keyword",
              "consulta", "requête", "suchanfrage"},
    "page": {"page", "pages", "landing page", "url", "top pages", "address"},
    "clicks": {"clicks", "click", "clics", "klicks"},
    "impressions": {"impressions", "impression", "impresiones", "impressionen"},
    "ctr": {"ctr", "click through rate", "click-through rate"},
    "position": {"position", "avg position", "average position", "posición",
                 "durchschnittliche position"},
    "date": {"date", "day", "fecha"},
    "country": {"country"},
    "device": {"device"},
}


def _canon(name):
    n = re.sub(r"[^a-z ]", " ", (name or "").strip().lower())
    n = " ".join(n.split())
    for canon, names in ALIASES.items():
        if n in names:
            return canon
    return None


def _num(v):
    """GSC writes '1,234', '3.5%', '12.3' and sometimes '<10'."""
    if v is None:
        return 0.0
    s = str(v).strip().replace(",", "").replace("<", "").replace("%", "")
    s = s.replace(" ", "").replace(" ", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def load(path):
    """Read a GSC CSV. Returns (rows, columns_found)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    if not text.strip():
        return [], {}
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    try:
        header = next(reader)
    except StopIteration:
        return [], {}

    cols = {}
    for i, h in enumerate(header):
        c = _canon(h)
        if c and c not in cols:
            cols[c] = i

    rows = []
    for raw in reader:
        if not any(x.strip() for x in raw):
            continue
        row = {}
        for c, i in cols.items():
            if i < len(raw):
                row[c] = raw[i]
        if "clicks" in row:
            row["clicks"] = _num(row["clicks"])
        if "impressions" in row:
            row["impressions"] = _num(row["impressions"])
        if "position" in row:
            row["position"] = _num(row["position"])
        if "ctr" in row:
            # GSC writes CTR as '0.07%' -- which is 0.0007, not 0.07. Guessing
            # from magnitude ("less than 1 must already be a fraction") silently
            # inflates every low CTR by 100x and hides exactly the pages this
            # script exists to find. The '%' sign is the real signal.
            raw_ctr = str(row["ctr"])
            ctr = _num(raw_ctr)
            row["ctr"] = ctr / 100.0 if "%" in raw_ctr else ctr
        elif row.get("impressions"):
            row["ctr"] = row.get("clicks", 0) / row["impressions"]
        rows.append(row)
    return rows, cols


def expected_ctr(position):
    p = int(round(position))
    if p <= 0:
        return CTR_CURVE[1]
    return CTR_CURVE.get(p, TAIL_CTR)


def analyse(rows, min_impressions):
    striking, ctr_gaps, cannibal, top_won = [], [], [], []

    has_query = any("query" in r for r in rows)
    has_page = any("page" in r for r in rows)

    for r in rows:
        imp = r.get("impressions", 0)
        pos = r.get("position", 0)
        if imp < min_impressions or not pos:
            continue
        label = r.get("query") or r.get("page") or "(unlabelled)"
        entry = {
            "term": label,
            "page": r.get("page"),
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(imp),
            "position": round(pos, 1),
            "ctr": round(r.get("ctr", 0), 4),
        }
        if STRIKING_LO <= pos <= STRIKING_HI:
            # What one more position band is worth, roughly. The point is the
            # ordering, not the forecast.
            gain = max(0.0, expected_ctr(max(1, pos - 3)) - r.get("ctr", 0)) * imp
            striking.append({**entry, "potential_extra_clicks": round(gain)})
        if pos <= 10:
            exp = expected_ctr(pos)
            actual = r.get("ctr", 0)
            if actual < exp * 0.5:
                ctr_gaps.append({**entry, "expected_ctr": round(exp, 4),
                                 "shortfall_clicks": round((exp - actual) * imp)})
            elif pos <= 3 and actual >= exp * 0.8:
                top_won.append(entry)

    if has_query and has_page:
        by_query = defaultdict(list)
        for r in rows:
            if r.get("query") and r.get("page") and r.get("impressions", 0) >= min_impressions:
                by_query[r["query"].strip().lower()].append(r)
        for q, rs in by_query.items():
            pages = {r["page"] for r in rs}
            if len(pages) > 1:
                rs = sorted(rs, key=lambda x: -x.get("impressions", 0))
                cannibal.append({
                    "term": q,
                    "urls": [{"page": r["page"], "clicks": int(r.get("clicks", 0)),
                              "impressions": int(r.get("impressions", 0)),
                              "position": round(r.get("position", 0), 1)}
                             for r in rs[:5]],
                    "total_impressions": int(sum(r.get("impressions", 0) for r in rs)),
                })

    striking.sort(key=lambda x: -x["potential_extra_clicks"])
    ctr_gaps.sort(key=lambda x: -x["shortfall_clicks"])
    cannibal.sort(key=lambda x: -x["total_impressions"])
    top_won.sort(key=lambda x: -x["clicks"])
    return {"striking_distance": striking, "ctr_gaps": ctr_gaps,
            "cannibalisation": cannibal, "winning": top_won,
            "has_query": has_query, "has_page": has_page}


def compare(current, previous, min_impressions):
    """Which terms lost ground? Decay is invisible in a single export, and a
    page sliding from 4 to 11 loses most of its traffic while still looking
    like it ranks."""
    def index(rows):
        out = {}
        for r in rows:
            key = (r.get("query") or r.get("page") or "").strip().lower()
            if key and r.get("impressions", 0) >= min_impressions:
                out[key] = r
        return out

    now, before = index(current), index(previous)
    declines, gains, lost = [], [], []
    for k, r in now.items():
        if k not in before:
            continue
        dp = r.get("position", 0) - before[k].get("position", 0)
        dc = r.get("clicks", 0) - before[k].get("clicks", 0)
        row = {"term": r.get("query") or r.get("page"),
               "position_now": round(r.get("position", 0), 1),
               "position_before": round(before[k].get("position", 0), 1),
               "position_change": round(dp, 1),
               "clicks_now": int(r.get("clicks", 0)),
               "clicks_before": int(before[k].get("clicks", 0)),
               "clicks_change": int(dc)}
        if dp >= 2 or dc <= -10:
            declines.append(row)
        elif dp <= -2 or dc >= 10:
            gains.append(row)
    for k, r in before.items():
        if k not in now and r.get("clicks", 0) >= 5:
            lost.append({"term": r.get("query") or r.get("page"),
                         "clicks_before": int(r.get("clicks", 0)),
                         "position_before": round(r.get("position", 0), 1)})
    declines.sort(key=lambda x: x["clicks_change"])
    gains.sort(key=lambda x: -x["clicks_change"])
    lost.sort(key=lambda x: -x["clicks_before"])
    return {"declines": declines, "gains": gains, "lost": lost}


def render(a, delta, min_impressions, total_rows):
    L = []
    w = L.append
    w("SEARCH CONSOLE OPPORTUNITIES")
    w("=" * 74)
    w(f"Rows analysed: {total_rows} (impressions >= {min_impressions})")
    if not a["has_page"]:
        w("Queries-only export: cannibalisation cannot be detected. Re-export with")
        w("the page dimension included to get it.")
    w("")

    w("1. STRIKING DISTANCE -- positions 4-20, already relevant")
    w("-" * 74)
    if not a["striking_distance"]:
        w("  None. Either the site ranks well already or it does not rank at all;")
        w("  check the impression totals to tell which.")
    for r in a["striking_distance"][:20]:
        w(f"  pos {r['position']:>5}  {r['impressions']:>7} impr  "
          f"{r['clicks']:>5} clicks  +{r['potential_extra_clicks']:>5} if moved to top 5")
        w(f"        {r['term']}")
        if r.get("page"):
            w(f"        -> {r['page']}")
    w("")
    w("  These are the cheapest wins available. Improve the existing page --")
    w("  match the intent more exactly, cover what the top results cover and it")
    w("  does not, add internal links from relevant pages. Do not write a new page.")
    w("")

    w("2. CLICK PROBLEMS -- ranking is fine, the snippet is not")
    w("-" * 74)
    if not a["ctr_gaps"]:
        w("  None found. Click-through is roughly in line with position.")
    for r in a["ctr_gaps"][:15]:
        w(f"  pos {r['position']:>5}  CTR {r['ctr'] * 100:>5.1f}% vs "
          f"~{r['expected_ctr'] * 100:.1f}% expected  "
          f"(~{r['shortfall_clicks']} clicks/period)")
        w(f"        {r['term']}")
        if r.get("page"):
            w(f"        -> {r['page']}")
    w("")
    w("  Rewrite the title and meta description; these rank already. A high")
    w("  position with poor CTR usually means the snippet answers a different")
    w("  question than the searcher asked -- or an AI overview took the click.")
    w("")

    w("3. CANNIBALISATION -- several URLs on one query")
    w("-" * 74)
    if not a["has_page"]:
        w("  (not checkable without the page dimension)")
    elif not a["cannibalisation"]:
        w("  None found.")
    for r in a["cannibalisation"][:12]:
        w(f"  '{r['term']}'  {r['total_impressions']} impressions across "
          f"{len(r['urls'])} URLs")
        for u in r["urls"]:
            w(f"        pos {u['position']:>5}  {u['clicks']:>4} clicks  {u['page']}")
    if a["cannibalisation"]:
        w("")
        w("  Pick one URL to own each query. Consolidate the others into it and")
        w("  redirect, or differentiate them onto genuinely distinct intents.")
    w("")

    if delta:
        w("4. MOVEMENT SINCE THE COMPARISON PERIOD")
        w("-" * 74)
        if delta["declines"]:
            w("  Losing ground:")
            for r in delta["declines"][:12]:
                w(f"    {r['position_before']} -> {r['position_now']}  "
                  f"({r['clicks_before']} -> {r['clicks_now']} clicks)  {r['term']}")
        if delta["lost"]:
            w("  Gone entirely:")
            for r in delta["lost"][:10]:
                w(f"    was pos {r['position_before']} with {r['clicks_before']} "
                  f"clicks: {r['term']}")
        if delta["gains"]:
            w("  Gaining:")
            for r in delta["gains"][:8]:
                w(f"    {r['position_before']} -> {r['position_now']}  "
                  f"(+{r['clicks_change']} clicks)  {r['term']}")
        if not any(delta.values()):
            w("  No material movement.")
        w("")
        w("  Decline on a page that used to work is worth more attention than any")
        w("  new opportunity: the relevance is proven, so something changed.")
        w("")

    w("Positions are averages across the export period, which flattens volatility")
    w("and mixes devices and countries. Segment before acting on a surprising one.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("csv_path", help="Search Console performance export (CSV)")
    ap.add_argument("--compare", metavar="PATH",
                    help="an earlier export, to find decay")
    ap.add_argument("--min-impressions", type=int, default=20)
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    rows, cols = load(args.csv_path)
    if not rows:
        print(f"No data rows found in {args.csv_path}", file=sys.stderr)
        return 2
    if "position" not in cols and not any("position" in r for r in rows):
        print("No 'Position' column found. Export from Search Console > Performance "
              "> Export, with the Average Position metric enabled.", file=sys.stderr)
        return 2

    a = analyse(rows, args.min_impressions)
    delta = None
    if args.compare:
        prev, _ = load(args.compare)
        if prev:
            delta = compare(rows, prev, args.min_impressions)

    print(render(a, delta, args.min_impressions, len(rows)))

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"opportunities": a, "movement": delta}, f, indent=2)
        print(f"\nWritten to {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
