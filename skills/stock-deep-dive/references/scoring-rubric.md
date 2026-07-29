# Scoring rubric

Anchors for the six dimensions. Score against observable evidence rather than impression —
unanchored scores drift toward 7/10 for everything, and a scorecard where nothing is ever a 3 or
a 9 carries no information at all.

Two rules that matter more than the individual anchors:

- **Score what you can evidence.** If the disclosure does not support a judgement, say so and
  score conservatively rather than generously. An unscoreable dimension is a finding.
- **Low scores are the useful ones.** The value of a scorecard is locating the weak link. A
  report where every dimension lands 7–8 has usually not looked hard enough.

## Contents

- [Business quality](#business-quality)
- [Moat](#moat)
- [Financial health](#financial-health)
- [Management](#management)
- [Valuation](#valuation)
- [Risk profile](#risk-profile)
- [Combining into a verdict](#combining-into-a-verdict)

---

## Business quality

Economics of the business itself: what it earns on the capital it employs, and whether it can
redeploy more at similar rates.

| Score | What it looks like |
| --- | --- |
| 9–10 | ROIC sustained above ~25% through a full cycle, cash conversion at or above 1x, long runway to reinvest at those rates, revenue substantially recurring or repeat |
| 7–8 | ROIC comfortably above cost of capital (roughly 15–25%), good conversion, credible reinvestment opportunities |
| 5–6 | ROIC around the cost of capital; the business earns its keep without creating much surplus |
| 3–4 | ROIC persistently below cost of capital, capital-hungry, or margins structurally thin and falling |
| 0–2 | Destroys capital, structurally negative free cash flow with no path shown, or dependent on continual outside funding |

**Evidence to cite:** ROIC or ROCE across years (not one year), cash conversion, capital intensity,
share of revenue that recurs.

**Trap:** high ROE produced by leverage rather than operating quality. Check ROIC alongside it — a
mediocre business with a lot of debt can post an excellent ROE right up until it cannot.

---

## Moat

Durable pricing power. The test is evidence, not adjectives.

| Score | What it looks like |
| --- | --- |
| 9–10 | Demonstrated pricing power across a cycle — held or raised prices through an input-cost spike without losing volume; share and margins stable or rising over 10+ years against real competition |
| 7–8 | Clear structural advantage (switching costs, network effects, scale economics, regulatory position) with supporting evidence in margins or share |
| 5–6 | Some differentiation, actively contested; margins wobble with competition |
| 3–4 | Largely a price taker; competes on cost or availability |
| 0–2 | Commodity economics with no advantage, or visibly losing share to a better-positioned entrant |

**Evidence to cite:** gross margin through an input-cost shock, realised price increases against
volume, market share over time, customer retention or churn.

**Trap:** confusing brand recognition with pricing power. Plenty of famous brands discount
constantly. The question is whether customers pay *more*, not whether they have heard of it.

---

## Financial health

Whether the company survives two bad years without a rescue.

| Score | What it looks like |
| --- | --- |
| 9–10 | Net cash or trivial leverage, interest cover comfortably above 10x, no near-term maturity wall, cumulative CFO/NI at or above 1x |
| 7–8 | Modest leverage (net debt/EBITDA under ~2x), cover above 5x, staggered maturities |
| 5–6 | Manageable but real leverage (~2–3x), cover 3–5x; the balance sheet constrains options |
| 3–4 | Elevated leverage (3–4x+), cover under 3x, refinancing dependence, or weak earnings quality |
| 0–2 | Covenant pressure, going-concern language, maturities that cannot be funded from operations, or a serious accruals/cash divergence |

**Evidence to cite:** net debt/EBITDA, interest cover, maturity schedule, cumulative CFO/NI, and
any flags raised by `quality_check.py`.

**Trap:** off-balance-sheet obligations — operating leases, guarantees, receivables factoring,
pledged shares. Headline debt can look tame while the real obligations do not.

---

## Management

Judged on capital allocation and candour, not on communication skill.

| Score | What it looks like |
| --- | --- |
| 9–10 | Long record of reinvesting at high returns, acquisitions that earned their cost, buybacks executed at low valuations, candid about mistakes, clean governance |
| 7–8 | Generally sound allocation, promises broadly met, no governance concerns |
| 5–6 | Mixed record — some value-destructive deals or poorly timed buybacks, but no integrity concerns |
| 3–4 | Repeated over-promising, empire-building acquisitions, buybacks at peaks funded with debt, or weak disclosure |
| 0–2 | Governance red flags — auditor resignations, unexplained related-party dealings, restatements, heavily pledged promoter holdings, related disclosures that do not reconcile |

**Evidence to cite:** where cash went over five years and what it returned, guidance versus
outcome, insider buying and selling, board independence.

**Trap:** rating management on how good the investor presentation is. Compare what was promised
three years ago against what happened — that is the only test that cannot be styled.

---

## Valuation

Score the gap between what the price implies and what the business can plausibly deliver. This is
the dimension most often scored on vibes, and it is the one where the reverse DCF gives a real
answer.

| Score | What it looks like |
| --- | --- |
| 9–10 | Price implies decline or near-zero growth for a business that is clearly healthy — a wide margin of safety |
| 7–8 | Price implies materially less than the business has plausibly demonstrated |
| 5–6 | Price implies roughly what the business can achieve — fairly valued, returns come from execution rather than re-rating |
| 3–4 | Price implies growth above what the record supports; needs things to go right |
| 0–2 | Price implies outcomes achieved by a small minority of companies historically — heroic assumptions with no margin for error |

**Evidence to cite:** implied growth from `reverse_dcf.py`, multiples against the company's own
history and a genuine peer set, sensitivity to the discount rate.

**Trap:** anchoring on the share price's own history. A stock down 70% is not cheap if earnings
fell 80%. Value against earnings and capital, never against a past price.

---

## Risk profile

Concentration and fragility — the things that turn a bad year into a permanent loss.

| Score | What it looks like |
| --- | --- |
| 9–10 | Diversified customers, suppliers and geographies; stable demand; low regulatory and technological exposure |
| 7–8 | Some concentration or cyclicality, well understood and managed |
| 5–6 | Meaningful exposure to one customer, regulator, commodity or geography |
| 3–4 | Severe concentration, active regulatory threat, or a credible disruption risk to the core product |
| 0–2 | Existential single point of failure — one customer or licence carrying the business, litigation that could exceed equity, or a technology shift already underway against it |

**Evidence to cite:** customer concentration from the filings, regulatory proceedings, commodity
sensitivity, geographic and political exposure, litigation.

**Trap:** treating volatility as risk. Share-price volatility is not the same as the probability
of permanent capital loss, and this dimension is about the latter.

---

## Combining into a verdict

**Weight for the situation, and say how you weighted.** A leveraged company is dominated by
financial health; a richly priced one by valuation; an early-stage business by moat and
management. Mechanical averaging obscures exactly the thing the reader needs.

**Some low scores are vetoes, not inputs.** A 2/10 on financial health is not offset by a 9/10 on
moat — an excellent business that may not survive its debt maturities is not a buy at any
scorecard average. Say explicitly when a dimension is acting as a veto.

Indicative bands, applied with judgement rather than arithmetic:

| Overall | Verdict |
| --- | --- |
| 8.0+ | Strong buy — quality and price both favourable, rare |
| 6.5–8.0 | Buy |
| 5.0–6.5 | Hold — usually a good business at a full price, or an average business cheaply |
| Below 5.0 | Avoid |

**Conviction is a separate axis from the score.** It reflects how confident you are in the inputs:
disclosure quality, how much rests on estimates, how wide the scenario spread is. A 7.5/10 on thin
disclosure is a low-conviction 7.5, and saying so is more useful than nudging the number down to
express doubt the reader cannot see.
