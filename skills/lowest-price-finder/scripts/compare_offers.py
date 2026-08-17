#!/usr/bin/env python3
"""Rank shopping offers on what you actually pay, after screening out the traps.

Three things make the cheapest listing the wrong answer, and all three are
invisible if you sort by sticker price:

  * The sticker is not the bill. Shipping, platform fees, import duty and the
    card offer you cannot use because you do not hold that bank's card all move
    the real number. A cheaper item with paid delivery routinely loses to a
    dearer one that ships free.
  * You may not be comparing the same product. A different generation, region
    variant, colour, capacity or bundle looks identical in a list of prices.
    Where listings publish a GTIN, this checks it.
  * An implausibly low price is evidence of a problem, not a bargain. Grey
    imports without warranty, counterfeits, and listings that never ship all
    present as the best deal on the page, and sorting by price puts them first.

    python3 compare_offers.py --example > offers.json
    python3 compare_offers.py offers.json
    python3 compare_offers.py offers.json --json ranked.json

Offers without a source URL and a fetch timestamp are listed but refused a
ranking. Prices move daily and a remembered one silently decides the purchase.

Standard library only.
"""

import argparse
import json
import statistics
import sys

# What a rupee of cashback is actually worth. Money returned in 60 days as
# store credit you may never spend is not the same as money off at checkout,
# and treating them as equal is how "effective price" marketing wins.
CASHBACK_VALUE = {
    "instant": 1.00,        # taken off at checkout
    "bank_cash": 0.90,      # real money, arrives later
    "wallet": 0.70,         # spendable, but only there
    "store_credit": 0.50,   # only with the same seller, often expires
    "points": 0.50,
    "voucher": 0.45,        # usually minimum-spend gated
}
SLOW_CASHBACK_DAYS = 45     # beyond this, discount it further

# Below this share of the median legitimate landed price, a listing is more
# likely to be a problem than a find.
ANOMALY_FLOOR = 0.60
THIN_SELLER_RATINGS = 50
POOR_SELLER_RATING = 3.5

EXAMPLE = {
    "product": {
        "name": "Sony WH-1000XM5 wireless headphones, black",
        "gtin": "4548736134560",
        "market": "IN",
        "currency": "INR"
    },
    "buyer": {
        "cards": ["HDFC Credit"],
        "memberships": ["Amazon Prime"],
        "accept_conditions": ["new"],
        "needs_warranty": True,
        "needs_by_days": 7
    },
    "offers": [
        {
            "store": "Amazon.in",
            "url": "https://amazon.example/dp/XYZ",
            "fetched_at": "2026-08-17T09:00:00Z",
            "price": 26990, "shipping": 0, "fees": 0,
            "instant_discount": 0,
            "card_offer": {"amount": 2000, "requires": "HDFC Credit"},
            "cashback": {"amount": 500, "type": "store_credit", "delay_days": 60},
            "condition": "new", "warranty": "manufacturer",
            "seller": "Appario Retail", "seller_rating": 4.5,
            "seller_ratings_count": 120000, "official_store": True,
            "gtin": "4548736134560", "in_stock": True,
            "delivery_days": 2, "returns_days": 10
        },
        {
            "store": "Flipkart",
            "url": "https://flipkart.example/p/abc",
            "fetched_at": "2026-08-17T09:02:00Z",
            "price": 25499, "shipping": 99, "fees": 0,
            "card_offer": {"amount": 1500, "requires": "Axis Credit"},
            "condition": "new", "warranty": "manufacturer",
            "seller": "RetailNet", "seller_rating": 4.3,
            "seller_ratings_count": 48000, "official_store": False,
            "gtin": "4548736134560", "in_stock": True,
            "delivery_days": 4, "returns_days": 7
        },
        {
            "store": "DealBazaar",
            "url": "https://dealbazaar.example/p/999",
            "fetched_at": "2026-08-17T09:05:00Z",
            "price": 14999, "shipping": 0,
            "condition": "new", "warranty": "seller",
            "seller": "MobileWorld", "seller_rating": 3.1,
            "seller_ratings_count": 22, "official_store": False,
            "in_stock": True, "delivery_days": 9, "returns_days": 0,
            "note": "listing says 'imported', no Indian warranty card"
        },
        {
            "store": "Croma",
            "url": "https://croma.example/p/555",
            "fetched_at": "2026-08-17T09:07:00Z",
            "price": 24990, "shipping": 0,
            "condition": "refurbished", "warranty": "seller",
            "seller": "Croma", "seller_rating": 4.4,
            "seller_ratings_count": 9000, "official_store": True,
            "gtin": "4548736134560", "in_stock": True, "delivery_days": 3
        },
        {
            "store": "SomeShop",
            "url": None, "fetched_at": None,
            "price": 23000, "condition": "new"
        }
    ],
    "_notes": {
        "card_offer.requires": "the exact card. It is only applied if the buyer "
                               "holds it -- an offer you cannot use is not a discount",
        "cashback.type": "instant | bank_cash | wallet | store_credit | points | voucher",
        "warranty": "manufacturer | seller | none",
        "gtin": "if it differs from product.gtin the listing is a different product",
        "url + fetched_at": "required. Without both, the offer is not ranked."
    }
}


