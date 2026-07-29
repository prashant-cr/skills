---
name: stock-deep-dive
license: MIT
description: Full fundamental analysis of a single listed company, the way a fund manager builds a position — business model, moat, financial and earnings quality, management and capital allocation, what the current price already implies, and a scored 0-10 verdict across six dimensions with bull/base/bear scenarios. Use whenever the user names a stock or ticker and asks whether to invest, buy, hold or avoid, wants a deep dive, fundamental analysis, valuation, research report or second opinion on a company, asks if something is overvalued, undervalued, a good long-term bet or what the future holds for it, is comparing two companies, or is reviewing a position they already own — including bare asks like "thoughts on NVDA?", "is Reliance worth buying", or "analyse this stock for me".
---

# Stock deep dive

Produces the analysis a fund manager would run before committing capital: what the business
actually does, whether its economics are durable, what the price already assumes, and a scored
verdict with the scenarios that would prove it right or wrong.

The instinct behind asking for "superhuman" analysis is right, but the thing that makes analysis
superhuman is not confidence. It is three unglamorous habits: doing the arithmetic from primary
sources instead of recalling it, knowing what the market has *already* priced in, and hunting
hard for the evidence that would make you wrong. Confident write-ups are common and cheap. Those
three are rare, and they are what this skill enforces.

## The one idea that organises everything below

**A great company and a great investment are different questions**, and only the second one is
open. The market has usually already worked out that a dominant business is dominant — that view
is in the price. What remains genuinely uncertain is whether the price demands more than the
business can deliver.

So the analysis does not stop at "is this good?". It asks: *what does the current price require to
be true, and is that achievable?* That reframing is what `scripts/reverse_dcf.py` exists to
answer, and it is why the valuation dimension frequently scores lowest on the best companies.

## What this needs

Live access to primary sources. If you cannot search or fetch filings, **say so and stop**.

Financial figures are the single highest-risk thing to produce from memory: revenue, margins,
debt and share counts recalled rather than read are wrong often enough, and confidently enough,
to poison every downstream number. A refusal is a fine outcome. A deep dive built on remembered
financials is worse than no analysis, because it looks rigorous.

Source hierarchy, best first: **company filings** (10-K/10-Q, annual report, investor
presentations, exchange disclosures) → **the company's own investor relations data** → financial
data aggregators → press coverage. Analyst summaries are the weakest source and the most likely
to be recycled from the company's own narrative.

## Workflow

### 1. Pin the company and pull the primary documents

Resolve the ticker to an exact listed entity and exchange — names collide across markets, and
group companies are frequently separate listings with unrelated economics. Then get the latest
annual report and most recent quarterly, plus the previous three to four years for trends.

State the currency and the reporting unit up front. Mixing crores, millions and billions is a
common and quietly fatal error.

### 2. Understand how it actually makes money

Before any ratio, be able to state in two sentences: what the customer buys, why they buy it
here, and what could stop them.

Then get the **segment breakdown** — revenue and profit by business line and by geography. This is
where most surface-level analysis fails: a company described as an "AI company" may earn 80% of
profit from a legacy segment, which means the story driving the multiple is not the story driving
the earnings. Divergences between the narrative and the segment data are among the most valuable
findings available.

### 3. Do the arithmetic yourself

Enter the reported figures and compute rather than eyeballing:

```bash
python3 scripts/quality_check.py --example > financials.json   # template to fill in
python3 scripts/quality_check.py financials.json
```

It computes growth, margins, cash conversion, leverage, returns and dilution across years, and
flags the divergences that are hard to see reading one year at a time — profit rising while
operating cash flow falls, receivables outgrowing sales, inventory building.

Treat every flag as a question, not a verdict. Growth companies legitimately absorb working
capital. But an unexplained gap between profit and cash is the earliest available warning of an
accounting problem, and it is worth more than any narrative.

