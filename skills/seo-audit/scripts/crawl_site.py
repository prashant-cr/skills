#!/usr/bin/env python3
"""Crawl a site and report the technical and on-page SEO facts, with evidence.

Every SEO audit that goes wrong goes wrong the same way: it recites a checklist
("add meta descriptions, improve page speed") that was never checked against the
site in question. This crawls the actual site so each finding carries a URL and
an observed value someone can go and look at.

    python3 crawl_site.py https://example.com
    python3 crawl_site.py https://example.com --max-pages 120 --delay 0.5
    python3 crawl_site.py https://example.com --json audit.json

It reports, per page: status and redirect chain, title, meta description, H1s,
word count, canonical, meta robots, images missing alt, structured data types,
internal links, and time-to-first-byte. Site-wide it resolves robots.txt,
sitemaps, HTTP-to-HTTPS and www canonicalisation, and whether unknown URLs
return a real 404. It then derives the issues that actually cost rankings --
duplicate titles, non-indexable pages, orphans, redirect chains, thin content,
pages buried too deep.

It obeys robots.txt for its own fetches and paces itself. Crawling is a cost you
impose on someone else's server; --delay exists to keep it small.

Standard library only.
"""

import argparse
import gzip
import hashlib
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import zlib
from collections import defaultdict, deque
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; SEOAuditBot/1.0; +https://skills.sh) Python-urllib"

# Thresholds. These are conventions, not laws Google published -- they exist so
# the report flags the same thing every time instead of drifting with the mood
# of whoever reads it. Google truncates titles by pixel width, not characters.
TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 70, 155
THIN_WORDS = 300
DEEP_CLICKS = 4
SLOW_TTFB_MS = 800
# A page whose rendered text is this short while carrying a lot of script is
# probably a JavaScript shell -- the HTML a crawler sees first has no content.
JS_SHELL_TEXT = 400

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
SKIP_EXT = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".css",
            ".js", ".pdf", ".zip", ".gz", ".mp4", ".mp3", ".woff", ".woff2",
            ".ttf", ".eot", ".xml", ".json", ".rss", ".avif", ".dmg", ".exe")


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------

TLS_WARNINGS = []