def effective_cashback(cb):
    """Discount cashback to what it is worth in hand today."""
    if not cb:
        return 0.0, ""
    amt = float(cb.get("amount") or 0)
    if not amt:
        return 0.0, ""
    kind = (cb.get("type") or "store_credit").lower()
    factor = CASHBACK_VALUE.get(kind, 0.5)
    delay = cb.get("delay_days") or 0
    if delay > SLOW_CASHBACK_DAYS:
        factor *= 0.8
    return amt * factor, f"{kind}, {int(factor * 100)}% of face"


def landed(offer, buyer):
    """What the buyer actually pays, and how that number was built."""
    lines = []
    price = float(offer.get("price") or 0)
    total = price
    lines.append(("price", price))

    for key, label in [("shipping", "shipping"), ("fees", "fees"),
                       ("duty", "import duty"), ("tax", "tax")]:
        v = float(offer.get(key) or 0)
        if v:
            total += v
            lines.append((label, v))

    inst = float(offer.get("instant_discount") or 0)
    if inst:
        total -= inst
        lines.append(("instant discount", -inst))

    coupon = float(offer.get("coupon") or 0)
    if coupon:
        total -= coupon
        lines.append(("coupon", -coupon))

    # Exchange/trade-in on phones, TVs and appliances routinely exceeds every
    # discount under discussion, and it varies by store -- so it belongs in the
    # price, not in a footnote. The quote is provisional and reassessed at
    # pickup, which is why it is reported as its own line rather than buried.
    ex = float(offer.get("exchange_value") or 0)
    if ex:
        total -= ex
        lines.append(("exchange/trade-in (provisional)", -ex))

    # A card or membership offer only counts if the buyer can actually use it.
    # This is the single biggest reason a "best price" list is wrong for the
    # person reading it.
    unusable = []
    co = offer.get("card_offer")
    if co and float(co.get("amount") or 0):
        need = co.get("requires")
        held = buyer.get("cards", []) + buyer.get("memberships", [])
        if not need or any(need.lower() in h.lower() or h.lower() in need.lower()
                           for h in held):
            total -= float(co["amount"])
            lines.append((f"card offer ({need})", -float(co["amount"])))
        else:
            unusable.append(f"{need} offer worth {co['amount']} — card not held")

    cb_val, cb_note = effective_cashback(offer.get("cashback"))
    if cb_val:
        total -= cb_val
        lines.append((f"cashback ({cb_note})", -cb_val))

    return round(total, 2), lines, unusable


def screen(offer, product, buyer, median_landed, my_landed):
    """Return (blocking_reasons, warnings). Blocking means do not rank it."""
    block, warn = [], []

    if not offer.get("url") or not offer.get("fetched_at"):
        block.append("no source URL and timestamp — price not verifiable")

    if offer.get("in_stock") is False:
        block.append("out of stock")

    # Same product? A GTIN mismatch is definitive; its absence is not proof of
    # a match, only absence of evidence.
    pg, og = product.get("gtin"), offer.get("gtin")
    if pg and og and str(pg).strip() != str(og).strip():
        block.append(f"different product (GTIN {og} vs {pg})")
    elif pg and not og:
        warn.append("no GTIN published — confirm it is the same variant by hand")

    cond = (offer.get("condition") or "unknown").lower()
    accept = [c.lower() for c in buyer.get("accept_conditions", ["new"])]
    if cond not in accept:
        block.append(f"condition '{cond}' not accepted (wanted {'/'.join(accept)})")

    if buyer.get("needs_warranty"):
        wty = (offer.get("warranty") or "none").lower()
        if wty in ("none", "no", ""):
            block.append("no warranty, and warranty was required")
        elif wty == "seller":
            warn.append("seller warranty only, not manufacturer — check who "
                        "honours a repair")

    need_by = buyer.get("needs_by_days")
    dd = offer.get("delivery_days")
    if need_by and dd and dd > need_by:
        block.append(f"arrives in {dd} days, needed in {need_by}")

    rating = offer.get("seller_rating")
    count = offer.get("seller_ratings_count")
    if rating is not None and rating < POOR_SELLER_RATING:
        warn.append(f"seller rated {rating} — below {POOR_SELLER_RATING}")
    if count is not None and count < THIN_SELLER_RATINGS:
        warn.append(f"only {count} seller ratings — too thin to judge")

    if not offer.get("returns_days") and offer.get("returns_days") is not None:
        warn.append("no returns window")

    # The inversion that matters: suspiciously cheap is a risk signal.
    if median_landed and my_landed < median_landed * ANOMALY_FLOOR:
        pct = int((1 - my_landed / median_landed) * 100)
        warn.append(f"{pct}% below the median legitimate price — verify before "
                    "buying; this pattern fits grey imports and counterfeits")

    return block, warn


