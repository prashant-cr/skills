# Data sources

Read this when a fetch fails, when you need data the bundled script does not cover, or when
verifying a token's identity.

## Contents

- [The rule](#the-rule)
- [What the script uses](#what-the-script-uses)
- [Beyond the script](#beyond-the-script)
- [Verifying identity](#verifying-identity)
- [Freshness and staleness](#freshness-and-staleness)
- [When sources disagree](#when-sources-disagree)
- [When a fetch fails](#when-a-fetch-fails)
- [Data that does not exist](#data-that-does-not-exist)

## The rule

Every number in the analysis is fetched, with a timestamp, or it is not used.

This is stricter than it sounds and it is deliberate. It applies to prices, market caps, supply
figures, ranks, all-time highs, dates and volumes. Not "check the ones that seem important" —
all of them, because the derived numbers are where the damage lands. A remembered price produces a
wrong market cap, which produces wrong dilution maths, which produces a wrong position size, and
each step looks reasonable.

The reason this needs saying at all is that a language model will happily produce a confident price
for any asset. In equities that answer is stale. Here it can be wrong by a multiple, because a token
can move 300% or -80% inside the gap between training and now.

## What the script uses

All keyless public endpoints, so nothing needs an account:

- **CoinGecko** (`api.coingecko.com/api/v3`) — the primary. Price, market cap, FDV, circulating and
  total and max supply, volume, all-time high and drawdown, rank, categories, contract addresses per
  chain. Free tier is roughly 10-30 calls a minute, which is ample for one analysis.
  `/search?query=` resolves a name or ticker to an id, and returns rank alongside each hit so
  impostor tokens are visible.
- **Binance** (`api.binance.com/api/v3/ticker/price`) — independent price cross-check on
  `SYMBOLUSDT`. Absence is informative: a token not listed here is thinner than one that is.
- **Coinbase** (`api.coinbase.com/v2/prices/SYMBOL-USD/spot`) — second independent cross-check.

Two cross-checks exist because a single source cannot detect its own staleness. If all three agree
within normal arbitrage, the price is real.

**One environment note.** Some Python installs — notably python.org builds on macOS — ship without a
usable CA bundle, so `urllib` fails with `CERTIFICATE_VERIFY_FAILED` while `curl` works. The script
detects this and falls back to `curl`, keeping certificate verification intact. Do not "fix" such an
error by disabling verification: this data decides where money goes, and an unauthenticated feed is
worse than no feed. The proper local fix is running `Install Certificates.command` from the Python
install directory, or `pip install --upgrade certifi`.

## Beyond the script

When the six dimensions need more than market data:

- **DefiLlama** (`api.llama.fi`, keyless) — TVL by protocol and chain, fees and revenue for many
  protocols. The best free source for the value-capture question, because fees are the closest thing
  to revenue that exists here.
- **Block explorers** — Etherscan, Solscan, BscScan and equivalents. Holder distribution, contract
  source and verification status, mint and owner functions, token age, transfer history. Essential
  for the red-flag screen and not substitutable.
- **Token unlock trackers** — for vesting schedules. Cross-check against the project's own
  documentation, because trackers are sometimes stale or incomplete, and a missed cliff is expensive.
- **The project's own docs and governance forum** — for supply policy, emissions and treasury. Read
  with the understanding that it is the project's own account of itself.
- **Perpetual funding rates** on any major venue — for the near-term positioning verdict. Persistent
  strongly positive funding means longs are paying to hold, which is a crowding signal.
- **Audit reports** — read the findings and whether they were fixed, not the fact of the audit.

## Verifying identity

Do this before analysing, not after. Getting it wrong produces a competent-looking report on an
unrelated asset.

1. Search the name and look at the **rank** of each hit. The real project is usually the ranked one.
2. Get the **contract address from the project's own website or docs**. Never from a search result, a
   social reply, or a screenshot.
3. Confirm that address on the explorer — token name, symbol, decimals, holder count, age.
4. For multi-chain tokens, confirm which deployment you have. A bridged or wrapped version carries
   the bridge's risk on top of the token's.
5. Note the chain in the report. "SYMBOL on Ethereum" and "SYMBOL on BSC" can be different assets
   entirely.

## Freshness and staleness

`live_data.py` reports the feed age and refuses above the limit — 30 minutes by default, tightened
with `--max-age`.

What counts as fresh depends on the question. For a long-term hold verdict, an hour-old price is
immaterial. For a near-term entry call, or in a fast-moving market, minutes matter. Tighten the limit
when the user is deciding about an entry today.

Always print the timestamp in the report. It tells the reader when the analysis expires, which
matters more here than in any other asset class — a verdict written a week ago may be about a
different price entirely.

## When sources disagree

The spread between sources is itself data:

- **Under about 0.5%** — normal arbitrage. Ignore.
- **0.5% to 1%** — worth a glance; possibly one stale feed.
- **1% to 5%** — flagged. The asset is thin enough that "the price" is a range rather than a number.
  Say so, and treat any precise valuation as false precision.
- **Above 5%** — treated as blocking. Either a feed is broken or the market is fragmented enough
  that you cannot state a price. Investigate before quoting anything.

For thin tokens the venue matters as much as the number. A price on one small pool is not a market
price, and it is not the price you would receive.

## When a fetch fails

Say so and stop. The correct output is "I could not get current data for this, so I cannot rate it",
optionally with what you would look at once data is available.

What not to do, in order of how tempting it is:

- Fall back to a remembered price. This is the failure the whole skill exists to prevent.
- Use a price the user mentioned in passing without confirming it. They may be quoting something
  they saw days ago, and it inherits no timestamp.
- Produce the qualitative analysis and quietly omit the numbers. The verdict and the position size
  both depend on price, so what remains is not a rating.

Rate limiting is the most common cause and it resolves in a minute. Retry once before giving up.

## Data that does not exist

Sometimes the honest finding is absence:

- **No price feed anywhere** — the token is untradeable or too new to value. That is a finding, not a
  gap. No rating applies.
- **No unlock schedule published** — report it as *unverified*, not clean. Undisclosed vesting is a
  risk in itself.
- **No fee or revenue data** — for many tokens there genuinely is none, which is the answer to the
  value-capture question rather than a missing input.
- **No audit** — state it plainly.

Absent data should lower a score or block a rating. It should never be quietly treated as neutral,
because that converts an unknown into an implied pass.