def _ssl_context():
    """Verify certificates, using certifi when the interpreter has no CA store.

    Python on macOS frequently ships without a usable trust store, which makes
    every HTTPS fetch fail in a way that looks like the site is broken. certifi
    fixes that when installed; when it is not, verification stays on and a real
    certificate problem still surfaces.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


VERIFIED_CTX = _ssl_context()
UNVERIFIED_CTX = ssl._create_unverified_context()


class _Recorder(urllib.request.HTTPRedirectHandler):
    """Records the redirect chain instead of silently collapsing it.

    Redirect chains matter: each hop leaks a little link equity and adds a
    round trip, and a chain that ends somewhere unexpected is how a site
    quietly deindexes a section.
    """

    def __init__(self):
        self.chain = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append({"from": req.full_url, "status": code, "to": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _decompress(body, encoding):
    try:
        if encoding == "gzip":
            return gzip.decompress(body)
        if encoding == "deflate":
            return zlib.decompress(body, -zlib.MAX_WBITS)
    except Exception:
        pass
    return body


def fetch(url, timeout=20, method="GET", _context=None):
    """Fetch a URL. Returns a dict -- never raises for HTTP errors."""
    context = _context or VERIFIED_CTX
    rec = _Recorder()
    opener = urllib.request.build_opener(
        rec, urllib.request.HTTPSHandler(context=context))
    req = urllib.request.Request(url, method=method, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
    })
    out = {"url": url, "final_url": url, "status": None, "redirect_chain": [],
           "headers": {}, "body": "", "bytes": 0, "ttfb_ms": None, "error": None}
    start = time.time()
    try:
        resp = opener.open(req, timeout=timeout)
        out["ttfb_ms"] = int((time.time() - start) * 1000)
        raw = resp.read()
        out["status"] = resp.status
        out["final_url"] = resp.geturl()
        out["headers"] = {k.lower(): v for k, v in resp.headers.items()}
        out["bytes"] = len(raw)
        body = _decompress(raw, out["headers"].get("content-encoding", "").lower())
        charset = resp.headers.get_content_charset() or "utf-8"
        out["body"] = body.decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        out["ttfb_ms"] = int((time.time() - start) * 1000)
        out["status"] = e.code
        out["final_url"] = e.url if hasattr(e, "url") else url
        out["headers"] = {k.lower(): v for k, v in (e.headers or {}).items()}
        try:
            raw = e.read()
            out["bytes"] = len(raw)
            out["body"] = _decompress(
                raw, out["headers"].get("content-encoding", "").lower()
            ).decode("utf-8", errors="replace")
        except Exception:
            pass
    except urllib.error.URLError as e:
        # A certificate that will not verify is a real SEO problem -- browsers
        # interstitial it and Google will not index it. But it is also what a
        # missing local CA store looks like, so retry unverified and report the
        # ambiguity rather than either ignoring it or calling the site broken.
        if isinstance(e.reason, ssl.SSLCertVerificationError) and _context is None:
            host = urllib.parse.urlsplit(url).hostname
            retry = fetch(url, timeout, method, _context=UNVERIFIED_CTX)
            if retry["status"]:
                # Which failure it is decides whether this is a finding about the
                # site or noise from this machine, and they need opposite
                # responses. A hostname mismatch or an expired certificate is
                # real and blocks indexing; "unable to get local issuer" usually
                # just means this interpreter has no CA bundle.
                reason = str(e.reason)
                if "Hostname mismatch" in reason or "doesn't match" in reason:
                    verdict = ("REAL: the certificate does not cover this hostname. "
                               "Browsers will interstitial it and Google will not "
                               "index it.")
                elif "expired" in reason.lower():
                    verdict = "REAL: the certificate has expired."
                elif "self signed" in reason.lower():
                    verdict = "REAL: the certificate is self-signed."
                elif "local issuer" in reason:
                    verdict = ("LIKELY LOCAL: this Python has no CA bundle "
                               "(pip install certifi). Confirm in a browser "
                               "before reporting it.")
                else:
                    verdict = "UNKNOWN: confirm in a browser."
                if not any(w["host"] == host for w in TLS_WARNINGS):
                    TLS_WARNINGS.append({"host": host, "verdict": verdict,
                                         "detail": reason.split(" (_ssl")[0]})
            retry["tls_unverified"] = True
            return retry
        out["error"] = f"{type(e).__name__}: {e}"
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    out["redirect_chain"] = rec.chain
    return out


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

class PageParser(HTMLParser):
    """Pull the on-page SEO signals out of one HTML document.

    HTMLParser switches to CDATA mode inside script/style by itself, so
    handle_data hands us raw script bodies -- tracked so they neither pollute
    the word count nor get missed when they hold JSON-LD.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_title = False
        self.meta = {}
        self.og = {}
        self.robots = None
        self.canonical = None
        self.hreflang = []
        self.viewport = None
        self.lang = None
        self.charset = None
        self.h = defaultdict(list)
        self._in_h = None
        self.links = []          # (href, rel, anchor_text, nofollow)
        self._link_stack = []
        self.images = []         # (src, alt_present, alt_text)
        self.jsonld = []
        self._in_script = False
        self._script_type = ""
        self._script_buf = []
        self.script_count = 0
        self.script_bytes = 0
        self.stylesheet_count = 0
        self.inline_style_bytes = 0
        self._in_style = False
        self._in_skip = 0        # nav/footer/header depth, for main-text heuristics
        self.text_parts = []
        self.microdata_types = []
        self.amp = False
        self.has_form = False
        self.iframes = 0

    # -- helpers
    @staticmethod
    def _attrs(attrs):
        return {k.lower(): (v or "") for k, v in attrs}

    def handle_starttag(self, tag, attrs):
        a = self._attrs(attrs)
        tag = tag.lower()
        if tag == "html":
            self.lang = a.get("lang") or None
            if "amp" in a or "⚡" in a:
                self.amp = True
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or a.get("http-equiv") or "").lower()
            content = a.get("content", "")
            if "charset" in a:
                self.charset = a["charset"]
            if name:
                if name.startswith("og:") or name.startswith("twitter:"):
                    self.og[name] = content
                else:
                    self.meta[name] = content
                if name == "robots":
                    self.robots = content.lower()
                elif name == "viewport":
                    self.viewport = content
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            href = a.get("href", "")
            if "canonical" in rel:
                self.canonical = href
            elif "alternate" in rel and a.get("hreflang"):
                self.hreflang.append({"hreflang": a["hreflang"], "href": href})
            elif "stylesheet" in rel:
                self.stylesheet_count += 1
            elif "amphtml" in rel:
                self.amp = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_h = tag
            self.h[tag].append("")
        elif tag == "a":
            href = a.get("href")
            rel = (a.get("rel") or "").lower()
            self._link_stack.append([href, rel, []])
        elif tag == "img":
            self.images.append({
                "src": a.get("src") or a.get("data-src") or "",
                "alt_present": "alt" in a,
                "alt": a.get("alt", ""),
                "loading": a.get("loading", ""),
                "has_dims": bool(a.get("width") and a.get("height")),
            })
        elif tag == "script":
            self._in_script = True
            self._script_type = (a.get("type") or "").lower()
            self._script_buf = []
            if a.get("src"):
                self.script_count += 1
        elif tag == "style":
            self._in_style = True
        elif tag in ("nav", "footer", "header", "aside"):
            self._in_skip += 1
        elif tag == "form":
            self.has_form = True
        elif tag == "iframe":
            self.iframes += 1
        if a.get("itemtype"):
            self.microdata_types.append(a["itemtype"])

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_h = None
        elif tag == "a" and self._link_stack:
            href, rel, text = self._link_stack.pop()
            if href:
                self.links.append({
                    "href": href,
                    "anchor": " ".join("".join(text).split())[:120],
                    "nofollow": "nofollow" in rel or "sponsored" in rel or "ugc" in rel,
                    "in_chrome": self._in_skip > 0,
                })
        elif tag == "script":
            raw = "".join(self._script_buf)
            self.script_bytes += len(raw)
            if "ld+json" in self._script_type:
                self.jsonld.append(raw)
            self._in_script = False
            self._script_buf = []
        elif tag == "style":
            self._in_style = False
        elif tag in ("nav", "footer", "header", "aside") and self._in_skip:
            self._in_skip -= 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self._in_script:
            self._script_buf.append(data)
            return
        if self._in_style:
            self.inline_style_bytes += len(data)
            return
        if self._in_title:
            self.title = (self.title or "") + data
        if self._in_h:
            self.h[self._in_h][-1] += data
        if self._link_stack:
            self._link_stack[-1][2].append(data)
        if data.strip():
            self.text_parts.append((data, self._in_skip > 0))


