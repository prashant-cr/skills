# Library selection

Open-source tooling, chosen by what actually blocks you rather than by popularity.
Read this once the probe has established the difficulty tier and rendering mode.

## Contents

- [Choosing by constraint](#choosing-by-constraint)
- [Python](#python)
- [JavaScript / TypeScript](#javascript--typescript)
- [Go](#go)
- [Parsing and extraction](#parsing-and-extraction)
- [Operational concerns](#operational-concerns)

---

## Choosing by constraint

Pick the least powerful tool that clears the actual obstacle. Every step up this ladder costs
an order of magnitude in memory, latency, and maintenance, so escalate only on evidence.

| What the probe found | Reach for |
| --- | --- |
| Server-rendered, no bot management | `httpx` or `requests` + `selectolax` |
| Embedded JSON (`__NEXT_DATA__`, JSON-LD) | plain HTTP client + `json` — no browser needed |
| Many pages, simple defenses | `Scrapy` (Python) or `Crawlee` (Node) |
| Client-rendered, no bot management | `Playwright` |
| TLS fingerprint blocking | `curl_cffi` (impersonates real browser handshakes) |
| Browser fingerprint blocking | `Camoufox` or `nodriver` |
| Content for an LLM pipeline | `Crawl4AI` or self-hosted `Firecrawl` |
| Interactive CAPTCHA on content path | none — find a sanctioned path instead |

The last row is not evasiveness. When a site puts a human-verification gate on its content, no
library choice makes automated collection appropriate; the engineering answer and the ethical
answer coincide.

---

## Python

**`httpx`** — the sensible default HTTP client. HTTP/2 support, sync and async, connection
pooling. Prefer over `requests` for new work; `requests` remains fine for simple scripts but
is HTTP/1.1 only, which is itself a fingerprint.

**`curl_cffi`** — `requests`-compatible API over curl-impersonate, reproducing the TLS and
HTTP/2 fingerprints of real browsers. This is the single highest-leverage upgrade when a site
blocks `requests` but serves a browser, because it addresses the actual detection layer at a
fraction of a browser's cost.

```python
from curl_cffi import requests
r = requests.get(url, impersonate="chrome")
```

**`Scrapy`** — the mature crawling framework: scheduling, deduplication, retries, concurrency,
item pipelines, `AutoThrottle`. Worth its learning curve past roughly a thousand pages; overkill
below that. `AutoThrottle` is also the politest default available, adapting concurrency to
observed latency.

**`Playwright`** — browser automation when content genuinely requires JS. Prefer it over
Selenium for new work: better waiting primitives, faster, less flaky. Use `page.route()` to
block images and fonts, which typically cuts page time substantially.

**`Camoufox`** — Firefox build hardened against fingerprinting, for when a stock headless
browser is detected. Heavier than Playwright; justified only when fingerprinting is the
demonstrated failure.

**`nodriver`** — successor to `undetected-chromedriver`, driving Chrome over CDP without the
usual automation tells.

**`Crawl4AI`** — crawling with LLM-oriented output (clean markdown, structured extraction).
Useful when the destination is a RAG pipeline rather than a database.

---

## JavaScript / TypeScript

**`Crawlee`** — the strongest all-in-one Node option: unified HTTP and browser crawlers,
autoscaling, proxy rotation, storage. Closest Node equivalent to Scrapy.

**`Playwright`** — same engine as the Python binding, first-class in Node.

**`Puppeteer`** — Chrome-focused, still widely used; Playwright is the better default for new
projects given cross-browser support.

**`got-scraping`** — HTTP client that mimics browser header ordering and TLS characteristics.
The Node analogue of `curl_cffi`.

**`cheerio`** — jQuery-style server-side HTML parsing.

---

## Go

**`Colly`** — fast, simple crawling framework with built-in rate limiting and caching. Excellent
throughput per unit memory for large static crawls.

**`chromedp`** — CDP driver for when JS rendering is required.

---

## Parsing and extraction

**`selectolax`** (Python) — CSS selection over a C parser, several times faster than
BeautifulSoup. Preferred for volume.

**`BeautifulSoup`** — forgiving and readable; fine below high volume.

**`lxml`** — when XPath is needed.

**Structured data first.** Before writing selectors, check for `application/ld+json`,
`__NEXT_DATA__`, or an `og:` meta block. Sites publish these deliberately for machine
consumption, and they break far less often than CSS selectors do. A JSON-LD `Product` block
gives you name, price, and availability already typed — that is strictly better than three
brittle selectors.

**Look for the underlying API.** A client-rendered page fetches its data from somewhere. Open
the network tab, find the XHR, and call that endpoint directly. It usually returns clean JSON,
costs one request instead of a full page render, and changes less often than markup. This is
the highest-value five minutes in most scraping projects.

---

## Operational concerns

**Rate limiting.** Honour `Crawl-delay` from robots.txt when present. Absent that, one request
per second per domain is a defensible default, and concurrency of 1–2 per host. Scrapy's
`AutoThrottle` handles this adaptively. Respect `Retry-After` on 429 rather than retrying blind.

**Caching.** Cache raw responses during development (`requests-cache`, Scrapy's `HTTPCACHE`).
Re-fetching a page because a selector was wrong wastes the origin's bandwidth as well as yours.

**Identification.** Set a User-Agent naming the crawler and a contact URL. Operators who can
identify you will often whitelist rather than block, and it converts an adversarial situation
into a conversation.

**Robots and terms.** `robots.txt` expresses machine-readable intent; terms of service express
legal intent. Neither is optional context. When they conflict with a business need, that is a
question for the site operator or a lawyer, not something to route around in code.

**Proxies.** Rotating residential proxies are standard commercial practice for scale, but note
what the block is telling you: if a site blocks datacenter IPs specifically, it has expressed a
preference about automated access. Weigh that before escalating.

**Personal data.** Public visibility is not the same as permission to collect and store. If the
content includes personal data, GDPR and similar regimes apply regardless of whether scraping
the page was technically easy.
