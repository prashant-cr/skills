---
name: ipo-rating
license: MIT
description: Rates an upcoming or open IPO and says whether to apply — scoring the business, valuation against listed peers, issue structure, promoters and disclosure quality, then giving two separate verdicts: one for listing-day gain and one for holding the stock. Reads pre-listing demand signals including grey market premium (GMP) where it exists, subscription figures and the anchor book, and maps the post-listing lock-in expiries. Works on any market. Use whenever the user asks whether to apply for, subscribe to or skip an IPO, wants an IPO analysis, rating or review, mentions GMP, grey market premium, listing gains, allotment, price band, RHP, DRHP or a new listing, asks how much an IPO might list up or down, or names a company that is about to go public — including bare asks like "is this IPO worth it", "should i apply", or "what's the GMP looking like".
---

# IPO rating

Rates an issue and answers the question the user actually has — **apply or skip** — with the two
halves of that decision separated, because they frequently disagree.

## Start from the asymmetry

An IPO is the one transaction where the seller chooses the timing, sets the price, and writes the
disclosure. Companies list when sentiment is high, not when the business is cheap. The bankers'
job is to leave as little on the table as the market will bear.

That does not make every IPO bad. It sets the prior: **the burden of proof is on the issue**, and
"the company is good" is not sufficient, because a good company sold at a price that captures all
of its value is still a poor purchase. Approach each issue asking what the seller knows that the
buyer does not.

## The two decisions people confuse

Almost every disappointed IPO investor made one decision while thinking about the other.

| | Driven by | Time horizon |
| --- | --- | --- |
| **Listing gain** | Demand: subscription multiples, anchor quality, grey market, float scarcity, market mood | Days |
| **Long-term hold** | Value: business quality, price against listed peers, where the money goes | Years |

These regularly point opposite ways. A heavily oversubscribed issue with a big grey market premium
can pop on listing and then fall for two years, because the same hype that produced the pop also
produced a price no fundamentals support. Deliver both verdicts, and when they disagree, say so
plainly — that disagreement is usually the single most useful line in the report.

## What this needs

Live access. The prospectus (RHP/DRHP in India, S-1 in the US, the equivalent elsewhere) is the
primary source; subscription and grey market figures change daily during the bidding window.

If you cannot search or fetch, **say so and stop**. IPO details — price band, dates, lot size, issue
split, GMP — are exactly the fast-moving, specific numbers that are worst to recall. A brief built
on remembered figures will be wrong about the one thing the user needs right now.

## Workflow

### 1. Pin the issue and its calendar

Get, and state: the exchange and market, price band, lot or minimum application size, issue size,
open and close dates, allotment date, and expected listing date. The user's decision is usually
time-boxed, so lead with how long they have.

Check the issue is actually open. Analysing a closed IPO as though it were live is a common and
embarrassing failure — and for a listed one, the right tool is a normal equity analysis rather
than this.

### 2. Read the structure before the story

The most informative fact in most prospectuses is the split between **fresh issue** and **offer for
sale**, and it takes one minute to find.

- **Fresh issue** — new shares; money goes to the company for growth, debt repayment or working
  capital. Dilutive, but the business gets funded.
- **Offer for sale (OFS)** — existing holders selling; **not one rupee reaches the company**. The
  transaction is a shareholder exit dressed as a fundraising event.

An issue that is overwhelmingly OFS is promoters or private equity cashing out. That is not
automatically disqualifying — early investors are entitled to exit — but it changes the question to
*why now, and why at this price*, and it means the "growth story" in the prospectus is not being
funded by the money you are handing over.

Then read **use of proceeds** on the fresh portion. Growth capex is a different proposition from
repaying debt, which is different again from "general corporate purposes" — a large unallocated
bucket is a disclosure weakness worth marking down.

```bash
python3 scripts/ipo_math.py --fresh 500 --ofs 4500
```

### 3. Read the financials, and check the pre-IPO year

Standard analysis of growth, margins, returns and cash conversion, with one addition specific to
IPOs: **the year before filing is very often the best year the company has ever had.**

Sometimes that is genuine momentum. Sometimes it is a margin that jumped on one-offs, a receivables
build inflating revenue, costs deferred into the next year, or related-party revenue. Look at three
to four years, not the headline growth rate the prospectus leads with, and ask what changed in the
final year and whether it recurs.

### 4. Value it against listed peers

The price band is the seller's opinion. The only external check is what the market already pays
for comparable listed businesses.

Compute the issue's multiple at the upper band and compare against genuine peers — similar
economics, not merely the same sector label. Where the issue is priced at a premium to established
listed companies, the report needs to say what justifies that premium, and "it is growing faster"
requires evidence that the growth is durable rather than recent.

```bash
python3 scripts/ipo_math.py --band 100-105 --eps 4.2 --peer-pe 21
```

For loss-making issuers, earnings multiples do not exist — use revenue or gross-profit multiples
against peers, and say plainly that the valuation rests on assumptions rather than earnings.

`references/valuation-and-red-flags.md` covers peer selection, the dressing-up checks, and the
governance flags worth a specific look in a prospectus.

### 5. Read the demand signals — including the grey market

This is what drives the listing-day verdict. Sources differ by market and
`references/pre-listing-signals.md` covers each; the shape is the same everywhere:

