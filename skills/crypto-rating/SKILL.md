---
name: crypto-rating
license: MIT
description: Rates a crypto asset on live data only and says whether to buy it and at what size — never from remembered prices, because in crypto a stale figure is wrong by a multiple rather than a little. Fetches and cross-checks the current price, market cap, supply and drawdown, screens new or thin tokens for rug and trap patterns before rating anything, does the dilution and unlock arithmetic, scores six dimensions, then turns the user's own capacity for loss into a maximum position size with the crash scenarios shown in money. Gives two separate verdicts, long-term hold and near-term entry, because they frequently disagree. Use whenever the user names a coin or token and asks whether to buy, sell, hold or avoid it, wants a crypto rating, analysis, second opinion or price view, asks how much of something to buy or how much to put in, mentions tokenomics, unlocks, FDV, altcoins, memecoins or whether a token is a scam, or asks about sizing and risk in their crypto portfolio.
---

# Crypto rating

Rates a digital asset on data fetched now, and converts that rating into a decision the specific
person in front of you can act on — including, often, "not at any size".

## Two things make this different from rating a stock

**There are no cash flows.** No earnings, no dividends, no book value, so discounted cash flow and
price-to-earnings have nothing to operate on. What remains is genuinely different: how much the
network is used and what it charges, how many tokens exist and how many are coming, who controls
the supply, and whether the thing survives. Importing equity habits here produces analysis that
sounds rigorous and measures nothing.

**Your training data is actively dangerous here.** A stock's fundamentals drift slowly; a token's
price can double or halve in a month, and every figure that matters is derived from it. A
remembered price silently corrupts the market cap, the dilution maths, the drawdown, and the
position size, while every number still looks plausible on the page.

This is not hypothetical. Run the data script and read what it says about Bitcoin's drawdown from
its high before assuming you know roughly where things stand. Analysts who "roughly remember" the
market are wrong in this asset class in a way they are not wrong about a utility company.

## The one idea that organises everything below

**The rating is not the decision. The position size is.**

Drawdowns of 80% happen to the majors — not to the failures, to Bitcoin and Ethereum. Everything
smaller should be sized on the assumption it goes to zero, because for most tokens ever launched
that is not a tail scenario, it is what happened.

So the useful output is never "this is a 7/10, buy it". Someone who buys the best asset in the
market at a size they cannot hold will sell it at the bottom and take the loss anyway — the asset
was right and the outcome was still bad. What determines whether they get the good outcome is
whether the position is small enough to be boring when it is down 70%.

That is why loss capacity is an input to the verdict rather than a disclaimer at the end of it.

## Never analyse without fetching first

```bash
python3 scripts/live_data.py --search "arbitrum"    # resolve the name to an id
python3 scripts/live_data.py arbitrum
```

It pulls price, market cap, FDV, supply, volume and drawdown from CoinGecko, cross-checks the price
against Binance and Coinbase, stamps the time, and **refuses** when the feed is stale or the
sources disagree. Standard library only.

Read its exit code, because it is the gate:

| Exit | Meaning | What to do |
| --- | --- | --- |
| 0 | Fresh, cross-checked | Proceed |
| 2 | Fetched but flagged | Proceed, and carry the flags into the report |
| 3 | Unusable | **Stop.** Say why. Do not substitute anything remembered. |

If you cannot fetch, the honest output is "I can't price this right now", not an analysis with
approximate numbers. An analysis built on a remembered price is worse than no analysis, because it
looks like work.

**Resolve identity before anything else.** Ticker collisions are not an edge case, they are a
deliberate tactic — impostor tokens reuse the symbols of real projects to catch exactly this
mistake. Confirm the market cap rank and, for anything on-chain, the contract address against the
project's own site. Rating the wrong token is a complete failure that reads as a normal report.

## Screen before you rate

For anything small, new, or thin, the dominant question is not whether it is undervalued. It is
whether it is a trap. Rating a honeypot 6/10 is far worse than refusing to rate it.

Run the screen when **any** of these hold: outside the top 100, under a year old, market cap under
about $50M, not listed on a major venue, or the user found it through social media.

Read `references/red-flags.md` for the full screen. Any of these ends the analysis at "do not
buy", with no rating:

- Mint authority still live, or an upgradeable contract with an unrestricted admin key
- Liquidity not locked, or shallow enough that exiting moves the price against you
- Trading restrictions in the contract — sells blocked, punitive sell tax, allow-lists
- Extreme holder concentration, especially wallets that received tokens for nothing
- Volume that cannot be organic relative to holders and market cap
- The team's only presence is a Telegram group and an anonymous X account

Say which specific check failed and what evidence you found. "This looks risky" teaches nothing;
"the deployer can still mint, so any holding can be diluted to nothing at will" is a reason.

## Workflow

### 1. Get the data and the supply picture

Fetch, then feed the supply figures into the dilution maths rather than eyeballing the market cap:

```bash
python3 scripts/tokenomics_math.py --example > token.json   # fill from live_data output
python3 scripts/tokenomics_math.py token.json
```

The number to bring forward is **how much the price must rise just to stand still** once all
tokens exist. A token at 4x FDV needs +300% before a holder is even level on dilution, which is a
hurdle that sits in front of every bullish argument and is usually left out of them.

