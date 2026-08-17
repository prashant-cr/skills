---
name: lowest-price-finder
license: MIT
description: Finds the cheapest legitimate place to buy a specific product the user has already chosen, and works out what they will actually pay. Asks only the questions that change the answer — market, exact variant, which bank cards or memberships they hold, whether refurbished is acceptable, when they need it — then searches live listings and ranks stores on landed cost including shipping, fees, duty, card offers and discounted cashback, not sticker price. Screens out grey imports, counterfeit-pattern listings, thin sellers and variant mismatches, treating an implausibly low price as a risk signal rather than a bargain. Quotes no price it did not fetch. Use whenever the user asks where to buy something cheapest, wants the lowest price or best deal on a named product, asks which site or store is cheaper, mentions price comparison, coupons, cashback or bank offers, asks whether to buy now or wait for a sale, or pastes a product link and asks whether the price is good.
---

# Lowest price finder

The user has already decided **what** to buy. This answers **where**, and for
how much all-in.

If they have not decided what to buy — they are choosing between products, or
asking what is worth the money — that is a different job, and the
`value-for-money` skill does it. Say so and switch rather than price-hunting a
product they should not buy.

## Why the cheapest listing is so often the wrong answer

Three failure modes, and sorting a list by price walks into all three:

- **The sticker is not the bill.** Shipping, platform fees, import duty, and a
  card discount the buyer cannot use because they do not hold that bank's card
  all move the real number. A cheaper item with paid delivery routinely loses.
- **You may not be comparing the same product.** A different generation, region
  variant, capacity, colour or bundle looks identical in a column of prices.
  This is the quietest way a comparison becomes meaningless.
- **An implausibly low price is evidence of a problem, not a bargain.** Grey
  imports with no local warranty, counterfeits, and listings that never ship
  all present as the best deal on the page — and a price sort puts them first.

## Prices you may and may not state

Every price is either **fetched** — you retrieved it this session, and you say
from where and when — or it does not go in the answer.

Never state a price from memory. Retail prices move weekly, promotions move
daily, and a remembered price is wrong in the specific way that costs money: it
looks precise. If a page cannot be read, say the price is unverified and hand
the user the link rather than filling the gap with a plausible number.

The same applies to claims about stock, delivery dates and offer terms. "10%
off with HDFC" is a claim with an expiry, a cap and a minimum spend, and the
cap is usually the number that matters.

## Workflow

### 1. Pin the exact product before pricing anything

Get to a single unambiguous variant: model number, capacity, colour, size,
generation, region edition, and whether accessories are bundled. "Sony XM5" and
"Sony XM4" are one character apart in a chat message and thousands apart in
price.

Where listings publish a **GTIN/EAN/UPC**, that is the definitive match — two
listings sharing one are the same physical product. `extract_offer.py` reports
it. Where none is published, confirm by hand and say that you did.

If the user pastes a link, start there: that listing defines the variant, and
the job becomes finding the same thing cheaper.

### 2. Ask the questions that change the answer

Ask these together, in one message, then proceed. Six questions asked once is
service; twenty asked one at a time is an interrogation, and the user came here
to buy something.

Only these reliably change the ranking:

1. **Which country, and roughly where?** Decides which stores exist at all,
   shipping cost, duty, and sometimes the price itself.
2. **Which cards, wallets or memberships do you have?** In India especially,
   bank offers routinely move the effective price by 5–10%. **An offer the
   buyer cannot use is not a discount**, and this is the single most common
   reason a published "best price" is wrong for the person reading it.
3. **New only, or is refurbished / open-box acceptable?** Often the largest
   single saving available, and entirely a preference.
4. **When do you need it?** Kills slow sellers, and decides whether "wait for
   the sale" is even available.
5. **Do you need manufacturer warranty?** The dividing line between the grey
   market and the official one, and the reason for most suspiciously cheap
   listings.
6. **Any store you already trust or want to avoid?** Cheap and unusable is not
   cheap.

When the user does not answer, **state your assumption and continue** — deliver
the comparison with assumptions visible rather than blocking on a reply. A
wrong assumption they can see is cheap to correct; a missing answer is not.

`references/questions.md` covers what to do with each answer and which further
questions are worth asking for particular categories.

### 3. Find the offers

Search live. Cover, in roughly this order of yield:

- The big marketplaces for that market, plus the **brand's own store** — which
  is often price-matched, and carries warranty without argument
- Category specialists (electronics chains, pharmacy, grocery) — frequently
  undercut marketplaces on their own categories
- Price-comparison and price-history sites for that market
- Coupon and cashback aggregators, checked against the specific product

Aim for five to eight real offers. Two is not a comparison, and twenty is
mostly duplicates of the same seller.

