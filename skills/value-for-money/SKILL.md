---
name: value-for-money
license: MIT
description: Finds the product that is genuinely the best buy for one person's use — asks what the thing is actually for, searches live listings, then ranks candidates on cost of ownership rather than sticker price, with ratings confidence-adjusted for how many reviews back them and manufactured-looking review distributions excluded rather than rewarded. Quotes no price it did not fetch, and is willing to answer that the right move is last year's model, a refurbished unit, waiting for a known sale, or not buying. Knows Indian retail specifics like seller warranty, GST invoice, grey imports and festive cycles, and asks the market first. Use whenever the user wants help choosing what to buy, asks which product is best or best value, wants the cheapest good option, a recommendation under a budget, a comparison between two or three products, whether something is worth the money or worth upgrading to, whether a deal or discount is real, or whether a product's ratings and reviews can be trusted.
---

# Value for money

Finds the thing worth buying for one specific person, and says plainly when that thing is
cheaper, older, second-hand, or nothing at all.

## The one idea that organises everything below

**"Best value" is a claim about a particular person's use, and both of its inputs are actively
manipulated.**

The rating is manipulated because reviews are cheap to buy and listings can be hijacked — a page
that sold phone cases last year keeps its 4.7 from 40,000 reviews when it starts selling laptops.
The price is manipulated because a discount is measured against a number the seller chose, and
"60% off" usually means the list price was set to make that sentence true.

So the work splits three ways, and skipping any one produces a confident wrong answer:

1. **Pin the use**, because the cheapest camera that is good enough is a different product for a
   travel vlogger and a wedding photographer, and neither is "the best camera".
2. **Verify the rating is evidence**, not decoration.
3. **Verify the price is real**, and is the whole price.

A recommendation that skips step 1 is a specification sheet. One that skips 2 and 3 is an
advertisement.

## Ask before you search

The user knows what they want the product *for*. They usually do not know which specifications
deliver it, which is why they asked. So ask about the use, not the specs.

Ask in one short block — six questions answered in one reply beats twelve delivered one at a
time. Always establish:

- **The market.** Price, availability, warranty and which sellers are trustworthy all differ by
  country. Default to India when nothing suggests otherwise, and say that you are assuming it.
- **What it is for**, concretely. Not "a laptop" but what runs on it, where, for how long a day.
- **Budget**, and whether it is firm. Ask what they would spend if something clearly better sat
  just above it — a surprising number of people have a soft ceiling and a hard one.
- **What they own now** and why they are replacing it. The reason is usually the real
  requirement, and it is frequently not the one they lead with.
- **How long they expect to keep it.** This decides whether ownership costs matter more than the
  purchase.
- **Any non-negotiables** — a port, a size, a brand they refuse, an ecosystem they are locked to.

`references/intake.md` has the questions that matter per category, and the ones that look
relevant but are not.

Two judgement calls. If they have already given you most of it, **build the shortlist and state
your assumptions** rather than interrogating them. And if the honest answer needs one fact you do
not have — the market, usually — ask only for that.

## Workflow

### 1. Search live, and record where every number came from

Prices change weekly, stock changes daily, and a recalled price is worse than no price because it
looks like research. Fetch listings and record the URL and the time for each. Where a listing will
not render or a price sits behind a login, **mark it unverified rather than filling in something
plausible** — an invented number does not announce itself, it just quietly wins or loses the
comparison.

Search broadly before narrowing: the retailer's own site, the marketplaces, and at least one
independent review source. A shortlist drawn from one marketplace inherits that marketplace's
incentives.

### 2. Judge the reviews before you judge the product

The two questions are separate, and this one comes first, because a rating you cannot trust is
not a cheap product — it is an unknown one.

**Sample size changes what a rating means.** 5.0 from 6 reviews is weaker evidence than 4.3 from
4,000, yet every "sort by rating" control ever built disagrees. The script handles this with a
confidence bound.

**Shape matters more than the average.** Genuine products accumulate a middle: people who are
mildly disappointed leave three stars, couriers damage things and produce ones. A distribution
that is 93% five-star with almost nothing between the extremes has usually been helped. Read the
histogram, not the headline number.

