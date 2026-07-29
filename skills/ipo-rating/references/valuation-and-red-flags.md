# Valuation and red flags

The market-agnostic half of an IPO rating: what the band is worth against listed peers, whether
the financials have been arranged for the occasion, and what in a prospectus deserves a second
look.

## Contents

- [Valuing the band against peers](#valuing-the-band-against-peers)
- [The pre-IPO year](#the-pre-ipo-year)
- [Reading the selling shareholders](#reading-the-selling-shareholders)
- [Prospectus red flags](#prospectus-red-flags)
- [Base rates worth carrying](#base-rates-worth-carrying)

---

## Valuing the band against peers

The price band is the seller's opinion, arrived at with bankers whose incentive is a successful
issue. It is not an independent valuation, and the prospectus will contain a peer comparison
chosen by the same people. Build your own.

**Select peers on economics, not sector labels.** A comparable company should have a similar
margin structure, growth rate, capital intensity and business model. A logistics company that owns
its fleet is not comparable to an asset-light aggregator, however identically they are classified.

**Compute the issue multiple at the upper band**, since that is where oversubscribed issues price.
Use `scripts/ipo_math.py --eps --peer-pe`. Then ask the only question that matters: if this issue
is priced above established listed peers, what justifies the premium, and is the evidence for it
durable or merely recent?

**Where earnings do not exist**, use revenue or gross-profit multiples and say explicitly that the
valuation rests on assumptions rather than earnings. Loss-making issuers are not un-rateable, but
the honest framing is that you are pricing a plan.

**Use the listed peer's own history too.** If the peer set is trading at the top of its historical
range, an issue priced "in line with peers" is priced in line with peak sentiment, not with
fundamentals.

**Watch for the peer set being cherry-picked.** Prospectuses frequently compare against the most
expensive available comparables. If the chosen peers look flattering, name the ones that were left
out.

---

## The pre-IPO year

The financial year immediately before filing is very often the best in the company's history. That
is not a coincidence — issuers control the timing, and they come to market after a good run.

Sometimes that momentum is real. The job is to distinguish the cases, and the evidence is in the
multi-year trend rather than the headline growth rate the prospectus leads with.

**What to check across three to four years:**

- **A margin that jumps in the final year.** Find out what changed. Operating leverage is a real
  explanation; a one-off gain, a cost deferred, or a change in accounting policy is not.
- **Receivables growing faster than revenue**, which inflates reported sales ahead of collection.
- **Cash conversion.** Profit that is not turning into operating cash flow is the earliest warning
  available, and it is disclosed.
- **Related-party revenue.** Sales to entities connected to the promoters can be genuine, and can
  also be a way to manufacture a growth record. The prospectus must disclose them.
- **Costs that vanish.** Employee costs, marketing or R&D falling as a share of revenue right
  before filing is often deferred spending that returns after listing.
- **A change of auditor** in the run-up.

None of these individually proves anything. Two or three together, in the year that sets the
valuation, changes the rating.

---

## Reading the selling shareholders

The offer-for-sale portion names who is selling and how much. This is one of the most informative
disclosures in the document and one of the least read.

**Questions to answer explicitly:**

- **Are the promoters selling, and what proportion of their holding goes?** Founders trimming a
  small stake for liquidity is ordinary. Founders selling a large share of their position at the
  first opportunity is a statement about their view of the price.
- **Is private equity exiting completely or partially?** A full exit at IPO means the most
  informed institutional holder is choosing to leave at this valuation.
- **What did earlier investors pay?** Prospectuses disclose the price of recent pre-IPO
  transactions. A band far above a placement done months earlier requires an explanation, and the
  gap is a good measure of how much of the value the issue is capturing for the seller.
- **How much post-issue holding remains locked?** Alignment after listing depends on what they
  still own, not on what they say.

---

## Prospectus red flags

Cheap to check and occasionally decisive:

- **"General corporate purposes"** taking a large share of the fresh issue — unallocated money with
  no stated return.
- **Fresh issue used mainly to repay debt** that was itself recently raised, particularly where the
  proceeds went to the promoters.
- **Litigation and contingent liabilities** that are material relative to net worth. The
  prospectus must disclose them; the summary rarely emphasises them.
- **Regulatory proceedings** involving the company, its promoters or its directors.
- **Customer concentration** — a large share of revenue from one or two customers, especially
  without long-term contracts.
- **Related-party transactions** that are material or hard to follow.
- **Recent share issues to insiders at prices far below the band**, which transfers value before
  the public arrives.
- **Frequent changes of auditor, CFO or key management** in the years before filing.
- **A risk-factors section that is boilerplate.** Candour about genuine risks is a positive
  signal; a section that could describe any company suggests the drafting was defensive.

---

## Base rates worth carrying

Priors that should shape a rating before any company-specific analysis:

- **Listing-day pops are common; sustained outperformance is not.** Studies across markets
  consistently find IPOs underperform the broader market over multi-year horizons. That is the
  base rate a long-term verdict starts from.
- **Hot markets produce worse issues.** Issuance clusters when sentiment is high, which is
  precisely when the seller has the advantage. A crowded IPO calendar is a reason for more
  scepticism, not less.
- **Heavily oversubscribed does not mean underpriced.** It means demand exceeded a deliberately
  limited supply — the scarcity is engineered, and it says more about float than about value.
- **The pop and the business are unrelated.** Listing gains come from demand exceeding available
  shares on one day. Long-run returns come from earnings. Nothing connects them, which is why the
  two verdicts in this skill are separate.
