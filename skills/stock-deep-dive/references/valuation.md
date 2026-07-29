# Valuation

Methods, when each applies, and the traps that make a valuation confidently wrong.

The organising idea: valuation is not a search for the "true" price. It is a way of making the
market's assumptions explicit so you can judge them. A number without the assumptions behind it
is not a valuation, it is a guess with decimal places.

## Contents

- [Reading the reverse DCF](#reading-the-reverse-dcf)
- [Multiples](#multiples)
- [Context: history and peers](#context-history-and-peers)
- [Sector-specific approaches](#sector-specific-approaches)
- [Traps](#traps)

---

## Reading the reverse DCF

`scripts/reverse_dcf.py` solves for the free cash flow growth the current price requires. Getting
value from it depends on what you do next.

**Compare the implied rate to the delivered rate.** If the price implies 15% and the company has
compounded free cash flow at 8% through good conditions, the burden of proof sits with the bull
case. If it implies 3% for a business that has done 10% consistently, that gap is the opportunity.

**Check it against base rates, not just the company's own history.** Sustaining double-digit
growth for a decade is achieved by a small minority of listed companies. Competition, scale and
mean reversion make it rare. A price implying it is making a strong claim.

**Run the sensitivity.** Re-run with the discount rate one to two points either side and with the
fade option. If the conclusion flips within that range, the honest report says the valuation is
not decisive, rather than quoting the central case as though it were.

**Sanity-check the starting FCF.** The whole output depends on it. If the latest year was
distorted by a one-off — a large working capital swing, an asset sale, an unusual tax item — use a
normalised figure and say that you did.

**Where a DCF does not apply**, say so and use the sector approach instead. Loss-making companies,
banks and early-stage businesses are not DCF problems.

---

## Multiples

Fast, comparative, and dependent on the denominator being meaningful.

| Multiple | Best for | Fails when |
| --- | --- | --- |
| P/E | Stable, profitable businesses | Earnings are cyclical, negative, or heavily adjusted |
| EV/EBITDA | Capital-structure-neutral comparison | Capex is heavy — EBITDA ignores the cost of staying in business |
| EV/Sales | Pre-profit or margin-recovery situations | Margins differ structurally between the companies compared |
| P/B | Banks, insurers, asset-heavy businesses | Assets are intangible or carried far from economic value |
| FCF yield | Cash-generative mature businesses | Capex is lumpy, or growth investment is suppressing FCF |
| PEG | Growth at a reasonable price screening | Growth estimates are unreliable, which is most of the time |

**EV/EBITDA deserves particular care.** EBITDA is not cash flow and treating it as such is the
most common error in leveraged situations — it excludes precisely the capex and interest that
determine whether the company survives.

---

## Context: history and peers

A multiple in isolation means nothing. Two contexts make it informative.

**The company's own history.** Compare the current multiple to its five- and ten-year range. Then
ask the real question: has the business changed to justify a re-rating, or is the market simply
more optimistic? A business whose returns on capital have structurally improved deserves a higher
multiple. One trading above its history on an unchanged business is being paid a sentiment premium.

**A genuine peer set.** Peers must share economics, not just an industry label. A software company
with 90% gross margin and 120% net revenue retention is not comparable to one at 45% with churn,
however similarly they are classified. When the peer set is weak, say so rather than averaging
unlike things.

Watch for the whole sector being re-rated together. Cheap relative to expensive peers is not
cheap.

---

## Sector-specific approaches

**Banks:** price/book read against ROE — a bank earning 18% on equity sustainably supports a much
higher book multiple than one earning 8%. Cross-check against provisioning adequacy, because book
value is only as sound as the loan marks behind it.

**Insurers:** price to embedded value for life; book value and combined ratio for general.

**REITs:** price/FFO and price/AFFO; net asset value per share against the price; implied cap rate
against private-market transactions.

**Cyclicals:** normalised mid-cycle earnings, or price/book against mid-cycle returns. Never
capitalise peak earnings.

**Loss-making growth:** EV/gross profit or EV/sales adjusted for growth and margin, plus an
explicit path to profitability with the assumptions stated. Any DCF here is an assumption
generator wearing a spreadsheet.

**Holding companies and conglomerates:** sum of the parts, valuing each segment on its own
appropriate basis, then applying a holding-company discount. State the discount and why.

---

## Traps

**Trailing versus forward.** Be explicit about which you are quoting. Mixing a trailing multiple
for one company with a forward multiple for another produces a comparison that means nothing.

**Adjusted earnings.** Companies present the version that flatters them. Reconcile to reported
figures and decide for yourself which adjustments are legitimate. Recurring "one-offs" are
operating costs.

**Anchoring on the share price's history.** A stock down 70% is not cheap if earnings fell 80%.
Value against earnings, cash flow and capital — never against a previous price.

**The value trap.** Persistently cheap is often correct pricing of structural decline. Before
concluding something is undervalued, articulate why the market is wrong and what will change its
mind. A cheap multiple with no catalyst and deteriorating fundamentals is a value trap, and the
multiple can fall further while the business shrinks beneath it.

**Ignoring dilution.** Heavy stock-based compensation makes per-share value grow far slower than
headline value. Use diluted share counts and treat SBC as the real cost it is.

**Currency.** For companies earning across currencies, be explicit about the reporting currency
and translation effects. Growth in a weakening reporting currency overstates the underlying
business.

**False precision.** A valuation range with stated assumptions is more honest and more useful than
a single number. Where the range is wide, that width is the finding — report it rather than
picking the midpoint to look decisive.
