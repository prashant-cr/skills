# Scoring rubric

Read this when scoring the six dimensions and converting them into a verdict.

## Contents

- [What the score is for](#what-the-score-is-for)
- [The scale](#the-scale)
- [Weights](#weights)
- [1. Network and usage](#1-network-and-usage)
- [2. Value capture](#2-value-capture)
- [3. Supply and tokenomics](#3-supply-and-tokenomics)
- [4. Liquidity and market structure](#4-liquidity-and-market-structure)
- [5. Security and dependencies](#5-security-and-dependencies)
- [6. Team, funding and durability](#6-team-funding-and-durability)
- [Capping rules](#capping-rules)
- [From score to verdict](#from-score-to-verdict)
- [The near-term verdict](#the-near-term-verdict)

## What the score is for

To force the analysis to be explicit and comparable, and to make disagreement productive. A reader
who thinks you are wrong should be able to point at a dimension and say why.

It is not a price target and it is not a decision. The decision is the score plus the position size,
and the size comes from the person's loss capacity rather than from the score.

Score against evidence you fetched in this session. Reputation is not a score, and a well-known name
scoring well on nothing checkable is exactly the failure this rubric is meant to prevent.

## The scale

| Score | Meaning |
| --- | --- |
| 9-10 | Best in the asset class on this dimension. Rare, and needs strong evidence |
| 7-8 | Clearly good, verified, with a specific reason |
| 5-6 | Adequate. Works, nothing distinguishing |
| 3-4 | Weak. A real problem a buyer should know about |
| 1-2 | Broken or absent. Triggers the cap below |
| 0 | Actively dangerous |

**Use the whole range.** Everything landing at 6 or 7 means the analysis is hedging, and a scorecard
that cannot distinguish between assets is doing no work. If you cannot verify a dimension, say so and
score it low rather than assigning a comfortable middle number — an unknown is not an average.

## Weights

| Dimension | Weight | Why |
| --- | --- | --- |
| Value capture | 25% | Determines whether network success reaches a holder at all |
| Supply and tokenomics | 20% | Dilution is the most reliable destroyer of returns here |
| Network and usage | 20% | Whether anything real is happening |
| Security and dependencies | 15% | Tail risk that takes the whole position |
| Liquidity and market structure | 10% | Whether a gain can become money |
| Team, funding and durability | 10% | Survival through a bear market |

Value capture is weighted highest because it is the bridge between a good project and a good
investment, and it is the most frequently missing. Show the weighted arithmetic so the total is
reproducible.

## 1. Network and usage

Is anyone using this for anything, and is that growing?

**Look at:** active addresses and the trend, transaction counts, fees actually paid, TVL where
relevant, whether usage survived the end of any incentive programme.

**High:** sustained organic growth, fees paid without incentives, usage that persisted after rewards
were cut.
**Low:** activity that tracks emissions exactly, flat or falling addresses, a chain with negligible
fees, "partnerships" with no measurable throughput.

Be sceptical of address counts, which are cheap to manufacture. Fees paid are harder to fake because
they cost real money.

## 2. Value capture

Does owning the token entitle you to anything? See `references/tokenomics.md` for the mechanisms.

**High:** fees flow to holders or stakers, burn from genuine usage, yield paid from revenue rather
than issuance, structural requirement to hold or spend the token.
**Low:** governance over nothing consequential, rewards paid purely from new supply, a fee switch
that exists on paper and has never been enabled, "utility" a stablecoin would serve better.

A 2 or below here caps the total, because a network whose token captures nothing is not an investment
regardless of how good the network is. That is the distinction this dimension exists to enforce.

## 3. Supply and tokenomics

Run `tokenomics_math.py`; do not eyeball it.

**High:** most supply circulating, low FDV multiple, no large cliffs ahead, modest or negative net
issuance, distribution not concentrated.
**Low:** FDV several times market cap, a large unlock inside 90 days, double-digit inflation, top-10
wallets holding most of the supply, no published schedule.

## 4. Liquidity and market structure

Can a position be exited at something like the quoted price?

**High:** listed on several major venues, deep books, tight spreads, volume a healthy share of market
cap.
**Low:** one venue or one pool, volume under about 0.5% of market cap, wide spreads, implausible
turnover suggesting wash trading.

Size the assessment against the *intended position*. Adequate liquidity for $500 and for $50,000 are
different findings, and this is where a rating becomes personal.

## 5. Security and dependencies

What could take the whole position irrespective of price?

**Look at:** contract control and upgradeability, audit findings and whether they were fixed, bridge
exposure, oracle design, custody assumptions, the security of the underlying chain, incident history
and how it was handled.

**High:** immutable or timelocked contracts, credible audits with findings resolved, minimal bridge
and oracle dependency, a clean or well-handled incident record.
**Low:** live admin keys, unverified source, heavy bridge dependency, a history of exploits,
concentrated custody.

Bridges deserve specific attention — they have been the single largest source of catastrophic loss in
this asset class, and an asset that only exists on the far side of one inherits that risk.

## 6. Team, funding and durability

Does this survive two years of falling prices?

**High:** identified team with relevant track record, funded runway, shipping consistently, survived a
previous bear market.
**Low:** anonymous team with privileged access, no visible development, treasury held entirely in its
own token, dependent on continuous new inflows.

A treasury denominated in the project's own token is not a runway. It falls exactly when it is needed.

## Capping rules

These exist because the dimensions are not independent, and averaging hides the failures that matter
most.

- **Any dimension at 2 or below caps the total at 4/10.** A single broken leg is not offset by strong
  ones.
- **Value capture at 3 or below caps the total at 5/10**, however good the network.
- **A terminal red flag means no rating at all** — not a low score. See `references/red-flags.md`.
  A number invites comparison and someone will act on it.
- **Unverifiable data caps the total at 6/10.** You cannot rate what you could not check, and
  confident scoring on missing evidence is worse than a hedged score.

State when a cap is applied and why. It is usually the most informative line in the report.

## From score to verdict

For the long-term hold verdict:

| Weighted score | Verdict |
| --- | --- |
| 8.0+ | Buy — strong on the dimensions that matter |
| 6.5 to 7.9 | Accumulate — good, size it properly |
| 5.0 to 6.4 | Hold — fine if owned, not compelling to add |
| 3.5 to 4.9 | Avoid — identifiable problems |
| Below 3.5 | Avoid — do not own this |

The verdict is incomplete without the position size. "Buy" at 15% of net worth and "buy" at 1% are
different recommendations, and in this asset class the difference between them matters more than the
difference between a 6 and an 8.

## The near-term verdict

Scored separately, on positioning rather than quality, because a good asset can be a bad entry.

**Look at:** distance from the recent high and from the all-time high, how far it has run in the last
week and month, perpetual funding rates and whether longs are paying to hold, whether an unlock sits
just ahead, and whether the move happened on real volume.

**Wait** is the right call when the asset has run hard on positive funding into a known unlock.
**Buy now** requires the entry to be unremarkable rather than obviously extended.

Say plainly that this half is lower confidence. Nobody can tell you what a price will do next month,
and a near-term view stated with the same certainty as a tokenomics finding is misleading about which
part of the analysis is solid.
