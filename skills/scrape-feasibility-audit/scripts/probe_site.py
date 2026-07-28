#!/usr/bin/env python3
"""Probe a public URL and report what would stand between a scraper and its content.

Deliberately gentle: a handful of requests, a delay between them, an honest
User-Agent, and robots.txt consulted before the target page is fetched. The
point is to characterise defenses, not to defeat them — a tool that hammered
the origin to find out whether the origin minds being hammered would be
answering its own question.

Standard library only, so it runs anywhere Python 3.8+ does.

Usage:
    python3 probe_site.py https://example.com/products
    python3 probe_site.py https://example.com --json
    python3 probe_site.py https://example.com --force   # path is robots-disallowed
"""

import argparse
import gzip
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from http.cookiejar import CookieJar

UA = "scrape-feasibility-audit/1.0 (+automated site audit; honors robots.txt)"
TIMEOUT = 20

# Edge/bot vendors, split by what a signal actually proves.
#
# This split is the whole point of the table. Nearly a fifth of the web sits behind
# Cloudflare, so "cf-ray is present" says only that the site uses a popular CDN — it
# says nothing about bot policy. Treating passive CDN markers as evidence of bot
# management would rate half the internet "hard" and make the tool useless.
#
#   passive_* : this vendor is in the request path (CDN, WAF, hosting)
#   active_*  : this vendor's bot-management logic is actually engaged
#
# Difficulty is only claimed when an active marker fires; passive-only detections
# are reported as informational.
VENDORS = [
    {
        "name": "Cloudflare",
        "passive_headers": ["cf-ray", "cf-cache-status"],
        "passive_cookies": ["__cflb", "__cfruid"],
        "active_headers": ["cf-mitigated"],
        "active_cookies": ["__cf_bm", "cf_clearance"],
        "active_body": ["/cdn-cgi/challenge-platform/", "cf-browser-verification"],
        "difficulty": "high",
        "note": "__cf_bm means Bot Management is scoring requests; cf_clearance means a challenge "
                "was passed. A bare cf-ray is just the CDN and implies nothing about bot policy.",
    },
    {
        "name": "Akamai Bot Manager",
        "passive_headers": ["x-akamai-transformed"],
        "passive_cookies": ["akacd_", "ak_bmsc"],
        "active_headers": ["akamai-grn"],
        "active_cookies": ["_abck", "bm_sz", "bm_sv"],
        "active_body": ["akam-sw.js", "/akam/"],
        "difficulty": "high",
        "note": "_abck is the sensor cookie and its value encodes whether the session is trusted. "
                "Block pages carry an akamai-grn reference number.",
    },
    {
        "name": "DataDome",
        "passive_headers": [],
        "passive_cookies": [],
        "active_headers": ["x-datadome", "x-dd-b"],
        "active_cookies": ["datadome"],
        "active_body": ["captcha.datadome.co", "js.datadome.co"],
        "difficulty": "high",
        "note": "ML-scored per request. Frequently pairs with a slider puzzle on challenge.",
    },
    {
        "name": "HUMAN Security (PerimeterX)",
        "passive_headers": [],
        "passive_cookies": [],
        "active_headers": ["x-px"],
        "active_cookies": ["_px3", "_px2", "_pxhd", "_pxvid", "_pxde"],
        "active_body": ["px-cloud.net", "perimeterx", "/px/captcha"],
        "difficulty": "high",
        "note": "Serves a 403 with a 'Please verify you are a human' interstitial when tripped.",
    },
    {
        "name": "Kasada",
        "passive_headers": [],
        "passive_cookies": [],
        "active_headers": ["x-kpsdk-ct", "x-kpsdk-cd", "x-kpsdk-r"],
        "active_cookies": ["KP_UIDz", "KP_UIDzskip"],
        "active_body": ["kpsdk"],
        "difficulty": "very high",
        "note": "Unbranded by design. A bare 429 or 403 with an almost-empty body and no vendor "
                "header anywhere is itself the Kasada tell.",
    },
    {
        "name": "Imperva (Incapsula)",
        "passive_headers": ["x-cdn"],
        "passive_cookies": [],
        "active_headers": ["x-iinfo"],
        "active_cookies": ["incap_ses_", "visid_incap_", "nlbi_"],
        "active_body": ["_Incapsula_Resource"],
        "difficulty": "high",
        "note": "Injects an _Incapsula_Resource script on challenge pages.",
    },
    {
        "name": "AWS WAF Bot Control",
        "passive_headers": ["x-amz-cf-id", "x-amz-cf-pop"],
        "passive_cookies": [],
        "active_headers": ["x-amzn-waf-action"],
        "active_cookies": ["aws-waf-token"],
        "active_body": ["awswaf.com"],
        "difficulty": "medium",
        "note": "x-amz-cf-id alone is plain CloudFront. The aws-waf-token cookie is what shows "
                "Bot Control is switched on.",
    },
    {
        "name": "F5 / BIG-IP ASM",
        "passive_headers": [],
        "passive_cookies": ["BIGipServer"],
        "active_headers": ["x-f5-", "x-waf-"],
        "active_cookies": ["TS01", "TSPD_101"],
        "active_body": ["/TSPD/", "/TSbd/"],
        "difficulty": "medium",
        "note": "BIGipServer alone is just load balancing; TS-prefixed cookies indicate ASM.",
    },
    {
        "name": "Sucuri",
        "passive_headers": ["x-sucuri-id", "x-sucuri-cache"],
        "passive_cookies": [],
        "active_headers": [],
        "active_cookies": ["sucuri_cloudproxy_uuid"],
        "active_body": ["sucuri_cloudproxy_js"],
        "difficulty": "low",
        "note": "Mostly a WAF; rarely fingerprints browsers deeply.",
    },
    {
        "name": "Fastly",
        "passive_headers": ["x-served-by", "x-fastly", "fastly-restarts"],
        "passive_cookies": [],
        "active_headers": [],
        "active_cookies": [],
        "active_body": [],
        "difficulty": "low",
        "note": "CDN only. Any bot rules run above it and would show as a generic block page.",
    },
    {
        "name": "Vercel",
        "passive_headers": ["x-vercel-id", "x-vercel-cache"],
        "passive_cookies": [],
        "active_headers": [],
        "active_cookies": [],
        "active_body": [],
        "difficulty": "low",
        "note": "Hosting/CDN. Vercel's optional Attack Challenge mode surfaces as a challenge page.",
    },
]

