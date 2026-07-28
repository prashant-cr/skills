# Extraction recipes

Working patterns for the common shapes. All standard library — swap in your own HTTP client.

## Contents

- [Reading JSON-LD by type](#reading-json-ld-by-type)
- [Products](#products)
- [Articles](#articles)
- [Listings and pagination](#listings-and-pagination)
- [Tables](#tables)
- [Normalising what you get](#normalising-what-you-get)

---

## Reading JSON-LD by type

The one helper worth having, because "take the first block" is the mistake everyone makes once.

```python
import json, re

def jsonld_objects(html):
    """Every JSON-LD entity on the page, with @graph containers flattened."""
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I,
    ):
        raw = m.group(1).strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            try:                       # trailing commas are common in hand-written blocks
                parsed = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))
            except json.JSONDecodeError:
                continue
        for obj in (parsed if isinstance(parsed, list) else [parsed]):
            if isinstance(obj, dict) and isinstance(obj.get("@graph"), list):
                yield from obj["@graph"]
            else:
                yield obj


def of_type(html, wanted):
    """JSON-LD entities of a given @type. @type may itself be a list."""
    for obj in jsonld_objects(html):
        t = obj.get("@type")
        types = t if isinstance(t, list) else [t]
        if wanted in types:
            yield obj
```

---

## Products

```python
def extract_product(html):
    product = next(of_type(html, "Product"), None)
    if product is None:
        raise LookupError("no Product JSON-LD on this page")

    offers = product.get("offers") or {}
    if isinstance(offers, list):          # multi-variant pages ship a list
        offers = offers[0] if offers else {}
    rating = product.get("aggregateRating") or {}

    return {
        "name": product["name"],                       # raise if the schema moved
        "sku": product.get("sku"),
        "brand": as_name(product.get("brand")),
        "price": offers.get("price"),
        "currency": offers.get("priceCurrency"),
        "in_stock": str(offers.get("availability", "")).rsplit("/", 1)[-1] == "InStock",
        "rating": rating.get("ratingValue"),
        "reviews": rating.get("reviewCount"),
    }


def as_name(value):
    """brand may be a string, an object, or a list of either."""
    if isinstance(value, dict):
        return value.get("name")
    if isinstance(value, list):
        return as_name(value[0]) if value else None
    return value
```

Note `product["name"]` versus `.get()` elsewhere. Required fields should raise; genuinely optional
ones shouldn't. That single distinction is what makes a schema change visible on night one instead
of surfacing as a column of nulls a month later.

---

## Articles

```python
def extract_article(html):
    art = next(of_type(html, "NewsArticle"), None) or next(of_type(html, "Article"), None)
    if art is None:
        raise LookupError("no Article JSON-LD")
    return {
        "headline": art["headline"],
        "published": art.get("datePublished"),      # ISO 8601, not "3 days ago"
        "modified": art.get("dateModified"),
        "author": as_name(art.get("author")),
        "section": art.get("articleSection"),
        "body": art.get("articleBody"),             # often absent; fall back to the page
    }
```

`articleBody` is inconsistently populated. When it's missing, Open Graph `og:description` gives a
summary, and full text needs the page itself.

---

## Listings and pagination

Listing pages are where embedded state earns its keep: the markup shows a page of items while the
JSON often carries totals and page counts that make pagination deterministic instead of
"keep going until a page looks empty".

```python
def json_blocks(html):
    for m in re.finditer(
        r'<script[^>]+type=["\']application/json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I,
    ):
        try:
            yield json.loads(m.group(1))
        except json.JSONDecodeError:
            continue


def dig(obj, *path, default=None):
    """Read a pinned key path. Explicit beats a recursive search you can't audit."""
    for key in path:
        if isinstance(obj, dict):
            obj = obj.get(key, default) if key == path[-1] else obj[key]
        elif isinstance(obj, list) and isinstance(key, int):
            obj = obj[key]
        else:
            raise KeyError(f"path broke at {key!r}")
    return obj
```

Use `extract.py --find` once to discover the path, then pin it with `dig(...)`. Re-searching at
runtime hides schema changes; a pinned path fails loudly and tells you where.

Also check `ItemList` JSON-LD — some listing pages publish every item on the page that way, which
removes the need to touch markup at all.

---

## Tables

```python
import csv, io

def table_to_dicts(table):
    """{'headers': [...], 'rows': [[...]]} from extract.py --dump tables."""
    headers = table["headers"] or [f"col{i}" for i in range(len(table["rows"][0]))]
    return [dict(zip(headers, row)) for row in table["rows"] if len(row) == len(headers)]
```

Rows whose length differs from the header row usually contain a `colspan` section divider. Dropping
them is normally right, but count what you drop — a silent filter that removes half the table is
the same class of bug as a silent selector failure.

---

## Proving resilience instead of asserting it

"This survives redesigns" is a claim you can test rather than promise. Strip the attributes
selectors bind to, re-extract, and compare — if the output is identical, the extraction genuinely
does not depend on presentation.

```python
import re

def strip_styling_hooks(html):
    """Remove exactly what a restyling would change: class, id, style."""
    for attr in ("class", "id", "style"):
        html = re.sub(rf'\s{attr}="[^"]*"', "", html)
        html = re.sub(rf"\s{attr}='[^']*'", "", html)
    return html


def assert_resilient(html, extract):
    before, after = extract(html), extract(strip_styling_hooks(html))
    assert before == after, "extraction depends on styling hooks — it is selector-coupled"
    return before
```

Run against a real page this removes hundreds of hooks — 1,351 on an Open Food Facts product —
and a structured-data extractor returns byte-identical output while every CSS selector on the page
would have broken.

**Do not extend this by renaming tags**, which is the tempting next step and is unsound. Renaming
`<h1>` to `<div>` on a page with unbalanced `</div>` makes a renamed element match a stray close
tag, collapsing the parser's element stack and dropping data — a failure caused by the test, not
the extractor. Verified: that mutation cut three extracted images to one, while attribute
stripping alone changed nothing. Keep the mutation to attributes, since those are what actually
change in a restyling.

## Normalising what you get

Structured data is typed but not clean.

**Numbers arrive as strings.** `"price": "29.99"` is a string in most JSON-LD. Convert once, at
the boundary, and fail on unparseable values rather than defaulting to zero.

**Enums are URLs.** `availability` is `https://schema.org/InStock`. Compare the final segment.

**Dates are usually ISO 8601 but not always complete.** Some publishers emit date-only values,
some include timezone offsets and some don't. Parse defensively and store the original string
alongside the parsed value.

**Fields may be scalar, object, or list.** `author`, `brand`, `image` and `offers` all vary. Write
one normaliser per shape (`as_name`, `as_list`) and route everything through it.

**HTML entities survive into JSON strings.** `&amp;` appears in JSON-LD text more often than you
would like; unescape before storing.

**Currency is not implied by price.** Always carry `priceCurrency`. A dataset of bare numbers
mixing USD and EUR is silently wrong in a way no assertion will catch later.
