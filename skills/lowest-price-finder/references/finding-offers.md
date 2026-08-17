# Finding the offers

Where to look, in what order, and what to do about pages you cannot read.

- [Search strategy](#search-strategy)
- [Sources by market](#sources-by-market)
- [Price history](#price-history)
- [Coupons and cashback](#coupons-and-cashback)
- [Pages you cannot read](#pages-you-cannot-read)
- [Recording an offer](#recording-an-offer)

## Search strategy

Search the **exact product string**, not a description. Model numbers are the
highest-signal query available: `WH-1000XM5` finds the product, "sony noise
cancelling headphones" finds a category and a hundred wrong variants.

Query shapes that work:

- `"<exact model>" price` — the baseline
- `"<exact model>" site:<retailer domain>` — for a specific store
- `<GTIN or EAN>` — an exact-product search across every store that publishes it
- `"<exact model>" coupon OR "promo code"` — separately, after the price sweep
- `<model> price history` — for the buy-now-or-wait question

Aim for **five to eight verified offers**. Two is not a comparison. Beyond
about eight you are usually collecting duplicate listings of the same seller
through different affiliate wrappers.

Cover at least: the market's two largest general marketplaces, the brand's own
store, one category specialist, and one price-comparison site.

## Sources by market

**India** — Amazon.in, Flipkart, and then the specialists that routinely
undercut them in their own categories: Croma, Reliance Digital and Vijay Sales
(electronics), Tata CLiQ, Myntra and Ajio (fashion), Nykaa (beauty), BigBasket
and Blinkit (grocery), 1mg and PharmEasy (pharmacy), plus the brand's own India
store. Price-comparison: MySmartPrice, PriceDekho, Smartprix. Price history for
Amazon: Keepa, camelcamelcamel.

Brand stores in India frequently match marketplace prices and sometimes beat
them with their own bank offers, and warranty claims are simpler. Always check.

**US** — Amazon, Walmart, Target, Best Buy, B&H and Adorama (photo/audio),
Newegg (components), the brand store. History: camelcamelcamel, Keepa.
Comparison: Google Shopping.

**UK/EU** — Amazon, Argos, Currys, John Lewis (UK); MediaMarkt, Bol, Cdiscount
(EU); idealo and Geizhals for comparison, which are unusually good.

**Anywhere** — Google Shopping is the fastest way to see many sellers at once,
though it misses stores that do not feed it and its prices lag. Treat it as a
way to *find* sellers, then verify on the seller's own page.

## Price history

The buy-now-or-wait question needs the product's own past, not its claimed
discount. A "40% off" against an invented list price tells you nothing; a price
that has sat at ₹26,990 for six months and is now ₹24,990 tells you plenty.

Where a history tool exists (Keepa and camelcamelcamel for Amazon,
comparison sites elsewhere), read: the all-time low, the typical price over the
last 90 days, and whether the current price is genuinely below trend.

Where none exists, the spread of current legitimate sellers is a workable
substitute — a price near the bottom of a tight cluster is a good price, and a
price far below a tight cluster needs explaining.

## Coupons and cashback

Check these **after** establishing the base prices, because they attach to
specific stores and can invert a ranking.

- **On-page coupons** — marketplace "clip this coupon" tiles, which often do
  not show in the displayed price
- **Store promo codes** — verify against the actual product; most codes exclude
  the categories people want them for
- **Cashback portals** — real money, but paid later and sometimes rejected;
  count them at a discount, which `compare_offers.py` does
- **Bank and card offers** — usually the largest, and only if the buyer holds
  the card

Be sceptical of coupon aggregator sites: most listed codes are expired or
fabricated to earn the click. A code is worth counting once it has been seen to
apply, not because a site claims it exists.

## Pages you cannot read

Large marketplaces block automated clients. `extract_offer.py` reports a block
rather than returning an empty price, because a blocked page is not a page with
no stock, and recording it as unavailable is worse than recording nothing.

When a page will not read:

1. **Use the search result snippet.** Search engines and Google Shopping often
   carry a price and a timestamp for the same listing.
2. **Try the mobile or AMP URL**, which is sometimes served without the wall.
3. **Ask the user.** They can open the page in one second, and it keeps them in
   the loop on a purchase they are making.
4. **Say it is unverified** and hand over the link.

Do not attempt to defeat bot protection to read a price. It is against the
operator's stated wishes, it breaks constantly, and the number is available by
just asking. Where a user wants to understand what a site is running,
`scrape-feasibility-audit` in this repo covers it properly.

## Recording an offer

Every offer needs a **URL and a fetch timestamp**, because `compare_offers.py`
refuses to rank without them, and because a price with no time on it is a
rumour. Also capture, where visible:

| Field | Why |
| --- | --- |
| price, currency | the base |
| shipping, fees, duty | the difference between sticker and bill |
| instant discount, coupon | applied at checkout |
| card offer + which card | only counts if the buyer holds it |
| cashback + type + delay | discounted to present value |
| condition | new / open-box / refurbished / used |
| warranty | manufacturer / seller / none |
| seller name, rating, count | who actually ships and honours it |
| official store | brand or authorised dealer |
| GTIN | proof it is the same product |
| in stock, delivery days | an unavailable bargain is not one |
| returns days | the cost of being wrong |

Missing fields are fine — the script handles absent values. Guessed fields are
not: a made-up shipping cost changes the ranking silently, which is worse than
leaving it out.