# CAPTCHA vendors, identified from script sources and widget markup.
CAPTCHAS = [
    {
        "name": "reCAPTCHA v2",
        "markers": ["g-recaptcha", "google.com/recaptcha/api.js", "g-recaptcha-response"],
        "exclude": ["render="],
        "kind": "interactive challenge",
    },
    {
        "name": "reCAPTCHA v3",
        "markers": ["recaptcha/api.js?render=", "grecaptcha.execute"],
        "exclude": [],
        "kind": "invisible score",
    },
    {
        "name": "hCaptcha",
        "markers": ["hcaptcha.com/1/api.js", "h-captcha", "h-captcha-response"],
        "exclude": [],
        "kind": "interactive challenge",
    },
    {
        "name": "Cloudflare Turnstile",
        "markers": ["challenges.cloudflare.com/turnstile", "cf-turnstile"],
        "exclude": [],
        "kind": "invisible or interactive",
    },
    {
        "name": "Arkose Labs (FunCaptcha)",
        "markers": ["arkoselabs.com", "funcaptcha", "fc-token"],
        "exclude": [],
        "kind": "interactive puzzle",
    },
    {
        "name": "GeeTest",
        "markers": ["/gt.js", "geetest", "gt_captcha"],
        "exclude": [],
        "kind": "slider puzzle",
    },
]

