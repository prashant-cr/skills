# Structured data formats

What each format is, how to read it, and what it is reliably good for.

## Contents

- [JSON-LD](#json-ld)
- [Microdata and RDFa](#microdata-and-rdfa)
- [Open Graph and meta tags](#open-graph-and-meta-tags)
- [Embedded application state](#embedded-application-state)
- [Feeds and sitemaps](#feeds-and-sitemaps)
- [Schema.org types worth knowing](#schemaorg-types-worth-knowing)

---

## JSON-LD

A `<script type="application/ld+json">` block holding schema.org-typed JSON. The default choice
when present, because sites maintain it for search-engine rich results and a broken block costs
them visibility.

```html
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Product","name":"Widget Pro",
 "offers":{"@type":"Offer","price":"29.99","priceCurrency":"USD"}}
</script>
```

**Reading it:**

- A page usually carries **several** blocks. Filter on `@type` rather than taking the first —
  `BreadcrumbList`, `Organization` and `WebSite` are commonly emitted before the entity you want.
- `@graph` is a container holding multiple entities. Iterate its children; the wrapper itself is
  not an entity.
- Values may be a scalar, an object, or a list of either. `author` might be `"Ada"`,
  `{"@type":"Person","name":"Ada"}`, or a list of both shapes. Normalise on read.
- `@type` itself can be a list (`["Product","Offer"]`).
- Blocks are hand-written often enough that trailing commas appear; a lenient reparse is worth it.

**Reliability:** high for the fields search engines display (name, price, availability, rating,
dates), lower for optional ones, which vary page to page even within a site.

---

## Microdata and RDFa

Attributes on ordinary markup: `itemscope` opens an entity, `itemtype` names it, `itemprop` labels
a field. Older than JSON-LD and still common on established sites.

```html
<div itemscope itemtype="https://schema.org/Person">
  <span itemprop="name">Ada Lovelace</span>
  <time itemprop="birthDate" datetime="1815-12-10">Dec 1815</time>
</div>
```

The value comes from the element's text *except* where a more precise attribute exists — `content`
on `<meta>`, `href` on `<a>`/`<link>`, `src` on media, `datetime` on `<time>`, `value` on `<data>`.
Often that is exactly what you want: `datetime="1815-12-10"` is machine-readable where the text
"Dec 1815" is not.

**But the `<a>` case cuts the other way.** A brand marked up as
`<a itemprop="brand" href="/facets/brands/Ferrero">Ferrero</a>` yields `/facets/brands/Ferrero` —
spec-correct, and not the name you wanted. Open Food Facts does exactly this. When a microdata
value comes back looking like a path, the human-readable form is in the element text, and you
either want the last path segment or a second pass that reads text for that property.

Two related warts: properties **repeat**, so `name` may arrive as a list containing a heading like
`"Book Details"` alongside the real title; and nesting errors are common because nothing visibly
breaks when they happen. JSON-LD has none of these problems, which is why it is preferred where it
carries your type.

RDFa uses `vocab`/`typeof`/`property` for the same purpose and appears mostly on older or
publishing-oriented sites.

**Reliability:** medium. Correctly structured when present, but nesting is easy to get wrong and
sites break it more often than they break JSON-LD, because nothing visibly fails when they do.

---

## Open Graph and meta tags

`<meta property="og:...">` drives link previews on social platforms and chat apps.

Consistently available: `og:title`, `og:description`, `og:image`, `og:url`, `og:type`,
`og:site_name`. Commerce sites often add `og:price:amount` and `og:price:currency`; articles add
`article:published_time` and `article:author`.

**Reliability:** high for presence, lower for fidelity. This is a *summary* written for a preview
card — descriptions are truncated, titles are shortened, and `og:url` is a canonical URL that may
differ from the one you fetched. Excellent for canonical URL, title and image; poor as a source of
full text.

Standard `<meta name="...">` tags remain useful too, especially `description`, `keywords`,
`author`, and `robots` (whose `noindex`/`nofollow` is a statement of intent worth reading).

---

## Embedded application state

Framework payloads shipped so the client can render without a second request:

- `__NEXT_DATA__` — Next.js, in a `<script type="application/json">` block
- `window.__NUXT__` — Nuxt
- `window.__INITIAL_STATE__` / `window.__PRELOADED_STATE__` — Redux-style stores
- `window.__APOLLO_STATE__` — Apollo GraphQL cache
- Named blocks such as GitHub's `react-app.embeddedData`

**Usually the richest source on the page** — internal ids, pagination totals, stock levels, exact
numbers, and fields the UI never renders.

**But it is an internal shape with no compatibility promise.** The site owes nothing to external
readers and can rename keys in any deploy. Use it when it carries what you need, pin the exact key
path, and let a missing path raise rather than defaulting quietly.

Extracting a `window.X = {...}` assignment needs brace matching, not a regex — JSON strings contain
braces, and a non-counting pattern will truncate on the first `}` inside a string.

---

## Feeds and sitemaps

**RSS/Atom** — declared via `<link rel="alternate" type="application/rss+xml">`. A documented,
stable interface for anything post-shaped: articles, releases, jobs, forum threads. Usually only
recent items, so unsuitable for backfill but ideal for monitoring.

**Sitemaps** — listed in robots.txt. The cheapest way to enumerate URLs on a site, often with
`lastmod` timestamps that let you fetch only what changed. Sitemap indexes nest, so follow them.

Both exist specifically to be consumed by machines, which makes them the least adversarial data
you can collect.

---

## Schema.org types worth knowing

| Type | Fields that matter |
| --- | --- |
| `Product` | `name`, `sku`, `brand`, `offers`, `aggregateRating`, `image` |
| `Offer` | `price`, `priceCurrency`, `availability`, `priceValidUntil` |
| `AggregateRating` | `ratingValue`, `reviewCount`, `bestRating` |
| `Article` / `NewsArticle` | `headline`, `datePublished`, `dateModified`, `author`, `articleBody` |
| `JobPosting` | `title`, `hiringOrganization`, `baseSalary`, `jobLocation`, `validThrough` |
| `Event` | `startDate`, `location`, `offers`, `performer` |
| `Recipe` | `recipeIngredient`, `recipeInstructions`, `cookTime`, `nutrition` |
| `LocalBusiness` | `address`, `telephone`, `openingHoursSpecification`, `geo` |
| `BreadcrumbList` | `itemListElement` — useful for category paths |
| `ItemList` | `itemListElement` — listing pages sometimes expose all items here |

`availability` uses URL-shaped enums (`https://schema.org/InStock`); compare on the final segment
rather than the whole string, since sites vary the prefix.
