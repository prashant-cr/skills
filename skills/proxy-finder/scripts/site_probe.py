#!/usr/bin/env python3
"""Measure the things about a site that decide which proxy you need, and how much it costs.

Two facts drive the whole budget and both are cheap to measure:

  1. Whether a plain request already works. If it does, the correct proxy spend is
     often zero, and everything else here is a discussion about money you did not
     need to spend. This is the most commonly skipped check and the most valuable.
  2. How many bytes a page costs. Residential proxies bill per gigabyte, so
     bandwidth *is* the bill. Whether you load images and fonts usually changes the
     monthly cost more than switching vendors does.

    python3 site_probe.py https://example.com/products
    python3 site_probe.py https://example.com --samples 5 --json

Deliberately polite: three requests by default, spaced out, and it will not probe a
path robots.txt disallows unless you pass --force. It is a measurement tool, not a
scraper -- keep it that way and it stays welcome.

Standard library only.
"""

import argparse
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
TIMEOUT = 20
DELAY = 1.5          # seconds between samples; do not hammer someone's origin
ASSET_SAMPLE = 8     # how many subresources to size before extrapolating

# Header and body fingerprints. Kept light on purpose -- scrape-feasibility-audit
# does the deep vendor detection, and duplicating it here would only let the two
# drift apart.
WAF_HEADERS = {
    "cf-ray": "Cloudflare", "cf-cache-status": "Cloudflare",
    "x-akamai-transformed": "Akamai", "akamai-grn": "Akamai",
    "x-datadome": "DataDome", "x-iinfo": "Imperva",
    "x-sucuri-id": "Sucuri", "x-amz-cf-id": "AWS CloudFront",
    "x-kasada-classification": "Kasada", "server-timing": None,
}
BLOCK_MARKERS = [
    (rb"just a moment", "Cloudflare interstitial"),
    (rb"checking your browser", "JS challenge"),
    (rb"cf-browser-verification", "Cloudflare challenge"),
    (rb"enable javascript and cookies", "JS/cookie challenge"),
    (rb"access denied", "hard block"),
    (rb"attention required", "Cloudflare block"),
    (rb"unusual traffic", "rate/behaviour block"),
    (rb"are you a robot", "bot challenge"),
    (rb"captcha", "CAPTCHA present"),
    (rb"datadome", "DataDome"),
    (rb"px-captcha", "HUMAN/PerimeterX"),
]
ASSET_RE = re.compile(
    rb"""<(?:img|script|source)[^>]+src=["']([^"']+)["']|"""
    rb"""<link[^>]+href=["']([^"']+)["']""", re.I)


def _ctx():
    return ssl.create_default_context()


def fetch(url, ua=BROWSER_UA, method="GET", max_bytes=3_000_000):
    """Return (status, headers, body, elapsed, error). Never raises on HTTP errors."""
    req = urllib.request.Request(url, method=method, headers={
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "identity",   # so byte counts mean what they say
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ctx()) as r:
            body = r.read(max_bytes)
            return r.status, dict(r.headers), body, time.time() - t0, None
    except urllib.error.HTTPError as e:
        try:
            body = e.read(max_bytes)
        except Exception:
            body = b""
        return e.code, dict(e.headers or {}), body, time.time() - t0, None
    except Exception as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            return _curl(url, ua, method)
        return None, {}, b"", time.time() - t0, f"{type(e).__name__}: {e}"


def _curl(url, ua, method):
    """Fallback for Python installs shipped without a CA bundle. Verification stays on."""
    import subprocess
    sep = "===HDRSPLIT==="
    cmd = ["curl", "-sS", "-m", str(TIMEOUT), "-A", ua, "-D", "-", "-o", "-",
           "-w", f"\n{sep}%{{http_code}}", url]
    if method == "HEAD":
        cmd.insert(1, "-I")
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        return None, {}, b"", 0.0, "no CA bundle and curl unavailable"
    raw = p.stdout
    status = None
    if sep.encode() in raw:
        raw, _, tail = raw.rpartition(sep.encode())
        try:
            status = int(tail.strip())
        except ValueError:
            status = None
    head, _, body = raw.partition(b"\r\n\r\n")
    headers = {}
    for line in head.decode("latin-1", "replace").splitlines()[1:]:
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip()] = v.strip()
    return status, headers, body, time.time() - t0, None


