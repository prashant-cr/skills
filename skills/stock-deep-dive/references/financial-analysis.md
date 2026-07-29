# Financial analysis

What to compute, what good looks like, how the toolkit changes by sector, and the governance
checks that are cheap to run and occasionally decisive.

## Contents

- [Core metrics](#core-metrics)
- [Earnings quality](#earnings-quality)
- [Sector toolkits](#sector-toolkits)
- [Governance red flags](#governance-red-flags)

---

## Core metrics

Compute across four to five years. A single year says almost nothing — the trend and its
consistency are the signal.

**Growth:** revenue, operating profit, net income, free cash flow. Compare their CAGRs against
each other. Profit growing faster than revenue means margin expansion (find out why, and whether
it can persist); free cash flow growing slower than profit is the divergence to investigate.

**Margins:** gross, operating, net. Gross margin is the cleanest read on pricing power because it
sits above discretionary spending. Operating margin mixes in efficiency and operating leverage.

**Returns on capital:**
- ROIC = NOPAT / (debt + equity − cash). The central measure of business quality.
- ROCE = EBIT / capital employed. A common alternative, especially outside the US.
- ROE = net income / equity. Useful but flattered by leverage — always read next to ROIC.

Compare ROIC against the cost of capital, not against zero. A business earning 8% on capital that
costs 10% is destroying value while reporting a profit.

**Cash generation:** operating cash flow, capex, free cash flow. Distinguish maintenance capex
(keeping the business running) from growth capex where disclosure allows — a company whose capex
is mostly growth can stop spending and harvest cash; one whose capex is maintenance cannot.

**Balance sheet:** net debt/EBITDA, interest cover (EBIT/interest), current ratio, maturity
schedule. The maturity schedule matters more than the total in a tightening credit environment.

**Per share:** check diluted share count over time. Revenue growth of 15% with 5% dilution is 10%
per share, and per share is what the owner receives.

---

## Earnings quality

Reported profit is an opinion; cash is closer to a fact. These checks find the gap. Run
`scripts/quality_check.py` to compute them, then interpret.

**Cash conversion (CFO / net income).** Cumulatively at or above 1x over several years is healthy.
Persistently below suggests profit is being recognised ahead of collection, or working capital is
consuming the business. Growth companies legitimately run below 1x — the question is whether it is
explained and improving.

**Receivables versus revenue.** Receivables growing materially faster than sales means revenue is
being booked faster than it is collected. Causes range from benign (a shift to enterprise
customers with longer terms) to serious (channel stuffing, uncollectible sales). Ask which.

**Inventory versus revenue.** A rising inventory-to-sales ratio flags obsolescence risk and
slowing sell-through, and often precedes a write-down.

**One-offs that recur.** "Exceptional" items appearing every year are not exceptional; they are
operating costs the company prefers you to exclude. Add them back and see what the margin looks
like.

**Capitalisation choices.** Costs capitalised rather than expensed flatter current profit at the
expense of future depreciation. A rising ratio of capitalised development costs to revenue is
worth a question.

**Tax rate.** A persistently low effective rate that is not explained by disclosed structure or
incentives may not persist, and normalising it changes forward earnings.

**Segment divergence.** Consolidated numbers can hide a deteriorating core masked by one strong
segment. Read segment disclosures separately.

---

## Sector toolkits

Applying generic ratios to a specialised business is the clearest sign of a shallow analysis. The
sectors below need different tools.

### Banks and lenders

EV/EBITDA and free cash flow are meaningless here — debt is raw material, not leverage. Use:

- **Net interest margin (NIM)** — the core spread the bank earns
- **Asset quality** — non-performing loans, provision coverage, credit cost as a share of loans,
  and the trend in early-stage delinquencies, which lead the headline number
- **Capital adequacy** (CAR / CET1) against the regulatory minimum — the buffer determines whether
  it can grow or must raise equity
- **Cost-to-income ratio** for efficiency
- **Loan growth and deposit mix** — low-cost current and savings deposits are the durable
  advantage; wholesale-funded growth is fragile
- Value on **price/book against ROE**, not on earnings multiples alone

The critical judgement is provisioning adequacy. A bank can report excellent profit by
under-provisioning, and it will look excellent right up until it does not.

### Insurance

- **Combined ratio** (below 100% means underwriting profit) for general insurers
- **Embedded value** and new business margin for life insurers
- Investment income and asset-liability duration matching
- Reserve adequacy and any history of reserve strengthening

### REITs and property

- **FFO and AFFO**, not net income — depreciation distorts property earnings badly
- Occupancy, rental growth, weighted average lease expiry
- Cap rates and net asset value against the share price
- Debt maturity profile and the proportion at fixed rates

### Commodities and cyclicals

- **Normalised earnings across the cycle**, never trough or peak earnings. A cyclical at a low P/E
  on peak earnings is expensive, not cheap — this inversion catches people repeatedly
- Position on the industry cost curve — low-cost producers survive troughs
- Price/book against mid-cycle returns is often more reliable than earnings multiples
- Capacity additions across the industry, which set the next cycle

### Loss-making growth companies

DCF on negative cash flow is meaningless. Instead:

- **Unit economics** — contribution margin per customer, payback on acquisition cost
- **Cohort behaviour** — do older cohorts spend more over time? This separates a growth business
  from a leaky bucket
- **Cash runway** at the current burn, and what raising more would cost existing holders
- Path to profitability: which line has to change, by how much, and what evidence exists that it is
  moving

### Utilities and regulated businesses

- The regulatory framework sets returns — read the allowed return and the review cycle
- Rate base growth is the earnings driver
- Interest-rate sensitivity, given high leverage and bond-like cash flows

### Pharmaceuticals and biotech

- Patent expiry schedule and the revenue exposed to it
- Pipeline by phase, with realistic probability-of-success weighting
- Concentration — one drug carrying the majority of profit is a risk-profile issue, not a
  footnote

---

## Governance red flags

Cheap to check, and occasionally the only thing that matters:

- **Auditor resignation or change**, especially mid-cycle or to a smaller firm
- **Restatements** of previously reported figures
- **Related-party transactions** that are material or poorly explained
- **Pledged promoter or founder shareholdings** (particularly relevant in India) — pledges force
  selling into weakness and can cascade
- **Frequent CFO turnover** — the CFO leaves before the problem surfaces more often than chance
  would suggest
- **Complex holding structures** with no operational rationale, especially involving related
  entities or opaque jurisdictions
- **Aggressive insider selling** during a period of upbeat guidance
- **Delays in filing** results or annual reports
- **Qualified audit opinions** or emphasis-of-matter paragraphs

None of these is proof of anything on its own. Several together, in a company whose reported
profit is not converting to cash, is a pattern worth acting on.