- **Subscription figures by category**, updated daily while bidding is open. Institutional demand
  is the most informative because those bidders do the most work; retail enthusiasm is the least.
- **The anchor book** — who took it and on what terms. Long-only institutions signal conviction;
  a book dominated by short-horizon money signals a trade.
- **Pre-listing price signal**, where the market has one. In India that is the **grey market
  premium (GMP)**; Hong Kong has a broker-run grey market; the UK has conditional dealing; the US
  has essentially nothing before the open.

**On GMP specifically, be straight with the user.** It is genuinely informative about sentiment and
it is what most Indian retail investors are actually asking about. It is also unofficial and
unregulated, it trades on thin volume, it can be moved by a small number of operators with an
interest in the issue looking hot, and it says nothing whatsoever about where the stock trades a
month later. Report it, use it, and never present it as a forecast.

Treat it as a market to *read*, not a market to participate in — it is unregulated and its trades
are not enforceable.

### 6. Map the supply that arrives after listing

Newly listed shares hit the market on a schedule, and those dates are known in advance. Anchor
lock-in expiries in particular have a track record of producing sharp falls.

```bash
python3 scripts/lockin_calendar.py --market IN --listing 2026-08-14
```

For anyone considering holding rather than flipping, this calendar is where the near-term pressure
comes from.

### 7. Score five dimensions

Score 0–10 with evidence. These are the investment-quality dimensions; demand signals are handled
separately because they belong to the listing-day question, not the business.

| Dimension | The question |
| --- | --- |
| Business quality | Are the economics good and is the growth durable? |
| Valuation vs peers | Is the band a discount or a premium to comparable listed companies, and is it justified? |
| Issue structure | Fresh vs OFS, where the money goes, how much dilution |
| Promoters & governance | Who is selling, how much, and what does the record show? |
| Disclosure quality | Is the prospectus candid about risks, related parties and contingencies? |

Weight for the situation and say how. A heavily OFS issue at a premium to peers is dominated by
structure and valuation regardless of how good the business is.

### 8. Give both verdicts, and a range with its caveats

**Listing gain:** APPLY / NEUTRAL / SKIP, from the demand signals. Where there is a pre-listing
price signal, give an indicative listing range — and attach what it is worth:

```bash
python3 scripts/ipo_math.py --band 100-105 --gmp 31 --lot 142
```

The script also shows what happens if it lists flat or below, which is the half people skip. If
GMP is the only support for the idea, say that the idea is a sentiment trade, not an investment.

**Long-term hold:** the scorecard verdict.

Where they disagree, lead with the disagreement.

## Report structure

```markdown
# <Company> IPO — rating

**Issue:** <price band, lot, issue size, fresh/OFS split>
**Dates:** <open, close, allotment, listing>  — <days left to decide>

## Verdict
OVERALL: <x.x>/10

**LISTING GAIN:  <APPLY / NEUTRAL / SKIP>** (<conviction>)
<demand evidence — subscription, anchor, grey market>
Indicative listing range: <range> — <what this is based on and how reliable it is>

**LONG-TERM HOLD: <APPLY / NEUTRAL / SKIP>** (<conviction>)
<the one-line thesis>

<If the two disagree, state it here in one sentence.>

Business quality     <n>/10  <bar>
Valuation vs peers   <n>/10  <bar>
Issue structure      <n>/10  <bar>
Promoters/governance <n>/10  <bar>
Disclosure quality   <n>/10  <bar>

## The business
## Issue structure — where the money goes
## Financials
## Valuation against listed peers
| Company | Multiple | Growth | Margin |
## Demand signals
## Post-listing supply
## Risks
## What I could not verify
```

## Failure modes

**Rating the company instead of the offer.** A great business at a full price is a poor issue.
The offer is what is being sold.

**Treating GMP as a price target.** It is a sentiment reading on an unregulated, thin market, and
it is least reliable on exactly the hyped issues where people lean on it hardest.

**Reading retail oversubscription as validation.** Retail is the least informed category and the
most sentiment-driven. Institutional demand carries more information.

**Ignoring the OFS split.** It is the fastest read on whether this is a fundraising or an exit.

**Comparing against sector, not economics.** Peers must share margin structure and growth profile,
not just an industry label.

**Recalling figures.** Bands, dates, lot sizes and GMP change; a stale number here is the one that
actually costs the user money.

## Judgement calls

**Say when you cannot rate it.** Some issues have too little disclosure or no comparable listed
peer. Saying that is more useful than a manufactured score.

**Watch the clock.** If the window closes tomorrow, the user needs a decision and the key risks
now, not a comprehensive report. Lead with the verdict and keep the detail beneath it.

**Small issues behave differently.** SME and small-board listings have thin liquidity, wider
spreads and far more volatile listings. Note the exit risk explicitly.

**Do not let a good listing pop justify a bad business.** If the recommendation is to apply and
sell, say exactly that, so the user does not accidentally hold something you rated a skip.

## What this is not

This is research to verify, not investment advice, and it cannot know the user's finances or risk
tolerance. Allotment in oversubscribed retail categories is often a lottery, so applying is not the
same as receiving shares.

Report the grey market as an observable signal. Do not advise anyone to trade in it — it is
unregulated and unenforceable, and that is a materially different act from reading what it says.
