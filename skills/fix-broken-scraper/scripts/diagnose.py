#!/usr/bin/env python3
"""Classify why a scraper stopped working, before anything gets changed.

The expensive mistake in scraper repair is treating every failure as a blocking
problem. "Blocked" is the loudest hypothesis, so people reach for browsers,
proxies and header spoofing — while the actual cause is usually that the page
still returns 200 and the selectors no longer match. Each wrong guess adds
permanent cost to the scraper and none of it addresses the fault.

So this classifies first. It makes at most three requests: one as a plain HTTP
client, one with browser-like headers if the first looked blocked, and robots.txt.
The difference between those two answers is diagnostic — it separates
header-level filtering from something deeper, and no amount of guessing does.

Standard library only, so it runs anywhere Python 3.8+ does.

Usage:
    python3 diagnose.py https://site.com/page --selector ".product-title"
    python3 diagnose.py https://site.com/page --expect-text "Add to cart"
    python3 diagnose.py https://site.com/page --selector "div.price" --json
"""

import argparse
import gzip
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from html.parser import HTMLParser
from http.cookiejar import CookieJar

PLAIN_UA = "python-urllib/3 scraper-diagnostic"
BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
               "image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
}
TIMEOUT = 20

# Just enough to name a vendor when a block is detected. The companion
# scrape-feasibility-audit skill carries the full signature table; repeating all
# of it here would mean two copies drifting apart.
BLOCK_VENDORS = [
    ("Cloudflare", ["__cf_bm", "cf_clearance", "cf-mitigated", "/cdn-cgi/challenge-platform/"]),
    ("Akamai", ["_abck", "bm_sz", "akamai-grn"]),
    ("DataDome", ["datadome", "x-datadome", "captcha-delivery.com"]),
    ("HUMAN/PerimeterX", ["_px3", "_pxhd", "px-cloud.net"]),
    ("Kasada", ["x-kpsdk", "kpsdk"]),
    ("Imperva", ["incap_ses_", "visid_incap_", "_Incapsula_Resource"]),
    ("AWS WAF", ["aws-waf-token", "awswaf.com"]),
]

BLOCK_PHRASES = [
    "access denied", "verify you are human", "are you a human", "unusual traffic",
    "enable javascript and cookies", "bot detected", "request blocked",
    "checking your browser", "attention required", "rate limit",
]


# --------------------------------------------------------------------------
# Minimal CSS selector matching
# --------------------------------------------------------------------------

def parse_selector(selector):
    """Parse a descendant selector chain like 'div.card a#link' into simple parts.

    Supports tag, .class, #id and combinations, separated by descendant spaces.
    That covers the overwhelming majority of selectors people actually write;
    anything more exotic is better checked with the real parsing library the
    scraper already uses.
    """
    parts = []
    for chunk in selector.split():
        tag = None
        classes = set()
        el_id = None
        token = chunk
        m = re.match(r"^([a-zA-Z][\w-]*)", token)
        if m:
            tag = m.group(1).lower()
            token = token[m.end():]
        for sym, value in re.findall(r"([.#])([\w-]+)", token):
            if sym == ".":
                classes.add(value)
            else:
                el_id = value
        parts.append({"tag": tag, "classes": classes, "id": el_id})
    return parts


