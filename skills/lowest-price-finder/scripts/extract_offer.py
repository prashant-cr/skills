#!/usr/bin/env python3
"""Read price, availability and product identity off a live product page.

Most e-commerce pages publish exactly what a price comparison needs, in machine
form: schema.org Product/Offer as JSON-LD, microdata, or Open Graph product
tags. Reading that beats scraping the rendered markup, because the markup is
where the formatting lives -- a page showing "1,299" might carry 1299.00 in the
JSON-LD, and a page showing "from $99" often carries the real variant price.

    python3 extract_offer.py https://store.example/product/abc
    python3 extract_offer.py URL --json          # machine-readable
    python3 extract_offer.py URL1 URL2 URL3      # several at once

The single most valuable field it recovers is the **GTIN/EAN/UPC or MPN**. Two
listings that share one are the same physical product; two that do not may
differ in generation, region, colour or bundle, and comparing their prices is
the most common way a price comparison quietly becomes meaningless.

Big marketplaces block plain HTTP clients. When that happens this says so
rather than returning an empty price that looks like a finding -- read the page
in a browser and enter the numbers by hand instead.

Standard library only.
"""

import argparse
import gzip
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import zlib
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# Phrases that mean "we served you a wall, not a product page". Reporting a
# price of None from one of these as though the product were unavailable would
# be worse than saying nothing.
BLOCK_MARKERS = [
    "captcha", "are you a human", "robot check", "access denied",
    "unusual traffic", "verify you are", "cf-browser-verification",
    "just a moment", "enable javascript and cookies", "request blocked",
    "to discuss automated access",
]

AVAIL = {
    "instock": "in stock", "in_stock": "in stock", "onlineonly": "in stock",
    "outofstock": "OUT OF STOCK", "soldout": "OUT OF STOCK",
    "preorder": "pre-order", "backorder": "backorder",
    "limitedavailability": "limited", "discontinued": "DISCONTINUED",
}

CONDITION = {
    "newcondition": "new", "usedcondition": "used",
    "refurbishedcondition": "refurbished", "damagedcondition": "damaged",
}


def _ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    try:
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=_ctx()))
        resp = opener.open(req, timeout=timeout)
        raw = resp.read()
        enc = (resp.headers.get("content-encoding") or "").lower()
        if enc == "gzip":
            raw = gzip.decompress(raw)
        elif enc == "deflate":
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), resp.status, None
    except urllib.error.HTTPError as e:
        return "", e.code, f"HTTP {e.code}"
    except Exception as e:
        return "", None, f"{type(e).__name__}: {e}"


class Collector(HTMLParser):
    """Pull JSON-LD blocks, microdata itemprops and product meta tags."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.jsonld = []
        self.meta = {}
        self.micro = {}
        self._in_ld = False
        self._buf = []
        self.title = None
        self._in_title = False
        self.text_len = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script" and "ld+json" in (a.get("type") or "").lower():
            self._in_ld = True
            self._buf = []
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"])
        elif a.get("itemprop"):
            prop = a["itemprop"].lower()
            val = a.get("content") or a.get("href") or a.get("src") or ""
            if val:
                self.micro.setdefault(prop, val)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self.jsonld.append("".join(self._buf))
            self._in_ld = False
            self._buf = []
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_ld:
            self._buf.append(data)
            return
        if self._in_title:
            self.title = ((self.title or "") + data).strip()
        self.text_len += len(data.strip())


def _walk(node):
    """Yield every dict in a nested JSON-LD structure."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _types(node):
    t = node.get("@type") or ""
    return {str(x).lower() for x in (t if isinstance(t, list) else [t])}


