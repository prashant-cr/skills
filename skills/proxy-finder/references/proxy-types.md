# Proxy types and pricing models

Read this when a proxy is genuinely the right shape of answer and you need to pick the tier.

## Contents

- [Climb only as far as the site forces](#climb-only-as-far-as-the-site-forces)
- [Datacenter](#datacenter)
- [ISP and static residential](#isp-and-static-residential)
- [Residential rotating](#residential-rotating)
- [Mobile](#mobile)
- [Geography](#geography)
- [Pricing models](#pricing-models)
- [Rotation and sessions](#rotation-and-sessions)
- [What proxies do not fix](#what-proxies-do-not-fix)

## Climb only as far as the site forces

Each rung is roughly an order of magnitude more expensive than the one below, and the higher rungs
work on everything — which is exactly the problem. Because residential proxies succeed everywhere,
buying them tells you nothing about whether datacenter IPs would also have succeeded. The
overspend is permanent and invisible.

So test downward, not upward. Start at the cheapest tier that could plausibly work, measure the
success rate on your actual target, and move up only when the measurement forces you to. This
takes an afternoon and routinely saves an order of magnitude.

## Datacenter

IPs belonging to hosting providers. Cheap, fast, plentiful, and trivially identifiable as
non-residential because the ASN gives them away.

**Works for:** sites with no bot defence, spreading rate limits across IPs, high-volume collection
where the target does not care, geo-unlocking where only country matters and the site does not
inspect ASN reputation.

**Fails on:** anything running Cloudflare Bot Management, DataDome, Akamai Bot Manager, Kasada,
HUMAN, or similar at anything above their loosest setting. These maintain ASN reputation lists and
datacenter ranges are the first thing they score down.

**Price shape:** cheapest per GB, or a flat fee per IP per month. Per-IP pricing is often the
better deal at volume, because bandwidth stops mattering — a fixed pool of IPs you own for the
month has no marginal cost per byte, which changes the whole optimisation.

Test these first, always. The failure is immediate and unambiguous, so the test is cheap.

## ISP and static residential

IPs registered to consumer ISPs but hosted in datacenters. Residential ASN reputation with
datacenter stability and speed.

**Works for:** sites that check ASN reputation but not much else. A good middle rung, and often the
sweet spot that gets skipped because people jump straight from datacenter to rotating residential.

**Price shape:** usually per IP per month rather than per GB, which makes them dramatically cheaper
than rotating residential for bandwidth-heavy work. If you are moving a lot of bytes through a
modest number of identities, this tier deserves a serious look.

**Limitation:** the pool is small and static. Fine for a few dozen persistent identities, wrong
for anything needing thousands of distinct IPs.

## Residential rotating

Real consumer IPs, usually sourced through SDKs embedded in apps or through bandwidth-sharing
schemes. Large pools, rotating per request or per session.

**Works for:** most protected sites, geo-specific content, anything where the target scores ASN
reputation heavily.

**Costs:** per GB, and this is where bandwidth becomes the entire bill. At typical rates a
page-weight difference between full-asset loading and HTML-only is the difference between two very
different invoices. See `references/cost-levers.md` — it is usually a bigger lever than the vendor
choice.

**Also slower.** Traffic routes through a consumer connection, so latency is higher and variance is
much higher. Factor that into concurrency planning; a job that takes twice as long may need twice
the concurrency, which interacts with rate limits.

**Sourcing is worth asking about.** Pools built from users who did not meaningfully consent are a
real category. A vendor that cannot explain where its IPs come from is telling you something, and
it is a reputational exposure for you as well as an ethical one.

## Mobile

IPs from mobile carrier networks. The most trusted tier, because carrier-grade NAT means thousands
of real users share an address and blocking one blocks many — so sites are reluctant to.

**Works for:** the small set of targets that specifically trust mobile ASNs, and mobile-app APIs
that expect carrier addresses.

**Cost:** the highest by a wide margin, frequently several times residential. Slow, and pools are
comparatively small.

Genuinely necessary rarely. If mobile is being recommended, ask what was measured that ruled out
residential — the answer is often nothing.

## Geography

A separate axis from type, and separately priced.

- **Country-level** targeting is usually included in the base rate.
- **City, state or ASN-level** targeting is frequently a premium tier or a higher per-GB rate.

Only pay for it if the content genuinely differs at that granularity. Verify before assuming:
fetch the target through two different countries and compare. Prices, availability and language
often vary by country; they rarely vary by city, and paying for city-level targeting you do not
need is a common quiet overspend.

## Pricing models

The reason cross-vendor comparison needs a script rather than a glance:

| Model | Bills on | Suits | Trap |
| --- | --- | --- | --- |
| Per GB | Bytes transferred | Light pages, low volume | Retries and assets are billable; a heavy page is a heavy bill |
| Per IP per month | Pool size | Bandwidth-heavy work | Idle IPs still bill; small pools get burned |
| Per request | Attempts | Predictable light traffic | You pay for blocked attempts too |
| Per successful request | Successes only | Hard sites | Higher unit rate, but the vendor carries the block risk |
| Flat monthly | Nothing marginal | Steady predictable load | Overage rates are where the margin lives — read them |

**Per-success is the one people undervalue.** On a site with a 40% block rate, per-request pricing
means paying for 1.67 attempts per useful page. Per-success at a higher headline rate can be
cheaper *and* removes the variance. `cost_model.py` handles this arithmetic because it is exactly
the comparison that gets eyeballed wrong.

Also read the fine print on: **bandwidth rounding** (per-request rounding to the nearest 100KB
inflates small requests substantially), **expiry** (prepaid GB that vanishes monthly), **minimum
commitments**, and **overage rates**, which are often multiples of the base rate.

## Rotation and sessions

- **Rotate per request** for broad crawling of independent pages. Maximum IP diversity.
- **Sticky sessions** — the same IP for minutes — for anything stateful: logins, carts, multi-step
  flows, pagination that depends on a server-side cursor.

Rotating mid-session is a classic self-inflicted block: the site sees a session jump countries
between requests, which no real user does. If pagination or a flow breaks under rotation, this is
usually why, and the fix is a sticky session rather than a better proxy.

Session duration is often billable or tier-limited. Check it against what your flow needs.

## What proxies do not fix

Worth being explicit, because it is the most expensive misunderstanding in this area. **A proxy
changes your IP. It changes nothing else.**

Modern bot detection scores TLS fingerprint (JA3/JA4), HTTP/2 frame ordering, header order and
casing, browser API surface, canvas and font fingerprints, mouse and timing behaviour, and cookie
and challenge state. A perfect residential IP presenting a Python `requests` TLS signature is still
obviously automated.

So if a site blocks you on fingerprint, buying better proxies produces the same block at a higher
price — and this is a genuinely common way to waste a month. The tell is that success rate barely
moves when you upgrade tier. When that happens, the problem is the client, not the address: the
fix is a real browser engine or a scraping API that handles it, not a bigger pool.

Diagnose before upgrading. One trial on a cheaper tier plus one on a more expensive tier, measured
on the same target, answers this in an afternoon.