def robots_for(url, ua="*"):
    """Fetch robots.txt and decide whether the target path is allowed.

    A small, deliberately conservative matcher: longest-match wins, and anything
    ambiguous is reported as such rather than resolved in our favour.
    """
    p = urllib.parse.urlparse(url)
    root = f"{p.scheme}://{p.netloc}"
    status, _h, body, _t, err = fetch(root + "/robots.txt")
    out = {"url": root + "/robots.txt", "status": status, "allowed": None,
           "matched_rule": None, "crawl_delay": None, "sitemaps": [], "error": err}
    if err or status != 200 or not body:
        out["allowed"] = None
        out["note"] = "no robots.txt readable -- absence is not permission, but it is not a prohibition either"
        return out

    text = body.decode("utf-8", "replace")
    path = p.path or "/"
    groups = {}
    # Consecutive User-agent lines share one rule block -- Google's own robots.txt
    # opens with "User-agent: *" then "User-agent: Yandex" before any rule. Treating
    # only the last one as current empties the "*" group, and the failure is silent
    # and permissive: a disallowed path reads as allowed. So collect the run of
    # agents and apply each following rule to all of them.
    current_agents, expecting_agents = [], True
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if not expecting_agents:
                current_agents, expecting_agents = [], True
            agent = v.lower()
            current_agents.append(agent)
            groups.setdefault(agent, {"allow": [], "disallow": [], "delay": None})
        elif k in ("allow", "disallow"):
            expecting_agents = False
            for a in current_agents:
                groups[a][k].append(v)
        elif k == "crawl-delay":
            expecting_agents = False
            for a in current_agents:
                try:
                    groups[a]["delay"] = float(v)
                except ValueError:
                    pass
        elif k == "sitemap":
            out["sitemaps"].append(v)

    rules = groups.get(ua.lower()) or groups.get("*")
    if not rules:
        out["allowed"] = True
        out["matched_rule"] = "no applicable group"
        return out
    out["crawl_delay"] = rules["delay"]

    best, best_len, best_kind = None, -1, None
    for kind in ("allow", "disallow"):
        for rule in rules[kind]:
            if not rule:
                continue
            pat = rule.rstrip("$")
            if path.startswith(pat) and len(pat) > best_len:
                best, best_len, best_kind = rule, len(pat), kind
    if best is None:
        out["allowed"] = True
        out["matched_rule"] = "no matching rule"
    else:
        out["allowed"] = (best_kind == "allow")
        out["matched_rule"] = f"{best_kind}: {best}"
    return out


def classify(status, headers, body):
    """Is this a real page, a challenge, or a block?"""
    lower = body[:200_000].lower()
    hits = [name for pat, name in BLOCK_MARKERS if re.search(pat, lower)]
    waf = set()
    for h, vendor in WAF_HEADERS.items():
        if h in {k.lower() for k in headers} and vendor:
            waf.add(vendor)
    srv = str(headers.get("Server", "")).lower()
    for token, vendor in (("cloudflare", "Cloudflare"), ("akamai", "Akamai"),
                          ("awselb", "AWS"), ("sucuri", "Sucuri")):
        if token in srv:
            waf.add(vendor)

    if status is None:
        verdict = "unreachable"
    elif status in (401, 403, 407):
        verdict = "blocked"
    elif status == 429:
        verdict = "rate_limited"
    elif status in (503, 520, 521, 522) and hits:
        verdict = "challenged"
    elif hits and len(body) < 60_000:
        verdict = "challenged"
    elif 200 <= status < 300:
        verdict = "ok"
    elif 300 <= status < 400:
        verdict = "redirect"
    else:
        verdict = f"http_{status}"
    return verdict, hits, sorted(waf)


