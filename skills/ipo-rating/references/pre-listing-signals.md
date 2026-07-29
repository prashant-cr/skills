# Pre-listing signals

Everything that tells you how an issue will be received before it trades: the grey market where
one exists, subscription figures, and the anchor book. These drive the listing-day verdict.

They tell you almost nothing about the long-term verdict, and keeping that separation is the whole
point of reading them carefully.

## Contents

- [Grey market premium](#grey-market-premium)
- [Where a pre-listing market exists](#where-a-pre-listing-market-exists)
- [Subscription figures](#subscription-figures)
- [The anchor book](#the-anchor-book)
- [Putting the demand read together](#putting-the-demand-read-together)

---

## Grey market premium

In India, GMP is an unofficial over-the-counter quote for what IPO shares are changing hands at
before listing. It is quoted per share, on top of the issue price: a band of ₹105 with a GMP of
₹31 implies a listing around ₹136.

Retail investors track it closely, and any honest IPO analysis has to engage with it — refusing to
mention it does not make people ignore it, it just means they read it somewhere with no caveats
attached.

**What it genuinely is:** a real-money sentiment reading. People are quoting prices they will
transact at, which makes it more informative than a survey. It correlates with listing-day pops
often enough to be worth knowing.

**What it is not, and this matters more:**

- **Unofficial and unregulated.** No exchange, no regulator, no clearing. SEBI does not recognise
  it. Trades are settled on trust and are not enforceable.
- **Thin.** Volumes are small relative to the issue, so the quote moves on little activity.
- **Movable.** A quote that costs little to push, and that materially affects retail subscription,
  is an obvious target for anyone with an interest in the issue looking hot. Treat a GMP that
  spikes late in the bidding window with particular suspicion.
- **Listing-day only.** It says nothing about where the stock trades in a month. Issues that
  listed at a large premium and then fell below issue price within a quarter are common.
- **Least reliable when it matters most.** On heavily hyped issues — exactly the ones where people
  lean on it hardest — it has the widest error.

**Related quotes you may see in India:** *kostak* is a fixed price paid for an application
regardless of allotment; *subject to sauda* is a price paid only if the application receives
allotment. Both are the same unregulated market and carry the same caveats.

**How to use it.** Report the level, report the direction of travel over recent days (a fading GMP
during bidding is a meaningful negative signal), and always show it beside the flat and downside
cases. `scripts/ipo_math.py --gmp` prints those together for exactly this reason.

**Where to draw the line.** Reading GMP as published data is ordinary analysis. Advising someone
on how to transact in the grey market is different — it is unregulated, unenforceable, and outside
what this skill does. Report it; do not route people into it.

---

## Where a pre-listing market exists

Grey markets are not universal. The absence of one is itself worth stating, because it means the
listing-day read rests entirely on subscription and anchor data.

| Market | Pre-listing price signal |
| --- | --- |
| **India** | Active grey market. GMP widely quoted by financial media and IPO sites. |
| **Hong Kong** | Formal grey market run by brokers on the evening before listing — more transparent than India's, with actual reported prices. |
| **United Kingdom** | Conditional dealing: shares trade on the exchange for several days before unconditional dealing begins. Real exchange prices, not a grey market. |
| **United States** | Essentially none. No retail-visible pre-listing price. The read comes from pricing versus the initial range, deal upsizing and institutional demand reported in the press. |
| **Japan, most others** | No meaningful grey market. Rely on subscription and allocation data. |

**In the US, the closest equivalent to a demand signal is where the deal prices relative to the
filed range.** Pricing above the range, or raising the range mid-roadshow, indicates strong
institutional demand; pricing below indicates the opposite. That is public and reliable, unlike a
grey market quote.

---

## Subscription figures

Published daily while bidding is open, broken down by investor category. This is the most
informative demand data in markets that have it, because it is official and exchange-reported.

**India's categories** (standard book-built issue for a profitable company):

| Category | Allocation | What its demand tells you |
| --- | --- | --- |
| QIB — qualified institutional buyers | 50% | The most informative. These bidders do real work and have access to management. |
| NII / HNI — non-institutional | 15% | Often leveraged and short-horizon; heavy NII demand frequently signals a flipping trade rather than conviction. |
| Retail | 35% | Least informative and most sentiment-driven — frequently follows GMP rather than leading it. |

For an issuer that does not meet SEBI's profitability criteria, the split changes to **QIB 75%,
HNI 15%, retail 10%**. That reallocation is itself a signal worth surfacing: it tells you the
company came to market under the route reserved for issuers without a qualifying profit record.

**Reading it well:**

- Weight QIB demand most heavily and retail least. An issue with 40x QIB and 3x retail is a very
  different proposition from 3x QIB and 40x retail, even at the same headline number.
- Watch the shape over the window. Institutional bids often land on the final day, so a quiet
  QIB book on day one is not yet a signal; a quiet one at close is.
- Total subscription determines allotment odds. Heavy retail oversubscription means allotment is
  a lottery — applying is not receiving, and the user should know that before planning around it.

---

## The anchor book

Anchor investors are allocated shares a day before the issue opens, at a fixed price. The book is
disclosed, and it is a strong signal because these are informed buyers committing before the
public.

**What to look for:**

- **Who took it.** Long-only domestic and global institutions, sovereign funds and insurers signal
  conviction. A book dominated by short-horizon or momentum money signals a trade.
- **Concentration.** A handful of names taking most of the book is more fragile than broad
  participation, because their lock-in expiry becomes a single large event.
- **Whether it filled at the top of the band.** Anchors priced at the upper band alongside strong
  names is the best pre-listing signal available in India.

**Then check when they can sell.** Since April 2022, Indian anchor allocations unlock in two
tranches — 50% at 30 days from allotment, 50% at 90 days. `scripts/lockin_calendar.py` maps these
alongside the promoter and pre-IPO expiries.

---

## Putting the demand read together

A defensible listing-day view usually rests on three things agreeing: strong QIB subscription, a
quality anchor book, and a stable or rising grey market. When they disagree, trust them in that
order — official institutional data first, unregulated sentiment last.

And regardless of how strong the demand read is, keep it out of the long-term verdict. Demand
signals describe how many people want the shares this week. They say nothing about what the
business is worth, and conflating the two is the specific error this skill exists to prevent.
