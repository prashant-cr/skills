# Output shaping

Read this before writing the output, especially for a batch.

## Contents

- [Pick the target from the content](#pick-the-target-from-the-content)
- [The row-granularity question](#the-row-granularity-question)
- [Batch schemas](#batch-schemas)
- [Getting types right](#getting-types-right)
- [Column names](#column-names)
- [Excel specifics](#excel-specifics)
- [CSV specifics](#csv-specifics)
- [Documents for prose](#documents-for-prose)
- [Reporting what you did](#reporting-what-you-did)

## Pick the target from the content

A spreadsheet can only represent something already tabular. This is worth a sentence of pushback
when someone asks to "put this PDF into Excel" and the PDF is a contract, because the grid version
is strictly worse than the original — clause structure lost, sentences chopped into cells, nothing
gained.

| Content | Target |
| --- | --- |
| Tables, ledgers, statements, price lists | `.xlsx`, a sheet per table |
| A single invoice, form or certificate | Key/value pairs, or one row |
| Many similar documents | One sheet, one row each, `source_file` column |
| Contract, report, letter, article | Markdown or `.docx` |
| Report containing tables | Document for the narrative plus sheets for the tables |
| Feeding another program | JSON, structure preserved |

When the ask and the content disagree, produce the form that works, explain the trade in one line,
and offer the other. Refusing is unhelpful; silently substituting is worse; doing the sensible thing
and saying so is right.

## The row-granularity question

For anything with line items this is the real question, and it is worth asking explicitly because
both answers are legitimate and they are not convertible without re-parsing.

**One row per document** — invoice number, date, vendor, total. Good for reconciliation, payment
tracking, and summing totals. Line-item detail is lost.

**One row per line item** — repeat the invoice-level fields on every row, then the item, quantity
and amount. Good for spend analysis and product-level questions. Totals must be summed rather than
read, and the document-level fields are duplicated.

**Both, as two sheets**, is often the right answer and costs almost nothing once parsed: a
`Documents` sheet and a `Lines` sheet joined by the invoice number. Offer this when the document has
line items — it is usually what someone wants once they see it.

State which one you produced. A user who assumed the other will otherwise sum a duplicated column
and get a wrong number that looks plausible.

## Batch schemas

The hard part of a folder is that the documents are not identical.

- **`source_file` on every row, always.** Rows from 50 statements are indistinguishable without it
  and the column cannot be reconstructed afterwards. Put it first or last, consistently.
- **Union the columns, do not intersect them.** If some invoices have a PO number and others do not,
  keep the column and leave it blank. Dropping it loses data from the files that had it.
- **Group by layout when vendors differ.** Invoices from different senders have genuinely different
  positions, so one column mapping will not fit all. If you detect two or three distinct layouts,
  either normalise to a common schema and say how, or write a sheet per layout. Do not force one
  mapping and produce columns that are right for some files and shifted for others.
- **A failure list is part of the output**, not an aside. `_failed.csv` or a `Failed` sheet with the
  file name, the type triage found, and the reason. "47 of 50, 3 listed" is a complete answer;
  "47 rows" from a 50-file folder is a bug the user finds later.
- **Keep a page reference** where you can. When a number looks wrong, being able to say which page
  it came from turns a dispute into a check.

## Getting types right

The most common way a correct extraction becomes a wrong spreadsheet.

**Must stay text**, because a numeric conversion destroys them:

- Anything with a **leading zero** — `00789`, `0012345`. The zeros vanish permanently.
- **Digit strings over 15 characters** — account numbers, card numbers, long references. They become
  floating point and lose their last digits, silently.
- **Identifiers generally** — invoice refs, GST and VAT ids, phone numbers, postcodes, IFSC and
  SWIFT codes. They are labels, not quantities. You never sum them.
- **Anything Excel would read as a date.** `3-4` becomes 3 April; some product codes become dates
  and cannot be recovered.

`to_workbook.py` applies these rules automatically and takes `--text-columns` for cases only you
can know about.

**Should become numbers**, so they can be summed: quantities, amounts, rates, percentages. Strip
thousands separators, and handle negatives in all their forms — `(1,234.00)`, `1,234.00-`,
`-1,234.00` all mean negative, and treating a parenthesised value as positive is a sign error in a
ledger.

**Dates** are best stored ISO (`2024-03-04`) with the raw string kept alongside if the source was
ambiguous. Say which convention you assumed when `03/04/2024` was involved.

## Column names

The names in the PDF are what the user recognises, so keep them where they are usable — but make
them work as columns:

- Preserve the document's own wording rather than inventing tidier synonyms. "Particulars" means
  something specific to someone reading a bank statement.
- Flatten stacked headers into single names — `2024_Q1`, not a header row above another.
- Make them unique. Duplicated headers are common in PDFs and break most consumers; suffix them.
- Strip footnote markers and line breaks out of header cells.
- For opaque form fields (`Text1`, `undefined_3`), map from the visible labels and confirm the
  mapping rather than shipping the raw names.

## Excel specifics

`to_workbook.py` writes real multi-sheet `.xlsx` with only the standard library, since an `.xlsx` is
a zip of XML parts. This matters because the machine needing a spreadsheet is often one where
`pip install openpyxl` is not an option, and handing over a CSV instead loses the sheet-per-table
structure.

Constraints it handles for you: sheet names are capped at 31 characters, cannot contain
`[ ] : * ? / \`, and must be unique — it truncates and de-duplicates. Control characters are
stripped, since they make Excel declare the file corrupt.

One sheet per table, named for the source and page, keeps a multi-table document navigable. Put a
short summary sheet first when there are many.

## CSV specifics

Right for a single table or a pipeline, and it has real limits worth knowing: no types, no multiple
sheets, and Excel will re-interpret everything on import — which undoes the type care described
above the moment someone double-clicks it.

Write UTF-8 with a BOM when the file is destined for Excel on Windows, or non-ASCII names arrive
mangled. Quote fields containing separators, quotes or newlines — the `csv` module does this
correctly, so use it rather than joining strings.

If the user says Excel and you produce CSV, say why, because the difference will show up as lost
leading zeros and they will not know where it came from.

## Documents for prose

For contracts, reports and letters, preserve the structure that carries the meaning: headings,
numbered clauses, lists, paragraph breaks, tables inline where they occur.

Markdown is the best default — readable, diffable, converts onward easily. Use `.docx` when the user
needs to edit in Word; `python-docx` is often available.

Keep clause and section numbering exactly as printed. In a contract the numbering *is* the
reference, and renumbering silently breaks every cross-reference and every citation someone has
already made to it.

## Reporting what you did

The output is not just the file. State plainly what came out of what:

- What each PDF was classified as, and what needed OCR.
- What was extracted — table shapes, field counts, character counts — and what was skipped.
- Which files failed and why.
- Any repair you applied: stitched tables, merged wrapped rows, flattened headers, dropped repeated
  headers. These are judgement calls and the user cannot see them in the spreadsheet.
- Anything you checked — totals reconciling, row counts matching. This is the difference between a
  result and a claim.
- The real column names, so the user can name what they want narrowed to.
