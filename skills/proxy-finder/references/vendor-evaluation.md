# Evaluating a vendor, and behaving well

Read this before anyone pays for anything.

## Contents

- [The only test that matters](#the-only-test-that-matters)
- [The trial protocol](#the-trial-protocol)
- [Reliability signals worth checking](#reliability-signals-worth-checking)
- [Marketing claims and what they mean](#marketing-claims-and-what-they-mean)
- [Contract traps](#contract-traps)
- [Where the IPs come from](#where-the-ips-come-from)
- [Verifying prices](#verifying-prices)
- [Crawling conduct](#crawling-conduct)

## The only test that matters

**Success rate on your target, at your concurrency, from your geography.**

Everything else a vendor publishes — pool size, uptime, "99.9% success rate", customer logos — is
either unverifiable or measured on something other than your site. A provider whose IPs are clean
on one retailer may be entirely burned on another, because the target maintains its own reputation
data and the two have no relationship.

This makes benchmark articles and comparison blogs close to worthless for a specific decision.
Most are affiliate-funded, and even the honest ones measured a different target on a different day.
Test it yourself. It takes an afternoon.

## The trial protocol

Most vendors offer a free trial or a small paid tier. Buy the smallest possible amount, never an
annual plan, and run this:

1. **Pick 200-500 representative URLs** from the actual target, spanning the page types you need —
 listing pages and detail pages behave differently.
2. **Run at your real concurrency.** Success at 1 request/second says nothing about 20. Blocking is
   frequently rate-triggered, so the concurrency is part of the test.
3. **Use your real geography.** If you need German results, test German exits.
4. **Measure**, and write the numbers down:
   - success rate (200 with the content actually present, not just a 200)
   - median and p95 latency — p95 is what determines whether your crawl finishes
   - bytes transferred, so you can check the vendor's accounting against your own
   - failure modes: 403 vs 429 vs challenge vs timeout. These mean different things and point at
     different fixes.
5. **Run it twice, hours apart.** Pool quality varies through the day, and a single run at a quiet
   hour flatters everything.
6. **Verify the billing.** Compare their reported usage against your measured bytes. Discrepancies
   here are common and they are the whole basis of the contract.

**Test at least two vendors on the same URL set.** Absolute numbers mean little; the comparison
means everything. Testing one vendor tells you whether it works, not whether you are overpaying.

A "success" that returns a challenge page with HTTP 200 is a failure. Check for your actual
content, not the status code — this is the single most common way a trial produces a flattering
number.

## Reliability signals worth checking

- **Does the trial reproduce twice?** Consistency matters more than a good first run.
- **Latency variance.** A p95 of 30 seconds against a median of 2 will wreck throughput planning
  more than a slightly lower success rate will.
- **Does support answer a technical question?** Ask something specific before buying — how they
  handle sticky sessions, how bandwidth is rounded. The answer, and how long it takes, is a
  reasonable proxy for what happens when something breaks at volume.
- **Is there a status page with real history?** Absence is a mild signal; a status page that has
  never recorded an incident is a stronger and worse one.
- **Documentation quality.** A vendor whose docs cannot explain their own rotation options will not
  be quick to debug yours.

## Marketing claims and what they mean

- **"150 million IPs"** — pool size, which says nothing about how many are clean for your target,
  or how many you can reach concurrently. Effectively decorative.
- **"99.9% uptime"** — their gateway is reachable. Not that requests through it succeed.
- **"99% success rate"** — on their benchmark set, against unspecified targets, at unspecified
  concurrency. Not on yours.
- **"Ethically sourced"** — an assertion. Ask how, specifically, and what the consent flow looks
  like.
- **"Unlimited bandwidth"** — check for fair-use clauses and throttling thresholds in the terms.
- **"Undetectable"** — not a claim anyone can make truthfully. Treat it as a signal about the
  vendor's honesty generally.

## Contract traps

Read the billing terms specifically, because this is where the effective price is set:

- **Bandwidth rounding.** Rounding each request up to 100KB roughly triples the cost of scraping
  small JSON responses. Ask what the rounding unit is.
- **Expiry.** Prepaid bandwidth that expires monthly turns unused capacity into pure loss. Common,
  and rarely prominent.
- **Overage rates.** Frequently several times the base rate. If your volume is variable, the
  overage rate may matter more than the headline.
- **Minimum commitments** and auto-renewal terms, especially on annual plans.
- **Whether failed requests are billed.** They usually are on per-GB and per-request plans, which
  is the retry surcharge.
- **What counts as a "request"** — redirects, retries and sub-resources may each count separately.
- **Refund policy.** Many are no-refund once bandwidth is provisioned, so the trial is your only
  real evaluation window.

## Where the IPs come from

Residential and mobile pools are built from real people's connections, and the sourcing varies from
genuinely consented bandwidth-sharing schemes with clear disclosure to SDKs bundled into free apps
where the consent is buried.

Ask directly how the pool is sourced and what the user-facing disclosure says. A vendor that
answers clearly and specifically is telling you something; a vendor that deflects to "ethically
sourced" without detail is telling you something else.

This is not only an ethical question. Pools built without meaningful consent attract regulatory
attention and get burned faster by targets, so it is also a durability question about the service
you are buying.

## Verifying prices

Fetch the pricing page at the time of the analysis, record the URL and the timestamp, and put both
in the comparison. Rates change, are heavily volume-tiered, and are frequently negotiable at
commitment — so a published rate is a starting point rather than a fact about what you will pay.

Where pricing is "contact us", mark it unverified rather than estimating. `cost_model.py` refuses
to rank an offering without `source_url` and `fetched_at` for exactly this reason: an invented rate
does not announce itself, it just quietly wins or loses the comparison.

For anything at meaningful volume, ask for a quote. Published rates are usually the worst price
available.

## Crawling conduct

Independent of vendor choice, and it protects you more than any proxy does. A crawler that behaves
well is rarely worth blocking specifically, and a specific block is the failure mode no amount of
money fixes.

- **Honour robots.txt**, including the crawl-delay. `site_probe.py` reports both.
- **Identify honestly where you can.** A real user-agent with contact details gets you an email
  before a ban, which is a much better outcome than discovering a block at 3am.
- **Rate-limit yourself** below what the site tolerates rather than up to it.
- **Back off on 429 and 503.** Exponentially. These are explicit requests to slow down.
- **Cache** so you never fetch the same thing twice.
- **Crawl at quiet hours** for the target's timezone where the schedule allows.
- **Take only what you need** — the fields, the pages, the frequency.
- **Stop when asked.** A specific, targeted block or a direct request to stop is a different thing
  from generic bot defence, and routing around it is not a technical decision.

The practical argument for all of this: sites escalate against sources that hurt them. Being cheap
to serve is the most durable anti-blocking measure available, and it costs nothing.
