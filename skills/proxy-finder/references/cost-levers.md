# Cutting the bill

Read this before negotiating with a vendor. These levers routinely beat the discount you would
have argued for, and most of them are a line of configuration rather than a project.

## Contents

- [Bandwidth is the bill](#bandwidth-is-the-bill)
- [Block assets](#block-assets)
- [Do not render when you do not have to](#do-not-render-when-you-do-not-have-to)
- [Fetch less often](#fetch-less-often)
- [Cache aggressively](#cache-aggressively)
- [Reduce the block rate](#reduce-the-block-rate)
- [Slow down](#slow-down)
- [Mix tiers](#mix-tiers)
- [Compression and encoding](#compression-and-encoding)
- [Order of attack](#order-of-attack)

## Bandwidth is the bill

On per-GB pricing — which is how residential and most rotating proxies bill — the invoice is
literally `bytes × rate`. There are only two variables and most people negotiate the wrong one.

Vendor negotiation might get 10-20% off the rate at a volume commitment. Loading only the HTML
instead of the full page routinely removes 60-90% of the bytes. That is not a better discount, it
is a different order of magnitude, and it does not require a sales call.

`site_probe.py` reports the HTML share of total page weight so this is a measured number for your
specific target rather than a rule of thumb.

## Block assets

The single largest lever. A typical page is mostly images, fonts, CSS, analytics and ad scripts,
and if you are parsing HTML you need none of it.

In a headless browser, intercept requests and abort by resource type — images, media, fonts,
stylesheets, and usually scripts you have identified as third-party. In a plain HTTP client you
get this free: you only fetch what you request, which is one reason plain HTTP is dramatically
cheaper than browser automation on per-GB pricing.

Two cautions. Some sites lazy-load content into the DOM via JS that depends on a script you
blocked, so verify the data still appears. And blocking stylesheets can change layout-dependent
extraction if you are selecting on rendered position rather than DOM structure.

## Do not render when you do not have to

Browser automation is expensive twice: it pulls the whole page, and it is slow, which means more
concurrency for the same throughput.

Before reaching for it, check whether the data is in the initial HTML, in an embedded JSON blob
(`__NEXT_DATA__`, `__NUXT__`, a state hydration script), or available from the JSON endpoint the
page itself calls. Very often it is, and the `structured-data-extraction` skill is built for
exactly this. Hitting the underlying JSON endpoint directly is usually the cheapest and most
robust option available — smaller payloads, no parsing, no rendering.

Render only the pages that genuinely require it, rather than routing the whole crawl through a
browser because some of it does.

## Fetch less often

Cost scales linearly with frequency, and frequency is usually chosen by habit rather than by need.

- **What decision does this data change, and how often does that decision get made?** Hourly
  collection feeding a weekly report is 168x the necessary cost.
- **Tier your targets.** Popular or volatile pages hourly, the long tail weekly. A uniform refresh
  rate across a catalogue is nearly always wrong.
- **Use the sitemap's `lastmod`.** Fetch only what changed. On a large catalogue this alone can cut
  volume by an order of magnitude.
- **Use conditional requests.** `If-Modified-Since` and `If-None-Match` return a 304 with almost no
  body, which on per-GB pricing is close to free. Widely supported and widely ignored.

## Cache aggressively

Cache everything you fetch, keyed by URL, with the timestamp. Then:

- Re-runs during development cost nothing. This matters more than it sounds — most bandwidth
  during a project's first weeks is re-fetching the same pages while fixing parsers.
- A parser change reprocesses from cache instead of re-crawling.
- A failed run resumes rather than restarting.

Disk is orders of magnitude cheaper than proxy bandwidth. Cache the raw response, not the parsed
output, so a parser bug does not cost a re-crawl.

## Reduce the block rate

Every blocked request is billed and delivers nothing. On per-GB pricing a 40% block rate is a 67%
surcharge, which is usually larger than the gap between vendor tiers.

Cheaper than upgrading tier: fix the client fingerprint (a real browser engine, or a properly
ordered header set and TLS profile), keep cookies and sessions across requests rather than
arriving fresh every time, honour the crawl-delay, and back off on the first 429 rather than
retrying into a harder block.

**Cap your retries.** Unbounded retry against a site that has decided to block you converts a
failure into an expense, and it is the most common way a bill goes wrong overnight. Retry twice,
then stop and alert.

## Slow down

Rate limiting is not a proxy problem and buying proxies to outrun it is buying your way around a
sign that says "please don't".

If the site publishes a crawl-delay, honour it — `site_probe.py` reports it. If it returns 429s,
that is a request to slow down and it is cheaper to comply than to buy IPs to distribute the same
aggression across. A crawl that takes six hours instead of one, on a schedule nobody is watching,
costs nothing extra and dramatically reduces both your block rate and your chance of being
noticed and specifically blocked.

## Mix tiers

Nothing requires one proxy type for the whole job.

Route the bulk of traffic through the cheapest tier that works for it, and reserve expensive IPs
for the requests that genuinely need them — the protected endpoints, the logged-in flows, the
geo-specific checks. A catalogue crawl might be 95% unprotected listing pages and 5% detail pages
behind a challenge, and paying residential rates for all of it is paying twenty times over for the
95%.

This needs a routing layer, which is real work, so it pays off at volume rather than at small
scale. Price it with `cost_model.py` before building it.

## Compression and encoding

Request `Accept-Encoding: gzip, br` and confirm the vendor bills the compressed size — most do,
some do not, and it is worth asking because HTML compresses to roughly a fifth.

Note that `site_probe.py` deliberately requests identity encoding so its byte counts are
comparable and honest. Your production client should do the opposite.

## Order of attack

Roughly by saving per unit of effort:

1. **Check for an official API.** Can remove the cost entirely. Minutes.
2. **Block assets.** Often 60-90% of bytes. One line of config.
3. **Skip the browser** where the data is in HTML or embedded JSON. Large, moderate effort.
4. **Cache everything.** Removes all re-fetching. Hours.
5. **Fetch only what changed**, via sitemap `lastmod` and conditional requests. Large on big
   catalogues.
6. **Cut frequency to what the decision actually needs.** Often the largest single saving, and
   free — it is a conversation, not a build.
7. **Fix the fingerprint** to cut the block rate. Moderate to hard.
8. **Then** negotiate the rate, or move tier.

Vendor negotiation is last on purpose. It is the lever people reach for first and it moves the
number least.
