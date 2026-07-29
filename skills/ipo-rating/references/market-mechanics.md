# Market mechanics

How the IPO process works per market: the documents, the timetable, who can bid for what, and the
local quirks that change the decision. Read the section for the market in play.

Lock-in schedules are computed by `scripts/lockin_calendar.py`; this file covers everything else.

## Contents

- [India](#india)
- [United States](#united-states)
- [United Kingdom](#united-kingdom)
- [Hong Kong](#hong-kong)
- [Markets not listed here](#markets-not-listed-here)

---

## India

**Documents:** DRHP (draft, filed with SEBI for review) then RHP (red herring prospectus, with the
price band, filed before the issue opens). The RHP is the primary source and is free on SEBI's
site, the exchanges and the lead managers' sites.

**Timetable:** typically issue opens for three business days, allotment a few days after close,
listing within about a week of close. The user's decision window is therefore short — lead with it.

**Allocation** for a mainboard book-built issue:

| Route | QIB | NII/HNI | Retail |
| --- | --- | --- | --- |
| Standard (issuer meets profitability criteria) | 50% | 15% | 35% |
| Issuer does not meet those criteria | 75% | 15% | 10% |

The second route exists for companies without a qualifying track record of profits. When you see
the 75/15/10 split, say so in the report — it is a disclosed fact about the issuer's history that
most retail applicants never notice.

**Applying:** retail applications are capped at ₹2 lakh; above that an applicant is NII/HNI.
Applications are in lots, and in an oversubscribed retail category allotment is by lottery — one
lot per successful applicant, many applicants get nothing. Applying is not receiving.

**Lock-ins** (see the script for dates): anchor 50% at 30 days and 50% at 90 days from allotment;
pre-IPO non-promoter holders about six months; promoter holding above the minimum contribution
about six months; the minimum promoter contribution of 20% of post-issue capital for 18 months.

**Quirks that matter:**

- **Price bands and circuit limits on listing.** Newly listed stocks are subject to price bands
  that can lock the stock limit-up or limit-down, meaning a quoted listing gain may not be
  realisable on day one.
- **SME issues are a different asset class.** Much smaller, far thinner liquidity, higher minimum
  application, and vastly more volatile listings. Rate them with an explicit liquidity and exit
  warning; the retail protections and coverage that apply to mainboard issues do not carry over.
- **Grey market premium is widely quoted** — see `pre-listing-signals.md` for how to handle it.

---

## United States

**Document:** Form S-1 (or F-1 for foreign issuers), filed publicly with the SEC and amended
through the process. Free on EDGAR. Note that EDGAR blocks some automated fetchers, so a failed
fetch is a tooling problem rather than evidence the filing does not exist — say which.

**Timetable:** confidential filing is common, then a public S-1, a roadshow of roughly two weeks,
pricing the evening before trading, and the open the next morning.

**Process differences that matter:**

- **There is no retail allocation to speak of.** Shares go to institutions through the
  underwriters; most retail buyers purchase in the open market after the stock lists, at whatever
  the first trade is. "Should I apply?" often does not apply — the real question is whether to buy
  on day one, which is a different and usually worse trade.
- **Pricing versus the filed range is the demand signal.** Pricing above the range or raising the
  range mid-roadshow indicates real institutional demand.
- **The greenshoe** (over-allotment option, typically 15%) lets underwriters stabilise the price
  after listing, which can support the stock early and mask true demand.
- **Quiet period** limits company communication; analyst coverage from the underwriting banks
  begins later and is not independent.
- **Direct listings and SPACs are not IPOs.** No new capital is raised in a direct listing and
  there is no traditional lock-up structure. SPAC mergers have entirely different economics and
  dilution. Identify which structure you are actually looking at before rating it.

**Lock-up:** commonly 180 days, contractual rather than regulatory, sometimes with early-release
triggers tied to price or the first earnings report. Read the prospectus.

---

## United Kingdom

**Document:** a prospectus approved by the FCA. Listings are on the Main Market (with premium and
standard segments) or AIM, which is lighter-touch.

**Process:**

- **Conditional dealing** runs for several days before unconditional dealing. Trades happen at
  real exchange prices but are void if the admission does not complete. This is the closest UK
  equivalent to a pre-listing price signal and is far more reliable than a grey market, since it
  is exchange-reported.
- Retail access is limited on many UK IPOs; institutional placings dominate, with retail
  participation via intermediaries where offered at all.

**Lock-ups** are negotiated per deal and disclosed in the prospectus — commonly 180 days for
directors, often longer for founders. There is no statutory period.

**AIM issues** carry lighter disclosure and governance requirements and far thinner liquidity.
Rate them with the same caution as Indian SME issues.

---

## Hong Kong

**Document:** a prospectus filed with HKEX and the SFC.

**Process:**

- A genuine **retail tranche** exists, with a clawback mechanism that increases the retail
  allocation when retail oversubscription is heavy — so retail demand mechanically changes the
  split, unlike most markets.
- A **broker-run grey market** operates the evening before listing with reported prices. More
  transparent than India's grey market, and a reasonable listing indicator.
- **Cornerstone investors** are the local equivalent of anchors, typically with a six-month
  lock-up, and are disclosed in the prospectus.

**Lock-up:** controlling shareholders are restricted from disposing for six months after listing,
and from ceasing to be controlling for twelve.

---

## Markets not listed here

Establish and state these before rating anything:

1. The prospectus equivalent and where it is filed.
2. Whether retail can participate at issue, or only buy after listing.
3. The allocation split between institutional and retail.
4. Whether any pre-listing price signal exists — and say so plainly when none does, because it
   changes how much weight the listing-day verdict can carry.
5. Lock-up periods, statutory or contractual.
6. Whether price limits apply on the listing day, which affects whether a quoted gain is
   realisable.
