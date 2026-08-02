# True cost

Read this when costing the shortlist. The sticker is the smallest part of most of these decisions.

## Contents

- [Cost the horizon, not the purchase](#cost-the-horizon-not-the-purchase)
- [Consumables by category](#consumables-by-category)
- [Subscriptions](#subscriptions)
- [Resale value](#resale-value)
- [Is the discount real](#is-the-discount-real)
- [Sale timing](#sale-timing)
- [Warranty and returns as costs](#warranty-and-returns-as-costs)
- [Financing framings](#financing-framings)
- [When cheap is correct](#when-cheap-is-correct)

## Cost the horizon, not the purchase

Ask how long they intend to keep it, then total everything that happens in that window. The
ranking frequently inverts, and the direction is predictable: **the cheaper purchase is often the
more expensive ownership**, because that is the business model.

The classic is a printer. A device at a third of the price with cartridges at three times the
price crosses over inside a year for anyone who prints. It is not a trick anyone hides — it is
simply invisible at the moment of choosing, because the two numbers are on different pages.

`value_score.py` takes consumables, subscriptions, one-off accessories and expected resale, and
reports the total over the horizon.

## Consumables by category

Worth checking specifically, since these are where lifetime cost hides:

- **Printers** — ink or toner per page. Compare cost per page, not cartridge price. Check whether
  third-party cartridges work or are blocked by firmware, and whether the firmware updates itself
  to block them later.
- **Coffee machines** — pods versus ground. A pod machine's lifetime cost is dominated by pods,
  and the lock-in is the point.
- **Razors, toothbrushes, water filters, vacuum bags** — the handle is priced to sell the refills.
- **Anything with a battery** — phones, laptops, e-bikes, cordless tools, earbuds. Ask whether it
  is replaceable and what a replacement costs. Sealed earbuds with a two-year battery are a
  two-year product.
- **Cordless tool ecosystems** — the battery platform is the real purchase. The second tool is
  cheap only if it shares the battery.
- **Cameras** — lenses, cards, spare batteries. The body is the down payment.
- **Cars and appliances** — servicing intervals, parts availability, insurance.
- **Smart home devices** — do they keep working if the vendor's service closes?

## Subscriptions

Increasingly attached to hardware, and easy to miss because the device works without it until it
does not:

- Cloud storage for cameras and doorbells, where local recording is often deliberately limited.
- Software subscriptions attached to a device.
- Connectivity fees.
- Features behind a paywall that the box implies are included.

Multiply by the horizon. A modest monthly fee over three years frequently exceeds the price
difference between the options being compared.

## Resale value

Works in the buyer's favour and is routinely ignored. Cost of ownership is purchase minus what it
is worth when they are done.

Products with strong resale — some phone and laptop brands, quality tools, well-known camera
systems — can be genuinely cheaper to own despite costing more to buy. Something that holds half
its value over three years versus a fifth is a large difference on a substantial purchase.

Only count it if they would actually sell. Many people will not, and for them it is zero.

## Is the discount real

A discount is measured against a number the seller chose.

- **Check the price history.** Price-tracking tools exist for the large marketplaces and are the
  fastest way to see whether "60% off" is off a price anyone ever paid. A list price that rose
  the week before a sale is the oldest move there is.
- **Compare across retailers**, not against the strikethrough. The real reference price is what
  else it costs today.
- **Watch for model substitution.** The heavily discounted model is often a slightly different
  SKU built for the sale, with a cheaper panel or less memory.
- **Bundles** can hide the price of the thing you want behind accessories you do not.
- **Check the total**, not the headline. Shipping, install, mandatory accessories, extended
  warranty pressure at checkout.

## Sale timing

Worth naming a specific window, not a vague "prices may fall". A recommendation to wait is only
actionable with a date and an expectation.

- **India** — the big festive sales around September and October are genuine for electronics and
  appliances, and the discounting on the previous generation is usually deepest. Republic Day
  sales in January are the next tier.
- **Global** — Black Friday and Cyclone/end-of-season events, and the weeks after a new model
  launches, when the outgoing one is cleared.
- **Product cycles** matter more than calendar sales. Buying a phone or laptop weeks before its
  successor is announced is the single most avoidable mistake in the category. Check the release
  cadence.
- **End of financial year** for vehicles and appliances in some markets.

If a known window is close enough to matter, say when, say what moved last time, and let them
decide whether waiting is worth it.

## Warranty and returns as costs

- **Warranty length and what voids it.** In India specifically, warranty on marketplace purchases
  frequently depends on the seller being authorised and on a GST invoice — see
  `references/india-retail.md`.
- **Where service happens.** A brand with no service presence in the user's city is a different
  product from the same brand with a service centre nearby.
- **The return path.** Free returns within a window is real money and real risk reduction,
  especially for anything fit-dependent. A non-returnable marketplace listing at a small discount
  is usually the worse deal.
- **Extended warranties** are usually poor value on reliable products, and occasionally sensible
  on expensive ones with known failure modes and costly repairs. Judge on the specific failure
  rate, not on principle.

## Financing framings

Designed to make the total look smaller:

- **No-cost EMI** is not free. The interest is generally built into the price, and paying upfront
  sometimes unlocks a discount of similar size. Compare the cash price against the total of the
  instalments.
- **Exchange offers** bundle a trade-in value into the discount. Check what the old device is
  worth sold privately — it is frequently more.
- **Bank and card offers** are real but conditional. Check the minimum spend, the cap, and whether
  the user actually holds the card.
- **Cashback** paid as store credit is worth less than cash and often expires.

None of these are traps exactly. They are just presented as savings when they are financing, and
the comparison should be on total outlay.

## When cheap is correct

Being sceptical of cheap options is not the same as recommending expensive ones. Categories where
the premium mostly buys brand:

- Cables and adapters meeting a published standard.
- Basic storage from any reputable manufacturer.
- Commodity consumables where a specification is met.
- Tools for genuinely occasional use, where a professional-grade version will be used four times.
- Products in a category that has fully converged, where the differences are real but small enough
  that nobody would notice them in the intended use.

Say so when it applies. **The point is finding the floor, not confirming the ceiling** — a
recommendation to spend less, with a reason, is worth more than a safe recommendation to spend
more.
