# Red flags and the rug screen

Read this before rating anything outside the top 100, under a year old, under roughly $50M market
cap, unlisted on a major venue, or found through social media.

## Contents

- [Why this comes before the rating](#why-this-comes-before-the-rating)
- [Terminal flags](#terminal-flags)
- [Contract control](#contract-control)
- [Liquidity traps](#liquidity-traps)
- [Holder concentration](#holder-concentration)
- [Fake activity](#fake-activity)
- [Social and team signals](#social-and-team-signals)
- [Identity and impostors](#identity-and-impostors)
- [How to report a failed screen](#how-to-report-a-failed-screen)

## Why this comes before the rating

For a token at this end of the market, "is it undervalued" is the wrong question and answering it
does harm. The prior is that most tokens ever launched are worth approximately nothing now, and a
meaningful share were designed that way from the start. A tidy 6/10 on a honeypot is worse than
refusing to score it, because the score is what the user will act on.

So the screen is a gate, not a section of the report. If a terminal flag is present, the analysis
ends at **do not buy** and no rating is produced. That is a complete answer, not a failure to
deliver one.

## Terminal flags

Any one of these ends it. There is no offsetting quality.

- **Mint authority still active.** The deployer can create unlimited new tokens, so any holding can
  be diluted to nothing at will. Nothing else matters.
- **Unrestricted upgradeable contract.** An admin key that can change the token's behaviour after
  you buy makes every other check provisional.
- **Sells blocked or taxed punitively.** The classic honeypot: buying works, selling reverts or
  costs a large share. Check that a sell path actually executes, not just that a buy does.
- **Liquidity not locked, or trivially small.** If the deployer can withdraw the pool, they can end
  the market in one transaction.
- **Blacklist or allow-list functions** that let the owner freeze specific holders.
- **Proxy contract pointing at an unverified implementation.** You cannot review what you cannot
  read.

## Contract control

The questions worth answering, in order of how much they matter:

1. **Who can mint?** Renounced, burned, or a multisig with published signers is acceptable. A single
   EOA is not.
2. **Is the contract upgradeable, and by whom?** Timelocks and multisigs are meaningful mitigation;
   an unlocked single-key upgrade is not.
3. **Is the source verified** on the relevant explorer? Unverified is disqualifying for anything
   asking to be taken seriously.
4. **Is there a timelock on privileged functions?** Even 48 hours changes the risk materially,
   because it gives holders a window to exit.
5. **Has it been audited, by whom, and were the findings fixed?** An audit is a document, not a
   guarantee — read what it actually says. "Audited" with no linkable report means nothing.

Automated scanners are a useful first pass and are not conclusive in either direction. A clean
scanner result on a contract nobody can read is not clean.

## Liquidity traps

Liquidity determines whether a paper gain can become money.

- **Pool depth against your intended position.** If your exit is a large share of the pool, the
  price you get is not the price you see. Size against depth, not against market cap.
- **Locked, and for how long?** A lock expiring next month is a countdown, not a protection. Get
  the date.
- **How many venues?** A single pool on one DEX is a single point of failure, and a delisting or a
  drained pool ends it.
- **Spread and slippage on a realistic size.** Quote the actual slippage for the position being
  considered rather than the headline price.
- **`live_data.py` reports 24h volume as a share of market cap.** Under about 0.5% is thin enough
  that exiting will move the price against you, and that belongs in the report.

## Holder concentration

- **Top 10 non-contract wallets as a share of supply.** Above roughly 50% for a token claiming to be
  distributed, ask who they are. Exchange and bridge contracts are not a concern; unlabelled
  wallets funded at launch are.
- **Wallets that received tokens for nothing.** Airdrops and team allocations have a different cost
  basis than yours and behave differently on the way up.
- **Clusters funded from one source.** Fifty wallets funded from the same address are one wallet
  wearing fifty hats, and they defeat "holder count" as a decentralisation measure.
- **How much sits on exchanges?** Large exchange balances are supply that can hit the market without
  an on-chain warning.

## Fake activity

Cheap to manufacture, and it is manufactured constantly:

- **Volume implausible against market cap.** `live_data.py` flags turnover above 2x market cap in a
  day. Real assets rarely do that; wash trading does it routinely.
- **Volume implausible against holders.** Enormous volume with a few hundred holders is not a
  market, it is a small number of addresses trading with themselves.
- **Uniform trade sizes and regular timing** in the trade history. Organic flow is ragged.
- **Follower counts against engagement.** A hundred thousand followers and eleven replies per post
  is purchased distribution.
- **Coordinated identical praise** appearing within a short window across accounts with no history.
- **Paid listings and "trending" placement** presented as organic ranking.

## Social and team signals

Not terminal on their own, but they compound:

- Anonymous team with no verifiable prior work. Anonymity is common and legitimate in this space;
  anonymity *plus* privileged contract access is not.
- No code repository, or a repository with no meaningful commits.
- A roadmap of marketing milestones rather than shipped functionality.
- Guaranteed or implied returns — anyone promising a yield without explaining where it comes from is
  either paying it from deposits or lying about it.
- Countdown pressure, "last chance", limited allocations. Urgency is a sales technique, and it is
  aimed at preventing exactly the checks on this page.
- Influencer promotion with undisclosed payment.
- A community where asking a technical question gets you removed.

## Identity and impostors

Worth separating out because it defeats every other check silently: **you can run a perfect analysis
on the wrong token.**

- Ticker reuse is deliberate. A token with the symbol of a real project may have no relationship to
  it.
- Get the contract address from the **project's own site or documentation**, never from a search
  result, a reply, or a screenshot.
- Cross-check the market cap rank. An impostor is usually unranked or ranked far below where the
  real project sits.
- Beware near-identical names, extra characters, and homoglyphs.
- On a chain with multiple deployments, confirm you have the canonical one and not a bridged or
  wrapped variant with different risk.

`live_data.py --search` shows rank alongside each match precisely so this collision is visible.

## How to report a failed screen

Name the check, the evidence, and the consequence. Compare:

> This token looks risky and I would avoid it.

with:

> Do not buy. The mint authority on the contract is still held by a single wallet, which means the
> deployer can create new tokens at any time and dilute your holding to nothing. That is not a
> risk that a good product would offset, so I stopped here rather than rating it.

The second is checkable, teaches the reader what to look for next time, and does not rely on them
trusting your judgement. It is also harder to argue with, which matters — someone who has already
decided to buy will push back, and a specific verifiable fact holds where a general caution does not.

If the user pushes back after a terminal flag, restate the specific finding once and let them
decide. It is their money. Do not soften a verified fact into a maybe, and do not produce the
rating you just declined to give.