def analyse_html(html):
    """Turn HTML into the signal dict the audit reasons over."""
    p = PageParser()
    try:
        p.feed(html)
        p.close()
    except Exception:
        pass  # malformed markup is itself a finding; keep whatever parsed

    body_words = 0
    main_words = 0
    for text, in_chrome in p.text_parts:
        n = len(text.split())
        body_words += n
        if not in_chrome:
            main_words += n

    schema_types = []
    for blob in p.jsonld:
        try:
            data = json.loads(blob)
        except Exception:
            schema_types.append("INVALID_JSON")
            continue
        for node in (data if isinstance(data, list) else [data]):
            if isinstance(node, dict):
                t = node.get("@type")
                if isinstance(t, list):
                    schema_types.extend(str(x) for x in t)
                elif t:
                    schema_types.append(str(t))
                for g in node.get("@graph", []) or []:
                    if isinstance(g, dict) and g.get("@type"):
                        gt = g["@type"]
                        schema_types.extend(gt if isinstance(gt, list) else [str(gt)])
    for it in p.microdata_types:
        schema_types.append(it.rstrip("/").rsplit("/", 1)[-1] + " (microdata)")

    title = " ".join((p.title or "").split()) or None
    desc = " ".join(p.meta.get("description", "").split()) or None
    text_len = sum(len(t) for t, _ in p.text_parts)

    return {
        "title": title,
        "title_len": len(title) if title else 0,
        "meta_description": desc,
        "desc_len": len(desc) if desc else 0,
        "h1": [" ".join(x.split()) for x in p.h.get("h1", []) if x.strip()],
        "h2_count": len([x for x in p.h.get("h2", []) if x.strip()]),
        "h3_count": len([x for x in p.h.get("h3", []) if x.strip()]),
        "canonical": p.canonical,
        "meta_robots": p.robots,
        "viewport": p.viewport,
        "lang": p.lang,
        "hreflang": p.hreflang,
        "og_title": p.og.get("og:title"),
        "og_image": p.og.get("og:image"),
        "schema_types": sorted(set(schema_types)),
        # word_count excludes nav/header/footer/aside so boilerplate does not
        # disguise a thin page; body_word_count keeps everything, because a big
        # gap between the two is itself a signal that the template outweighs
        # the content.
        "word_count": main_words or body_words,
        "body_word_count": body_words,
        "text_chars": text_len,
        "images": len(p.images),
        "images_missing_alt": sum(1 for i in p.images if not i["alt_present"]
                                  or not i["alt"].strip()),
        "images_no_dims": sum(1 for i in p.images if not i["has_dims"]),
        "images_lazy": sum(1 for i in p.images if i["loading"] == "lazy"),
        "script_refs": p.script_count,
        "inline_script_bytes": p.script_bytes,
        "stylesheets": p.stylesheet_count,
        "iframes": p.iframes,
        "amp": p.amp,
        "links": p.links,
        "content_hash": hashlib.sha1(
            " ".join(t.strip() for t, c in p.text_parts if not c).encode()
        ).hexdigest()[:16],
    }


# --------------------------------------------------------------------------
# url handling
# --------------------------------------------------------------------------