# Client-side app shells: if the page is one of these and carries little text,
# the content arrives via XHR and the HTML alone is not worth parsing.
SPA_MARKERS = [
    ('id="__next"', "Next.js"),
    ("__NEXT_DATA__", "Next.js"),
    ('id="__nuxt"', "Nuxt"),
    ("__NUXT__", "Nuxt"),
    ("<app-root", "Angular"),
    ('id="root"', "React-style root"),
    ('data-reactroot', "React"),
    ("window.__INITIAL_STATE__", "embedded state"),
    ("window.__APOLLO_STATE__", "Apollo GraphQL"),
]


def make_ssl_context():
    """Default trust store, falling back to certifi.

    Framework Python builds on macOS ship with an empty CA store until the user
    runs 'Install Certificates.command', which turns every probe into a confusing
    CERTIFICATE_VERIFY_FAILED. Borrowing certifi's bundle when the default store
    is empty keeps verification on instead of tempting anyone to disable it.
    """
    ctx = ssl.create_default_context()
    paths = ssl.get_default_verify_paths()
    if not paths.cafile and not paths.capath:
        try:
            import certifi
            ctx.load_verify_locations(cafile=certifi.where())
        except Exception:
            pass
    return ctx


def build_opener():
    ctx = make_ssl_context()
    jar = CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar),
    )
    opener.addheaders = [
        ("User-Agent", UA),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Language", "en-US,en;q=0.9"),
    ]
    return opener, jar


def decode_body(raw, encoding):
    if encoding == "gzip":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
    elif encoding == "deflate":
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            try:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            except zlib.error:
                pass
    return raw.decode("utf-8", errors="replace")


def fetch(opener, url, max_bytes=600_000):
    """Return (status, final_url, headers_dict, body_text, error)."""
    request = urllib.request.Request(url)
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            raw = response.read(max_bytes)
            headers = {k.lower(): v for k, v in response.headers.items()}
            body = decode_body(raw, headers.get("content-encoding", "").lower())
            return response.status, response.geturl(), headers, body, None
    except urllib.error.HTTPError as exc:
        raw = exc.read(max_bytes) if hasattr(exc, "read") else b""
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        body = decode_body(raw, headers.get("content-encoding", "").lower())
        # A blocked response is a finding, not a failure — keep it.
        return exc.code, url, headers, body, None
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as exc:
        return None, url, {}, "", str(exc)


def parse_robots(text, path):
    """Return robots.txt facts relevant to `path` under a generic user-agent."""
    result = {
        "present": True,
        "path_disallowed": False,
        "matched_rule": None,
        "crawl_delay": None,
        "sitemaps": [],
        "blocks_all_bots": False,
        "named_scraper_bans": [],
    }
    star_rules = []
    current_agents = []
    # Consecutive User-agent lines share one rule group; the first directive after
    # them closes the group, so the next User-agent line starts a fresh one.
    last_line_was_agent = False
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()

        if field == "user-agent":
            if not last_line_was_agent:
                current_agents = []
            current_agents.append(value.lower())
            last_line_was_agent = True
            continue

        last_line_was_agent = False
        if field == "sitemap":
            result["sitemaps"].append(value)
            continue

        applies_to_star = "*" in current_agents
        if field in ("disallow", "allow") and applies_to_star:
            star_rules.append((field, value))
            if field == "disallow" and value == "/":
                result["blocks_all_bots"] = True
        if field == "crawl-delay" and applies_to_star:
            try:
                result["crawl_delay"] = float(value)
            except ValueError:
                pass
        if field == "disallow" and value == "/":
            result["named_scraper_bans"].extend(a for a in current_agents if a != "*")

    # Longest matching prefix wins, matching the robots.txt convention.
    best = None
    for field, value in star_rules:
        if value and path.startswith(value) and (best is None or len(value) > len(best[1])):
            best = (field, value)
    if best:
        result["matched_rule"] = f"{best[0].title()}: {best[1]}"
        result["path_disallowed"] = best[0] == "disallow"
    return result


