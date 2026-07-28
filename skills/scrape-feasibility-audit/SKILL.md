---
name: scrape-feasibility-audit
description: Audits a public website to determine how hard it will be to scrape and what to build it with — identifies bot detection (Cloudflare, Akamai, DataDome, HUMAN/PerimeterX, Kasada, Imperva, AWS WAF), CAPTCHA types (reCAPTCHA, hCaptcha, Turnstile, Arkose, GeeTest), robots.txt rules, rate limits, and whether content is server- or client-rendered, then recommends open-source libraries. Use this whenever the user asks whether a site can be scraped, why their scraper is getting blocked or returning empty pages, what anti-bot protection a site uses, which scraping library or framework to pick, or is planning any data-collection or crawling project — even if they only mention a URL and extracting data from it.
---

# Scrape feasibility audit

Answers two questions before anyone writes a scraper: **should we collect this, and what will
it take?** Getting these wrong is expensive in a specific way — teams build a Playwright cluster
for a site that publishes JSON-LD, or spend a week fighting Kasada for data behind an official
API that would have taken an afternoon.

The output is a decision, with evidence, not a pile of observations.

## Scope

Covers **public, unauthenticated content**: pages any visitor can reach without logging in.

Outside scope, and worth saying plainly to the user if a request lands here:

- Content behind authentication, paywalls, or purchased access
- Defeating an interactive CAPTCHA that gates the content itself
- Evading a block on a site that has explicitly refused automated access

These aren't arbitrary lines. Each marks the point where a technical obstacle has become a
stated decision by the operator, and where routing around it stops being an engineering
question. When an audit lands there, the useful contribution is to say so and redirect to a
sanctioned path — that is a more valuable answer than a fragile workaround, because it is the
one that still works in six months.

## Workflow

### 1. Look for the sanctioned path first

Do this before probing anything. It is the step most often skipped and the one that most often
ends the project early, in a good way. Check for:

- An official API — try `/api`, `/api/docs`, `/openapi.json`, `/graphql`, and a web search for
  "<site> developer API"
- Bulk downloads, data dumps, or an exports page
- RSS/Atom feeds
- A sitemap (the probe reports these from robots.txt) — the cheapest way to enumerate URLs
- Commercial licensing, for data that is the company's actual product

If a sanctioned path exists, recommend it and stop. An API that returns typed JSON under a
clear usage policy beats any scraper on reliability, cost, and durability. Report the finding
rather than treating it as a failed audit.

### 2. Probe the target

```bash
python3 scripts/probe_site.py https://example.com/the/actual/page
```

Point it at a representative **content** page, not the homepage — defenses and rendering often
differ between them, and the homepage is the least representative page on most sites.

The probe fetches robots.txt, then the page, with a delay between requests and an honest
User-Agent. It refuses to fetch a robots-disallowed path unless given `--force`. Add `--json`
for machine-readable output.

It reports: robots.txt rules and crawl-delay, bot-management vendors (distinguishing engaged
from merely present), CAPTCHA types, rendering mode, rate-limit headers, and a difficulty tier.

### 3. Interpret, don't just relay

The probe produces evidence; the judgement is yours. Three checks matter most:

**Was the probe itself blocked?** If `blocked_on_first_request` is set, everything the probe
saw describes a block page, which may hide the real defenses — and may equally overstate them,
since a plain Python client is the easiest thing in the world to detect. Say so rather than
reporting the block page's contents as the site's architecture.

**Is the vendor engaged or just present?** A `cf-ray` header means the site uses a common CDN
and nothing more. Only a scoring cookie (`__cf_bm`, `_abck`, `datadome`, `_px3`) or a challenge
script shows bot management is actually running. Confusing the two is the most common way these
audits go wrong, and it produces confidently wrong "this site is hard" verdicts.

**Where is the CAPTCHA?** One on the login form is irrelevant to public-content scraping. One on
the content path is a stop signal.

For vendor-by-vendor detail, block-page forensics, and which detection layer a given symptom
points to, read `references/signatures.md`.

### 4. Check what a browser would add

If the probe says `client-rendered`, confirm before recommending a browser — this decision
carries most of the project's ongoing cost.

Look for an embedded JSON blob first (`__NEXT_DATA__`, `__NUXT__`, `application/ld+json`,
`window.__INITIAL_STATE__`); the probe reports these. If one exists, the data is already in the
HTML and a plain HTTP client is enough.

Otherwise the page fetches its data from an endpoint, and calling that endpoint directly is
almost always better than rendering: one request instead of a full browser, clean JSON instead
of parsed markup, and an interface that changes less often than markup does. Recommend looking
for the XHR in devtools before recommending Playwright.

### 5. Choose tooling on evidence

Pick the least powerful tool that clears the *demonstrated* obstacle — each step up costs an
order of magnitude in memory, latency, and maintenance. `references/libraries.md` maps findings
to specific libraries across Python, Node, and Go, and covers rate limiting, caching, and
identification practices.

The short version: static HTML → `httpx` + `selectolax`; scale → `Scrapy` or `Crawlee`;
TLS-fingerprint blocking → `curl_cffi`; genuine JS rendering → `Playwright`; browser
fingerprinting → `Camoufox` or `nodriver`.

### 6. Report

Use this structure. It leads with the decision because that is what the reader needs first;
the evidence is there to be argued with, not admired.

```markdown
# Scrape feasibility: <site>

**Verdict:** <Go / Go with constraints / Use the API instead / Not advisable>
**Difficulty:** <trivial | easy | moderate | hard | very hard>

## Recommended approach
<One paragraph: the path to take and why. Name the library and the reason it is the
right level of power for what was actually found.>

## What's in the way
| Layer | Finding | Evidence |
| --- | --- | --- |
| Bot management | <vendor, engaged or not> | <cookie/header/script> |
| CAPTCHA | <type and where it appears> | <marker> |
| Rendering | <server / client / embedded JSON> | <chars of text, framework> |
| robots.txt | <allowed or disallowed, crawl-delay> | <matched rule> |

## Sanctioned alternatives
<API, feeds, dumps, licensing — or "none found", having actually looked.>

## Build notes
- Libraries and why
- Request pacing (honour Crawl-delay; ~1 req/s per host otherwise)
- What will break first and what to monitor

## Compliance notes
<robots.txt stance, ToS if checked, personal-data exposure under GDPR-style regimes.
State what was and wasn't verified — don't imply a legal review happened.>
```

## Judgement calls

**Report uncertainty as uncertainty.** A single probe from one IP at one moment is a narrow
sample. Defenses vary by path, geography, IP reputation, and time. If the result is thin,
say what would sharpen it rather than overstating confidence.

**Rate the target, not the probe.** Being blocked tells you a plain Python client is blocked,
which is nearly free information. It does not establish that a well-built scraper would be.

**Volume changes the answer.** A hundred pages once and a hundred thousand daily are different
projects against the same defenses. Ask about scale when the user hasn't said, because it
changes both the tooling recommendation and whether the project is reasonable at all.

**Flag personal data when you see it.** Public visibility is not permission to collect and
store. If the target holds names, contact details, or profiles, note the obligation — it is
usually the largest risk in the project and the one least likely to have been considered.
