#!/usr/bin/env python3
"""Harvest every machine-readable structure a page already publishes.

Most scrapers are written against markup that was never meant to be an
interface. Meanwhile the same page usually ships JSON-LD for search engines,
Open Graph for social cards, and its own state as JSON for the frontend — all
of it typed, all of it stable across redesigns, because breaking it costs the
site something. Selectors break on restyling; these do not.

So before writing a selector, look at what is already there. This finds it, and
--find locates a value by name so you get a JSON path instead of guessing at
DOM structure.

Standard library only, so it runs anywhere Python 3.8+ does.

Usage:
    python3 extract.py https://site.com/product          # what's available
    python3 extract.py https://site.com/product --find price
    python3 extract.py https://site.com/product --dump jsonld
    python3 extract.py --file saved.html --dump tables
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

UA = "structured-data-extraction/1.0 (+reads published structured data)"
TIMEOUT = 20
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


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


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=make_ssl_context()) as r:
            raw = r.read(3_000_000)
            enc = r.headers.get("Content-Encoding", "").lower()
            charset = r.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"error: {url} returned HTTP {exc.code}. If the page is defended or "
                         "client-rendered, save the HTML you do have and pass --file instead.")
    except Exception as exc:
        raise SystemExit(f"error: could not fetch {url}: {exc}")

    if enc == "gzip":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
    elif enc == "deflate":
        for wbits in (15, -15):
            try:
                raw = zlib.decompress(raw, wbits)
                break
            except zlib.error:
                continue
    return raw.decode(charset, errors="replace")


# --------------------------------------------------------------------------
# Harvesters
# --------------------------------------------------------------------------

class ScriptCollector(HTMLParser):
    """Collect <script> payloads by type, plus <link rel=alternate> feeds."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.jsonld_raw, self.json_raw, self.feeds = [], [], []
        self._capture = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            t = a.get("type", "").lower().strip()
            if t == "application/ld+json":
                self._capture = ["jsonld", []]
            elif t in ("application/json", "application/x-json"):
                # id first, buffer last — handle_data appends to the final slot.
                self._capture = ["json", a.get("id") or a.get("data-target") or "", []]
        elif tag == "link":
            rel = a.get("rel", "").lower()
            typ = a.get("type", "").lower()
            if "alternate" in rel and ("rss" in typ or "atom" in typ):
                self.feeds.append({"type": typ, "href": a.get("href"), "title": a.get("title")})

    def handle_data(self, data):
        if self._capture:
            self._capture[-1].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._capture:
            if self._capture[0] == "jsonld":
                self.jsonld_raw.append("".join(self._capture[1]))
            else:
                self.json_raw.append((self._capture[1], "".join(self._capture[2])))
            self._capture = None


class MetaCollector(HTMLParser):
    """Open Graph, Twitter card, and plain name/content meta tags."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.opengraph, self.twitter, self.meta = {}, {}, {}
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            content = a.get("content", "")
            key = (a.get("property") or a.get("name") or "").lower()
            if not key:
                return
            if key.startswith("og:"):
                self.opengraph[key[3:]] = content
            elif key.startswith("twitter:"):
                self.twitter[key[8:]] = content
            else:
                self.meta[key] = content

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


class MicrodataCollector(HTMLParser):
    """Schema.org microdata: itemscope/itemtype/itemprop into nested dicts."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self._scopes = []      # open itemscope dicts
        self._stack = []       # (tag, is_scope, prop_name, buffer)

    @staticmethod
    def _value_from(tag, a):
        if tag in ("meta",):
            return a.get("content")
        if tag in ("a", "link", "area"):
            return a.get("href")
        if tag in ("img", "audio", "video", "source", "iframe", "embed", "track"):
            return a.get("src")
        if tag == "time":
            return a.get("datetime")
        if tag in ("data", "meter"):
            return a.get("value")
        return None

    def _assign(self, prop, value):
        if not self._scopes or prop is None:
            return
        target = self._scopes[-1]
        if prop in target:
            if not isinstance(target[prop], list):
                target[prop] = [target[prop]]
            target[prop].append(value)
        else:
            target[prop] = value

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        is_scope = "itemscope" in a
        prop = a.get("itemprop")
        if is_scope:
            obj = {}
            if a.get("itemtype"):
                obj["@type"] = a["itemtype"].rsplit("/", 1)[-1]
            if prop and self._scopes:
                self._assign(prop, obj)
            self._scopes.append(obj)
        elif prop:
            direct = self._value_from(tag, a)
            if direct is not None:
                self._assign(prop, direct)
                prop = None  # value already captured; no text needed
        if tag not in VOID:
            self._stack.append([tag, is_scope, prop, []])
        elif is_scope:
            closed = self._scopes.pop()
            if not self._scopes:
                self.items.append(closed)

    def handle_data(self, data):
        if self._stack and self._stack[-1][2]:
            self._stack[-1][3].append(data)

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                for frame in reversed(self._stack[i:]):
                    _, is_scope, prop, buf = frame
                    if prop:
                        text = re.sub(r"\s+", " ", "".join(buf)).strip()
                        if text:
                            self._assign(prop, text)
                    if is_scope:
                        closed = self._scopes.pop()
                        if not self._scopes:
                            self.items.append(closed)
                del self._stack[i:]
                break