def normalise(url, drop_query=False):
    """Canonicalise a URL for identity comparison.

    Fragments never identify a distinct page. Trailing slashes and default
    ports usually do not either, and treating them as distinct is how a crawler
    reports imaginary duplicate content.
    """
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return url
    scheme, host = u.scheme.lower(), u.hostname or ""
    if u.port and not ((scheme == "http" and u.port == 80) or
                       (scheme == "https" and u.port == 443)):
        host = f"{host}:{u.port}"
    path = urllib.parse.quote(urllib.parse.unquote(u.path), safe="/%:@!$&'()*+,;=~-._")
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]
    query = "" if drop_query else u.query
    return urllib.parse.urlunsplit((scheme, host, path or "/", query, ""))


def same_site(url, root_host):
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return host == root_host or host == "www." + root_host or root_host == "www." + host


def crawlable(url):
    path = urllib.parse.urlsplit(url).path.lower()
    return not path.endswith(SKIP_EXT)


# --------------------------------------------------------------------------
# site-level probes
# --------------------------------------------------------------------------

def read_robots(root):
    out = {"url": urllib.parse.urljoin(root, "/robots.txt"), "found": False,
           "sitemaps": [], "crawl_delay": None, "disallow_all": False,
           "lines": 0, "blocks_googlebot": [], "raw": ""}
    r = fetch(out["url"])
    if r["status"] != 200 or not r["body"].strip():
        return out, None
    out["found"] = True
    out["raw"] = r["body"][:4000]
    out["lines"] = len(r["body"].splitlines())
    agent = None
    for line in r["body"].splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            agent = val.lower()
        elif key == "sitemap":
            out["sitemaps"].append(val)
        elif key == "crawl-delay" and agent in ("*", None):
            try:
                out["crawl_delay"] = float(val)
            except ValueError:
                pass
        elif key == "disallow" and agent in ("*", "googlebot"):
            if val == "/":
                out["disallow_all"] = True
            if agent == "googlebot" and val:
                out["blocks_googlebot"].append(val)

    rp = urllib.robotparser.RobotFileParser()
    rp.parse(r["body"].splitlines())
    return out, rp


def read_sitemaps(urls, limit=5, seen=None):
    """Parse sitemap XML (and sitemap indexes) with regex -- they are simple
    enough, and this avoids failing on the malformed ones that are common."""
    seen = seen if seen is not None else set()
    found, errors = [], []
    for su in urls[:limit]:
        if su in seen:
            continue
        seen.add(su)
        r = fetch(su)
        if r["status"] != 200:
            errors.append(f"{su} -> HTTP {r['status'] or r['error']}")
            continue
        body = r["body"]
        if su.endswith(".gz") and not body.lstrip().startswith("<"):
            errors.append(f"{su} -> gzipped sitemap not decoded")
            continue
        locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", body, re.I | re.S)
        if "<sitemapindex" in body.lower():
            sub, suberr = read_sitemaps(locs, limit=limit, seen=seen)
            found.extend(sub)
            errors.extend(suberr)
        else:
            found.extend(u.strip() for u in locs)
    return found, errors


def check_canonicalisation(root):
    """Do the four host/scheme variants converge on one URL?

    If http:// and https://, or www and non-www, both serve 200, the site is
    publishing up to four copies of every page and splitting its own signals.
    """
    u = urllib.parse.urlsplit(root)
    host = u.hostname or ""
    bare = host[4:] if host.startswith("www.") else host
    variants = [f"http://{bare}/", f"https://{bare}/",
                f"http://www.{bare}/", f"https://www.{bare}/"]
    results, finals = [], set()
    for v in variants:
        r = fetch(v)
        entry = {"variant": v, "status": r["status"],
                 "final_url": normalise(r["final_url"]) if r["status"] else None,
                 "hops": len(r["redirect_chain"]), "error": r["error"]}
        results.append(entry)
        if r["status"] == 200:
            finals.add(entry["final_url"])
    return {"variants": results, "distinct_endpoints": sorted(finals),
            "converges": len(finals) <= 1}


def check_404(root):
    """A 'page not found' that answers 200 is a soft 404. Google then indexes
    an unbounded number of empty pages, which is one of the few technical
    problems that gets actively worse over time."""
    probe = urllib.parse.urljoin(root, "/zz-seo-audit-probe-404-nonexistent-path")
    r = fetch(probe)
    return {"probe_url": probe, "status": r["status"],
            "is_soft_404": r["status"] == 200,
            "words": analyse_html(r["body"])["word_count"] if r["body"] else 0}


# --------------------------------------------------------------------------
# crawl
# --------------------------------------------------------------------------

