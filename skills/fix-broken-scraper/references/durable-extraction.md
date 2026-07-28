# Durable extraction

How to repair a scraper so the same class of break doesn't recur. Read this after the fix is
verified — the ten minutes spent here is what separates a scraper that breaks monthly from one
that runs for years.

## Contents

- [Anchor priority](#anchor-priority)
- [Writing selectors that survive redesigns](#writing-selectors-that-survive-redesigns)
- [Parsing embedded JSON](#parsing-embedded-json)
- [Failing loudly](#failing-loudly)
- [Pacing that doesn't earn blocks](#pacing-that-doesnt-earn-blocks)

---

## Anchor priority

Bind extraction to whatever the site has the least incentive to change. In descending order of
durability:

1. **An official API.** Versioned, documented, typed. Nothing else comes close.
2. **Structured data** — JSON-LD (`application/ld+json`), microdata, Open Graph tags. Sites publish
   these for search engines and are actively motivated to keep them stable and correct.
3. **Embedded state JSON** — `__NEXT_DATA__`, `__NUXT__`, `application/json` script blocks. Tied to
   the site's own data model, which changes far more slowly than its presentation.
4. **Semantic HTML and stable attributes** — `id`, `data-testid`, `data-product-id`, `itemprop`.
   Test hooks in particular are stable because breaking them breaks the site's own test suite.
5. **Structural CSS selectors** — `article > h2`, `main .content p`. Survive restyling but not
   restructuring.
6. **Generated class names** — `.css-1x2y3z`, `.jsx-284719`, Tailwind utility stacks. These change
   whenever anyone touches the styles. Treat a selector built on them as temporary by construction.

Most breakages are someone having anchored at level 6 when level 2 or 3 was available on the same
page. Before writing a selector, search the HTML for `ld+json` and `application/json`.

---

## Writing selectors that survive redesigns

**Prefer attributes that carry meaning.** `[data-product-id]` describes what the element *is*;
`.card-inner-wrap` describes how it currently looks.

**Anchor on text you can verify, then navigate.** Finding the element containing "Price" and taking
its sibling is often more durable than a positional path, because the label is user-visible and
changing it has a cost.

**Avoid deep positional chains.** `div > div > div:nth-child(3) > span` breaks when anyone adds a
wrapper. Prefer the shortest path from a stable ancestor.

**Scope to a container, then extract within it.** Select the product card by a stable attribute,
then pull fields relative to it. Field-level selectors that reach across the whole document pick up
unrelated matches when the layout shifts — the mechanism behind silent wrong values.

**Assert cardinality.** If a listing page should yield 20–50 items, check that. Getting 1 or 500 is
a signal the selector is matching the wrong thing, and it is the difference between noticing today
and noticing next quarter.

---

## Parsing embedded JSON

Extracting a blob is a few lines and repays itself immediately:

```python
import json, re

def embedded_json_blocks(html):
    """Yield parsed objects from <script type="application/json"> blocks."""
    for m in re.finditer(
        r'<script[^>]+type=["\']application/json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I,
    ):
        try:
            yield json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
```

For JSON-LD, match `type="application/ld+json"` instead; a page often carries several blocks, so
filter by `@type` (`Product`, `Article`, `BreadcrumbList`) rather than taking the first.

Explore the structure once interactively, note the key path, and pin extraction to that path with a
clear error when it disappears. A `KeyError` naming the missing path is far more useful at 3am than
an empty list.

---

## Failing loudly

Silent failure is why breakages persist for weeks. A scraper returning zero rows should be as
visible as one that crashes.

- **Raise on empty.** If a page should always yield items, zero items is an error, not a result.
- **Never wrap extraction in a bare `except: pass`.** It converts every fault into an empty result
  and destroys the diagnosis you would otherwise have had.
- **Validate shape, not just presence.** A price that parses as `0.0`, a date in 1970, or a name of
  `""` should fail the record.
- **Track the rate.** A per-run count of successful extractions makes a partial break — 40% of
  pages silently failing — visible, which per-record logging does not.
- **Keep one canonical URL as a smoke test.** A page you know well, checked before each run, tells
  you whether the site or your code moved.

---

## Pacing that doesn't earn blocks

Much "blocking" is a response to behaviour rather than identity, which means pacing is a fix and
not a workaround.

- Honour `Crawl-delay` from robots.txt; absent it, roughly one request per second per host is a
  defensible default.
- Keep concurrency to 1–2 per host. Parallelise across hosts, not within one.
- Respect `Retry-After` on 429 and 503 rather than retrying immediately — retrying blind is how a
  soft throttle becomes a hard ban.
- Back off exponentially with jitter; synchronised retries are themselves a detectable pattern.
- Cache aggressively during development so a selector iteration doesn't re-fetch the origin.
- Send a User-Agent identifying the crawler with a contact URL. Operators who can identify you will
  often whitelist rather than block.
- Use conditional requests (`ETag`, `If-Modified-Since`) on re-runs; a 304 is cheap for both sides.