def _money(v):
    """'₹1,29,900.00' / '1299.00' / 1299 -> float. Indian grouping included."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.,]", "", str(v))
    if not s:
        return None
    # Last separator with 1-2 trailing digits is the decimal point.
    m = re.search(r"[.,](\d{1,2})$", s)
    if m:
        s = s[:m.start()].replace(",", "").replace(".", "") + "." + m.group(1)
    else:
        s = s.replace(",", "").replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _enum(v, table):
    if not v:
        return None
    key = str(v).rstrip("/").rsplit("/", 1)[-1].lower().replace(" ", "")
    return table.get(key, str(v).rstrip("/").rsplit("/", 1)[-1])


def parse(html):
    c = Collector()
    try:
        c.feed(html)
        c.close()
    except Exception:
        pass

    out = {"name": None, "brand": None, "gtin": None, "mpn": None, "sku": None,
           "price": None, "currency": None, "list_price": None,
           "availability": None, "condition": None, "seller": None,
           "rating": None, "review_count": None, "shipping": None,
           "source": []}

    def take(field, value, where):
        if value not in (None, "", []) and out.get(field) in (None, "", []):
            out[field] = value
            if where not in out["source"]:
                out["source"].append(where)

    # --- JSON-LD, the richest source when present
    for blob in c.jsonld:
        try:
            data = json.loads(blob)
        except Exception:
            try:  # trailing commas and stray control chars are common
                data = json.loads(re.sub(r",\s*([}\]])", r"\1", blob))
            except Exception:
                continue
        for node in _walk(data):
            if not isinstance(node, dict):
                continue
            t = _types(node)
            if "product" in t or "productmodel" in t:
                take("name", node.get("name"), "json-ld")
                b = node.get("brand")
                take("brand", b.get("name") if isinstance(b, dict) else b, "json-ld")
                for k in ("gtin13", "gtin12", "gtin8", "gtin14", "gtin", "ean", "upc"):
                    if node.get(k):
                        take("gtin", str(node[k]).strip(), "json-ld")
                        break
                take("mpn", node.get("mpn"), "json-ld")
                take("sku", node.get("sku"), "json-ld")
                agg = node.get("aggregateRating")
                if isinstance(agg, dict):
                    take("rating", _money(agg.get("ratingValue")), "json-ld")
                    rc = agg.get("reviewCount") or agg.get("ratingCount")
                    take("review_count", int(_money(rc)) if _money(rc) else None,
                         "json-ld")
            if "offer" in t or "aggregateoffer" in t:
                p = node.get("price") or node.get("lowPrice")
                take("price", _money(p), "json-ld")
                take("currency", node.get("priceCurrency"), "json-ld")
                take("list_price", _money(node.get("highPrice")), "json-ld")
                take("availability", _enum(node.get("availability"), AVAIL), "json-ld")
                take("condition", _enum(node.get("itemCondition"), CONDITION), "json-ld")
                s = node.get("seller")
                take("seller", s.get("name") if isinstance(s, dict) else s, "json-ld")
                spec = node.get("priceSpecification")
                if isinstance(spec, dict) and not out["price"]:
                    take("price", _money(spec.get("price")), "json-ld")
                    take("currency", spec.get("priceCurrency"), "json-ld")
                sd = node.get("shippingDetails")
                if isinstance(sd, dict):
                    rate = sd.get("shippingRate")
                    if isinstance(rate, dict):
                        take("shipping", _money(rate.get("value")), "json-ld")

    # --- microdata
    take("name", c.micro.get("name"), "microdata")
    take("price", _money(c.micro.get("price")), "microdata")
    take("currency", c.micro.get("pricecurrency"), "microdata")
    take("availability", _enum(c.micro.get("availability"), AVAIL), "microdata")
    take("gtin", c.micro.get("gtin13") or c.micro.get("gtin12"), "microdata")
    take("sku", c.micro.get("sku"), "microdata")

    # --- Open Graph / product meta, the last resort
    m = c.meta
    take("price", _money(m.get("product:price:amount") or m.get("og:price:amount")
                         or m.get("twitter:data1")), "og-meta")
    take("currency", m.get("product:price:currency") or m.get("og:price:currency"),
         "og-meta")
    take("name", m.get("og:title") or c.title, "og-meta")
    take("brand", m.get("product:brand"), "og-meta")
    take("gtin", m.get("product:ean") or m.get("product:upc"), "og-meta")
    take("availability", _enum(m.get("product:availability")
                               or m.get("og:availability"), AVAIL), "og-meta")

    return out, c.text_len


def looks_blocked(html, status):
    low = html[:6000].lower()
    hits = [w for w in BLOCK_MARKERS if w in low]
    if status in (403, 429, 503):
        hits.append(f"HTTP {status}")
    return hits


def run(url):
    html, status, err = fetch(url)
    rec = {"url": url, "status": status, "error": err, "blocked": False,
           "block_signals": [], "offer": None}
    if err and not html:
        return rec
    signals = looks_blocked(html, status)
    offer, text_len = parse(html)
    # A block page can still carry stray metadata; treat a blocked page with no
    # price as blocked, and one with a price as usable but flagged.
    if signals and offer.get("price") is None:
        rec["blocked"] = True
        rec["block_signals"] = signals
        return rec
    rec["block_signals"] = signals
    rec["offer"] = offer
    rec["page_text_chars"] = text_len
    return rec


def render(rec):
    L = []
    w = L.append
    w(f"URL      {rec['url']}")
    w(f"Status   {rec['status']}{'  ' + rec['error'] if rec['error'] else ''}")
    if rec["blocked"]:
        w(f"BLOCKED  {', '.join(rec['block_signals'])}")
        w("         This is a bot wall, not the product page. Open it in a "
          "browser and enter the price by hand -- do not record a missing "
          "price here as 'unavailable'.")
        return "\n".join(L)
    if rec["offer"] is None:
        # A fetch that never returned HTML says nothing about the page. Printing
        # "no price found" here would invite recording an unreachable store as
        # one with no stock.
        w("FETCH FAILED — the page was never retrieved, so nothing is known "
          "about its price or stock. Retry, or open it in a browser.")
        return "\n".join(L)
    o = rec["offer"]
    if not o.get("price"):
        w("NO PRICE FOUND in structured data. The page may set the price with "
          "JavaScript, or split it per variant. Check it in a browser.")
    if rec["block_signals"]:
        w(f"WARNING  block markers present ({', '.join(rec['block_signals'])}) "
          f"but a price was still readable -- verify it")
    w("")
    for label, key in [("Product", "name"), ("Brand", "brand"),
                       ("Price", "price"), ("Currency", "currency"),
                       ("Was/list", "list_price"), ("Shipping", "shipping"),
                       ("Availability", "availability"), ("Condition", "condition"),
                       ("Seller", "seller"), ("Rating", "rating"),
                       ("Reviews", "review_count")]:
        if o.get(key) not in (None, ""):
            w(f"  {label:<13}{o[key]}")
    w("")
    ident = [f"{k.upper()}={o[k]}" for k in ("gtin", "mpn", "sku") if o.get(k)]
    if ident:
        w(f"  Identity     {'  '.join(ident)}")
        if o.get("gtin"):
            w("               GTIN present -- two listings sharing it are the "
              "same product. Use it to confirm you are comparing like for like.")
    else:
        w("  Identity     none published. You cannot confirm from the page alone "
          "that this")
        w("               is the same variant as another listing -- check model "
          "number, capacity,")
        w("               colour and generation by hand before comparing prices.")
    if o.get("source"):
        w(f"  Read from    {', '.join(o['source'])}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    recs = [run(u) for u in args.urls]
    if args.json:
        print(json.dumps(recs, indent=2))
    else:
        for i, r in enumerate(recs):
            if i:
                print("\n" + "-" * 70 + "\n")
            print(render(r))
    return 0 if any(r.get("offer") for r in recs) else 1


if __name__ == "__main__":
    sys.exit(main())
