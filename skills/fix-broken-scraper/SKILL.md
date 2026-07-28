---
name: fix-broken-scraper
license: MIT
description: Diagnoses why a working web scraper or crawler broke and repairs it one verified step at a time — separates stale CSS selectors and site redesigns from real blocking, 403/429 responses, expired sessions, changed URL routing, and content that moved into embedded JSON or client-side rendering. Use this whenever a scraper, spider, crawler or parser that used to work now returns empty results, None, an empty list, zero rows, HTTP 403/429, a CAPTCHA page or wrong data — whenever someone says their scraping script stopped working, broke overnight, worked yesterday, is suddenly blocked, or their BeautifulSoup, Scrapy, Playwright, Puppeteer or requests code returns nothing.
---

# Fix a broken scraper

Scrapers break constantly, and almost all of the cost is misdiagnosis. "I'm being blocked" is the
loudest hypothesis, so people reach for headless browsers, proxies and spoofed headers — while the
page returns HTTP 200 and the selectors simply no longer match. Each wrong guess is permanent: a
browser added for a markup change stays in the stack forever, slower and more fragile than the code
it replaced, and it never addressed the fault.

So this skill classifies before it repairs, and changes one thing at a time.

## Workflow

### 1. Get the symptom precisely

Vague symptoms produce vague fixes. Pin down:

- **What exactly comes back?** Empty list, `None`, a partial row, wrong values, an exception, a
  non-200 status — these are different failures with different causes.
- **All URLs or some?** A subset failing points at page variants, not at blocking.
- **Since when, and what changed?** A site redesign, a dependency upgrade, a new deployment, or a
  changed IP each suggest a different class. "It worked yesterday" is worth pinning to a date.
- **First request or after N?** Failing immediately is a different problem from failing after two
  hundred requests, which is pacing or session state.

Ask when these aren't given. The answers routinely make the diagnosis obvious before any request.

### 2. Reproduce at the smallest scale

Get to a single failing URL and a single extraction step. A scraper that fails inside a Scrapy
pipeline, a retry wrapper and a proxy rotator gives you no signal about which layer is at fault.
One URL, one request, one selector.

### 3. Classify with the diagnostic

```bash
python3 scripts/diagnose.py https://site.com/page --selector ".product-title"
python3 scripts/diagnose.py https://site.com/page --expect-text "Add to cart"
```

Pass the selector the scraper actually uses and, where possible, text you know should be on the
page. Those two together are what separate the classes: text present but selector matching nothing
is a markup change; both absent with a thin page is client rendering; a non-200 is blocking.

The script makes at most three requests. When a plain request looks blocked it retries once with
browser-like headers — same IP, same TLS stack, only headers differ — because the difference
between those two outcomes isolates header-level filtering from something deeper, and guessing
cannot.

### 4. Repair the class you found, and nothing else

| Class | What it means | Repair |
| --- | --- | --- |
| `target intact` | Page and selector both fine | The fault is in your code or environment, not the site |
| `selectors stale` | 200, content present, selector dead | Rebuild the selector on durable anchors |
| `content moved into embedded JSON` | Data ships in a JSON blob | Parse the blob; do **not** add a browser |
| `client-rendered` | Thin HTML, no embedded data | Find the XHR endpoint; browser only as last resort |
| `routing changed` | Redirected elsewhere | Fix the URL template, then re-diagnose |
| `header-level filtering` | Plain refused, browser headers pass | Send a complete, consistent header set |
| `blocked` | Refused regardless of headers | Below the header layer — see below |
| `transport` | DNS/TLS/connection failure | Network or hostname, not scraper logic |
| `content changed or removed` | Page fine, content gone | Confirm by eye before changing code |

The discipline that matters: **apply one change, re-run the diagnostic, and only then consider
another.** Stacking three fixes at once means never learning which one worked, and it is how
scrapers accumulate proxies and browsers they never needed. If a change doesn't move the
diagnosis, revert it.

`references/failure-modes.md` has the symptom tables, the less common classes (encoding, pagination,
session expiry, partial data), and how to tell them apart.

### 5. When the diagnosis is `blocked`

A genuine block is different from the other classes, because it may be a decision rather than a
defect. Before engineering around it, establish which:

- **Is it new?** Try from another network. Success elsewhere means the block is against your IP,
  not your code — and often means your pacing earned it.
- **Is there a CAPTCHA on the content path?** That is the site asking for a human. Look for a
  sanctioned route — an official API, a feed, a data licence — rather than automating past it.
  This is also the durable answer: the API still works next quarter.
- **Did the site's stance change?** Re-read robots.txt and the terms. A site that recently added
  bot management may have decided against automated access, and that decision deserves respect
  even when it is technically surmountable.

Where the site does permit automated collection and the block is incidental, the useful fixes are
slowing down, honouring `Crawl-delay` and `Retry-After`, and matching a coherent real client
(`curl_cffi` addresses the TLS layer that header changes cannot). Identifying your crawler with a
contact URL often converts a block into a conversation.

### 6. Verify, then make it durable

A fix that isn't re-tested isn't a fix. Re-run the diagnostic, then the real scraper against several
URLs — including one that never failed, to catch a repair that broke the working path.

Then spend the extra ten minutes that prevents the next incident: prefer embedded JSON and
structured data over markup, select on stable anchors rather than generated class names, and add a
check that fails loudly when extraction returns nothing. Scrapers that fail silently are how a
selector change becomes three weeks of empty rows.
`references/durable-extraction.md` covers this.

## Report structure

```markdown
# Scraper diagnosis: <target>

**Class:** <the diagnostic's classification>
**Root cause:** <one sentence, concrete>

## Evidence
<status, what matched, what didn't — the observations that pin the class>

## Fix
<the specific change, with code where useful>

## Verification
<what was re-run and what it returned>

## Preventing a repeat
<durable anchors, structured data, failure alerting>
```

## Judgement calls

**Trust the status code over the story.** A user certain they are blocked, on a page returning 200
with intact content, is describing their own code. Say so plainly — that saves more time than any
workaround.

**A browser is a last resort, not a fallback.** It costs memory, latency and permanent maintenance.
Add one only after confirming the data is genuinely unavailable in the response, which the
diagnostic's embedded-JSON check settles cheaply.

**Silent partial data is worse than a crash.** A selector matching a *different* element returns
plausible wrong values indefinitely. When output is wrong rather than absent, verify records by eye
against the live page before declaring the repair done — and spread the sample across the output
rather than checking the first few. Misalignment usually starts at the first irregular record, so
the top of a listing is the part most likely to look correct while everything below it is wrong.

**Repeated breakage is a design signal.** A scraper that breaks monthly is coupled to markup that
changes monthly. The fix is switching anchors, not another patch.