Then the unlock schedule. An unlock is public, dated, and one of the few genuinely predictable
things in this market. Expressed as **days of trading volume**, it tells you whether the supply can
be absorbed quietly — a cliff worth ten days of volume will not be, however good the project is.
Waiting past a large unlock is frequently better odds than buying into one.

If no schedule is available, say it is *unverified* rather than clean. An unchecked vesting
schedule has ended a lot of otherwise sound theses.

### 2. Score the six dimensions

Score 0-10 each, and show the evidence per dimension. `references/scoring-rubric.md` has what each
score means and the weights.

1. **Network and usage** — real users, transactions, fees paid. Is anyone using this for anything?
2. **Value capture** — does token holding actually accrue the value the network creates, or is the
   token decorative? This is where most projects fail and where most write-ups skip.
3. **Supply and tokenomics** — float, dilution, unlocks, issuance, concentration.
4. **Liquidity and market structure** — depth, venues, spread, how hard exiting is.
5. **Security and dependencies** — audits, contract control, bridges, oracles, custody, chain risk.
6. **Team, funding and durability** — who builds it, is it funded, what happens when the cycle turns.

Two rules keep the score honest. **Any dimension scoring 2 or below caps the total**, because these
are not independent — a strong network with a token that captures none of its value is not a good
investment, it is a good project you cannot own. And **score against evidence you fetched**, not
reputation. A well-known name is not a score.

### 3. Size it to the person's capacity for loss

This step is not optional, and it needs their situation. Ask for it in one short block if you do
not have it: investable net worth, the loss they could absorb without changing their plans, how
long they can leave it, months of expenses in cash, what they already hold in crypto, whether they
use leverage, and whether they have held through a crash before.

```bash
python3 scripts/risk_profile.py --example > profile.json
python3 scripts/risk_profile.py profile.json --rank 98 --market-cap 1900000000
```

It applies three independent caps and the tightest one wins — the loss budget, total crypto
exposure, and single-asset concentration — then shows the position at -30%, -50%, -80% and -100% in
their money. It also **gates**: no emergency fund, or money needed inside the horizon, and the
answer is do not buy at any size, however good the asset is. Say that it is about the circumstances
rather than the asset, and what would need to change.

The concentration cap is what stops a micro-cap being sized like Bitcoin. Without it, a total
exposure limit alone lets one speculative token take the whole allocation, which inverts the point
of the tiers.

### 4. Give two verdicts, separately

They disagree often, and blending them into one number destroys the information.

- **Long-term hold** — driven by the scorecard, tokenomics and durability. Answers whether this
  should be owned at all.
- **Near-term entry** — driven by positioning. How far it has already run, where it sits against
  its high, funding and leverage if you can see them, whether an unlock sits just ahead.

"Worth owning, but not here" is a common and useful answer. So is "fine entry, but the asset does
not deserve a position", which should read as a no.

## Output format

```
## As of [timestamp] — every figure below was fetched, none recalled
[Price with cross-check spread, market cap, FDV and ratio, 24h volume, drawdown from ATH]

## Verdict
Long-term hold   X/10   [Buy / Accumulate / Hold / Avoid]
Near-term entry  X/10   [Buy now / Wait for X / Avoid]
Maximum position [X% of net worth = $Y], bound by [which cap]
[If gated: DO NOT BUY, and the reason, which is about circumstances not the asset]

## If it falls
[-30 / -50 / -80 / -100% in their money, and whether each stays inside their stated budget]

## Scorecard
[Six dimensions, score, and the evidence for each. Note any capped by a low score.]

## Supply and unlocks
[Float, FDV multiple, the rise needed to stand still, dated unlocks as days of volume]

## What would change this
[The two or three specific, observable things that would move the verdict either way,
 with the level or date. Not "if adoption improves" — a number or an event.]
```

Lead with the timestamp. It is the load-bearing fact, and a price without a time is not a fact.

## Failure modes to avoid

- **Any figure from memory.** Prices, market caps, supply, ranks, dates. Fetch or say you cannot.
- **Rating a token you have not identified.** Confirm rank and contract address; impostors rely on
  you not doing this.
- **A rating with no size.** It is not a decision until it has a number attached to it, and the
  size is the part that determines the outcome.
- **Treating -80% as a tail risk.** It is the base case for a bad cycle in the majors, and total
  loss is the base rate outside them.
- **Skipping dilution.** A "cheap" market cap at 5x FDV is not cheap. Do the arithmetic.
- **Confusing a good project with a good investment.** Value capture is the bridge between them and
  it is frequently absent.
- **Recommending leverage, or sizing as if spot rules applied to it.** A -80% move liquidates a
  leveraged long long before the bottom, so the sizing here does not transfer.
- **Talking someone into a position their circumstances rule out.** If the gate fires, hold it.
- **Hedging everything.** Say the scope limit once — this is analysis, not financial advice, and
  nobody can tell you what a price will do — then commit to a view and show the reasoning.

## Reference files

- `references/data-sources.md` — which endpoints to use, what each is good for, verifying contract
  addresses, and what to do when a fetch fails.
- `references/red-flags.md` — read before rating anything small or new. The rug and trap screen.
- `references/tokenomics.md` — read when working through supply, unlocks, emissions, value capture.
- `references/scoring-rubric.md` — the six dimensions, what each score means, weights, and the
  capping rules.