def size_assets(base_url, body, sample=ASSET_SAMPLE):
    """Estimate full page weight by sizing a sample of subresources.

    This is what turns 'a page' into 'a number of gigabytes a month', which is the
    only way to compare a per-GB proxy against a per-request API honestly.
    """
    urls, seen = [], set()
    for m in ASSET_RE.finditer(body):
        raw = (m.group(1) or m.group(2) or b"").decode("latin-1", "replace")
        if not raw or raw.startswith(("data:", "javascript:", "#")):
            continue
        full = urllib.parse.urljoin(base_url, raw)
        if full in seen:
            continue
        seen.add(full)
        urls.append(full)

    total_assets = len(urls)
    if not total_assets:
        return {"asset_count": 0, "sampled": 0, "sampled_bytes": 0,
                "est_asset_bytes": 0}

    sampled, sampled_bytes = 0, 0
    for u in urls[:sample]:
        status, headers, b, _t, err = fetch(u, max_bytes=1_500_000)
        if err or status is None or status >= 400:
            continue
        n = int(headers.get("Content-Length") or 0) or len(b)
        if n:
            sampled += 1
            sampled_bytes += n
        time.sleep(0.2)

    avg = (sampled_bytes / sampled) if sampled else 0
    return {"asset_count": total_assets, "sampled": sampled,
            "sampled_bytes": sampled_bytes,
            "est_asset_bytes": int(avg * total_assets)}