def detect_vendors(headers, cookies, body):
    """Identify vendors, recording whether bot management is merely present or engaged."""
    header_blob = " ".join(headers.keys()).lower()
    cookie_blob = " ".join(cookies).lower()
    body_lower = body.lower()

    def hits_for(header_keys, cookie_keys, body_keys):
        hits = []
        hits += [f"header:{h}" for h in header_keys if h.lower() in header_blob]
        hits += [f"cookie:{c}" for c in cookie_keys if c.lower() in cookie_blob]
        hits += [f"body:{b}" for b in body_keys if b.lower() in body_lower]
        return hits

    found = []
    for vendor in VENDORS:
        passive = hits_for(vendor["passive_headers"], vendor["passive_cookies"], [])
        active = hits_for(vendor["active_headers"], vendor["active_cookies"], vendor["active_body"])
        if not passive and not active:
            continue
        found.append({
            "vendor": vendor["name"],
            "engaged": bool(active),
            # Claiming a difficulty on passive-only evidence would overstate the case.
            "difficulty": vendor["difficulty"] if active else "not indicated",
            "evidence": active + passive,
            "active_evidence": active,
            "passive_evidence": passive,
            "note": vendor["note"],
        })
    return found


def detect_captchas(body):
    body_lower = body.lower()
    found = []
    for captcha in CAPTCHAS:
        hits = [m for m in captcha["markers"] if m.lower() in body_lower]
        if not hits:
            continue
        if captcha["exclude"] and any(e.lower() in body_lower for e in captcha["exclude"]):
            # e.g. don't report v2 when the render= param marks it as v3
            if captcha["name"] == "reCAPTCHA v2":
                continue
        found.append({"type": captcha["name"], "kind": captcha["kind"], "evidence": hits})
    return found


def analyse_rendering(body):
    """Decide whether useful content is in the HTML or arrives later via JS."""
    stripped = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", body)
    text = re.sub(r"(?s)<[^>]+>", " ", stripped)
    text = re.sub(r"\s+", " ", text).strip()

    frameworks = sorted({label for marker, label in SPA_MARKERS if marker in body})
    embedded = []
    if "__NEXT_DATA__" in body:
        embedded.append("__NEXT_DATA__ JSON blob")
    if "window.__NUXT__" in body:
        embedded.append("__NUXT__ state")
    if "application/ld+json" in body:
        embedded.append("JSON-LD structured data")
    if "window.__INITIAL_STATE__" in body:
        embedded.append("__INITIAL_STATE__ blob")
    if "window.__APOLLO_STATE__" in body:
        embedded.append("__APOLLO_STATE__ cache")
    # The generic case, and the one most often missed: a React-style app that ships
    # its data in a plain JSON script tag. GitHub does this via
    # data-target="react-app.embeddedData". Such a page looks client-rendered by
    # every other measure while the data sits in the HTML already — mistaking it
    # for one sends people to a headless browser to render JSON they already have.
    json_blocks = len(re.findall(r'<script[^>]+type=["\']application/json["\']', body, re.I))
    if json_blocks:
        embedded.append(f"{json_blocks} application/json script block(s)")

    if embedded:
        verdict = "server-embedded JSON"
        rationale = "Data ships inside the HTML — parse the JSON blob directly, no browser needed."
    elif len(text) < 800 and frameworks:
        verdict = "client-rendered"
        rationale = f"Only {len(text)} chars of text alongside a {'/'.join(frameworks)} shell."
    elif len(text) < 800:
        verdict = "thin"
        rationale = (f"Only {len(text)} chars of text and no framework shell — either a genuinely "
                     "small page or an interstitial. Check the status and block signals below.")
    else:
        verdict = "server-rendered"
        rationale = f"{len(text)} chars of text present in the initial HTML."

    return {
        "verdict": verdict,
        "rationale": rationale,
        "visible_text_chars": len(text),
        "frameworks": frameworks,
        "embedded_data": embedded,
    }


def looks_like_block_page(status, body, vendors, captchas):
    if status in (401, 403, 407, 429, 503):
        return True
    signals = ["access denied", "are you a human", "verify you are human", "unusual traffic",
               "enable javascript and cookies", "bot detected", "request blocked",
               "checking your browser", "attention required"]
    low = body.lower()
    if any(s in low for s in signals):
        return True
    # A challenge CAPTCHA on what should be a content page is itself a block.
    return bool(captchas) and len(body) < 20_000 and bool(vendors)


