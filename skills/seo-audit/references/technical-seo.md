# Technical SEO reference

How to interpret what the crawl found, and how to debug the problems it cannot
see by itself. Read the section you need rather than the whole file.

- [Indexation comes first](#indexation-comes-first)
- [Reading the crawl findings](#reading-the-crawl-findings)
- [JavaScript rendering](#javascript-rendering)
- [Canonicals](#canonicals)
- [Redirects and migrations](#redirects-and-migrations)
- [hreflang and international](#hreflang-and-international)
- [Core Web Vitals](#core-web-vitals)
- [Structured data](#structured-data)
- [Crawl budget](#crawl-budget)
- [Diagnosing a traffic drop](#diagnosing-a-traffic-drop)

## Indexation comes first

Every ranking question is downstream of one binary fact: is the page in the
index? A user reporting "we don't rank for X" is describing a symptom with two
completely different causes and opposite fixes.

Check in this order, stopping at the first failure:

1. **Is it crawlable?** robots.txt `Disallow` blocks the *fetch*. A page blocked
   here can still be indexed — from links alone, with no snippet — which is why
   robots.txt is the wrong tool for keeping something out of search.
2. **Is it indexable?** `noindex` in a meta tag or the `X-Robots-Tag` header.
   This is the correct tool for exclusion. Note the trap: a page that is
   *both* `Disallow`ed and `noindex`ed stays indexed forever, because the
   crawler is never allowed to fetch the page and see the `noindex`.
3. **Does it canonicalise to itself?** A canonical pointing elsewhere is a
   request to index the other URL instead.
4. **Does it return 200?** Including soft 404s — a "not found" page answering
   200 (see below).
5. **Is it discoverable?** In the sitemap, and linked from a page that is
   itself indexed. Orphans get crawled rarely or never.

Search Console's **Page Indexing** report gives the authoritative answer per
URL, and its URL Inspection tool shows what Google actually fetched and
rendered. Nothing derived from a crawl overrides it. When the user has access,
ask for the "Why pages aren't indexed" breakdown — it names the exact reason.

### Soft 404s

A URL that does not exist but returns HTTP 200 with a "not found" message. Two
consequences, both bad: Google wastes crawl budget on infinite non-existent
URLs, and it may class real thin pages the same way and drop them. The crawler
probes for this. The fix is a genuine 404 or 410 status code — the visible page
content is irrelevant, only the header matters.

## Reading the crawl findings

The crawler groups by severity, but severity is generic. These are the ones
whose meaning changes most with context:

**`noindex-pages`** — Correct on staging, thank-you pages, internal search
results, and thin tag archives. Catastrophic on a service or product page.
Always ask before calling it a fault; on a template-driven site one misplaced
`noindex` can remove a whole section.

**`duplicate-content`** — Identical body text across URLs. Common and usually
benign in one form (`/` and `/index.html`, or a print view) where a canonical
resolves it. Genuinely damaging when it is the same product or article on many
URLs with no canonical, because Google picks one arbitrarily and it may not be
the one you promote.

**`thin-content`** — Word count is a proxy, never a target. A 150-word page that
answers a specific question completely is fine; a 2,000-word page padded to hit
a number is worse. The finding matters when the page is *meant* to compete on an
informational query and says less than everything ranking above it. Homepages
are exempt — they rank on brand and links.

**`js-rendered-content`** — Little text in the initial HTML alongside heavy
script. See below.

**`orphan-pages`** — In the sitemap but linked from nothing. No internal links
means no authority flow and rare crawling. Often reveals a whole section
orphaned by a navigation change.

**`no-contextual-inbound-links`** — Reachable only through nav, header or
footer. Site-wide navigation links pass much less weight than an in-content
link from a relevant page. A money page with no contextual inbound links is the
most common quiet cause of underperformance.

**`deep-pages`** — Four or more clicks from the homepage. Crawl frequency drops
with depth. Fix by flattening the internal link graph — hub pages, related
links, better categories — not by adding sitemap entries.

**`slow-ttfb`** — Server response time, distinct from page load. High TTFB
usually means an unoptimised database query, no caching, or a distant origin.
It gates everything else, and a CDN is often the whole fix.

**`missing-canonical`** — Low severity alone. High severity on any site with URL
parameters — filters, sorting, tracking tags — because each parameter otherwise
mints a duplicate.

## JavaScript rendering

Google renders JavaScript, but as a second pass, queued after the initial crawl
and with no guaranteed timing. The practical consequences:

- Content in the initial HTML is indexed reliably and quickly. Content requiring
  rendering is indexed later, sometimes much later, and sometimes not.
- Links only present after rendering are discovered late, so the crawler finds
  the site more slowly.
- Other engines and most LLM crawlers render less than Google, or not at all.
  A site depending on client rendering is invisible to a growing share of
  traffic sources.

**Diagnosis:** compare the raw HTML with the rendered DOM. The crawler flags a
likely shell (little text, heavy script). Confirm with `curl` and look for the
main content, or use Search Console's URL Inspection → View Crawled Page → HTML,
which shows exactly what Google received.

**Fixes, in order of preference:** server-side rendering or static generation;
prerendering for crawlers; hydration of server-rendered markup. A pure
client-rendered app that must rank needs an architecture change, and saying so
early is more useful than a list of tags.

Also check that links are real `<a href>` elements. A `<div onclick>` router
link is not a link, is not followed, and passes nothing.

## Canonicals

A canonical is a hint, not a directive — Google can and does ignore one it
disagrees with. Rules worth knowing:

- Every indexable page should have a self-referencing canonical. It costs
  nothing and immunises against parameter duplication.
- Canonicals must be absolute URLs, and must point to a 200 page. A canonical
  to a redirect, a 404 or a `noindex` page sends a contradictory signal and
  Google falls back to guessing.
- Do not canonicalise paginated pages to page 1. Each page should
  self-canonicalise, or the products on pages 2+ never get discovered.
- Cross-domain canonicals are legitimate for syndicated content — they hand
  credit to the original.
- If Google reports "Duplicate, Google chose different canonical", the page
  it chose is telling you what it considers the better version; investigate why
  rather than repeating the declaration.

## Redirects and migrations

- **301** permanent, passes signals, the default for a moved page.
- **302** temporary. Google eventually treats a long-lived 302 as a 301, but
  slowly. Use 301 unless the move genuinely is temporary.
- **Chains** — each hop adds latency and Google stops following after several.
  Always redirect to the final destination directly.
- **Loops** — a page that never resolves is removed from the index.

Migrations fail in a predictable way: redirecting everything to the homepage.
This is treated as a soft 404 and loses effectively all the value of every
redirected URL. Map old URLs to their closest equivalent one by one; where no
equivalent exists, a 410 is more honest than a homepage redirect.

After any migration, expect a temporary drop of a few weeks. A drop that has not
recovered after two months is a problem, not a settling period.

## hreflang and international

Only relevant with genuinely different language or region versions of the same
content. The rules are unforgiving:

- Annotations must be **reciprocal**. If A points at B, B must point back at A.
  A one-way annotation is ignored entirely.
- Every set must include a **self-referencing** entry.
- Use `x-default` for the fallback when no version matches.
- Language codes are ISO 639-1, region codes ISO 3166-1 Alpha-2. `en-UK` is
  invalid — the country is `GB`.
- hreflang does not consolidate ranking signals; it selects which version to
  show. Duplicate English pages for US and UK still compete unless canonicalised.

## Core Web Vitals

**Not measurable from a crawl.** The crawler reports TTFB and page weight, which
are related but not the same thing. Do not report CWV numbers you did not
measure.

- **LCP** (loading, target < 2.5s) — usually the hero image or heading. Fixed by
  server response time, image optimisation, and removing render-blocking
  resources.
- **INP** (interactivity, target < 200ms) — replaced FID. Fixed by cutting main
  thread JavaScript work.
- **CLS** (visual stability, target < 0.1) — fixed by setting width and height
  on images, and reserving space for ads and embeds.

Field data — real users, in Search Console's Core Web Vitals report or CrUX —
is what Google uses. Lab data from PageSpeed Insights or Lighthouse is a
diagnostic that suggests causes but does not decide the assessment.

Keep the weight honest: Core Web Vitals is a real but small ranking factor, and
mostly a tiebreaker between comparable pages. A slow page with the best content
usually still wins. Recommending a performance project ahead of an indexation
fix or a content gap gets the order wrong.

## Structured data

Does not improve rankings directly. It earns rich results — stars, FAQs, prices,
breadcrumbs — which raise click-through at the same position, and that is worth
real traffic.

Most-used types: `Organization`, `LocalBusiness`, `Product` (with `Offer` and
`AggregateRating`), `Article`, `BreadcrumbList`, `FAQPage`, `HowTo`, `Event`,
`Recipe`, `JobPosting`. JSON-LD is Google's preferred format.

The markup must describe content actually visible on the page. Marking up
reviews that are not shown, or prices that differ from the page, is a
structured-data spam violation and risks a manual action. Validate with Google's
Rich Results Test — a type Google does not support produces no rich result no
matter how correct the syntax.

## Crawl budget

Only a real constraint on large sites — roughly tens of thousands of URLs and
up. Below that, worrying about it is a distraction.

Where it does apply, the waste is usually: faceted navigation generating
combinatorial URLs, internal search result pages, session or tracking
parameters, and infinite calendars. Fix by blocking the patterns in robots.txt,
`noindex`ing what must stay reachable, and keeping the sitemap to canonical
URLs only. Server log files are the ground truth for what Google actually
crawls; Search Console's Crawl Stats report is the accessible version.

## Diagnosing a traffic drop

Get the date first. The shape of the decline names the cause:

- **Sharp, single day, sitewide** — technical or manual. Check for a robots.txt
  change, a sitewide `noindex` (a staging config pushed to production is the
  classic), a failed migration, an expired certificate, or a manual action in
  Search Console.
- **Sharp, and it matches a known algorithm update** — quality or relevance
  reassessment. No quick fix; addressed by improving the content, not by
  technical work.
- **Gradual over months** — competitors improving, content decaying, or slow
  relevance loss. Compare against the same period last year to separate it from
  seasonality.
- **Confined to one section** — look for what changed in that template.
- **Impressions flat, clicks down** — not a ranking loss at all. An AI overview
  or a new SERP feature is taking the clicks, or a competitor wrote a better
  title. This distinction is visible only in Search Console and is missed
  constantly.

Always check whether the drop is in impressions, clicks, or position. They mean
different things and a single "traffic is down" number hides which.
