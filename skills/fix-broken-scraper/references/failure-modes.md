# Failure modes

Symptom tables for telling scraper failures apart, including the classes `diagnose.py` cannot
detect on its own because they need more than one request or more than one URL.

## Contents

- [Symptom to class](#symptom-to-class)
- [The four that get confused](#the-four-that-get-confused)
- [Classes needing more than one request](#classes-needing-more-than-one-request)
- [Data is returned but wrong](#data-is-returned-but-wrong)
- [Environment and own-code faults](#environment-and-own-code-faults)

---

## Symptom to class

| What you observe | Most likely class | Distinguishing check |
| --- | --- | --- |
| Empty list, HTTP 200 | selectors stale | Is the expected text in the raw HTML? |
| Empty list, HTTP 200, thin page | client-rendered | Visible text under ~800 chars |
| Empty list, HTTP 200, rich page | selectors stale | Text present, selector matches zero |
| HTTP 403 immediately | blocked or header filtering | Retry with full browser headers |
| HTTP 429 | rate limited | Check `Retry-After`; reduce concurrency |
| HTTP 404 on URLs that worked | routing changed | Follow one URL by hand |
| Redirect to homepage or login | routing or session | Compare final URL to requested |
| Works locally, fails in production | environment | Compare IP, egress, Python and library versions |
| Works for 200 pages then stops | pacing or session | Note the request count at failure |
| Some URLs work, others don't | page variants | Diff a working URL against a failing one |
| Fields present but values wrong | selector drift | Verify records by eye against the live page |
| Exception in the parser | own code | Read the traceback before touching the site |

---

## The four that get confused

These account for most misdiagnosis, and the distinction is cheap to make.

**Blocked** — a non-200, or a 200 whose body is an interstitial. The content never arrived.
*Tell:* status code, vendor cookies, challenge scripts, block phrases in the body.

**Selectors stale** — the content arrived and is in the HTML; your query no longer finds it. Almost
always a redesign or a generated class name that changed.
*Tell:* expected text is present in the raw HTML while the selector matches zero.

**Content moved into embedded JSON** — the content arrived, but inside a `<script>` block rather
than markup. Common with React, Next.js and similar, and easy to mistake for client rendering.
*Tell:* thin visible markup alongside `__NEXT_DATA__`, `__NUXT__`, JSON-LD, or an
`application/json` script block. Parse the blob — a browser here renders data you already hold.

**Client-rendered** — the content genuinely did not arrive; JavaScript fetches it after load.
*Tell:* thin page, no embedded data, a framework shell such as `<div id="root">`.
*Fix:* find the XHR in devtools and call that endpoint. It is usually clean JSON, one request
instead of a full render, and more stable than markup.

The costly error is treating the middle two as the fourth, because the repair is a headless browser
that was never needed.

---

## Classes needing more than one request

`diagnose.py` looks at one URL, so these need deliberate checks.

### Rate limiting and pacing
Symptom: the first N requests succeed, then 429s or blocks. N is often suspiciously round.
Check `Retry-After` and any `X-RateLimit-*` headers. Reduce concurrency to 1–2 per host and honour
`Crawl-delay`. Blocking that arrives on schedule is earned by behaviour, and slowing down is the
actual fix rather than a workaround.

### Session and cookie expiry
Symptom: works briefly after a manual login, then redirects to a login page. Sessions expire,
tokens rotate, CSRF values are single-use. If content requires authentication it is outside the
scope of public-content scraping — check the site's position before automating a login.

### Pagination changes
Symptom: page 1 works, page 2 is empty or repeats page 1. Sites move between `?page=`, cursors and
infinite scroll. Verify the pagination parameter still exists, and that the last page terminates
the way your loop expects — an off-by-one that silently stops at page 1 looks identical to a block.

### Per-variant differences
Symptom: a subset of URLs fails. Products out of stock, users without avatars, articles behind a
partial paywall all render differently. Diff a failing page against a working one rather than
assuming the site broke.

---

## Data is returned but wrong

More dangerous than an empty result, because nothing alerts.

**Selector drift** — the selector now matches a different element. A `.price` that picked up a
"compare at" value returns plausible numbers that are simply wrong. Verify a handful of records
against the live page after any selector change.

**Encoding** — mojibake (`â€™` for an apostrophe) means the declared charset was ignored. Respect
the `Content-Type` charset or the meta tag rather than assuming UTF-8.

**Locale and formatting** — `1.234,56` is not `1234.56` everywhere, and date order varies by
region. Parse with the site's locale in mind.

**Whitespace and entities** — leading/trailing whitespace, `&nbsp;`, and zero-width characters
break exact matching and numeric parsing. Normalise before comparing.

**Duplicate or stale content** — identical results across pages suggests a cached response or a
pagination bug, not a site change.

---

## Environment and own-code faults

When the diagnostic reports `target intact`, the fault is on your side.

- **Dependency upgrades.** This is the most under-suspected cause, because "nothing in our code
  changed" is usually true — and irrelevant, since the dependencies changed underneath it. An
  unpinned requirement floats on every rebuild of a CI image or container, so the upgrade happens
  on a night nobody deployed.

  The damaging variant removes an API without a shim or a `DeprecationWarning`. Scrapy 2.17.0
  (released 2026-07-07) dropped `Spider.start_requests()`: a spider defining it issues zero
  requests, scrapes zero items, logs no error, and exits with `finish_reason: 'finished'`. Every
  signal says success. A nightly job like that looks exactly like a site blocking you, which is
  why it gets misdiagnosed as one.

  So when the page checks out, get the versions before theorising: compare the installed set
  against the last known-good run, and check the changelog of anything that moved. Pinning is the
  repair, and pinning is also what makes the next incident diagnosable.
- **Local versus production.** Different egress IP, different Python, different TLS. A scraper that
  works locally and fails deployed is usually an IP reputation or network difference.
- **Cached fixtures.** Tests passing against a saved HTML file prove nothing about the live page.
- **Silent exception handling.** A broad `except: pass` around extraction converts every failure
  into an empty result, which is why the breakage went unnoticed for weeks.

Isolate by saving the live HTML once and running the parser against the file. If parsing the file
succeeds, the fault is in fetching; if it fails, the fault is in parsing. That single split
resolves most of these quickly.