class SelectorCounter(HTMLParser):
    """Count elements matching a descendant selector chain."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, parts):
        super().__init__(convert_charrefs=True)
        self.parts = parts
        self.stack = []
        self.count = 0

    def _simple_match(self, part, node):
        if part["tag"] and part["tag"] != node["tag"]:
            return False
        if part["classes"] and not part["classes"].issubset(node["classes"]):
            return False
        if part["id"] and part["id"] != node["id"]:
            return False
        return True

    def _chain_matches(self):
        # The last part must match the current element; earlier parts must appear
        # as ancestors in order, though not necessarily contiguously.
        if not self._simple_match(self.parts[-1], self.stack[-1]):
            return False
        need = list(reversed(self.parts[:-1]))
        idx = len(self.stack) - 2
        for part in need:
            while idx >= 0 and not self._simple_match(part, self.stack[idx]):
                idx -= 1
            if idx < 0:
                return False
            idx -= 1
        return True

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        node = {
            "tag": tag.lower(),
            "classes": set((attrs.get("class") or "").split()),
            "id": attrs.get("id"),
        }
        self.stack.append(node)
        if self.stack and self._chain_matches():
            self.count += 1
        if tag.lower() in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break


def count_matches(html, selector):
    try:
        counter = SelectorCounter(parse_selector(selector))
        counter.feed(html)
        return counter.count
    except Exception:
        return None


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def make_ssl_context():
    ctx = ssl.create_default_context()
    paths = ssl.get_default_verify_paths()
    if not paths.cafile and not paths.capath:
        try:
            import certifi
            ctx.load_verify_locations(cafile=certifi.where())
        except Exception:
            pass
    return ctx


def decode_body(raw, encoding):
    if encoding == "gzip":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
    elif encoding == "deflate":
        for wbits in (15, -15):
            try:
                raw = zlib.decompress(raw, wbits)
                break
            except zlib.error:
                continue
    return raw.decode("utf-8", errors="replace")


def fetch(url, headers, ctx):
    """Return a dict describing the response, or the transport error."""
    jar = CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar),
    )
    request = urllib.request.Request(url, headers=headers)
    started = time.time()
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            raw = response.read(800_000)
            hdrs = {k.lower(): v for k, v in response.headers.items()}
            return {
                "status": response.status, "final_url": response.geturl(),
                "headers": hdrs, "body": decode_body(raw, hdrs.get("content-encoding", "").lower()),
                "cookies": [c.name for c in jar], "elapsed": round(time.time() - started, 2),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read(800_000) if hasattr(exc, "read") else b""
        hdrs = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        return {
            "status": exc.code, "final_url": url, "headers": hdrs,
            "body": decode_body(raw, hdrs.get("content-encoding", "").lower()),
            "cookies": [c.name for c in jar], "elapsed": round(time.time() - started, 2),
            "error": None,
        }
    except Exception as exc:
        return {"status": None, "final_url": url, "headers": {}, "body": "",
                "cookies": [], "elapsed": round(time.time() - started, 2),
                "error": f"{type(exc).__name__}: {exc}"}


def looks_blocked(resp):
    if resp["status"] in (401, 403, 407, 429, 503):
        return True
    low = resp["body"][:20_000].lower()
    return any(p in low for p in BLOCK_PHRASES)


def name_vendor(resp):
    blob = (" ".join(resp["headers"].keys()) + " " + " ".join(resp["cookies"]) + " "
            + resp["body"][:60_000]).lower()
    return [name for name, markers in BLOCK_VENDORS if any(m.lower() in blob for m in markers)]


def find_embedded_json(html):
    found = []
    if "__NEXT_DATA__" in html:
        found.append("__NEXT_DATA__")
    if "window.__NUXT__" in html:
        found.append("__NUXT__")
    if "window.__INITIAL_STATE__" in html:
        found.append("__INITIAL_STATE__")
    if "window.__APOLLO_STATE__" in html:
        found.append("__APOLLO_STATE__")
    if "application/ld+json" in html:
        found.append("JSON-LD")
    n = len(re.findall(r'<script[^>]+type=["\']application/json["\']', html, re.I))
    if n:
        found.append(f"{n} application/json script block(s)")
    return found


def visible_text(html):
    stripped = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", stripped)).strip()


# --------------------------------------------------------------------------
# Diagnosis
# --------------------------------------------------------------------------

def diagnose(url, selector=None, expect_text=None, delay=1.0):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SystemExit(f"error: expected an http(s) URL, got {url!r}")

    ctx = make_ssl_context()
    result = {"url": url, "selector": selector, "expect_text": expect_text, "checks": []}

    def check(name, ok, detail):
        result["checks"].append({"check": name, "ok": ok, "detail": detail})

    # 1. Transport. Distinguishing "cannot connect" from "connected and refused"
    # matters, because they have nothing in common as repairs.
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        socket.getaddrinfo(host, port)
        check("dns", True, f"{host} resolves")
    except socket.gaierror as exc:
        check("dns", False, f"{host} does not resolve: {exc}")
        result["verdict"] = {
            "class": "transport",
            "summary": f"DNS resolution failed for {host}.",
            "next_steps": ["Confirm the hostname is still correct — sites do rename and retire domains.",
                           "Check local DNS/VPN/network before touching scraper code."],
        }
        return result

    plain = fetch(url, {"User-Agent": PLAIN_UA, "Accept": "*/*"}, ctx)
    if plain["error"]:
        check("connect", False, plain["error"])
        result["verdict"] = {
            "class": "transport",
            "summary": f"Could not complete a request: {plain['error']}",
            "next_steps": ["Retry to rule out a transient fault.",
                           "If TLS-related, check the certificate chain and your Python trust store.",
                           "If it times out only from this host, suspect a network- or IP-level block."],
        }
        return result

    check("connect", True, f"HTTP {plain['status']} in {plain['elapsed']}s")
    result["plain"] = {"status": plain["status"], "bytes": len(plain["body"]),
                       "final_url": plain["final_url"], "elapsed": plain["elapsed"]}

    redirected = plain["final_url"].rstrip("/") != url.rstrip("/")
    if redirected:
        check("redirect", False, f"redirected to {plain['final_url']}")
    result["redirected_to"] = plain["final_url"] if redirected else None

    blocked_plain = looks_blocked(plain)
    vendors = name_vendor(plain)
    check("plain request accepted", not blocked_plain,
          f"status {plain['status']}" + (f", vendor markers: {', '.join(vendors)}" if vendors else ""))

    # 2. If the plain client looks blocked, retry once with browser headers. The
    # comparison is the whole point: same IP, same TLS stack, only the headers
    # differ, so a different outcome isolates the failure to the header layer.
    browser = None
    if blocked_plain:
        time.sleep(delay)
        browser = fetch(url, BROWSER_HEADERS, ctx)
        blocked_browser = browser["error"] is not None or looks_blocked(browser)
        check("browser-header request accepted", not blocked_browser,
              browser["error"] or f"status {browser['status']}")
        result["browser"] = {"status": browser["status"], "bytes": len(browser["body"]),
                             "error": browser["error"]}

    best = browser if (browser and not browser["error"] and not looks_blocked(browser)) else plain
    html = best["body"]
    result["embedded_json"] = find_embedded_json(html)
    text_len = len(visible_text(html))
    result["visible_text_chars"] = text_len

    # 3. Does the extraction target still exist?
    selector_hits = count_matches(html, selector) if selector else None
    if selector:
        result["selector_matches"] = selector_hits
        check(f"selector {selector!r} matches", bool(selector_hits),
              f"{selector_hits} element(s)" if selector_hits is not None else "could not parse selector")

    text_present = (expect_text.lower() in html.lower()) if expect_text else None
    if expect_text:
        result["expect_text_present"] = text_present
        check(f"text {expect_text!r} present in HTML", bool(text_present),
              "found" if text_present else "absent from raw HTML")

    result["verdict"] = classify(
        plain=plain, browser=browser, blocked_plain=blocked_plain, vendors=vendors,
        redirected=redirected, selector=selector, selector_hits=selector_hits,
        expect_text=expect_text, text_present=text_present,
        embedded=result["embedded_json"], text_len=text_len,
    )
    return result


def classify(plain, browser, blocked_plain, vendors, redirected, selector,
             selector_hits, expect_text, text_present, embedded, text_len):
    """Name the failure class and give the next actions for that class only."""
    vendor_note = f" ({', '.join(vendors)} markers present)" if vendors else ""

    if blocked_plain and browser and not browser["error"] and not looks_blocked(browser):
        return {
            "class": "header-level filtering",
            "summary": (f"The plain client is refused (HTTP {plain['status']}) but the same request "
                        f"with browser headers succeeds{vendor_note}. The block is at the header "
                        "layer, not the network or TLS layer."),
            "next_steps": [
                "Send a realistic, complete header set — including Accept, Accept-Language and a "
                "credible User-Agent — rather than a single spoofed User-Agent.",
                "Keep headers internally consistent; a Chrome User-Agent with no Sec-Fetch-* headers "
                "is a contradiction that is easy to spot.",
                "Re-check robots.txt and terms: a site that started filtering may have changed its "
                "stance on automated access, which is a decision to respect rather than route around.",
            ],
        }

    if blocked_plain:
        return {
            "class": "blocked",
            "summary": (f"Refused with HTTP {plain['status']}{vendor_note}, and browser headers did "
                        "not change the outcome. The decision is being made below the header layer — "
                        "TLS fingerprint, IP reputation or behavioural history."),
            "next_steps": [
                "Confirm this is new: try the same URL from a different network. If it succeeds there, "
                "the block is against your IP, not your code.",
                "If the response is a CAPTCHA on the content path, treat that as the site asking for a "
                "human and look for a sanctioned path — an API, feed, or licensing route.",
                "Only if the site permits automated access, a fingerprint-matching client such as "
                "curl_cffi addresses the TLS layer; header changes will not.",
            ],
        }

    if redirected:
        return {
            "class": "routing changed",
            "summary": f"The request was redirected to {plain['final_url']}. The URL pattern the "
                       "scraper was built against no longer serves this content.",
            "next_steps": [
                "Follow the redirect by hand and confirm what the destination actually contains — "
                "redirects to a generic landing or profile page silently produce empty results.",
                "Update the URL template, then re-run this diagnosis against the new URL.",
            ],
        }

    if selector is not None and selector_hits == 0:
        if expect_text and text_present:
            return {
                "class": "selectors stale",
                "summary": (f"The page returns HTTP {plain['status']} and still contains "
                            f"{expect_text!r}, but {selector!r} matches nothing. The markup was "
                            "restructured; the data is present and reachable."),
                "next_steps": [
                    "Locate the expected text in the HTML and read the surrounding structure.",
                    "Rebuild the selector against something durable — a data attribute, an id, or "
                    "structured data — rather than the nearest generated class name.",
                    "Check for embedded JSON first; it survives redesigns far better than markup.",
                ],
            }
        if embedded:
            return {
                "class": "content moved into embedded JSON",
                "summary": (f"{selector!r} matches nothing, but the page ships data in "
                            f"{', '.join(embedded)}. The content is in the response — it is no longer "
                            "in the markup you were parsing."),
                "next_steps": [
                    "Parse the JSON blob directly instead of the rendered markup. It is both more "
                    "stable and cheaper than any browser.",
                    "Do not add a headless browser for this: it would render JSON you already have.",
                ],
            }
        if text_len < 800:
            return {
                "class": "client-rendered",
                "summary": (f"HTTP {plain['status']} with only {text_len} characters of text and no "
                            "embedded data. The content is fetched by JavaScript after load."),
                "next_steps": [
                    "Open the page in devtools, watch the Network tab, and find the XHR that returns "
                    "the data. Calling that endpoint directly beats rendering the page.",
                    "Reach for Playwright only if no such endpoint is usable.",
                ],
            }
        return {
            "class": "selectors stale",
            "summary": (f"The page loads normally (HTTP {plain['status']}, {text_len} chars of text) "
                        f"but {selector!r} matches nothing. This is a markup change, not a block."),
            "next_steps": [
                "Diff the current HTML against a known-good copy if you have one.",
                "Rebuild the selector against stable anchors — ids, data attributes, structured data.",
            ],
        }

    if expect_text and not text_present:
        if embedded:
            return {
                "class": "content moved into embedded JSON",
                "summary": (f"{expect_text!r} is absent from the markup, but the page ships "
                            f"{', '.join(embedded)}. Check inside the JSON before assuming it is gone."),
                "next_steps": ["Parse the embedded JSON and look for the value there.",
                               "If present, switch extraction to the JSON blob permanently."],
            }
        if text_len < 800:
            return {
                "class": "client-rendered",
                "summary": f"Only {text_len} chars of text and {expect_text!r} absent — the content "
                           "arrives after load via JavaScript.",
                "next_steps": ["Find the XHR that supplies the data and call it directly.",
                               "Use a browser only if that endpoint is unusable."],
            }
        return {
            "class": "content changed or removed",
            "summary": f"The page loads normally but {expect_text!r} does not appear anywhere in it.",
            "next_steps": ["Confirm by eye that the content still exists at this URL.",
                           "If it moved, find the new location before changing parsing code."],
        }

    if selector and selector_hits:
        return {
            "class": "target intact",
            "summary": (f"HTTP {plain['status']}, and {selector!r} still matches {selector_hits} "
                        "element(s). The page is not the problem."),
            "next_steps": [
                "Suspect your own code or environment: a dependency upgrade, a changed parser, or a "
                "difference between local and production.",
                "Run the scraper against a saved copy of this HTML to isolate parsing from fetching.",
                "If it fails only at volume, the cause is pacing or session state, not extraction.",
            ],
        }

    return {
        "class": "no fault reproduced",
        "summary": (f"HTTP {plain['status']} with {text_len} chars of text and no extraction target "
                    "given, so nothing failed here."),
        "next_steps": [
            "Re-run with --selector or --expect-text so the extraction step is actually tested.",
            "Intermittent failures point at pacing, session state or a subset of URLs — collect the "
            "failing URLs and compare them against a working one.",
        ],
    }


def render_text(r):
    out = [f"Target:   {r['url']}"]
    if r.get("plain"):
        out.append(f"Response: HTTP {r['plain']['status']}  {r['plain']['bytes']} bytes  "
                   f"{r['plain']['elapsed']}s")
    if r.get("redirected_to"):
        out.append(f"Redirect: {r['redirected_to']}")
    out.append("")

    out.append("Checks")
    for c in r["checks"]:
        out.append(f"  [{'ok' if c['ok'] else '!!'}] {c['check']}: {c['detail']}")
    out.append("")

    if r.get("embedded_json"):
        out.append(f"Embedded data: {', '.join(r['embedded_json'])}")
        out.append("")

    v = r["verdict"]
    out.append(f"Diagnosis: {v['class'].upper()}")
    out.append(f"  {v['summary']}")
    out.append("")
    out.append("Next steps")
    for i, step in enumerate(v["next_steps"], 1):
        out.append(f"  {i}. {step}")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description="Diagnose why a scraper stopped working.")
    p.add_argument("url")
    p.add_argument("--selector", help="CSS selector the scraper uses (tag, .class, #id, descendants)")
    p.add_argument("--expect-text", help="text that should appear on the page")
    p.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default 1.0)")
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = p.parse_args()

    result = diagnose(args.url, selector=args.selector,
                      expect_text=args.expect_text, delay=args.delay)
    print(json.dumps(result, indent=2) if args.json else render_text(result))


if __name__ == "__main__":
    sys.exit(main())
