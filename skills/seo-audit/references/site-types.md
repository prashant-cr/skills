# Site types

The default audit priorities shift substantially by site type. Read the section
matching the site.

- [Ecommerce](#ecommerce)
- [Local business](#local-business)
- [SaaS and B2B](#saas-and-b2b)
- [Publishers and blogs](#publishers-and-blogs)
- [Marketplaces and listings](#marketplaces-and-listings)
- [Single-page apps](#single-page-apps)

## Ecommerce

**Faceted navigation is the defining problem.** Filters for colour, size, price
and brand generate combinatorial URLs — thousands of near-duplicate pages that
consume crawl budget and dilute signals. Decide deliberately which facet
combinations deserve to be indexable: the ones with real search demand ("blue
running shoes") get indexable, canonical, linked pages with unique copy;
everything else gets `noindex` or is blocked from crawling. Never leave it to
chance, and never leave every combination indexable.

**Category pages usually matter more than product pages.** They target the
commercial terms with real volume ("women's trail running shoes"), while
individual products chase model numbers with little demand. Most ecommerce sites
under-invest in category copy. Add genuinely useful content — buying guidance,
size and fit, comparison — above or below the grid, not a keyword-stuffed block
nobody reads.

**Out-of-stock and discontinued products.** Deleting the page throws away
accumulated links and rankings. Keep the page up if the product returns; if it
is gone for good, 301 to the closest equivalent or the parent category. Never
mass-404 a catalogue, and never redirect everything to the homepage.

**Duplicate product descriptions.** Manufacturer copy appears on every retailer
selling the item, so nothing distinguishes yours. Original descriptions, real
photography and genuine reviews are the differentiator.

**Pagination.** Each page self-canonicalises. Do not canonicalise page 2 to page
1 — the products on later pages then never get discovered. `rel=next/prev` is no
longer used by Google; sound internal linking replaces it.

**Structured data** earns disproportionate returns here: `Product` with `Offer`,
price, availability and `AggregateRating` produces rich results that lift
click-through at the same position. It must match what is visible on the page.

**Also check:** parameter handling for tracking and sorting, internal search
result pages left indexable, thin category pages with three products, and site
speed on image-heavy templates.

## Local business

**Google Business Profile outweighs the website** for local intent. Categories,
name, address, phone, hours, photos, services and reviews all feed the local
pack, which sits above organic results. An audit that ignores it has missed the
main channel.

**NAP consistency** — name, address and phone identical everywhere: the site,
GBP, directories, social profiles. Inconsistency is a common and quiet cause of
weak local ranking.

**Location pages.** One per location, each with a unique address, embedded map,
local phone number, staff, opening hours and genuinely local content. Templated
pages differing only in the city name are the standard mistake — they are thin
duplicates and rank accordingly.

**Reviews** are both a ranking factor and the main conversion lever in the local
pack. A steady flow of genuine reviews with responses beats a burst.

**Structured data:** `LocalBusiness` with address, geo-coordinates, opening
hours and service area.

**Local keywords** carry "near me" and city modifiers, and Google localises
results automatically — so check rankings from the target location, not from
wherever you happen to be. Results elsewhere are misleading.

**Also check:** service-area definition, citations in relevant local
directories, and mobile experience, since local search is overwhelmingly mobile.

## SaaS and B2B

**The buying cycle is long and multi-touch**, so content must serve every stage:
problem-aware ("why is our churn high"), solution-aware ("customer retention
software"), and vendor-aware ("competitor X alternatives", "X vs Y", "X
pricing"). Most SaaS sites publish only top-of-funnel blog posts and wonder why
traffic does not convert.

**Comparison and alternative pages** are the highest-converting SEO asset in the
category and are consistently under-built. "Alternatives to [large competitor]"
has genuine volume, clear intent, and is winnable because the competitor will
not write it.

**Programmatic pages** — integrations, templates, use cases by industry or role
— scale well when each page is genuinely useful. They become thin-content
liabilities when spun from a template with a variable swapped.

**Documentation ranks** and is usually ignored by the marketing team, despite
attracting exactly the technical evaluators who make purchase decisions.

**Free tools** are the most reliable link magnet in B2B: a calculator,
generator or checker that solves one small problem.

**Also check:** whether the pricing page is indexable and complete, whether
login and app subdomains are correctly excluded, blog subfolder versus subdomain
(subfolder is preferable), and case studies targeting industry-specific terms.

## Publishers and blogs

**Publishing volume is not the strategy.** Depth on a defined subject beats
breadth. A site covering one topic completely outranks one covering twenty
topics shallowly, especially at low authority.

**Content decay is the main threat.** Articles lose rankings steadily as they
age and competitors publish newer versions. A systematic refresh programme —
driven by the Search Console comparison — usually returns more than new
publishing.

**Tag and archive pages** are the most common source of index bloat. Most are
thin, duplicative lists that should be `noindex`ed unless a tag has genuine
search demand and its own curated content.

**Author pages and bylines** matter more than elsewhere, because E-E-A-T weighs
heavily on informational content. Real authors with credentials and history.

**Also check:** ad density hurting Core Web Vitals and reader experience,
`Article` structured data, Google News and Discover eligibility if relevant,
syndication using cross-domain canonicals so the original keeps the credit, and
whether the category structure reflects how readers search.

## Marketplaces and listings

**Listing turnover** is the structural challenge: pages that expire constantly.
Decide what happens to a sold or delisted item — keep, 410, or redirect to the
category — and apply it consistently. Leaving thousands of dead listings
indexable erodes quality signals sitewide.

**Thin listings at scale.** Individual listings are often near-identical.
Aggregate pages — by category, location, price band — usually carry the search
demand and deserve the investment.

**User-generated content quality** directly affects rankings. Spam listings,
duplicate posts and empty categories are a sitewide liability.

**Crawl budget genuinely applies** here, at the scale these sites reach. Server
log analysis is worth doing.

## Single-page apps

Read the JavaScript rendering section of `technical-seo.md` first — the whole
category lives or dies on it.

**The core problem:** content that requires rendering is indexed late, partially,
or not at all, and other search engines and LLM crawlers render even less than
Google.

**Check first:** whether main content appears in the raw HTML (`curl` the page),
whether links are real `<a href>` elements rather than click handlers, whether
routes have distinct URLs that return 200 on direct load rather than only
working via client-side navigation, and whether titles and meta tags update per
route rather than being fixed in `index.html`.

**Fixes in order:** server-side rendering or static generation; prerendering for
crawlers; hydration of server-rendered markup. If none is possible, say plainly
that organic search is structurally limited for this architecture rather than
recommending tags that cannot fix it. That is the honest answer and it is the
one that leads to the right decision.
