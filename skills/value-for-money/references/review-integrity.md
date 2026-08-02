
# Review integrity

Read this before treating any rating as evidence.

## Contents

- [Why the rating is the weakest number on the page](#why-the-rating-is-the-weakest-number-on-the-page)
- [Sample size](#sample-size)
- [Distribution shape](#distribution-shape)
- [Hijacked and merged listings](#hijacked-and-merged-listings)
- [Incentivised and manufactured reviews](#incentivised-and-manufactured-reviews)
- [Vetting the seller](#vetting-the-seller)
- [Reading the negatives properly](#reading-the-negatives-properly)
- [Sources worth more than the star rating](#sources-worth-more-than-the-star-rating)
- [What to tell the user](#what-to-tell-the-user)

## Why the rating is the weakest number on the page

Price can be checked against other retailers. Specifications can be checked against the
manufacturer. The star rating can be checked against nothing, is trivially cheap to manufacture,
and is the number most buyers weight most heavily. That combination is why it is worth auditing
rather than reading.

The goal is not cynicism. Most ratings on established products from established sellers are
broadly honest, and treating every listing as fraudulent is as unhelpful as trusting all of them.
The goal is knowing which ratings carry information.

## Sample size

A rating without its count is meaningless, and averages sort in exactly the wrong order:

| Rating | Reviews | What it is worth |
| --- | --- | --- |
| 5.0 | 3 | Almost nothing. Three friends, or three seeded reviews |
| 4.8 | 60 | Weak, and 4.8 at that count is itself a little odd |
| 4.3 | 4,000 | Strong. Enough people, enough spread |
| 4.1 | 50,000 | Very strong, and 4.1 across that many is a genuinely good product |

`value_score.py` applies a Wilson lower bound — the pessimistic end of the confidence interval —
so a thin sample scores below its average on purpose. Compare products on that adjusted number,
not on stars.

The counter-intuitive consequence worth explaining to users: **a 4.3 can be a better product than
a 4.8.** People resist this, and the resistance is why "sort by rating" sells so much rubbish.

## Distribution shape

More informative than the mean, and less commonly faked because faking it well requires effort
that mostly is not spent.

**Genuine consumer products** land roughly at 50-70% five-star, 15-25% four, 5-10% three, 3-6%
two, and 5-15% one. There is always a tail. Couriers damage things, units arrive dead, and some
people are impossible to please.

**The tells:**

- **Missing middle.** 90%+ five-star with almost nothing at two, three and four. Real products
  collect a middle, because "it is fine, slightly disappointing" is the most common honest
  reaction to most purchases.
- **Implausible top share.** Above roughly 92% five-star is higher than well-reviewed flagship
  products achieve.
- **No one-star tail at volume.** Past a few hundred reviews, logistics alone generates ones.
- **Bimodal with nothing between** — a wall of fives and a wall of ones. Often genuine negatives
  buried under purchased positives.

`value_score.py` flags these and excludes the candidate from the price ranking rather than letting
it win. That framing matters: it is not a claim the product is bad, it is a claim the rating is
not evidence about it. Such a product might still be worth buying — judged on the seller, the
warranty and a returns policy you can actually use.

## Hijacked and merged listings

The manipulation most people have never heard of, and the one that most cleanly defeats a careful
buyer.

A seller builds or buys a listing with thousands of good reviews for one product, then swaps the
product. The reviews stay. A page selling a laptop stand with 4.7 from 12,000 reviews may have
earned every one of them as a phone case.

**How to spot it:**

- Reviews describing a different product entirely. Read a few — it is immediately obvious.
- Review photos showing something that is not the item.
- A review timeline where the product name or brand changes partway through.
- Variations on one listing that are unrelated products rather than sizes or colours.
- A review count wildly out of proportion to a product's apparent age.

Marketplaces where a single listing carries many variations are the most exposed. When a review
count looks too good for how new the product is, this is usually why.

## Incentivised and manufactured reviews

- **Review-for-refund schemes.** A card in the box offering a refund or gift card for a five-star
  review. Widespread, against most marketplace policies, and effective.
- **Review farms.** Bulk purchased, often posted in bursts, sometimes with recognisably similar
  phrasing.
- **Vine and early-reviewer programmes.** Disclosed and legitimate, but reviewers who received the
  product free rate systematically higher. Weight them down rather than discounting them.
- **Competitor sabotage.** One-star campaigns exist too, so a sudden cluster of negatives with
  little detail is not automatically a real problem.
- **Velocity spikes.** Hundreds of reviews in days on a product that took months to gather its
  first hundred.

Where a marketplace exposes it, filter to verified purchases. It is not proof — verified purchase
reviews are buyable — but it raises the floor.

## Vetting the seller

On a marketplace you are buying from a seller, not from the marketplace, and this decides whether
the warranty and the return actually exist:

- **Who is the seller?** The brand, an authorised distributor, the marketplace itself, or an
  unknown third party?
- **Seller rating and age.** A new seller with a great rating is a new seller.
- **Where does it ship from?** Cross-border shipping changes the return path, the timeline and
  frequently the warranty.
- **Is it fulfilled by the marketplace?** Usually improves returns, and does nothing for
  authenticity — commingled inventory means a genuine seller's stock can be mixed with
  counterfeits.
- **Is the price much lower than everywhere else?** For branded goods this is the strongest
  counterfeit and grey-import signal there is. A 40% gap on a current-model branded product is not
  a deal.

## Reading the negatives properly

The most useful ten minutes available, and it is not about counting.

**Sort by most recent**, not most helpful. Helpful votes accumulate on old reviews and describe a
product that may since have been revised.

**Look for the repeated specific failure.** One person saying the hinge broke is noise. Fifteen
people saying the hinge broke at around eight months is the product's actual defect, and it will
not appear in any specification.

**Filter for failures that matter to this user.** A keyboard's negative reviews might all be about
Bluetooth pairing on Linux. Decisive for one buyer, irrelevant to another. This is where the
intake pays off — you know which complaints to weight.

**Check whether the complaint is the product or the delivery.** Damaged in transit is a courier
problem and inflates nothing about build quality.

**Read the three-star reviews first.** They are the most honest and the least gamed — nobody pays
for a three-star review. They usually contain the clearest statement of what the product actually
is.

## Sources worth more than the star rating

- **Independent testing outlets** that buy their own units and publish methodology.
- **Long-term owner reports** — subreddits, forums, owners' groups. Six-month reports surface the
  failures that launch reviews cannot.
- **Professional and trade reviews** for tools and equipment, where the reviewer's own work
  depends on the thing.
- **Return rates**, where a retailer exposes them. One of the most honest signals available.
- **The manufacturer's own support forum.** The recurring threads are the recurring defects.

Weight a careful independent test above a thousand marketplace reviews.

## What to tell the user

Be specific about *why* a rating was discounted, because "this looks suspicious" teaches nothing
and invites argument. Compare:

> This product's reviews look unreliable.

with:

> I have left this one out of the ranking. 93% of its 74 reviews are five-star with almost nothing
> at two, three or four — real products collect a middle, and this pattern usually means the
> reviews were helped. That is not a claim the product is bad. It means its rating tells you
> nothing, so it should be judged on the seller and the returns policy instead.

The second is checkable, teaches the buyer what to look at next time, and survives pushback from
someone who has already decided they want the cheap one.
