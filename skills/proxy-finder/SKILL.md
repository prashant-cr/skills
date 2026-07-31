---
name: proxy-finder
license: MIT
description: Works out what proxy or scraping infrastructure a specific site actually needs and what it will really cost per month — probes the target for its bot-defence posture and page weight, checks robots.txt for the paths you want, then prices every option including the ones that are not proxies at all (official API, scraping API, data vendor) on total cost of ownership with retries and engineering time included. Fetches vendor pricing live and refuses to rank a price it could not verify, because proxy rates change constantly. Use whenever the user asks which proxy or proxy provider to use for a site, wants the cheapest or most reliable proxies, asks about residential versus datacenter versus mobile IPs, rotating IPs, proxy pricing per GB, scraping APIs or unblockers, says their scraper is getting blocked and asks what to buy, wants to compare proxy vendors or cut proxy costs, or asks what infrastructure a scraping project will need and what the monthly bill looks like.
---

# Proxy finder

Works out what a specific site actually requires, prices every route to the data including
the ones that are not proxies, and tells you the cheapest thing that genuinely works.

**Scope note, because "check the site's security" is ambiguous.** This examines a site's
**bot-defence posture** — what will block an automated client, how it responds to plain requests,
what its robots.txt permits, how heavy its pages are. That is a scraping-feasibility question. It
is not a vulnerability assessment, and this skill does not probe for weaknesses, test inputs, or
look for exploitable flaws in someone else's site. If that is what you need, it is a different job
requiring the site owner's written authorisation.

## The one idea that organises everything below

**The cheapest proxy is the weakest one that is not blocked — and quite often the answer is not a
proxy at all.**

Two failures follow from getting this wrong, and they are not symmetrical:

- **Under-buying is loud.** Datacenter IPs against a protected site fail immediately, you see it,
  you fix it. Annoying, cheap, self-correcting.
- **Over-buying is silent.** Residential proxies work on everything, so nobody ever discovers that
  datacenter IPs at a tenth of the price would have worked fine. The bill just arrives, forever.

Almost everyone lands on the expensive side, because the expensive option is the one that always
works and nobody gets fired for buying it. The job here is to find the floor rather than confirm
the ceiling — start from "do you need anything at all" and add capability only where the site
actually forces it.

The second half matters as much. For a hard-protected site the honest comparison usually is not
between two proxy vendors, it is between proxies-plus-two-weeks-of-fingerprint-work and a scraping
API that costs more per request and needs an afternoon. Price your own time and the ranking often
inverts.

## Check what you are allowed to do first

This is quick and it changes the answer, so it comes before any shopping.

```bash
python3 scripts/site_probe.py https://target.example/products
```

It reads robots.txt, resolves the rules for your target path, and **refuses to probe a path the
site disallows** unless you pass `--force`. That refusal is the point: if robots.txt says no, the
question "which proxy gets me in" has stopped being a technical one, and answering it with
infrastructure is answering the wrong question.

Beyond robots.txt, three things are worth establishing before spending money:

- **Is the data personal?** Names, contact details, profiles. Different rules apply in most
  jurisdictions and "it was public" is not the defence people assume it is.
- **Is it behind a login?** Authenticated scraping breaks terms far more clearly than public-page
  scraping, and a proxy does not change that.
- **Have you already been asked to stop?** A specific block aimed at you — a cease and desist, an
  account ban, a targeted rule — is a different situation from generic bot defence. Rotating
  around it is not a tooling decision.

For ordinary public data on allowed paths, note the terms, note the crawl-delay if one is
published, and get on with it. `references/vendor-evaluation.md` covers keeping your own conduct
defensible: honest identification, rate limits, caching, honouring the delay.

## Workflow

### 1. Measure the site rather than assuming it

The probe returns the two numbers the whole budget hangs on:

- **Whether plain requests already succeed.** If they do at your real volume, the right proxy
  spend may be zero. This is the most skipped check and the most valuable, because it is the only
  one that can remove the entire line item.
- **Bytes per page.** Residential proxies bill per gigabyte, so page weight *is* the bill. The
  probe sizes a sample of subresources and reports what share is HTML versus images, fonts and
  CSS. That share is a lever you control.

It also reports the edge/WAF vendor and any challenge markers. For deep bot-detection
fingerprinting — CAPTCHA variants, exact vendor behaviour, rendering requirements — use the
`scrape-feasibility-audit` skill and bring its findings here rather than duplicating that work.

A caution the probe states itself: succeeding three times from one IP does not mean succeeding
100,000 times from a datacenter range. Many sites tolerate low volume and start blocking on
pattern, not on the first request. Treat an open result as "no evidence you need proxies yet",
and validate at volume before deciding.

### 2. Ask whether a proxy is the right purchase at all

Before comparing vendors, check the routes that skip the problem. `references/alternatives.md`
covers these properly; the short version:

- **An official API.** Frequently exists, frequently unknown to the person about to build a
  scraper. Usually free or cheap, always more stable, and it ends the blocking problem entirely.
  The catch is coverage — check it exposes the fields you actually need before celebrating.
- **Sitemaps, RSS, and bulk exports.** Cheap, sanctioned, often sufficient for change detection.
- **A scraping API or unblocker.** Someone else owns the proxy pool and the fingerprinting. Higher
  unit price, near-zero engineering, and the block risk moves to them — which is worth real money
  on a hard site.
- **Buying the data.** For common datasets a vendor may already sell it, and the total is often
  lower than building.
