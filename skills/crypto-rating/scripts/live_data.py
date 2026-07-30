#!/usr/bin/env python3
"""Fetch live market data for a crypto asset, cross-check it, and refuse if it is stale.

This is the gate the rest of the analysis sits behind, and it exists because of a
specific failure mode: a language model asked about a crypto price will produce a
confident number from training data, and in this asset class that number is not
merely out of date, it is often wrong by a multiple. A remembered price poisons
every downstream calculation -- market cap, dilution, drawdown from the high, the
position size -- while looking entirely plausible.

So no figure used in an analysis should come from memory. It comes from here, with
a timestamp attached, or the analysis stops.

    python3 live_data.py bitcoin
    python3 live_data.py --search "arbitrum"      # find the right id first
    python3 live_data.py solana --json
    python3 live_data.py bitcoin --max-age 15     # minutes

Sources are keyless public endpoints: CoinGecko for market and supply data,
Binance and Coinbase for independent price cross-checks. Standard library only.

Exit codes: 0 fresh and cross-checked, 2 fetched but flagged, 3 unusable.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; crypto-rating-skill/1.0)"
TIMEOUT = 20
DEFAULT_MAX_AGE_MIN = 30
# Majors arbitrage to within a few basis points. Anything wider means one feed is
# stale, or the asset is thin enough that "the price" is not a single number.
DIVERGENCE_WARN_PCT = 1.0
DIVERGENCE_FAIL_PCT = 5.0


# Some Python installs -- notably python.org builds on macOS -- ship without a
# usable CA bundle, so urllib raises CERTIFICATE_VERIFY_FAILED while curl works
# fine off the system keychain. Falling back to curl keeps verification intact.
# Disabling verification would also "work" and is not an option here: this data
# decides where someone puts money, so an unauthenticated feed is worse than no
# feed. The proper local fix is noted in references/data-sources.md.
_USE_CURL = False


def _via_curl(url):
    import subprocess
    try:
        # -w prints the status on its own final line. Without this curl exits 0 on a
        # 404, so an API error body parses as valid JSON and the caller believes it
        # got data -- which is how a lookup for a non-existent coin came back as a
        # record full of nulls instead of an error.
        p = subprocess.run(["curl", "-sS", "-m", str(TIMEOUT), "-H", f"User-Agent: {UA}",
                            "-H", "Accept: application/json", "-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
    except FileNotFoundError:
        return None, "curl not installed and urllib has no CA bundle"
    if p.returncode != 0:
        return None, f"curl failed: {p.stderr.strip()[:160]}"
    body, _, status = p.stdout.rpartition("\n")
    if status.strip() and not status.strip().startswith("2"):
        return None, f"HTTP {status.strip()}"
    try:
        return json.loads(body), None
    except json.JSONDecodeError:
        return None, "response was not JSON"


def get_json(url):
    global _USE_CURL
    if _USE_CURL:
        return _via_curl(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            _USE_CURL = True
            return _via_curl(url)
        return None, f"{type(e).__name__}: {e}"


def search(query):
    url = "https://api.coingecko.com/api/v3/search?query=" + urllib.parse.quote(query)
    data, err = get_json(url)
    if err:
        return [], err
    out = []
    for c in (data or {}).get("coins", [])[:12]:
        out.append({"id": c.get("id"), "symbol": (c.get("symbol") or "").upper(),
                    "name": c.get("name"), "rank": c.get("market_cap_rank")})
    return out, None


def coingecko(coin_id):
    url = (f"https://api.coingecko.com/api/v3/coins/{urllib.parse.quote(coin_id)}"
           "?localization=false&tickers=false&market_data=true"
           "&community_data=false&developer_data=false&sparkline=false")
    data, err = get_json(url)
    if err:
        return None, err
    md = data.get("market_data") or {}

    def usd(key):
        v = md.get(key)
        return (v or {}).get("usd") if isinstance(v, dict) else v

    return {
        "id": data.get("id"),
        "symbol": (data.get("symbol") or "").upper(),
        "name": data.get("name"),
        "rank": md.get("market_cap_rank") or data.get("market_cap_rank"),
        "price_usd": usd("current_price"),
        "market_cap_usd": usd("market_cap"),
        "fdv_usd": usd("fully_diluted_valuation"),
        "volume_24h_usd": usd("total_volume"),
        "change_24h_pct": md.get("price_change_percentage_24h"),
        "change_7d_pct": md.get("price_change_percentage_7d"),
        "change_30d_pct": md.get("price_change_percentage_30d"),
        "change_1y_pct": md.get("price_change_percentage_1y"),
        "ath_usd": usd("ath"),
        "ath_change_pct": (md.get("ath_change_percentage") or {}).get("usd"),
        "ath_date": (md.get("ath_date") or {}).get("usd"),
        "atl_change_pct": (md.get("atl_change_percentage") or {}).get("usd"),
        "circulating_supply": md.get("circulating_supply"),
        "total_supply": md.get("total_supply"),
        "max_supply": md.get("max_supply"),
        "last_updated": md.get("last_updated") or data.get("last_updated"),
        "platforms": {k: v for k, v in (data.get("platforms") or {}).items() if v},
        "categories": [c for c in (data.get("categories") or []) if c][:8],
    }, None


def binance_price(symbol):
    data, err = get_json("https://api.binance.com/api/v3/ticker/price?symbol="
                         + urllib.parse.quote(symbol + "USDT"))
    if err or not data:
        return None
    try:
        return float(data["price"])
    except (KeyError, TypeError, ValueError):
        return None


def coinbase_price(symbol):
    data, err = get_json(f"https://api.coinbase.com/v2/prices/{urllib.parse.quote(symbol)}-USD/spot")
    if err or not data:
        return None
    try:
        return float(data["data"]["amount"])
    except (KeyError, TypeError, ValueError):
        return None


def age_minutes(iso_ts):
    if not iso_ts:
        return None
    try:
        s = iso_ts.replace("Z", "+00:00")
        import datetime
        dt = datetime.datetime.fromisoformat(s)
        return (time.time() - dt.timestamp()) / 60.0
    except Exception:
        return None


def collect(coin_id, max_age_min):
    cg, err = coingecko(coin_id)
    if err:
        hint = ""
        if "404" in str(err):
            hint = (" -- that id does not exist. Run with --search to find the "
                    "correct one; ids are slugs like 'bitcoin', not tickers.")
        return {"ok": False, "fatal": f"CoinGecko unavailable ({err}){hint}"}

    if not cg.get("price_usd") or not cg.get("id"):
        # Second line of defence. If a source ever returns a 200 with an empty body,
        # a record of nulls must not reach the analysis looking like data.
        return {"ok": False, "fatal": (
            f"no usable market data returned for {coin_id!r}. Check the id with "
            "--search. If the token genuinely has no price feed anywhere, that is a "
            "finding: it is untradeable or too new to value, and no rating applies.")}

    r = dict(cg)
    r["fetched_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    r["data_age_minutes"] = round(age_minutes(cg.get("last_updated")) or -1, 1)

    # Independent cross-checks. Their job is to catch a stale or wrong primary
    # feed, which a single source cannot do for you by definition.
    checks = {}
    if cg.get("symbol"):
        b = binance_price(cg["symbol"])
        c = coinbase_price(cg["symbol"])
        if b:
            checks["binance"] = b
        if c:
            checks["coinbase"] = c
    r["cross_check"] = checks

    prices = [p for p in ([cg.get("price_usd")] + list(checks.values())) if p]
    if len(prices) >= 2:
        spread = (max(prices) - min(prices)) / min(prices) * 100
        r["price_spread_pct"] = round(spread, 3)
    else:
        r["price_spread_pct"] = None

    problems, warnings = [], []

    if not cg.get("price_usd"):
        problems.append("no price returned")
    if r["data_age_minutes"] is not None and r["data_age_minutes"] > max_age_min:
        problems.append(f"data is {r['data_age_minutes']:.0f} minutes old, older than "
                        f"the {max_age_min} minute limit -- do not analyse on this")
    if r["price_spread_pct"] is not None:
        if r["price_spread_pct"] > DIVERGENCE_FAIL_PCT:
            problems.append(f"sources disagree by {r['price_spread_pct']:.2f}% -- one feed "
                            "is wrong or the asset is too thin to have one price")
        elif r["price_spread_pct"] > DIVERGENCE_WARN_PCT:
            warnings.append(f"sources differ by {r['price_spread_pct']:.2f}%, wider than "
                            "normal arbitrage -- treat the price as approximate")
    if not checks:
        warnings.append("price confirmed by ONE source only -- not listed on Binance or "
                        "Coinbase, which is itself a liquidity signal")

    vol, mc = cg.get("volume_24h_usd"), cg.get("market_cap_usd")
    if vol is not None and mc:
        turn = vol / mc
        r["volume_to_mcap"] = round(turn, 4)
        if turn < 0.005:
            warnings.append(f"24h volume is {turn:.2%} of market cap -- very thin, so "
                            "exiting a position may move the price against you")
        elif turn > 2.0:
            warnings.append(f"24h volume is {turn:.1f}x market cap -- implausible organic "
                            "turnover, check for wash trading")
    else:
        r["volume_to_mcap"] = None

    if cg.get("fdv_usd") and mc:
        r["fdv_to_mcap"] = round(cg["fdv_usd"] / mc, 2)
    else:
        r["fdv_to_mcap"] = None

    r["problems"] = problems
    r["warnings"] = warnings
    r["ok"] = not problems
    return r


def fmt_usd(v):
    """Abbreviated -- for market caps and volumes, where magnitude is the point."""
    if v is None:
        return "n/a"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6)):
        if abs(v) >= div:
            return f"${v / div:,.2f}{unit}"
    return f"${v:,.0f}"


def fmt_price(v):
    """Full precision -- a price is a number someone will act on, so never abbreviate
    it. Small-cap tokens also need many decimals before they mean anything."""
    if v is None:
        return "n/a"
    if abs(v) >= 1000:
        return f"${v:,.2f}"
    if abs(v) >= 1:
        return f"${v:,.4f}".rstrip("0").rstrip(".")
    return f"${v:,.10f}".rstrip("0")


def fmt_pct(v):
    return "n/a" if v is None else f"{v:+.1f}%"


def render(r):
    if not r.get("ok") and r.get("fatal"):
        return (f"CANNOT ANALYSE\n  {r['fatal']}\n\n"
                "Stop here. Do not substitute a remembered price -- in crypto that is\n"
                "wrong by a multiple often enough to invalidate the whole analysis.")

    o = [f"{r['name']} ({r['symbol']})   rank #{r.get('rank') or 'unranked'}",
         f"  fetched {r['fetched_at']}   feed age {r['data_age_minutes']} min", ""]
    o.append(f"  Price        {fmt_price(r['price_usd'])}")
    if r["cross_check"]:
        cc = "   ".join(f"{k} {fmt_price(v)}" for k, v in r["cross_check"].items())
        spread = f"spread {r['price_spread_pct']}%" if r["price_spread_pct"] is not None else ""
        o.append(f"  Cross-check  {cc}   {spread}")
    o.append(f"  Market cap   {fmt_usd(r['market_cap_usd'])}"
             f"      FDV {fmt_usd(r['fdv_usd'])}"
             + (f"   FDV/MC {r['fdv_to_mcap']}x" if r["fdv_to_mcap"] else ""))
    o.append(f"  Volume 24h   {fmt_usd(r['volume_24h_usd'])}"
             + (f"   {r['volume_to_mcap']:.1%} of mcap" if r["volume_to_mcap"] else ""))
    o.append("")
    o.append(f"  Change       24h {fmt_pct(r['change_24h_pct'])}   "
             f"7d {fmt_pct(r['change_7d_pct'])}   "
             f"30d {fmt_pct(r['change_30d_pct'])}   "
             f"1y {fmt_pct(r['change_1y_pct'])}")
    o.append(f"  From ATH     {fmt_pct(r['ath_change_pct'])}   "
             f"(ATH {fmt_price(r['ath_usd'])} on {(r['ath_date'] or '?')[:10]})")
    o.append("")
    sup = (f"  Supply       circ {r['circulating_supply']:,.0f}" if r["circulating_supply"]
           else "  Supply       n/a")
    if r.get("total_supply"):
        sup += f"   total {r['total_supply']:,.0f}"
    if r.get("max_supply"):
        sup += f"   max {r['max_supply']:,.0f}"
    o.append(sup)
    if r.get("categories"):
        o.append(f"  Categories   {', '.join(r['categories'])}")

    if r["problems"]:
        o.append("")
        o.append("  BLOCKING -- do not produce a rating on this data")
        for p in r["problems"]:
            o.append(f"    x {p}")
    if r["warnings"]:
        o.append("")
        o.append("  FLAGS")
        for w in r["warnings"]:
            o.append(f"    ! {w}")
    o.append("")
    o.append(f"  Every figure above is as of {r['fetched_at']}. Quote that timestamp in")
    o.append("  the analysis, because a price without a time is not a fact.")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("coin_id", nargs="?", help="CoinGecko id, e.g. bitcoin, solana")
    ap.add_argument("--search", help="find the id for a name or ticker")
    ap.add_argument("--max-age", type=float, default=DEFAULT_MAX_AGE_MIN,
                    help=f"maximum feed age in minutes (default {DEFAULT_MAX_AGE_MIN})")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.search:
        hits, err = search(args.search)
        if err:
            print(f"search failed: {err}", file=sys.stderr)
            return 3
        if not hits:
            print(f"nothing matched {args.search!r}. If this is a very new token it may "
                  "not be listed anywhere yet, which is a finding in itself.")
            return 2
        if args.json:
            print(json.dumps(hits, indent=2))
        else:
            print(f"matches for {args.search!r} -- pick the id, and check the rank, "
                  "because tickers are reused by impostors:\n")
            for h in hits:
                print(f"  {h['id']:<28} {h['symbol']:<8} #{h['rank'] or '-':<6} {h['name']}")
        return 0

    if not args.coin_id:
        ap.error("give a coin id, or --search to find one")

    r = collect(args.coin_id, args.max_age)
    print(json.dumps(r, indent=2) if args.json else render(r))
    if r.get("fatal"):
        return 3
    return 0 if r["ok"] and not r["warnings"] else 2


if __name__ == "__main__":
    sys.exit(main())