def crawl(start, max_pages, delay, respect_robots=True, include_query=False):
    start_fetch = fetch(start)
    if start_fetch["error"]:
        return {"fatal": f"could not reach {start}: {start_fetch['error']}"}
    root = start_fetch["final_url"]
    root_host = (urllib.parse.urlsplit(root).hostname or "").lower()

    robots, rp = read_robots(root)
    if robots["crawl_delay"] and robots["crawl_delay"] > delay:
        delay = min(robots["crawl_delay"], 5.0)

    sitemap_urls, sitemap_errors = read_sitemaps(
        robots["sitemaps"] or [urllib.parse.urljoin(root, "/sitemap.xml")])

    pages, queue, seen = {}, deque([(normalise(root, not include_query), 0)]), set()
    seen.add(normalise(root, not include_query))
    blocked_by_robots = []

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if respect_robots and rp and not rp.can_fetch(UA, url):
            blocked_by_robots.append(url)
            continue
        if pages:
            time.sleep(delay)
        r = fetch(url)
        sig = analyse_html(r["body"]) if r["body"] else {}
        ctype = r["headers"].get("content-type", "")
        page = {
            "url": url,
            "final_url": normalise(r["final_url"], not include_query),
            "status": r["status"],
            "error": r["error"],
            "depth": depth,
            "ttfb_ms": r["ttfb_ms"],
            "bytes": r["bytes"],
            "compressed": bool(r["headers"].get("content-encoding")),
            "cache_control": r["headers"].get("cache-control"),
            "content_type": ctype,
            "x_robots_tag": r["headers"].get("x-robots-tag"),
            "redirect_chain": r["redirect_chain"],
            "hops": len(r["redirect_chain"]),
        }
        if "html" in ctype or (not ctype and r["body"]):
            page.update({k: v for k, v in sig.items() if k != "links"})
            page["outlinks"] = []
            page["external_links"] = 0
            for link in sig.get("links", []):
                href = link["href"].strip()
                if not href or href.startswith(("#", "mailto:", "tel:", "javascript:",
                                                "data:", "sms:", "whatsapp:")):
                    continue
                absolute = urllib.parse.urljoin(r["final_url"], href)
                if not same_site(absolute, root_host):
                    page["external_links"] += 1
                    continue
                n = normalise(absolute, not include_query)
                page["outlinks"].append(
                    {"url": n, "anchor": link["anchor"], "nofollow": link["nofollow"],
                     "in_chrome": link["in_chrome"]})
                if n not in seen and crawlable(n) and len(seen) < max_pages * 4:
                    seen.add(n)
                    queue.append((n, depth + 1))
        pages[url] = page

    return {
        "start_url": start,
        "root": root,
        "root_host": root_host,
        "https": root.startswith("https://"),
        "pages": pages,
        "robots": robots,
        "sitemap_urls": sitemap_urls,
        "sitemap_errors": sitemap_errors,
        "blocked_by_robots": blocked_by_robots,
        "queued_not_crawled": max(0, len(seen) - len(pages)),
        "canonicalisation": check_canonicalisation(root),
        "not_found": check_404(root),
        "crawl_delay_used": delay,
    }


# --------------------------------------------------------------------------
# issue derivation
# --------------------------------------------------------------------------

def indexable(p):
    """Can this page rank at all? Everything else is downstream of this.

    A noindex or a canonical pointing elsewhere means the page is excluded from
    search by the site's own instruction -- which is fine when deliberate and
    catastrophic when it lands on a page someone is paying to promote.
    """
    if p.get("status") != 200:
        return False, f"HTTP {p.get('status')}"
    robots = (p.get("meta_robots") or "") + " " + (p.get("x_robots_tag") or "")
    if "noindex" in robots.lower():
        return False, "noindex"
    canon = p.get("canonical")
    if canon:
        try:
            if normalise(urllib.parse.urljoin(p["url"], canon)) != normalise(p["final_url"]):
                return False, "canonical points elsewhere"
        except Exception:
            pass
    return True, ""