`references/finding-offers.md` lists sources by market, including price-history
tools, and covers what to do about listings you cannot read.

### 4. Read each listing's real price

```bash
python3 scripts/extract_offer.py <url> [<url> ...] --json
```

Pulls price, currency, availability, condition, seller, rating and the
GTIN/MPN out of the page's structured data, which is more reliable than the
rendered markup — a page displaying "from ₹1,299" often carries the real
variant price underneath.

Large marketplaces block plain HTTP clients. When that happens the script says
so rather than returning an empty price. **A blocked page is not a page with no
stock** — open it in a browser, or use search results, and record the number by
hand with its timestamp.

### 5. Rank on landed cost

```bash
python3 scripts/compare_offers.py --example > offers.json   # documented format
python3 compare_offers.py offers.json
```

Computes what the buyer actually pays: price plus shipping, fees, duty and tax,
minus instant discounts, coupons, **card offers they can actually use**, and
cashback discounted to what it is worth in hand. Store credit arriving in 60
days is not the same as money off at checkout, and counting it at face value is
how "effective price" marketing wins.

It refuses to rank any offer lacking a URL and a fetch timestamp, screens for
the traps below, and reports the excluded listings with reasons rather than
hiding them — some reasons the buyer will happily accept.

**Check exchange or trade-in on anything a buyer is replacing** — phones,
laptops, televisions, large appliances. The quoted value routinely exceeds
every discount under discussion and it differs by store, so it belongs in the
price rather than in a footnote (`exchange_value` in the offer). Flag that the
quote is provisional and reassessed at pickup, because downgrades at the door
are common.

### 6. Take the trap screening seriously

The script flags these; the judgement is yours:

- **Condition and warranty** — refurbished or grey-import when the buyer wanted
  new with manufacturer cover
- **Variant mismatch** — a GTIN that does not match
- **Thin or poor sellers** — few ratings is as informative as bad ratings
- **Price anomaly** — far below the median of the legitimate offers

That last one is the inversion worth internalising: **the more a price beats
the market, the more evidence it needs**, not less. `references/traps.md`
covers counterfeit and grey-market signals, seller vetting, and how to tell a
real discount from an inflated "was" price.

### 7. Say whether to buy now or wait

A complete answer includes timing. Check whether the current price is actually
good against its own history, and whether a known sale is close — in India the
festive sales move electronics far more than day-to-day discounting does.
`references/india.md` covers the sale calendar, bank-offer mechanics, GST
invoice and grey-import specifics.

Where the user needs it now, say so and stop. Where waiting three weeks saves
15%, that is worth more than any store choice.

## Report structure

```markdown
# Best price: <exact product and variant>

**Buy from: <store> — <total landed price>**
<One line: why this one, including the offer or condition that decided it.>
<Direct link.>

## What you actually pay
| Store | Seller | Sticker | Shipping/fees | Offers applied | **You pay** | Delivery |
<Ordered by landed cost. Note where the lowest sticker is not the lowest bill.
Name the seller on marketplace listings and say who honours the warranty — the
platform is not the seller, and on Amazon or Flipkart that distinction decides
returns and whether the item is genuine.>

## Excluded, and why
<Cheaper listings that failed screening, each with its reason. The buyer
decides whether the reason matters — do not silently drop them.>

## Buy now or wait
<Price against its recent history, any sale close enough to matter.>

## Assumptions and what I could not verify
<Assumed market, variant, cards. Any listing that could not be read, with the
link so the user can check it themselves.>
```

Lead with the answer. Someone asking where to buy a kettle wants a store and a
number in the first two lines, not a methodology.

## Judgement calls

**Small differences are not worth the user's time.** If the top three are
within 2%, say they are equivalent and pick on delivery speed, return policy or
trust. Sending someone to an unfamiliar store to save ₹80 is bad advice
dressed as diligence.

**Total, not per-item, when quantity is in play.** Bulk pricing, free-shipping
thresholds and multi-buy offers change the ranking, sometimes inverting it.

**A trusted store at a small premium is often correct.** Returns that work,
warranty honoured without argument, and a card already on file have real value.
Name the premium and let the buyer choose rather than deciding for them.

**Marketplace ≠ seller.** On Amazon and Flipkart, the platform is not who ships
it. The seller determines warranty, returns and whether the item is genuine, so
report the seller, not just the site.

**Say when the search was thin.** If only two stores could be read and three
were blocked, the answer is "cheapest of what I could verify", not "cheapest
available". State which is which.

**Do not defeat bot protection to read a price.** If a store blocks automated
access, hand the user the link. A price is not worth building a scraper for,
and the repo's own `scrape-feasibility-audit` covers why that fight is not
winnable in an afternoon.