def score(findings):
    """Roll findings into a tier. Explains itself so the caller can argue with it."""
    reasons = []
    level = 0

    diff_rank = {"low": 1, "medium": 2, "high": 3, "very high": 4}
    for vendor in findings["bot_protection"]:
        if not vendor["engaged"]:
            # Present in the request path but not scoring us; not evidence of difficulty.
            reasons.append(f"{vendor['vendor']} is in the path but shows no active bot management")
            continue
        rank = diff_rank.get(vendor["difficulty"], 1)
        if rank >= 3:
            reasons.append(f"{vendor['vendor']} bot management is actively engaged")
        level = max(level, rank)

    for captcha in findings["captchas"]:
        if captcha["kind"] != "invisible score":
            level = max(level, 3)
            reasons.append(f"{captcha['type']} gates the page")

    if findings["blocked_on_first_request"]:
        level = max(level, 3)
        reasons.append("the very first unauthenticated request was blocked")

    if findings["rendering"]["verdict"] == "client-rendered":
        level = max(level, 2)
        reasons.append("content is client-rendered, so a plain HTTP client sees an empty shell")

    robots = findings["robots"]
    if robots.get("blocks_all_bots"):
        reasons.append("robots.txt disallows all crawlers — a policy signal, not a technical one")
    if findings["rendering"]["embedded_data"]:
        reasons.append("but structured data is embedded in the HTML, which simplifies extraction")

    tiers = {0: "trivial", 1: "easy", 2: "moderate", 3: "hard", 4: "very hard"}
    return {"tier": tiers[level], "reasons": reasons}


def probe(url, force=False, delay=1.0):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SystemExit(f"error: expected an http(s) URL, got {url!r}")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path or "/"

    opener, jar = build_opener()
    findings = {"url": url, "origin": origin, "path": path}

    # robots.txt first — it decides whether the page fetch happens at all.
    _, _, _, robots_body, robots_err = fetch(opener, f"{origin}/robots.txt")
    if robots_err or not robots_body.strip() or "<html" in robots_body[:200].lower():
        findings["robots"] = {"present": False, "path_disallowed": False, "sitemaps": [],
                              "crawl_delay": None, "blocks_all_bots": False,
                              "named_scraper_bans": [], "matched_rule": None}
    else:
        findings["robots"] = parse_robots(robots_body, path)

    if findings["robots"]["path_disallowed"] and not force:
        findings["skipped_page_fetch"] = (
            f"robots.txt disallows {path} for generic crawlers ({findings['robots']['matched_rule']}). "
            "Page not fetched. Re-run with --force only if you have permission that robots.txt "
            "does not reflect, such as auditing a site you operate."
        )
        findings["bot_protection"] = []
        findings["captchas"] = []
        findings["rendering"] = {"verdict": "not assessed", "rationale": "page not fetched",
                                 "visible_text_chars": 0, "frameworks": [], "embedded_data": []}
        findings["blocked_on_first_request"] = False
        findings["status"] = None
        findings["assessment"] = {"tier": "unknown", "reasons": ["page not fetched; robots.txt disallows it"]}
        return findings

    time.sleep(delay)
    status, final_url, headers, body, error = fetch(opener, url)
    if error:
        raise SystemExit(f"error: could not reach {url}: {error}")

    cookie_names = [c.name for c in jar]
    for raw in (headers.get("set-cookie", ""),):
        cookie_names += re.findall(r"(?:^|,\s*)([A-Za-z0-9_\-.]+)=", raw)

    findings["status"] = status
    findings["final_url"] = final_url
    findings["redirected"] = final_url.rstrip("/") != url.rstrip("/")
    findings["server"] = headers.get("server")
    findings["cookies_set"] = sorted(set(cookie_names))
    findings["bot_protection"] = detect_vendors(headers, cookie_names, body)
    findings["captchas"] = detect_captchas(body)
    findings["rendering"] = analyse_rendering(body)
    findings["blocked_on_first_request"] = looks_like_block_page(
        status, body, findings["bot_protection"], findings["captchas"])
    findings["rate_limit_headers"] = {
        k: v for k, v in headers.items()
        if "ratelimit" in k.replace("-", "") or k in ("retry-after",)
    }
    findings["auth_required"] = status in (401, 403) and not findings["bot_protection"]
    findings["assessment"] = score(findings)
    return findings