def probe(url, samples=3, ua=BROWSER_UA, do_assets=True):
    r = {"url": url, "probed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "samples": [], "note": None}

    r["robots"] = robots_for(url)

    statuses = []
    first_body, first_headers = b"", {}
    for i in range(samples):
        status, headers, body, elapsed, err = fetch(url, ua=ua)
        verdict, hits, waf = classify(status, headers, body)
        if i == 0:
            first_body, first_headers = body, headers
        statuses.append(verdict)
        r["samples"].append({"n": i + 1, "status": status, "verdict": verdict,
                             "seconds": round(elapsed, 2), "bytes": len(body),
                             "markers": hits, "waf": waf, "error": err})
        if i < samples - 1:
            time.sleep(DELAY)

    # A redirect is content moving, not a refusal. Counting it as a block
    # would tell someone to buy proxies for a site that simply moved a URL.
    ok = statuses.count("ok") + statuses.count("redirect")
    r["ok_rate"] = round(ok / len(statuses), 2)
    r["verdicts"] = statuses
    r["waf"] = sorted({w for s in r["samples"] for w in s["waf"]})
    r["markers"] = sorted({m for s in r["samples"] for m in s["markers"]})

    html_bytes = len(first_body)
    r["html_bytes"] = html_bytes
    if do_assets and html_bytes and ok:
        a = size_assets(url, first_body)
        r["assets"] = a
        r["full_page_bytes"] = html_bytes + a["est_asset_bytes"]
        if r["full_page_bytes"]:
            r["html_only_share"] = round(html_bytes / r["full_page_bytes"], 3)
    else:
        r["assets"] = None
        r["full_page_bytes"] = html_bytes
        r["html_only_share"] = 1.0

    # --- the verdict that drives the budget -------------------------------
    if r["ok_rate"] == 1.0:
        r["access"] = "open"
        r["proxy_need"] = (
            "Plain requests from this machine's IP succeeded every time. Before "
            "buying anything, confirm that still holds at your real request volume "
            "and from your production IP -- many sites only start blocking after a "
            "few hundred requests. If it holds, the right proxy spend may be zero.")
    elif r["ok_rate"] == 0.0:
        r["access"] = "blocked"
        r["proxy_need"] = (
            "Every plain request failed. Proxies alone may not fix this if the block "
            "is fingerprint-based rather than IP-based -- test a trial proxy before "
            "committing to a plan.")
    else:
        r["access"] = "intermittent"
        r["proxy_need"] = (
            f"{ok} of {len(statuses)} plain requests succeeded. Intermittent blocking "
            "usually means rate limiting rather than an IP ban, and slowing down is "
            "cheaper than any proxy.")

    if r["robots"].get("allowed") is False:
        r["note"] = ("robots.txt disallows this path for the tested user-agent. That is "
                     "the site asking you not to. Recommending infrastructure to do it "
                     "anyway is not a technical question.")
    return r


def render(r):
    o = [f"{r['url']}", f"  probed {r['probed_at']}", ""]
    rb = r["robots"]
    allowed = {True: "allowed", False: "DISALLOWED", None: "unknown"}[rb.get("allowed")]
    o.append(f"  robots.txt   {allowed}"
             + (f"   ({rb['matched_rule']})" if rb.get("matched_rule") else "")
             + (f"   crawl-delay {rb['crawl_delay']}s" if rb.get("crawl_delay") else ""))
    o.append(f"  Access       {r['access'].upper()}   {int(r['ok_rate'] * 100)}% of "
             f"{len(r['samples'])} plain requests succeeded")
    seq = " ".join(s["verdict"] for s in r["samples"])
    o.append(f"  Sequence     {seq}")
    if r["waf"]:
        o.append(f"  Edge/WAF     {', '.join(r['waf'])}")
    if r["markers"]:
        o.append(f"  Markers      {', '.join(r['markers'])}")
    o.append("")
    o.append(f"  HTML         {r['html_bytes'] / 1024:,.0f} KB")
    if r.get("assets"):
        a = r["assets"]
        o.append(f"  Assets       {a['asset_count']} refs, sampled {a['sampled']}"
                 f" -> est {a['est_asset_bytes'] / 1024:,.0f} KB")
        o.append(f"  Full page    {r['full_page_bytes'] / 1024:,.0f} KB"
                 f"   HTML is {r['html_only_share']:.0%} of it")
        saving = 1 - r["html_only_share"]
        if saving > 0.4:
            o.append(f"  -> Blocking images, fonts and CSS cuts about {saving:.0%} of "
                     "bytes. On per-GB proxy pricing that is the same as a "
                     f"{saving:.0%} discount, and it is usually larger than any "
                     "discount you can negotiate.")
    o.append("")
    o.append(f"  {r['proxy_need']}")
    if r.get("note"):
        o.append("")
        o.append(f"  ! {r['note']}")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("url")
    ap.add_argument("--samples", type=int, default=3, help="plain requests to make (default 3)")
    ap.add_argument("--ua", default=BROWSER_UA)
    ap.add_argument("--no-assets", action="store_true", help="skip subresource sizing")
    ap.add_argument("--force", action="store_true",
                    help="probe even if robots.txt disallows the path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url

    rb = robots_for(args.url)
    if rb.get("allowed") is False and not args.force:
        msg = (f"robots.txt disallows this path ({rb['matched_rule']}).\n"
               "Not probing. The site is asking not to be crawled here, and the honest\n"
               "answer to 'which proxy gets me in' is that this is not a proxy problem.\n"
               "If you have permission the site's robots.txt does not reflect, or you\n"
               "are the owner, re-run with --force.")
        print(msg, file=sys.stderr)
        return 3

    if args.samples > 10:
        print("note: capping samples at 10 -- this is a measurement, not a load test",
              file=sys.stderr)
        args.samples = 10

    r = probe(args.url, samples=args.samples, ua=args.ua, do_assets=not args.no_assets)
    print(json.dumps(r, indent=2) if args.json else render(r))
    return 0 if r["access"] == "open" else 2


if __name__ == "__main__":
    sys.exit(main())