`references/financial-analysis.md` covers what to compute, what good looks like, and how the
toolkit changes by sector — this matters more than it sounds, because banks, insurers, REITs and
cyclicals cannot be analysed with the same ratios as an ordinary operating company. Applying
EV/EBITDA to a bank is a reliable sign the analysis is generic.

### 4. Test the moat rather than asserting it

"Strong brand" is a claim; pricing power is evidence. Look for it in the numbers: sustained gross
margin through an input-cost spike, price increases that did not cost volume, returns on capital
that stayed high while competitors entered.

Ask what would have to happen for a well-funded competitor to take 20% of this business in five
years. If that is easy to imagine, the moat is narrower than the narrative.

### 5. Judge management on capital allocation, not communication

Management quality shows up in where the cash went. Track it: reinvestment and what it returned,
acquisitions and whether they earned their cost, buybacks and whether they were done at sensible
prices, dividends, debt paydown. Buybacks at peak valuations funded by debt are a governance
signal regardless of how shareholder-friendly they sound.

Read what they promised three years ago against what happened. Consistent over-promising is
predictive; a single miss usually is not.

`references/financial-analysis.md` also lists the governance red flags worth checking explicitly
— auditor changes, related-party transactions, pledged promoter holdings, unusual related
disclosures — because these are cheap to check and occasionally decisive.

### 6. Establish what the price already implies

```bash
python3 scripts/reverse_dcf.py --price 175 --shares 15.2e9 --fcf 95e9 --discount 0.10
```

This solves for the FCF growth rate the current price requires. Judging whether a business can
compound at, say, 12% for a decade is a far more tractable question than forecasting a price, and
it converts valuation from an opinion into a testable claim.

Then sanity-check the answer against base rates. Sustained double-digit growth for ten years is
achieved by a small minority of companies; a price implying it is making a strong claim that
deserves strong evidence. Run the sensitivity — if the conclusion flips on a one-point change in
the discount rate, say so rather than quoting a single figure.

`references/valuation.md` covers multiples, when each method applies, and the sector-specific
approaches where DCF is the wrong tool entirely.

### 7. Build the bear case as though you believed it

Write the strongest possible argument against the position, from the perspective of someone who
is short the stock and well informed. Not a token risks section — the actual case.

Look for what the sceptics are saying and why, whether short interest is elevated, which
assumption the bull case depends on most heavily, and what single fact would break the thesis.

An analysis that cannot articulate why an intelligent person is on the other side has not
finished. This step, more than any other, is what separates a deep dive from a rationalisation.

### 8. Score the six dimensions

Score each 0-10 using the anchors in `references/scoring-rubric.md`. Read it rather than scoring
by feel — anchored scores are comparable across companies and across time, and unanchored ones
drift toward 7/10 for everything, which carries no information.

| Dimension | The question it answers |
| --- | --- |
| Business quality | Are the economics good — returns on capital, cash conversion, reinvestment runway? |
| Moat | Is there durable pricing power, evidenced rather than asserted? |
| Financial health | Can it survive a bad two years — leverage, cover, liquidity, earnings quality? |
| Management | Has capital been allocated well, and is governance clean? |
| Valuation | What does the price imply, and how plausible is that? |
| Risk | Concentration, regulation, cyclicality, disruption, single points of failure |

Weight them by what the situation demands rather than averaging mechanically — for a highly
leveraged company, financial health dominates; for a richly priced one, valuation does. State the
weighting so the reader can disagree with it.

### 9. Scenarios, not a forecast

Give bull, base and bear, each with the **assumptions it depends on** and the **signposts** that
would confirm it early. The value is not in the numbers but in making the assumptions explicit
enough to be checked as evidence arrives.

Attach rough probabilities and let them be uneven. Three scenarios at 33% each usually means the
analysis has not committed to anything.

### 10. Deliver the verdict at both horizons, separately