def derive(site):
    """Group findings by severity. Ordering is the whole point: an indexation
    blocker outranks a hundred missing alt attributes, and a report that lists
    them at the same weight is the reason SEO audits get ignored."""
    pages = site["pages"]
    html_pages = {u: p for u, p in pages.items() if "title" in p}
    ok = {u: p for u, p in html_pages.items() if p["status"] == 200}

    issues = {"critical": [], "high": [], "medium": [], "low": []}

    def add(sev, code, detail, evidence):
        issues[sev].append({"code": code, "detail": detail, "evidence": evidence[:15],
                            "count": len(evidence)})

    # --- site-wide, indexation first
    if not site["https"]:
        add("critical", "no-https", "Site is served over HTTP.", [site["root"]])
    if site["robots"]["disallow_all"]:
        add("critical", "robots-disallow-all",
            "robots.txt contains 'Disallow: /' -- crawling of the whole site is "
            "blocked.", [site["robots"]["url"]])
    if site["robots"]["blocks_googlebot"]:
        add("high", "robots-blocks-googlebot",
            "robots.txt has Googlebot-specific Disallow rules.",
            site["robots"]["blocks_googlebot"])
    if not site["robots"]["found"]:
        add("low", "no-robots-txt", "No robots.txt (harmless, but sitemaps cannot "
            "be declared there).", [site["robots"]["url"]])
    if not site["robots"]["sitemaps"] and site["sitemap_urls"]:
        add("low", "sitemap-not-declared",
            "A sitemap exists but is not referenced in robots.txt.",
            [site["robots"]["url"]])
    if not site["sitemap_urls"]:
        add("high", "no-sitemap", "No XML sitemap found at /sitemap.xml or in "
            "robots.txt -- discovery relies entirely on internal links.",
            [urllib.parse.urljoin(site["root"], "/sitemap.xml")])
    if not site["canonicalisation"]["converges"]:
        add("critical", "host-not-canonical",
            "More than one host/scheme variant serves 200 without redirecting. "
            "The same page exists at several addresses and its signals are split.",
            site["canonicalisation"]["distinct_endpoints"])
    if site["not_found"]["is_soft_404"]:
        add("high", "soft-404", "A non-existent URL returns HTTP 200 instead of "
            "404. Search engines can index unlimited empty pages.",
            [site["not_found"]["probe_url"]])

    # --- per page
    missing_title, long_title, short_title = [], [], []
    missing_desc, long_desc = [], []
    no_h1, many_h1, thin, deep, slow, noindexed = [], [], [], [], [], []
    no_canonical, no_viewport, no_lang, missing_alt, no_schema = [], [], [], [], []
    js_shell, uncompressed, broken, chains = [], [], [], []
    titles, descs, hashes = defaultdict(list), defaultdict(list), defaultdict(list)

    for u, p in html_pages.items():
        if p["status"] and p["status"] >= 400:
            broken.append(f"{u} -> HTTP {p['status']}")
            continue
        if p["hops"] > 1:
            chains.append(f"{u} -> {p['hops']} hops -> {p['final_url']}")
        if p["status"] != 200:
            continue

        idx, why = indexable(p)
        if not idx and why == "noindex":
            noindexed.append(u)
        if not p.get("title"):
            missing_title.append(u)
        else:
            titles[p["title"].strip().lower()].append(u)
            if p["title_len"] > TITLE_MAX:
                long_title.append(f"{u} ({p['title_len']} chars)")
            elif p["title_len"] < TITLE_MIN:
                short_title.append(f"{u} ({p['title_len']} chars)")
        if not p.get("meta_description"):
            missing_desc.append(u)
        else:
            descs[p["meta_description"].strip().lower()].append(u)
            if p["desc_len"] > DESC_MAX:
                long_desc.append(f"{u} ({p['desc_len']} chars)")
        if not p.get("h1"):
            no_h1.append(u)
        elif len(p["h1"]) > 1:
            many_h1.append(f"{u} ({len(p['h1'])} H1s)")
        # Homepages are exempt: they rank on brand, links and navigation rather
        # than body copy, so flagging one as thin produces a finding nobody
        # should act on.
        if p.get("word_count", 0) < THIN_WORDS and p["depth"] > 0:
            thin.append(f"{u} ({p.get('word_count', 0)} words)")
        if p["depth"] >= DEEP_CLICKS:
            deep.append(f"{u} ({p['depth']} clicks from home)")
        if p["ttfb_ms"] and p["ttfb_ms"] > SLOW_TTFB_MS:
            slow.append(f"{u} ({p['ttfb_ms']} ms)")
        if not p.get("canonical"):
            no_canonical.append(u)
        if not p.get("viewport"):
            no_viewport.append(u)
        if not p.get("lang"):
            no_lang.append(u)
        if p.get("images_missing_alt"):
            missing_alt.append(f"{u} ({p['images_missing_alt']}/{p['images']} images)")
        if not p.get("schema_types"):
            no_schema.append(u)
        if (p.get("text_chars", 0) < JS_SHELL_TEXT
                and p.get("inline_script_bytes", 0) > 2000):
            js_shell.append(f"{u} ({p.get('text_chars', 0)} chars of text)")
        if not p["compressed"] and p["bytes"] > 30000:
            uncompressed.append(f"{u} ({p['bytes'] // 1024} KB uncompressed)")
        if p.get("content_hash"):
            hashes[p["content_hash"]].append(u)

    dup_titles = {t: us for t, us in titles.items() if len(us) > 1}
    dup_descs = {d: us for d, us in descs.items() if len(us) > 1}
    dup_content = {h: us for h, us in hashes.items() if len(us) > 1}

    if broken:
        add("critical", "broken-internal-links",
            "Internal links point at pages returning 4xx/5xx.", broken)
    if noindexed:
        add("critical", "noindex-pages",
            "Pages carry a noindex directive and cannot rank. Verify each is "
            "meant to be excluded.", noindexed)
    if dup_content:
        add("critical", "duplicate-content",
            "Pages share identical main body text.",
            [f"{us[0]} == {', '.join(us[1:4])}" for us in dup_content.values()])
    if js_shell:
        add("high", "js-rendered-content",
            "Little text in the initial HTML alongside heavy script -- content is "
            "probably injected by JavaScript. Google renders it, but later and "
            "less reliably than server-rendered HTML.", js_shell)
    if missing_title:
        add("high", "missing-title", "Pages have no title tag.", missing_title)
    if dup_titles:
        add("high", "duplicate-titles",
            "Several pages share one title, so they compete for the same query.",
            [f"'{t[:60]}' on {len(us)} pages: {', '.join(us[:3])}"
             for t, us in dup_titles.items()])
    if chains:
        add("high", "redirect-chains", "Internal URLs redirect more than once.", chains)
    if no_h1:
        add("high", "missing-h1", "Pages have no H1.", no_h1)
    if thin:
        add("high", "thin-content",
            f"Pages under {THIN_WORDS} words of main content.", thin)
    if missing_desc:
        add("medium", "missing-meta-description",
            "No meta description -- Google writes its own snippet, usually a worse "
            "one for click-through.", missing_desc)
    if dup_descs:
        add("medium", "duplicate-meta-description",
            "Several pages share one meta description.",
            [f"{len(us)} pages: {', '.join(us[:3])}" for us in dup_descs.values()])
    if long_title:
        add("medium", "title-too-long",
            f"Titles over ~{TITLE_MAX} chars get truncated in results.", long_title)
    if short_title:
        add("low", "title-too-short",
            f"Titles under ~{TITLE_MIN} chars leave room unused.", short_title)
    if long_desc:
        add("low", "description-too-long",
            f"Descriptions over ~{DESC_MAX} chars get truncated.", long_desc)
    if many_h1:
        add("low", "multiple-h1", "More than one H1 on a page.", many_h1)
    if deep:
        add("medium", "deep-pages",
            f"Pages {DEEP_CLICKS}+ clicks from the homepage get crawled less often.", deep)
    if slow:
        add("medium", "slow-ttfb",
            f"Server responded slower than {SLOW_TTFB_MS} ms.", slow)
    if no_canonical:
        add("medium", "missing-canonical",
            "No canonical tag -- any URL parameter creates a duplicate.", no_canonical)
    if no_viewport:
        add("high", "missing-viewport",
            "No mobile viewport meta tag. Google indexes the mobile page.", no_viewport)
    if missing_alt:
        add("low", "images-missing-alt",
            "Images without alt text -- accessibility, and image search traffic.",
            missing_alt)
    if no_schema:
        add("medium", "no-structured-data",
            "No JSON-LD or microdata, so no rich-result eligibility.", no_schema)
    if no_lang:
        add("low", "missing-lang", "No lang attribute on the html element.", no_lang)
    if uncompressed:
        add("medium", "uncompressed-html",
            "HTML served without gzip/brotli.", uncompressed)

    # sitemap vs crawl reconciliation -- orphans are the classic silent loss
    crawled = {normalise(u) for u in html_pages}
    sm = {normalise(u) for u in site["sitemap_urls"]}
    linked_to = set()
    for p in html_pages.values():
        for link in p.get("outlinks", []):
            linked_to.add(normalise(link["url"]))
    orphans = sorted(sm - linked_to - {normalise(site["root"])})
    if orphans and len(crawled) >= len(sm) * 0.5:
        add("high", "orphan-pages",
            "In the sitemap but not linked from any crawled page. Nothing passes "
            "them authority and users cannot reach them.", orphans)
    missing_from_sitemap = sorted(crawled - sm)
    if sm and missing_from_sitemap:
        add("low", "not-in-sitemap",
            "Crawlable pages absent from the sitemap.", missing_from_sitemap)

    # internal link distribution -- pages nobody links to cannot rank
    inbound = defaultdict(int)
    for p in html_pages.values():
        for link in p.get("outlinks", []):
            if not link["in_chrome"]:
                inbound[normalise(link["url"])] += 1
    weak = sorted(u for u in crawled
                  if inbound.get(u, 0) == 0 and u != normalise(site["root"]))
    if weak:
        add("medium", "no-contextual-inbound-links",
            "Reached only through navigation, header or footer -- no in-content "
            "link from another page.", weak)

    return issues, {
        "pages_crawled": len(pages),
        "html_pages": len(html_pages),
        "status_200": len(ok),
        "indexable": sum(1 for p in ok.values() if indexable(p)[0]),
        "sitemap_count": len(site["sitemap_urls"]),
        "avg_words": round(sum(p.get("word_count", 0) for p in ok.values())
                           / max(1, len(ok))),
        "avg_ttfb_ms": round(sum(p["ttfb_ms"] or 0 for p in ok.values())
                             / max(1, len(ok))),
        "with_schema": sum(1 for p in ok.values() if p.get("schema_types")),
        "duplicate_title_groups": len(dup_titles),
        "orphans": len(orphans),
    }


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def report(site, issues, stats):
    L = []
    w = L.append
    w(f"SEO CRAWL: {site['root']}")
    w("=" * 72)
    w(f"Pages crawled       {stats['pages_crawled']}   "
      f"(HTML {stats['html_pages']}, 200 OK {stats['status_200']}, "
      f"indexable {stats['indexable']})")
    if site["queued_not_crawled"]:
        w(f"Not reached         {site['queued_not_crawled']} URLs discovered beyond "
          f"--max-pages; findings describe the crawled subset only")
    w(f"Sitemap URLs        {stats['sitemap_count']}"
      + ("" if site["sitemap_urls"] else "   (none found)"))
    w(f"robots.txt          {'found' if site['robots']['found'] else 'MISSING'}"
      f"   crawl-delay used {site['crawl_delay_used']}s")
    w(f"HTTPS               {'yes' if site['https'] else 'NO'}")
    w(f"Host canonical      {'yes' if site['canonicalisation']['converges'] else 'NO -- ' + ', '.join(site['canonicalisation']['distinct_endpoints'])}")
    w(f"404 handling        {'SOFT 404 (returns 200)' if site['not_found']['is_soft_404'] else 'correct (' + str(site['not_found']['status']) + ')'}")
    w(f"Avg main-body words {stats['avg_words']}      Avg TTFB {stats['avg_ttfb_ms']} ms")
    w(f"Pages with schema   {stats['with_schema']}/{stats['status_200']}")
    if site["blocked_by_robots"]:
        w(f"Skipped by robots   {len(site['blocked_by_robots'])} URLs")
    for tw in TLS_WARNINGS:
        w(f"TLS                 {tw['host']}: certificate did not verify "
          f"({tw['detail']})")
        w(f"                    {tw['verdict']}")
    if site["sitemap_errors"]:
        w(f"Sitemap errors      {'; '.join(site['sitemap_errors'][:3])}")
    w("")

    order = [("critical", "CRITICAL -- blocks ranking outright"),
             ("high", "HIGH -- costs traffic now"),
             ("medium", "MEDIUM -- worth fixing this quarter"),
             ("low", "LOW -- polish")]
    total = sum(len(v) for v in issues.values())
    if not total:
        w("No issues detected in the crawled subset.")
    for sev, label in order:
        if not issues[sev]:
            continue
        w(label)
        w("-" * 72)
        for i in issues[sev]:
            w(f"  [{i['code']}] {i['detail']}")
            w(f"      affected: {i['count']}")
            for ev in i["evidence"][:6]:
                w(f"        - {ev}")
            if i["count"] > 6:
                w(f"        ... and {i['count'] - 6} more")
        w("")
    w("Counts describe the pages actually crawled, not necessarily the whole site.")
    w("Core Web Vitals, actual index coverage and ranking positions are not "
      "measurable from a crawl -- get them from PageSpeed Insights and Search Console.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("url")
    ap.add_argument("--max-pages", type=int, default=60)
    ap.add_argument("--delay", type=float, default=1.0,
                    help="seconds between requests (default 1.0)")
    ap.add_argument("--json", metavar="PATH", help="write full findings as JSON")
    ap.add_argument("--include-query", action="store_true",
                    help="treat ?query strings as distinct pages")
    ap.add_argument("--ignore-robots", action="store_true",
                    help="crawl paths robots.txt disallows (you own the site)")
    args = ap.parse_args()

    url = args.url if "://" in args.url else "https://" + args.url
    site = crawl(url, args.max_pages, args.delay,
                 respect_robots=not args.ignore_robots,
                 include_query=args.include_query)
    if site.get("fatal"):
        print(site["fatal"], file=sys.stderr)
        return 2

    issues, stats = derive(site)
    print(report(site, issues, stats))

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"site": {k: v for k, v in site.items() if k != "pages"},
                       "stats": stats, "issues": issues, "pages": site["pages"]},
                      f, indent=2, default=str)
        print(f"\nFull findings written to {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
