# Tables and layout

Read this when tables come out wrong, or when the detector reports something you do not trust.

## Contents

- [How detection works, and its limits](#how-detection-works-and-its-limits)
- [Sparse tables and wrapped records](#sparse-tables-and-wrapped-records)
- [Tables that span pages](#tables-that-span-pages)
- [Merged cells and stacked headers](#merged-cells-and-stacked-headers)
- [Ruled versus whitespace tables](#ruled-versus-whitespace-tables)
- [Multi-column page layouts](#multi-column-page-layouts)
- [Rotated and landscape pages](#rotated-and-landscape-pages)
- [Numbers, dates and currency](#numbers-dates-and-currency)
- [When to reach for a library](#when-to-reach-for-a-library)

## How detection works, and its limits

`pdf_extract.py` reads layout-preserved text, groups consecutive non-blank lines into blocks, and
finds the character columns that are blank on **every** line of a block. Those runs of blank
columns are the gaps between real columns.

It is deliberately simple, needs nothing installed, and handles the common case — a ledger, a
statement, a price list — well. Knowing how it decides tells you when to doubt it.

Two guards stop it inventing tables, both added because it did:

- **Two-column blocks are treated with suspicion.** Wrapped prose constantly produces a character
  column blank on every line, which splits a paragraph into a "table" whose second column is empty
  on most rows. On a plain contract this produced 23 phantom tables. A two-column candidate now
  has to be evenly filled, narrow, and dense before it counts.
- **Fill evenness decides the rest.** Measured across real documents, genuine tables fill their
  columns evenly while a prose split is lopsided — one full column against one mostly empty. The
  detector compares the variation in fill across columns rather than the absolute level, which is
  what lets it accept a sparse-but-even table and reject a dense-but-lopsided paragraph.

What it does **not** model: merged cells, stacked headers, cells with internal line breaks, or
tables separated by ruling lines rather than whitespace. When you hit those, say so rather than
emitting a grid that looks tidy and has values in the wrong columns.

## Sparse tables and wrapped records

Tables flagged `sparse` (shown with `~`) have columns that are evenly filled but mostly empty. That
almost always means **one logical record spans several physical lines** — a description wrapping,
an address stacked, a transaction with a continuation line.

The rows are real data in the wrong shape. Do not hand them over as one-record-per-row.

To repair, find the column that reliably starts a record — usually a date, an invoice number, a
line number — and merge every following line that has that column empty into the previous record,
joining the wrapped cells with a space. Verify the record count afterwards against something known:
the number of transactions the statement claims, or the count on the last page.

If no column reliably marks a record boundary, say so and show the raw rows. A wrong merge is
harder to detect than an obvious mess.

## Tables that span pages

Common in statements and long reports, and the two failure modes are opposite:

- **Repeated headers.** The header row reappears on each page, so a naive concatenation scatters
  header rows through the data. Detect and drop them by comparing each row against the first
  header row.
- **Interrupted tables.** Page furniture — footers, page numbers, a "continued" banner — splits
  one logical table into several detected ones. Stitch tables from consecutive pages when their
  column count and column positions match.

Always check totals after stitching. A statement usually carries a closing balance or a row count
you can reconcile against, and that check catches both duplicated and dropped rows.

## Merged cells and stacked headers

A merged cell occupies one visual box across several columns; whitespace-based detection sees only
one value and blanks in the neighbours. A stacked header (`2024` above `Q1 Q2 Q3 Q4`) is two header
rows that belong together.

Neither is recoverable from layout text alone with any reliability. The options, in order:

1. Flatten stacked headers by hand into single names — `2024_Q1`, `2024_Q2` — which is quick and
   makes the sheet usable.
2. Move to a coordinate-aware library that exposes cell boxes (`pdfplumber`, or `camelot` in
   lattice mode when the table is ruled).
3. Show what you have, name the limitation, and ask.

Do not silently forward-fill merged values. It is a guess, it is invisible in the output, and in a
financial table it produces numbers that are wrong rather than missing.

## Ruled versus whitespace tables

Two ways a PDF suggests a table, needing different tools:

- **Whitespace-aligned** — columns held apart by spacing. This is what the bundled detector
  handles, and what `pdftotext -layout` preserves.
- **Ruled** — actual drawn lines around cells. Here the lines are the ground truth and are far more
  reliable than whitespace, especially when cells contain wrapped text that breaks column
  alignment. `camelot` in `lattice` mode and `pdfplumber`'s table settings both use them.

If a table looks clearly ruled in the rendered page and whitespace detection is producing a mess,
that mismatch is the reason — switch tools rather than tuning thresholds.

## Multi-column page layouts

Academic papers, newsletters and some catalogues set text in two or three columns. Layout-preserved
extraction reads across the physical line, interleaving the columns into nonsense, and the detector
may report the columns as a "table" with evenly sparse fill.

The tell is prose-shaped cells — long sentence fragments where a table would have short values.
Handle it by splitting the page at the column boundary and extracting each side separately;
`pdftotext -x -y -W -H` crops to a region, and pdfplumber can crop by bounding box.

## Rotated and landscape pages

A page with a `/Rotate` entry, or a landscape table inside a portrait document, extracts with
scrambled or vertical text. `pdftotext` mostly handles rotation; if not, normalise first with
`qpdf --rotate=-90:3 in.pdf out.pdf` for the affected page, then extract.

Wide financial tables are frequently rotated, so check for this whenever a landscape-looking table
extracts badly.

## Numbers, dates and currency

Values in a PDF are formatted for a reader, and the formatting varies within one document:

- **Negatives** appear as `(1,234.00)`, `1,234.00-`, `-1,234.00` or red text. Parenthesised
  negatives silently become positives if you strip punctuation blindly — a sign error in a ledger.
- **Thousands separators** differ by locale: `1,234.56` and `1.234,56` mean the same amount, and
  Indian grouping `12,34,567.89` breaks naive parsers.
- **Currency symbols** may be in a neighbouring column, or attached, or in the header only.
- **Dates** are wildly ambiguous — `03/04/2024` is two different days depending on locale. Infer
  the convention from a value where day exceeds 12 and state which you used.

Keep the raw string alongside the parsed value when the parse is at all uncertain. Being able to
show what the page said is worth more than a tidy column.

## When to reach for a library

The bundled scripts need nothing installed, which is why they exist. Escalate when the document
demands it:

- **`pdfplumber`** — per-character coordinates, explicit table settings, cropping. The best next
  step for stubborn tables.
- **`camelot`** — `lattice` for ruled tables, `stream` for whitespace. Strong on ruled financial
  tables.
- **`PyMuPDF` (`fitz`)** — very fast, good rendering, useful when you need images or coordinates.

Say plainly when a document needs one of these and give the install command. That is a better
answer than a long struggle producing a half-right grid.