def run(data):
    product = data.get("product", {})
    buyer = data.get("buyer", {})
    offers = data.get("offers", [])

    computed = []
    for o in offers:
        total, lines, unusable = landed(o, buyer)
        computed.append({"offer": o, "landed": total, "lines": lines,
                         "unusable": unusable})

    # Two passes, because the reference price has to be built from clean offers.
    # Including a suspect listing in the median drags the benchmark down toward
    # itself, which is precisely how a counterfeit stops looking anomalous.
    # Pass 1 screens on everything except price, to find the legitimate set.
    for c in computed:
        c["blocked"], c["warnings"] = screen(c["offer"], product, buyer, None,
                                             c["landed"])

    clean = [c["landed"] for c in computed if not c["blocked"]]
    median_landed = statistics.median(clean) if clean else None

    # Pass 2 measures every offer, including the excluded ones, against that
    # clean median -- an excluded listing still deserves the "and it was also
    # implausibly cheap" note.
    ranked, excluded = [], []
    for c in computed:
        c["blocked"], c["warnings"] = screen(c["offer"], product, buyer,
                                             median_landed, c["landed"])
        (excluded if c["blocked"] else ranked).append(c)

    ranked.sort(key=lambda c: c["landed"])
    return ranked, excluded, median_landed, product, buyer


def money(v, cur):
    return f"{cur} {v:,.2f}" if cur else f"{v:,.2f}"


def render(ranked, excluded, median_landed, product, buyer):
    cur = product.get("currency", "")
    L = []
    w = L.append
    w(f"LOWEST LANDED PRICE: {product.get('name', '(product)')}")
    w("=" * 74)
    if product.get("gtin"):
        w(f"Matching on GTIN {product['gtin']}")
    held = buyer.get("cards", []) + buyer.get("memberships", [])
    w(f"Buyer holds: {', '.join(held) if held else '(none given — card offers '
      f'cannot be applied)'}")
    if buyer.get("needs_by_days"):
        w(f"Needed within {buyer['needs_by_days']} days")
    w("")

    if not ranked:
        w("No offer passed screening. The excluded list below says why — that is")
        w("the finding, not a failure. Widen the accepted condition, drop the")
        w("warranty requirement, or allow more delivery time to open options up.")
    for i, c in enumerate(ranked, 1):
        o = c["offer"]
        tag = "  <-- best" if i == 1 else ""
        w(f"{i}. {o.get('store', '?')}   {money(c['landed'], cur)}{tag}")
        parts = [f"{lbl} {v:+,.0f}" for lbl, v in c["lines"][1:]]
        w(f"     {money(float(o.get('price') or 0), cur)} sticker"
          + (f"  |  {'  '.join(parts)}" if parts else "  |  no adjustments"))
        meta = []
        if o.get("condition"):
            meta.append(o["condition"])
        if o.get("warranty"):
            meta.append(f"{o['warranty']} warranty")
        if o.get("delivery_days") is not None:
            meta.append(f"{o['delivery_days']}d delivery")
        if o.get("seller"):
            meta.append(f"seller {o['seller']}"
                        + (f" {o['seller_rating']}★" if o.get("seller_rating") else ""))
        if meta:
            w(f"     {' · '.join(meta)}")
        for u in c["unusable"]:
            w(f"     not applied: {u}")
        for x in c["warnings"]:
            w(f"     WARNING: {x}")
        w(f"     {o.get('url')}")
        w("")

    if len(ranked) > 1:
        gap = ranked[1]["landed"] - ranked[0]["landed"]
        w(f"Gap to second place: {money(gap, cur)}")
        cheapest_sticker = min(ranked, key=lambda c: float(c["offer"].get("price") or 0))
        if cheapest_sticker is not ranked[0]:
            w(f"Note: {cheapest_sticker['offer'].get('store')} has the lowest "
              f"sticker price but not the lowest bill — this is the case the "
              f"whole comparison exists to catch.")
        w("")

    if excluded:
        w("EXCLUDED — not ranked")
        w("-" * 74)
        for c in excluded:
            o = c["offer"]
            w(f"  {o.get('store', '?')}  (sticker "
              f"{money(float(o.get('price') or 0), cur)})")
            for b in c["blocked"]:
                w(f"     x {b}")
            for x in c["warnings"]:
                w(f"     ! {x}")
        w("")
        w("  A cheaper excluded listing is not a missed saving until the reason")
        w("  is resolved. Show these to the buyer with the reason rather than")
        w("  hiding them — some reasons they may happily accept.")
        w("")

    if median_landed:
        w(f"Median landed price across sourced offers: {money(median_landed, cur)}")
    w("Prices verified only at the timestamps given. Confirm at checkout — the")
    w("final bill is the only number that is real.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", nargs="?")
    ap.add_argument("--example", action="store_true",
                    help="print a documented example input and exit")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.input:
        ap.error("give an input file, or --example to see the format")

    with open(args.input) as f:
        data = json.load(f)

    ranked, excluded, med, product, buyer = run(data)
    print(render(ranked, excluded, med, product, buyer))

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"ranked": [{"store": c["offer"].get("store"),
                                   "landed": c["landed"],
                                   "warnings": c["warnings"]} for c in ranked],
                       "excluded": [{"store": c["offer"].get("store"),
                                     "reasons": c["blocked"]} for c in excluded],
                       "median_landed": med}, f, indent=2)
        print(f"\nWritten to {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