- **Not collecting it.** Sometimes the requirement dissolves under questioning.

### 3. Match proxy type to what the site actually enforces

Only if a proxy is the right shape of answer. `references/proxy-types.md` has the detail; the
principle is to climb this ladder only as far as the site forces you, because each rung is
roughly an order of magnitude more expensive than the last:

| Type | Typical use | Cost shape |
| --- | --- | --- |
| No proxy | Site does not block you | Free |
| Datacenter | Volume and rate spreading, no serious bot defence | Cheapest per GB, or flat per IP |
| ISP / static residential | Residential trust with datacenter stability | Middle, usually per IP |
| Residential rotating | Real anti-bot, geo-specific content | Expensive per GB |
| Mobile | Only where mobile ASNs are specifically trusted | Most expensive by a distance |

Geography is a separate axis and a separate cost. Country-level targeting is usually included;
city or ASN-level targeting often is not. Only pay for it if the content genuinely differs by
location — verify that before assuming it.

### 4. Get real prices, and refuse to guess

Proxy pricing changes constantly and published rates are heavily conditioned on volume tier and
commitment. Any figure recalled rather than read is likely wrong, and a wrong $/GB silently
decides the entire comparison.

So fetch the pricing page for each candidate at run time, record the URL and the timestamp, and
where a price is only available on request, mark it unverified rather than filling in a plausible
number. `cost_model.py` enforces this — an offering without `source_url` and `fetched_at` is
listed but refused a ranking.

If a vendor's pricing page cannot be read, say so and recommend getting a quote. "I could not
verify this one" is a useful, honest output. An invented rate is not.

### 5. Price the same job through every option

```bash
python3 scripts/cost_model.py --example > job.json   # fill from the probe and the fetched prices
python3 scripts/cost_model.py job.json --months 12
```

It normalises per-GB, per-IP, per-request, per-success and flat pricing into one monthly number
for one job, and includes two things that decide the ranking and are usually left out:

- **Retries.** A blocked attempt still consumes bandwidth on per-GB pricing. A 40% block rate is a
  67% surcharge that appears nowhere on the rate card. This is also why per-*success* pricing can
  beat a cheaper per-request rate — the vendor absorbs the failures.
- **Engineering time, at your rate.** Setup and monthly upkeep. This is what makes a scraping API
  beat cheap proxies on a hard site, and it is invisible if you compare sticker prices.

It also separates out options whose block rate makes them non-viable rather than ranking them,
because a mostly-blocked option looks *cheap* on per-GB pricing — a blocked response is a small
response — and that is a trap worth naming explicitly.

Run it over a realistic horizon. Setup cost amortises, so a one-month view flatters whatever needs
least configuration and can invert the answer.

### 6. Trial before committing

Never buy an annual plan on a rate card. Buy the smallest amount possible and measure the success
rate on **your** target, at **your** concurrency, from the geography you need. Vendors quote pool
sizes and uptime; neither predicts whether their IPs work on the one site you care about.

`references/vendor-evaluation.md` has the trial protocol and the contract traps worth knowing —
bandwidth rounding, expiring data, minimum commitments, what "99.9% uptime" is measuring.

## Output format

```
## What the site enforces
[robots.txt verdict for the target paths, access result from plain requests, edge/WAF,
 crawl-delay, page weight and the HTML share. Say plainly if no proxy appears necessary.]

## What you are buying, if anything
[The recommendation, and the reason the tier below it is insufficient. If the answer is
 an official API or no purchase, lead with that.]

## Costed comparison
[The table from cost_model.py at a realistic horizon: block rate, infra, engineering,
 total. Non-viable options listed separately, not ranked. Unverified prices marked.]

## Ways to cut this
[The bandwidth lever with its number, caching, concurrency and delay, session reuse.]

## Before you pay
[The trial to run, what success rate to require, and the contract terms to check.]
```

Show the timestamp on every fetched price. A price without a date is not a price.

## Failure modes to avoid

- **Recommending proxies without checking whether they are needed.** Measure first. The best
  outcome available is deleting the line item.
- **Quoting a price from memory.** Rates move and are volume-conditioned. Fetch it or mark it
  unverified.
- **Comparing sticker prices across pricing models.** Per-GB against per-request is not a
  comparison until both are priced through the same job.
- **Ignoring retries.** They are pure surcharge on per-GB billing and they scale with the block
  rate you were trying to avoid.
- **Ignoring your own time.** Two weeks of fingerprint work dwarfs a year of the price difference
  it was meant to save.
- **Defaulting to residential.** It always works, which is exactly why it hides that something
  cheaper would have too.
- **Buying an annual plan untested.** Pool size and uptime say nothing about your target site.
- **Treating a robots.txt disallow as an obstacle to route around.** It is the site declining. Say
  so and stop, rather than answering a question about permission with a question about tooling.
- **Building a scraper when an API exists.** Check first. It is the single most common avoidable
  cost in this whole area.

## Reference files

- `references/proxy-types.md` — what each proxy type is, when a site genuinely forces the next
  rung, pricing models and their traps.
- `references/alternatives.md` — read before recommending any proxy. Official APIs, scraping APIs,
  data vendors, and when to buy nothing.
- `references/cost-levers.md` — bandwidth reduction, caching, concurrency, retry policy and
  session reuse. Usually beats switching vendors.
- `references/vendor-evaluation.md` — reliability signals, the trial protocol, contract traps, and
  keeping your own crawling conduct defensible.
