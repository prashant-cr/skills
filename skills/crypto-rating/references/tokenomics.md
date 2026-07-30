# Tokenomics

Read this when working through supply, dilution, unlocks and whether the token captures any value.

## Contents

- [Market cap is not the price of the network](#market-cap-is-not-the-price-of-the-network)
- [Float and FDV](#float-and-fdv)
- [Unlocks](#unlocks)
- [Issuance and inflation](#issuance-and-inflation)
- [Value capture](#value-capture)
- [Fees and revenue](#fees-and-revenue)
- [Buybacks and burns](#buybacks-and-burns)
- [Distribution and who is above you](#distribution-and-who-is-above-you)
- [Stablecoins and yield](#stablecoins-and-yield)

## Market cap is not the price of the network

Market cap is price times *circulating* supply, so it prices only the tokens that exist today. If
half the supply has yet to arrive, market cap understates what you are actually buying into by half.

This is the most common analytical error in crypto and it is systematically in one direction: it
makes tokens look cheaper than they are. A project can be presented as a "$200M network" while the
fully diluted figure is $1.2B, and the difference is a dated schedule of future selling that is
public information.

`tokenomics_math.py` computes both and the ratio between them. Lead with the ratio when it is high.

## Float and FDV

Fully diluted value is price times ultimate supply. The useful derived numbers:

- **Float** — circulating divided by ultimate supply. A 15% float means 85% is still to come.
- **Price drag at constant market cap** — if the market cap stays where it is while supply completes,
  the price falls by exactly the share not yet circulating.
- **The rise needed to stand still** — the inverse, and the one to quote to a holder. At 4x FDV a
  holder needs +300% just to be level once every token exists. That hurdle sits in front of every
  bullish argument.

Rough reading of the FDV multiple, which is a starting point rather than a rule:

| FDV / market cap | What it implies |
| --- | --- |
| Under 1.2x | Supply substantially issued; market cap is close to the real price |
| 1.2x to 2x | Meaningful dilution ahead; adjust expectations |
| 2x to 4x | Significant. Dilution is a primary risk, not a footnote |
| Above 4x | The dominant fact about the token. Low float and high FDV is how a token trades well at launch and badly for two years |

Low float with high FDV deserves specific suspicion, because it can be engineered: a small tradable
supply is easy to mark up, which produces an attractive chart and a valuation that later supply
cannot support.

## Unlocks

Unlocks are the rare thing in this market that is genuinely predictable — dated, sized and published.
That makes them one of the few places where doing the arithmetic gives a real edge.

What to establish:

- **Date and size** of each tranche ahead.
- **Size as a share of circulating float.** Above 10% in 90 days is material.
- **Size as days of trading volume.** This is the number that matters, because it says whether the
  market can absorb the supply quietly. A cliff worth 10 days of total volume cannot be, even if only
  a fraction of it sells.
- **Who receives it.** Team and early investor tokens have a near-zero cost basis and a fiduciary
  reason to sell. Ecosystem or treasury unlocks may not hit the market at all. Do not treat these the
  same way.
- **Whether it is a cliff or a stream.** Continuous daily vesting is priced in gradually; a single
  large cliff is an event.

**Practical consequence:** buying immediately before a large unlock is usually worse odds than
waiting past it. Say the date explicitly so the user can act on it, and if the near-term entry
verdict is "wait", the unlock date is often the reason.

If no schedule is published, report it as **unverified**. Silence is not the same as absence, and an
unchecked vesting schedule has ended a lot of otherwise sound theses.

## Issuance and inflation

Separate from unlocks: new tokens minted for staking rewards, mining or liquidity incentives.

Annual issuance as a percentage of circulating supply is the headwind. At 10% a year, demand must
grow more than 10% annually before the price can rise at all, and that compounds against a holder
every year they wait.

Distinguish **incentive emissions** — rewards paid to attract liquidity or users — from **security
emissions** paid to validators or miners. Incentive emissions frequently buy activity that leaves the
moment they stop, so check whether usage survived any past reduction. That is the cleanest available
test of whether the demand was real.

Net supply change is what matters where a burn exists: issuance minus burn. A token can be
inflationary in name and net deflationary in practice, or the reverse.

## Value capture

**The single most important question, and the one most often skipped: does owning the token entitle
you to anything?**

A network can be genuinely successful while its token accrues none of that success. The mechanisms
that actually connect them:

- **Fee accrual** — protocol fees flow to holders or stakers. The strongest link.
- **Burn from usage** — fees destroy supply, so use reduces float.
- **Staking yield paid from real fees** rather than from new issuance. If the yield is minted, it is
  dilution wearing a coupon.
- **Required collateral or gas** — the token must be held or spent to use the network, creating
  structural demand.
- **Governance over a treasury with real assets** — weak on its own, meaningful when the treasury is
  large and actually controlled by holders.

Weak or absent capture looks like: governance over nothing consequential, a token used only for
rewards nobody keeps, "utility" that a stablecoin would serve better, or a fee switch that exists in
documentation but has never been turned on.

When capture is absent, say so plainly and score it low. It is entirely possible to admire a project
and conclude the token is not worth owning — those are different statements, and conflating them is
how good analysis produces bad decisions.

## Fees and revenue

The nearest analogue to revenue, and the most useful quantitative handle available.

- **Fees** — total paid by users.
- **Revenue** — the share retained by the protocol rather than passed to suppliers.
- **Holder earnings** — the share that reaches token holders. Frequently zero even where revenue is
  large, and this is the number the token's value depends on.

A price-to-fees or price-to-revenue multiple is a legitimate comparison *within* a category —
exchanges against exchanges, lending against lending. Across categories it means little.

Check the trend and the composition rather than the level alone. Fees that spiked during an incentive
programme and collapsed after are not a run rate, and a single week is not a trend.

## Distribution and who is above you

Ask what the people above you paid, because it determines how they behave.

- **Insider and investor share**, and their cost basis. Someone in at a hundredth of the current
  price is a different holder from you.
- **Airdrop recipients** hold something they were given, and historically most of it sells.
- **Treasury** — how large, who controls it, has it been sold into the market before.
- **Concentration** — top-10 non-contract wallets. High concentration means the price is set by a few
  decisions, not by a market.
- **Exchange balances** — supply that can move without an on-chain warning.

## Stablecoins and yield

If the asset is a stablecoin or a yield product, the analysis is a different one and the rating
framework here largely does not apply. What matters instead:

- **What backs it**, verified how, and by whom. Attestation is not audit.
- **Redemption** — who can redeem, at what size, on what timeline. A peg without redemption is a
  market price, not a peg.
- **Depeg history.** Every event, and what caused it.
- **Where the yield comes from.** This is the whole question. Yield that cannot be explained
  mechanically is being paid from deposits, from token emissions, or from risk that has not shown up
  yet. Double-digit "stable" yield is a risk premium being described as a feature — say what the risk
  is, and if you cannot identify it, say that instead.