class TableCollector(HTMLParser):
    """HTML tables as {headers, rows} — the format people most often hand-parse."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._t = None
        self._row = None
        self._cell = None
        self._is_header = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            # Collect rows with their header-ness and decide the shape at </table>.
            # Deciding per-row cannot distinguish a header row from a key-value
            # table, where every row opens with a <th> that is a label, not a column.
            self._t = {"collected": []}
        elif tag == "tr" and self._t is not None:
            self._row, self._is_header = [], False
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            self._is_header = self._is_header or tag == "th"

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self._t["collected"].append((self._is_header, self._row))
            self._row, self._is_header = None, False
        elif tag == "table" and self._t is not None:
            self.tables.append(self._shape(self._t["collected"]))
            self._t = None

    @staticmethod
    def _shape(collected):
        """Decide whether row 1 is a header or every row is a key-value pair."""
        if not collected:
            return {"headers": [], "rows": [], "orientation": "empty"}
        header_rows = sum(1 for is_h, _ in collected if is_h)

        # Every row carrying a <th> means the <th> labels the row, not a column.
        if header_rows == len(collected) and len(collected) > 1:
            return {"headers": [], "rows": [cells for _, cells in collected],
                    "orientation": "key-value"}

        if collected[0][0] and header_rows == 1:
            return {"headers": collected[0][1],
                    "rows": [cells for _, cells in collected[1:]],
                    "orientation": "column"}

        return {"headers": [], "rows": [cells for _, cells in collected],
                "orientation": "column"}


def js_state_blobs(html):
    """window.__NEXT_DATA__ / __NUXT__ / __INITIAL_STATE__ style assignments.

    Brace-matched rather than regex-captured, because a JSON object containing
    braces in strings defeats any non-counting approach.
    """
    out = {}
    for m in re.finditer(r"(?:window\.)?(__[A-Z0-9_]+__)\s*=\s*", html):
        name = m.group(1)
        start = html.find("{", m.end())
        if start == -1 or start - m.end() > 8:
            continue
        depth, in_str, quote, esc = 0, False, "", False
        for i in range(start, min(len(html), start + 2_000_000)):
            ch = html[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == quote:
                    in_str = False
            elif ch in "\"'":
                in_str, quote = True, ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        out[name] = json.loads(html[start:i + 1])
                    except json.JSONDecodeError:
                        pass
                    break
    return out


def harvest(html, base_url=None):
    scripts = ScriptCollector()
    scripts.feed(html)

    # Feed hrefs are usually relative; an unresolved "rss" is not actionable.
    if base_url:
        for feed in scripts.feeds:
            if feed.get("href"):
                feed["href"] = urllib.parse.urljoin(base_url, feed["href"])

    jsonld = []
    for raw in scripts.jsonld_raw:
        try:
            parsed = json.loads(raw.strip())
        except json.JSONDecodeError:
            # Trailing commas and stray comments are common in hand-written blocks.
            try:
                parsed = json.loads(re.sub(r",\s*([}\]])", r"\1", raw.strip()))
            except json.JSONDecodeError:
                continue
        for obj in (parsed if isinstance(parsed, list) else [parsed]):
            # An @graph wrapper is a container, not an entity — emit its children
            # instead so the count reflects real objects and types line up.
            if isinstance(obj, dict) and isinstance(obj.get("@graph"), list):
                jsonld.extend(obj["@graph"])
            else:
                jsonld.append(obj)

    json_blocks = []
    for name, raw in scripts.json_raw:
        try:
            json_blocks.append({"id": name, "data": json.loads(raw.strip())})
        except json.JSONDecodeError:
            continue

    meta = MetaCollector(); meta.feed(html)
    micro = MicrodataCollector(); micro.feed(html)
    tables = TableCollector(); tables.feed(html)

    return {
        "jsonld": jsonld,
        "json_blocks": json_blocks,
        "js_state": js_state_blobs(html),
        "opengraph": meta.opengraph,
        "twitter": meta.twitter,
        "meta": meta.meta,
        "title": (meta.title or "").strip() or None,
        "microdata": micro.items,
        "tables": tables.tables,
        "feeds": scripts.feeds,
    }


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def find(sources, term):
    """Locate a term in keys or values across every harvested source."""
    low = term.lower()
    key_hits, value_hits = [], []
    for source, data in sources.items():
        if not data:
            continue
        for path, value in walk(data, source):
            leaf = path.rsplit(".", 1)[-1].split("[")[0]
            if low in leaf.lower():
                key_hits.append({"path": path, "value": value})
            elif isinstance(value, str) and low in value.lower() and len(value) < 300:
                value_hits.append({"path": path, "value": value})
    return {"matched_keys": key_hits, "matched_values": value_hits}


def summarise(s):
    types = []
    for item in s["jsonld"]:
        if isinstance(item, dict):
            t = item.get("@type")
            types.extend(t if isinstance(t, list) else [t] if t else [])
    return {
        "jsonld": {"count": len(s["jsonld"]), "types": sorted({str(t) for t in types})},
        "json_blocks": [{"id": b["id"] or "(unnamed)",
                         "top_level_keys": sorted(b["data"].keys())[:12]
                         if isinstance(b["data"], dict) else "(not an object)"}
                        for b in s["json_blocks"]],
        "js_state": sorted(s["js_state"].keys()),
        "opengraph": sorted(s["opengraph"].keys()),
        "microdata": {"count": len(s["microdata"]),
                      "types": sorted({str(i.get("@type")) for i in s["microdata"] if i.get("@type")})},
        "tables": [{"headers": t["headers"][:8], "rows": len(t["rows"])} for t in s["tables"]],
        "feeds": s["feeds"],
    }


def render(s, summary):
    out = []
    if s.get("title"):
        out.append(f"Title: {s['title'][:110]}")
        out.append("")

    found_any = False
    j = summary["jsonld"]
    if j["count"]:
        found_any = True
        out.append(f"JSON-LD          {j['count']} object(s)"
                   + (f"  types: {', '.join(j['types'])}" if j["types"] else ""))
        out.append("                 most durable source here — sites maintain it for search engines")

    if summary["microdata"]["count"]:
        found_any = True
        out.append(f"Microdata        {summary['microdata']['count']} item(s)"
                   + (f"  types: {', '.join(summary['microdata']['types'])}"
                      if summary["microdata"]["types"] else ""))

    for b in summary["json_blocks"]:
        found_any = True
        keys = b["top_level_keys"]
        out.append(f"JSON block       id={b['id']}"
                   + (f"  keys: {', '.join(keys)}" if isinstance(keys, list) else f"  {keys}"))

    if summary["js_state"]:
        found_any = True
        out.append(f"JS state         {', '.join(summary['js_state'])}")

    if summary["opengraph"]:
        found_any = True
        out.append(f"Open Graph       {', '.join(summary['opengraph'][:10])}")

    for i, t in enumerate(summary["tables"]):
        found_any = True
        head = ", ".join(t["headers"]) if t["headers"] else "(no header row)"
        out.append(f"Table [{i}]        {t['rows']} row(s)  headers: {head}")

    if summary["feeds"]:
        found_any = True
        for f in summary["feeds"]:
            out.append(f"Feed             {f['href']}  ({f['type']})")

    if not found_any:
        out.append("No structured data found.")
        out.append("")
        out.append("That is itself informative: this page publishes nothing machine-readable,")
        out.append("so selectors may genuinely be the only route. Before accepting that, check")
        out.append("whether a different page type carries it — product and article pages very")
        out.append("often do while listing pages do not — and look for an underlying API.")
        return "\n".join(out)

    out.append("")
    out.append("Next: --find <term> to locate a value, or --dump <source> for the raw JSON.")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description="Extract structured data a page already publishes.")
    p.add_argument("url", nargs="?", help="page URL (omit when using --file)")
    p.add_argument("--file", help="read saved HTML instead of fetching")
    p.add_argument("--find", metavar="TERM", help="locate a term in keys or values")
    p.add_argument("--dump", metavar="SOURCE",
                   help="jsonld | json_blocks | js_state | opengraph | twitter | meta | "
                        "microdata | tables | feeds | all")
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = p.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as fh:
            html = fh.read()
    elif args.url:
        html = fetch(args.url)
    else:
        p.error("provide a URL or --file")

    sources = harvest(html, base_url=args.url)

    if args.dump:
        key = args.dump.lower()
        if key == "all":
            print(json.dumps(sources, indent=2, default=str))
        elif key in sources:
            print(json.dumps(sources[key], indent=2, default=str))
        else:
            raise SystemExit(f"error: unknown source {args.dump!r}. "
                             f"Choose from: {', '.join(sorted(sources))}, all")
        return

    if args.find:
        hits = find(sources, args.find)
        if args.json:
            print(json.dumps(hits, indent=2, default=str))
            return
        if not hits["matched_keys"] and not hits["matched_values"]:
            print(f"No key or value matching {args.find!r} in any structured source.")
            print("Try a synonym (cost/amount for price, headline for title), or --dump all "
                  "to read what is actually there.")
            return
        if hits["matched_keys"]:
            print(f"Keys matching {args.find!r}:")
            for h in hits["matched_keys"][:25]:
                print(f"  {h['path']} = {json.dumps(h['value'], default=str)[:120]}")
        if hits["matched_values"]:
            print(f"\nValues containing {args.find!r}:")
            for h in hits["matched_values"][:15]:
                print(f"  {h['path']} = {json.dumps(h['value'], default=str)[:120]}")
        return

    summary = summarise(sources)
    print(json.dumps(summary, indent=2, default=str) if args.json else render(sources, summary))


if __name__ == "__main__":
    sys.exit(main())