`references/review-integrity.md` covers the rest — hijacked listings, incentivised reviews,
seller vetting, and how to read the negative reviews for the failure that would actually bother
*this* user rather than the loudest complaint.

### 3. Cost it over the time they will own it

```bash
python3 scripts/value_score.py --example > shortlist.json   # fill from your fetched listings
python3 scripts/value_score.py shortlist.json --years 3
```

It confidence-adjusts each rating, totals cost of ownership across the horizon, excludes
candidates whose review distribution looks manufactured, refuses to rank anything without a
source and timestamp, and separates options that fail the quality bar from options that are
merely expensive.

**Cost of ownership is where the ranking usually inverts.** Ink, pods, blades, filters, batteries
and subscriptions routinely exceed the purchase price over three years, and the cheap unit is
frequently the one designed to make that happen. Resale value works the other way and is
similarly ignored — a phone that holds half its value is much cheaper to own than one that holds
a fifth.

`references/true-cost.md` covers consumables by category, price history, sale timing, and the
financing framings that make a total look smaller than it is.

### 4. Say what to actually do, including the answers that are not a purchase

The genuinely useful answers are frequently not "buy the one I picked":

- **Buy last year's model.** The delta between generations is often a marketing bullet and a
  price step. Name the actual difference and what it costs.
- **Buy refurbished with a warranty**, where a reputable channel exists.
- **Wait**, when a known sale window is close enough to matter. Say the window and the expected
  move, not a vague "prices may drop".
- **Buy nothing**, when what they own does the job, or when nothing in the budget does it and
  buying a thing that cannot is worse than waiting to afford one that can.
- **Buy the cheap one deliberately**, when the category has genuinely converged and the premium
  buys brand rather than function.

Someone who came for a product name and leaves having not spent money they were about to waste
has been served well. Say it plainly and give the reason, then let them decide.

## Output format

```
## What I understood you need
[One or two lines. State assumptions explicitly, especially the market.]

## The pick
[Product, price with retailer and timestamp, and the one-sentence reason it wins for
 this use. If the recommendation is wait, used, older, or nothing, that goes here.]

## How the options compare
[Table: price, cost over the horizon, rating with review count, adjusted score.
 Anything excluded for unreliable reviews or unverified price is listed separately,
 with the reason.]

## What you are giving up
[The honest weakness of the pick, and who should buy the runner-up instead.]

## Before you buy
[Seller and warranty checks, what makes the price real, the return path, and the
 sale window if one is close.]
```

Show the timestamp beside every price. A price without a time is a claim, not a fact.

## Failure modes to avoid

- **Quoting a price from memory.** Fetch it or mark it unverified. This is the fastest way to
  produce confident nonsense in this domain.
- **Ranking by star rating.** It ignores sample size and rewards manipulation. Use the adjusted
  score.
- **Trusting a suspiciously perfect distribution.** 93% five-star is not excellence, and the
  correct response is to exclude the rating as evidence rather than to praise it.
- **Comparing sticker prices** where consumables or subscriptions differ. Cost the horizon.
- **Recommending the most expensive option because it is safest.** Over-buying is the quiet
  failure — it always works, so nobody discovers the cheaper thing would have too.
- **Recommending the cheapest thing that cannot do the job.** That wastes all of the money rather
  than some of it.
- **Ignoring the market.** A price, a warranty and a seller mean different things in different
  countries.
- **Presenting a specification table as a recommendation.** They asked what to buy.
- **Padding the shortlist.** Three genuinely considered options beat ten listed ones.

## Reference files

- `references/intake.md` — what to ask, by category, and how the same product becomes the wrong
  answer for a different use.
- `references/review-integrity.md` — read before trusting any rating. Manipulation patterns,
  hijacked listings, seller vetting, how to read negatives usefully.
- `references/true-cost.md` — consumables, subscriptions, resale, price history, sale timing,
  warranty and financing framings.
- `references/india-retail.md` — read when the market is India. Marketplace sellers, warranty and
  GST invoices, grey imports, festive cycles, EMI. Has a short section on other markets.
