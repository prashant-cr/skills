# Alternatives to buying proxies

Read this **before** recommending any proxy. The best outcome available is usually deleting the
line item, and that option disappears the moment the conversation becomes "which vendor".

## Contents

- [Why this comes first](#why-this-comes-first)
- [No proxy at all](#no-proxy-at-all)
- [An official API](#an-official-api)
- [Sitemaps, feeds and bulk exports](#sitemaps-feeds-and-bulk-exports)
- [Scraping APIs and unblockers](#scraping-apis-and-unblockers)
- [Buying the dataset](#buying-the-dataset)
- [Asking](#asking)
- [Not collecting it](#not-collecting-it)
- [How to present the comparison](#how-to-present-the-comparison)

## Why this comes first

Someone arriving with "which proxy should I buy" has already decided the shape of the answer, and
the decision usually happened before anyone checked whether it was necessary. The cheapest
infrastructure is the infrastructure you do not run, and the second cheapest is somebody else's.

This is not a reason to be unhelpful about proxies. It is a reason to spend two minutes on the
routes that end the problem before spending money on the route that manages it.

## No proxy at all

Test it. `site_probe.py` makes plain requests and reports whether they succeed.

Plenty of sites do not block anything. Small sites, documentation, government data, most public
sector portals, many B2B catalogues. If the target is one of them and your volume is modest, the
right answer is a polite crawler with a sensible delay and no proxy line item.

The caveat the probe states itself: three successes from one IP is not 100,000 successes from a
datacenter range. Many sites tolerate low volume and block on pattern. So treat an open result as
"no evidence you need proxies yet" and validate at your real rate before concluding. But start
there, because the alternative — buying proxies you never needed — is invisible once you have
them.

## An official API

Check for one every time. This is the highest-value two minutes in the whole process and it is
skipped constantly, usually because the person already framed the task as scraping.

Where to look: `/developers`, `/api`, `/docs` on the site, the footer, the site's GitHub
organisation, a search for the company name plus "API". Many sites expose an undocumented JSON
endpoint that the front end itself calls — visible in the network tab and often far cleaner than
parsing HTML, though it may be undocumented on purpose and can change without notice.

What an official API gives you: stability, no blocking, sanctioned access, usually structured data
that needs no parsing. What it may not give you: complete coverage. **Check it exposes the fields
you actually need before celebrating** — an API covering 60% of your fields may still be worth
using for those, with a much smaller scraper for the rest.

Watch for rate limits and pricing tiers, but compare them against the true cost of scraping —
proxies plus engineering plus breakage — rather than against zero.

## Sitemaps, feeds and bulk exports

Underrated and frequently sufficient:

- **`sitemap.xml`** — a list of every URL the site wants indexed, often with last-modified dates.
  For change detection that alone can replace crawling entirely: poll the sitemap, fetch only what
  changed.
- **RSS and Atom feeds** — for news, blogs, listings. Cheap, stable, designed to be consumed.
- **Bulk downloads** — many data-publishing sites offer a CSV or a dump somewhere unglamorous.
  Government and academic sources almost always do.
- **Common Crawl** — an open crawl of much of the web. Free, already collected, and worth checking
  for historical or broad-coverage work before crawling anything yourself.

The probe reports sitemaps found in robots.txt. Look at them.

## Scraping APIs and unblockers

You send a URL, they return the HTML, having handled proxies, browser fingerprinting, JS rendering
and CAPTCHAs. Priced per request or per successful request.

**When they win**, and they win more often than proxy-first thinking expects:

- The site has serious bot defence. You are otherwise buying residential proxies *and* building
  fingerprint evasion, and the second part is open-ended work against an adversary who updates.
- The volume is low to moderate. Per-request pricing is fine at thousands, painful at tens of
  millions.
- Your time is worth more than the price difference. Usually true for anyone employed.
- You want the block risk to be somebody else's problem. Per-success pricing transfers it
  literally.

**When they lose**: very high volume where per-request pricing compounds, sites that need no help
at all, or workflows needing fine control over the session, headers and timing.

The comparison people get wrong: a scraping API at a few hundred a month against proxies at a few
tens looks obvious until you price the two weeks of fingerprint work, the ongoing breakage, and
the failure rate difference. `cost_model.py` includes engineering time precisely because this
comparison is otherwise decided by the wrong number.

## Buying the dataset

For common data — company registries, product catalogues, pricing, job postings, property
listings — a vendor may already sell it, cleaned and updated.

Worth a look when the data is commodity rather than proprietary to your idea, when you need
history you cannot crawl retroactively, or when compliance risk matters more than cost. Often
cheaper than the fully loaded cost of building and maintaining collection, and it comes with
someone contractually responsible for it.

## Asking

Genuinely underused. A short email to the site owner explaining who you are and what you need
sometimes produces a data dump, an API key, or an allowlist entry. It costs one message.

It works more often than expected for academic and non-commercial use, for small sites flattered
by the interest, and where you can offer something back. It also converts an adversarial
relationship into a permitted one, which is worth more than any proxy.

## Not collecting it

Sometimes the requirement does not survive the question "what decision does this data change?"
Sampling 500 pages may answer it as well as scraping 5 million. A weekly refresh may do the work
of an hourly one at a fraction of the cost, and the cost scales with frequency.

Not a rhetorical point — reducing scope is often the largest available saving, and it is the one
nobody proposes because it sounds like doing less.

## How to present the comparison

Put the alternatives in the same costed table as the proxies rather than mentioning them in
passing. Someone who asked about proxies and receives a table where an official API sits at the
top with a lower total has been given a genuine answer to their real question, which was never
about proxies.

Two things keep that honest. State the coverage caveat next to any API option, because "free but
missing the field you need" is not free. And put engineering time on every row, including the
alternatives — a free API still costs a day of integration, and pretending otherwise just moves
the dishonesty around.