def render_text(f):
    out = []
    out.append(f"Target:   {f['url']}")
    if f.get("status") is not None:
        out.append(f"Status:   {f['status']}" + ("  (redirected)" if f.get("redirected") else ""))
    if f.get("server"):
        out.append(f"Server:   {f['server']}")
    out.append("")

    if "skipped_page_fetch" in f:
        out.append("!! " + f["skipped_page_fetch"])
        out.append("")

    robots = f["robots"]
    out.append("robots.txt")
    if not robots["present"]:
        out.append("  none published")
    else:
        out.append(f"  path {f['path']}: {'DISALLOWED' if robots['path_disallowed'] else 'allowed'}"
                   + (f" ({robots['matched_rule']})" if robots["matched_rule"] else ""))
        if robots["crawl_delay"]:
            out.append(f"  crawl-delay: {robots['crawl_delay']}s  <- pace requests at least this slowly")
        if robots["blocks_all_bots"]:
            out.append("  disallows ALL crawlers site-wide")
        if robots["named_scraper_bans"]:
            out.append(f"  bans named agents: {', '.join(sorted(set(robots['named_scraper_bans']))[:8])}")
        if robots["sitemaps"]:
            out.append(f"  sitemaps: {len(robots['sitemaps'])} declared  <- cheapest way to enumerate URLs")
            for sitemap in robots["sitemaps"][:3]:
                out.append(f"    {sitemap}")
    out.append("")

    out.append("Bot protection")
    if not f["bot_protection"]:
        out.append("  none detected from headers, cookies, or markup")
    for vendor in f["bot_protection"]:
        state = f"ENGAGED [{vendor['difficulty']}]" if vendor["engaged"] else "present, not engaged"
        out.append(f"  {vendor['vendor']}  {state}")
        out.append(f"    evidence: {', '.join(vendor['evidence'][:5])}")
        out.append(f"    {vendor['note']}")
    out.append("")

    out.append("CAPTCHA")
    if not f["captchas"]:
        out.append("  none present on this response")
    for captcha in f["captchas"]:
        out.append(f"  {captcha['type']} ({captcha['kind']})")
        out.append(f"    evidence: {', '.join(captcha['evidence'])}")
    out.append("")

    rendering = f["rendering"]
    out.append("Content delivery")
    out.append(f"  {rendering['verdict']}: {rendering['rationale']}")
    if rendering["frameworks"]:
        out.append(f"  framework: {', '.join(rendering['frameworks'])}")
    if rendering["embedded_data"]:
        out.append(f"  embedded data: {', '.join(rendering['embedded_data'])}")
    out.append("")

    if f.get("rate_limit_headers"):
        out.append("Rate limiting")
        for key, value in f["rate_limit_headers"].items():
            out.append(f"  {key}: {value}")
        out.append("")

    if f.get("blocked_on_first_request"):
        out.append("!! The first plain request was already challenged or blocked.")
        out.append("   Everything above describes the block page, which may hide the real defenses.")
        out.append("")

    assessment = f["assessment"]
    out.append(f"Assessment: {assessment['tier'].upper()}")
    for reason in assessment["reasons"]:
        out.append(f"  - {reason}")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Probe a public URL for scraping obstacles.")
    parser.add_argument("url")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--force", action="store_true",
                        help="fetch even if robots.txt disallows the path")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="seconds between requests (default 1.0)")
    args = parser.parse_args()

    findings = probe(args.url, force=args.force, delay=args.delay)
    print(json.dumps(findings, indent=2) if args.json else render_text(findings))


if __name__ == "__main__":
    sys.exit(main())