A great business at a demanding price is a genuinely different call over five years than over
one, and collapsing the two hides the disagreement rather than resolving it:

- **Long term (3–5 years):** judged as a business owner — durability, compounding, reinvestment.
- **Nearer term (12 months):** entry price, catalysts, what could de-rate it.

Where they diverge, say so plainly. "Excellent business, poor entry point" is a complete and
useful answer.

## Report structure

```markdown
# <Company> (<ticker>, <exchange>) — deep dive
<currency and units stated once, here>

## Verdict
OVERALL: <x.x>/10 — <STRONG BUY / BUY / HOLD / AVOID> (<conviction>)

Business quality   <n>/10  <bar>
Moat               <n>/10  <bar>
Financial health   <n>/10  <bar>
Management         <n>/10  <bar>
Valuation          <n>/10  <bar>
Risk profile       <n>/10  <bar>

**Long term (3-5y):** <verdict and one-line thesis>
**Next 12 months:**  <verdict and one-line thesis>
**Thesis in three sentences:** <what you are betting on and why>
**What would change this view:** <the concrete fact>

## The business
<what it sells, to whom, segment revenue and profit split>

## Financials
<computed trends, margins, returns, cash conversion, balance sheet, with the flags raised>

## Moat and competitive position
<evidence of pricing power, and what would erode it>

## Management and capital allocation
<where the cash went and what it returned; governance notes>

## Valuation — what the price implies
<reverse DCF output, multiples in historical and peer context, sensitivity>

## The bear case
<the strongest argument against, made properly>

## Scenarios
| Scenario | Assumptions | Rough probability | Signposts to watch |

## Risks
<ranked, with which are survivable and which are terminal>

## What I could not verify
<gaps, stale figures, paywalled sources, estimates used>
```

Lead with the verdict because that is what the reader needs first, and put the evidence beneath it
to be argued with. Keep **What I could not verify** even when short — an analysis that never
admits a gap is not more thorough, it is less honest, and the reader has no way to tell which.

## Failure modes

**Recalling financials instead of reading them.** The most common and most damaging. Every figure
should be traceable to a filing.

**Generic ratios on a specialised business.** Banks need net interest margin, credit costs,
capital adequacy and provisioning — not EV/EBITDA. Insurers need combined ratios. REITs need FFO.
Cyclicals need normalised earnings; judging a steel company at trough P/E gets the sign wrong.

**Narrative-led analysis.** Deciding the verdict from the story and then selecting numbers that
support it. The tell is a report where every metric agrees.

**Confusing a good business with a good price**, which the reverse DCF exists to prevent.

**Averaging the scorecard mechanically.** A 3/10 on financial health is not offset by a 9/10 on
moat — a solvency problem is not compensated by brand strength. Some low scores are vetoes, and
should be stated as such.

**Scoring by feel.** Without the rubric's anchors, everything converges on 7/10 and the scorecard
stops carrying information.

## Judgement calls

**Say when you cannot reach a verdict.** Insufficient disclosure, an opaque holding structure, or
a business genuinely outside your competence are real outcomes. "I cannot assess this reliably,
here is what is missing" is more useful than a number with nothing behind it.

**Let conviction be low.** Most situations do not warrant high conviction, and a scorecard where
everything is high-conviction is not analysis.

**Distinguish fact from inference throughout.** The filings are fact; the interpretation is yours.
Keep them visibly separate so a reader can accept your data and reject your conclusion.

**Update, don't defend.** If the numbers contradict the thesis you formed early, the thesis was
wrong. Say so in the report rather than reconciling it.

## What this is not

This is research for the user to verify and act on themselves, not investment advice. It cannot
know their portfolio, time horizon, tax position, liquidity needs or risk tolerance, and the
scorecard is an analytical summary rather than a recommendation calibrated to any person.

Say that once, plainly, and then make it meaningful by showing the reasoning and sourcing the
numbers so the conclusions can actually be checked rather than trusted.
