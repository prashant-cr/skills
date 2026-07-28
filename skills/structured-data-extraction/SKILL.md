---
name: structured-data-extraction
license: MIT
description: Extracts data from web pages without writing CSS selectors or XPath, by reading the machine-readable structures a page already publishes — JSON-LD, schema.org microdata, Open Graph tags, embedded __NEXT_DATA__ and application/json state blobs, HTML tables and RSS feeds — and locating a value by name so you get a JSON path instead of guessing at DOM structure. Use this whenever someone is writing selectors to scrape a page, asks how to get product prices, article metadata, listings, ratings or tables off a site, wants extraction that survives redesigns, is tired of selectors breaking, or is about to reach for BeautifulSoup, parsel or a headless browser to pull fields out of HTML.
---

# Structured data extraction

Most scrapers parse markup that was never intended to be an interface, which is why they break on
every restyling. The same pages usually publish typed, documented data alongside that markup —
JSON-LD for search engines, Open Graph for social previews, and their own application state as
JSON for the frontend. Those exist because breaking them costs the site traffic or functionality,
which is exactly the property you want to depend on.

So look before you select. It is frequently faster, usually more accurate, and it survives the
redesign that would have broken a selector.

## Why this beats selectors

**Stability.** A generated class name like `.css-1x2y3z` changes when anyone edits the styles.
A JSON-LD `Product.offers.price` changes when the site changes its data model, which is rare and
deliberate.

**Accuracy.** Markup holds what was formatted for a human; structured data holds what the site
stores. GitHub's DOM renders a star count as `141k` while the JSON on the same page carries
`141146`. Scraping the text loses three digits and looks perfectly fine doing it. The same gap
produces truncated descriptions, relative timestamps where an ISO datetime exists, and
locale-formatted prices.

**Typing.** `"price": 29.99` with `"priceCurrency": "USD"` needs no parsing. `"$29.99"` scraped
from a span needs currency stripping, locale handling, and a decision about what `"Free"` means.

**Completeness.** Embedded state routinely carries fields the page never displays — stock levels,
internal ids, pagination totals, canonical URLs — which are the fields that make a dataset useful.

## Workflow

### 1. Survey what the page publishes

```bash
python3 scripts/extract.py https://site.com/product
```

Reports every structured source found: JSON-LD objects and their schema.org types, microdata,
`application/json` script blocks with their top-level keys, `window.__STATE__` blobs, Open Graph,
tables, and feeds.

Run this on a **content** page — a product, article or profile — not a listing or homepage.
Listing pages often publish nothing while the detail pages behind them are richly annotated.

### 2. Locate the field by name

```bash
python3 scripts/extract.py https://site.com/product --find price
python3 scripts/extract.py https://site.com/product --find rating
```

This is the step that replaces selector-hunting. It searches keys *and* values across every source
and returns JSON paths:

```
Keys matching 'price':
  jsonld[0].offers.price = "29.99"
  jsonld[0].offers.priceCurrency = "USD"
  opengraph.price:amount = "29.99"
```

Nothing found doesn't mean the field is absent — it means that name isn't used. Try synonyms
(`cost`, `amount`, `value` for price; `headline`, `name` for title; `stars`, `count` for ratings),
or read what's actually there with `--dump all`.

### 3. Read the source you'll bind to

```bash
python3 scripts/extract.py https://site.com/product --dump jsonld
python3 scripts/extract.py https://site.com/product --dump json_blocks
```

Confirm the path holds across two or three pages before writing code against it. A path that only
exists on the page you tested is a bug waiting for the second URL.

### 4. Choose the source deliberately

When several carry the same field, prefer in this order, and say why in the code:

| Source | Use when | Watch for |
| --- | --- | --- |
| JSON-LD | It carries the `@type` you need | Optional fields vary between pages |
| Microdata / RDFa | No JSON-LD *of that type* | Verbose; values split across attributes |
| Embedded state JSON | Richest data, or JSON-LD is thin | Undocumented; the site may rename keys |
| Open Graph | Title, image, description, canonical URL | Deliberately summarised, often truncated |
| HTML tables | Genuinely tabular content | Column order changes silently |
| RSS/Atom feed | Article or post listings | Usually only recent items |

JSON-LD is the default because sites are motivated to keep it correct for search engines.
Embedded state is often *richer* but is an internal shape with no compatibility promise — use it
when it carries fields you need, and pin the key path explicitly so a rename fails loudly.

**"Has JSON-LD" and "has the entity you want in JSON-LD" are different questions**, and conflating
them is the most likely way to misread the survey. Plenty of pages emit JSON-LD describing the
*site* — `Organization`, `WebSite`, `BreadcrumbList` — while the `Product` or `Article` itself is
expressed as microdata, or not at all. Open Food Facts and Open Library both do exactly this: two
JSON-LD objects that never mention the product, and a full `Product`/`Book` in microdata alongside.

This is why step 1 prints the types for every source. Read the types before choosing, rather than
seeing a JSON-LD line and stopping there.

### 5. Write extraction that fails loudly

Read the path directly rather than defensively walking it. A `KeyError` naming
`offers.price` on the night a site changes its schema is worth far more than a silent `None` that
propagates into your dataset for a month.

Check `@type` before trusting an object — pages carry several JSON-LD blocks, and the first is
often `BreadcrumbList` or `Organization` rather than the `Product` you want.

## When there is nothing to find

Some pages genuinely publish nothing machine-readable, and the script says so. Before falling back
to selectors:

- **Check a detail page.** Listing pages are commonly bare while item pages are annotated.
- **Look for the underlying API.** A client-rendered page fetches its data from somewhere; that
  endpoint returns clean JSON and beats both selectors and structured data.
- **Check for a feed.** RSS/Atom is a stable, documented interface for anything post-shaped.
- **Then use selectors** — anchored on ids, `data-` attributes and semantic elements rather than
  generated class names, and with an assertion on how many records you expect.

## Report structure

```markdown
# Extraction plan: <target>

**Source chosen:** <JSON-LD / embedded state / table / feed> — <why this one>

## Field map
| Field | Path | Type | Notes |
| --- | --- | --- | --- |

## Code
<working extraction, reading the paths directly>

## Verification
<records checked against the live page, count assertion, second URL tested>

## Fragility
<what would break this, and what fails loudly when it does>
```

## Judgement calls

**Verify against the rendered page once.** Structured data is occasionally stale or wrong —
a cached JSON-LD block advertising an old price is a real failure mode. Check a couple of records
by eye before trusting it at volume.

**Don't mix sources per field without saying so.** Taking the title from Open Graph and the price
from JSON-LD is fine, but record the decision; a future reader will otherwise assume one source.

**Prefer fewer requests, not more.** All of this comes from the page you already fetched. If you
find yourself fetching a second time to get structured data, harvest both in one pass.

**Respect the same limits as any scraping.** Structured data being easy to read is not permission
to collect at any rate, and personal data carries the same obligations however convenient the
format.
