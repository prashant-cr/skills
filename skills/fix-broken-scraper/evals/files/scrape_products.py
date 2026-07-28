"""Nightly product/price export for the Northgate catalogue.

Runs against the live category page in production; pass a local HTML file as
argv[1] to test without hitting the site.
"""

import csv
import sys

import requests
from bs4 import BeautifulSoup

CATEGORY_URL = "https://northgate-coffee.example.com/collections/brewing"
EXPECTED_PRODUCTS = 12


def load_html(source):
    if source:
        with open(source, encoding="utf-8") as fh:
            return fh.read()
    resp = requests.get(CATEGORY_URL, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    titles = [el.get_text(strip=True) for el in soup.select("h3.product-title")]
    prices = [el.get_text(strip=True) for el in soup.select("span.price")]

    rows = list(zip(titles, prices))

    # Sanity check so we notice if the page stops returning products.
    assert len(rows) == EXPECTED_PRODUCTS, f"expected {EXPECTED_PRODUCTS}, got {len(rows)}"
    return rows


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else None
    rows = parse(load_html(source))

    writer = csv.writer(sys.stdout)
    writer.writerow(["title", "price"])
    writer.writerows(rows)
    print(f"\n{len(rows)} products exported", file=sys.stderr)


if __name__ == "__main__":
    main()
