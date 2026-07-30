---
name: pdf-parsing
license: MIT
description: Parses any PDF into structured usable data — classifies the document first (text layer, scanned, fillable form, encrypted), extracts text, tables and form fields with whatever toolchain is actually installed, OCRs scans that have no text layer, and writes a real multi-sheet Excel workbook, CSV, JSON or document without needing pandas or openpyxl. Handles one file or a whole folder into a single spreadsheet with a source-file column plus a list of what failed and why. Use whenever the user wants to parse, read or extract a PDF, pull tables, invoices, bank statements, bills, payslips, receipts, forms or report figures out of one, convert a PDF to Excel, xlsx, CSV, Word or JSON, asks why a PDF returns empty text or scrambled columns, mentions a scanned PDF or OCR, or has a folder of PDFs to turn into a spreadsheet.
---

# PDF parsing

Turns a PDF into data you can actually compute on — text, tables, form fields — and writes it out
as a spreadsheet or a document, choosing the target from what the PDF really contains.

## The one idea that organises everything below

**A PDF is not a data format. It is a page-description format**: instructions for painting glyphs
at coordinates. There is no "table" inside a PDF, and often no "text" either — there are marks
positioned on a canvas, which a human eye groups into rows and columns.

Everything downstream follows from that. It means extraction quality is decided almost entirely by
**correctly identifying what kind of PDF you have before you touch it**, because the four main
kinds need four different tools and using the wrong one does not raise an error — it returns
nothing, or something subtly scrambled, which is worse.

The failure this skill exists to prevent: point a text extractor at a scanned document and it
returns an empty string. Not an exception. The natural next thought is "the file is corrupt" or
"this library is broken", and ten minutes disappear into debugging the wrong thing. The file was
fine. It contained no text at all.

## Workflow

### 1. Triage first, always

```bash
python3 scripts/pdf_triage.py file.pdf
python3 scripts/pdf_triage.py folder/ --batch
```

Standard library only — nothing to install. It reads the PDF's own object structure, inflates the
content streams, and reports what the document actually is plus the route that will work:

| Type | What it means | Route |
| --- | --- | --- |
| `TEXT` | Real text layer | Extract directly |
| `SCANNED` | Pictures of text, no text layer | OCR is the only option |
| `MIXED` | Images with a thin text layer | Extract, then check whether that was most of the content |
| `FORM` | AcroForm with fillable fields | Read field values, not page text |
| `XFA_FORM` | LiveCycle form | Data is in embedded XML, not page content |
| `ENCRYPTED` | Password protected | Try an empty user password, else ask |
| `NO_TEXT_LAYER` | Neither text nor images | Render a page and look before guessing |
| `NOT_A_PDF` | Renamed file | It reports what the file actually is |

It also reports the character count it can see, the shape of the text runs, which external tools
are present, and specifically what is missing for *this* file. Read the `MISSING` section — if a
scan needs OCR and tesseract is absent, that is the whole story and no amount of retrying changes
it.

Two numbers in its output are worth understanding, because they drive the decisions below:

- **chars/page** distinguishes a real text layer from a scan. Under about 50 there is effectively
  nothing to extract, whatever the file looks like in a viewer.
- **Run shape** — the share of text runs 12 characters or shorter. Table cells are short runs;
  prose lines are long ones. Above roughly 60% short runs the page is cell-shaped, which means
  layout must be preserved or the columns will collapse into each other.

### 2. Extract with the layout intact

```bash
python3 scripts/pdf_extract.py file.pdf -o out/
python3 scripts/pdf_extract.py folder/ --batch -o out/
python3 scripts/pdf_extract.py file.pdf --pages 2-5 --force-ocr --lang eng+hin
```

It routes itself from the triage result and uses the best extractor present, preferring
layout-preserving text and falling back through pdfplumber and pypdf, or to OCR when there is no
text layer. It writes the text, one CSV per detected table, and form fields as JSON.

**Preserving layout is not cosmetic.** Plain text extraction concatenates runs in drawing order,
so a three-column table becomes one column of interleaved values with no way to recover which
value belonged to which column. The information is destroyed at that point, not merely untidy.
This is the single most common way "the numbers came out wrong" happens.

### 3. Look at what came out before shaping it

Extraction is the easy half. The half that produces wrong answers is trusting it.

- **Compare the character count to the document.** A 40-page report yielding 900 characters means
  the text layer is a fragment and the rest is images.
- **Check the table shapes it reports.** Detection is honest but simple — it finds the character
  columns that are blank on every line of a block. It flags tables it considers `sparse` with a
  `~`, meaning records probably wrap across several physical lines or the page is a multi-column
  layout. A sparse table is real data in the wrong shape; do not pass it off as one-record-per-row.
- **Spot-check values against the page.** Read a few numbers from the extracted output and confirm
  they match the PDF. Column drift is invisible in aggregate and obvious in three samples.
- **Expect nothing from merged cells and nested headers.** The detector does not model them. Say
  so rather than emitting a confidently wrong grid.

`references/tables-and-layout.md` covers multi-page tables, merged cells, rotated pages and the
repairs that work when detection is not enough.

### 4. Choose the output format from the PDF, not from the request

This is where a lot of PDF work goes wrong, and it is worth pushing back on gently. **A spreadsheet
can only represent something that is already tabular.** Asked to "put this contract into Excel",
the honest answer is that a contract has no rows — forcing it into cells produces a grid that is
harder to read than the original and loses the clause structure.

Let the document decide:

| What the PDF is | Right target | Why |
| --- | --- | --- |
| Tables, statements, ledgers, price lists | `.xlsx`, one sheet per table | Rows and columns already exist |
| One invoice or form | A single row, or key/value pairs | The fields are the data |
| Many invoices or statements | One sheet, one row each, plus a `source_file` column | The set is the table |
| Contract, report, letter, article | Markdown or `.docx`, structure preserved | Prose has no rows |
| Mixed report with tables inside it | Document for the narrative plus sheets for the tables | Both, rather than one badly |

When someone asks for Excel and the content is prose, produce the document form, say in one line
why a spreadsheet would lose rather than add, and offer the sheet if they still want it. Being
useful here means giving them the thing that works, not refusing and not silently substituting.

```bash
python3 scripts/to_workbook.py out.xlsx table1.csv table2.csv --names Invoices,Lines
python3 scripts/to_workbook.py out.xlsx extract.json          # straight from --json
python3 scripts/to_workbook.py out.xlsx data.csv --text-columns 0,4
```

`to_workbook.py` writes real multi-sheet `.xlsx` using only the standard library, because the
machine that needs a spreadsheet is often the one where `pip install` is not available. It turns
numeric cells into real numbers so they can be summed, and deliberately keeps as text anything a
numeric conversion would destroy — leading zeros, digit strings over 15 characters, account and
invoice references. Those are exactly the fields people most need intact, and Excel corrupts them
silently on import. Use `--text-columns` when you know a column must stay text.

### 5. Deliver everything, then offer to narrow

Give the user the full parse on the first turn — every table, every field, written out — and then
show them the field names you found and offer to reshape. Do not open by asking which data points
they want.

The reason is that they usually cannot answer yet. The field names in the PDF are rarely the ones
they would guess, and a question like "which fields do you need?" asked before they have seen the
document produces vaguer answers than the same question asked next to a list of real column
names. Extracting everything costs one run and leaves them with something usable immediately.

So the shape of the reply is: here is the output, here is what I found, tell me what to cut or
reshape. When they do name the fields they want, that is the point to produce the narrow version.

If they have *already* told you the fields — "just the date, amount and reference from each one" —
use them, and still say what else was available so they know what they are leaving behind.

## Batch

The reason most people want this automated is a folder, not a file.

```bash
python3 scripts/pdf_triage.py invoices/ --batch          # what am I dealing with
python3 scripts/pdf_extract.py invoices/ --batch -o out/ # extract everything
```

Triage the folder first. It groups by type and lists only the files needing a decision, which is
what makes a 200-file directory tractable. Then extract, and report honestly:

- **Every successful file gets a `source_file` value.** Rows from 50 statements are
  indistinguishable without it, and the column is impossible to reconstruct later.
- **Failures go in their own list with the reason** — `_failed.csv`, or a `Failed` sheet. Never
  drop a file silently. "47 of 50" with three named reasons is a useful result; "47 rows" from a
  50-file folder is a bug the user finds a month later.
- **Watch for a shape that varies.** Invoices from different vendors have genuinely different
  layouts, so one column mapping will not fit all. Group by layout and say so.

## Output format

```
## What these PDFs are
[Type per file, or a count by type for a folder. Anything needing OCR or a password, named.]

## What I extracted
[Per file or in total: tables with their shapes, fields found, character counts.
 Flag sparse tables and anything you could not read.]

## Files written
[Paths, with what is in each sheet.]

## What I found in it
[The actual field or column names, so the user can choose from real names.]

## Anything you want narrowed or reshaped?
[One line. Name the obvious alternative shapes — one row per document versus one row per
 line item is usually the real question.]
```

## Failure modes to avoid

- **Reporting empty output as success.** If extraction yields nothing, say the document is scanned
  and needs OCR. "No data found" is a wrong answer to a file full of data.
- **Losing columns to plain text extraction.** Always preserve layout on anything tabular. Once
  runs are concatenated, the column assignment cannot be recovered.
- **Inventing structure.** If a table has merged cells or stacked headers the detector cannot
  model, show what you got and name the limitation. A tidy grid with values in the wrong columns
  is the worst possible output, because it looks right.
- **Silently dropping files in a batch.** Every input is either in the output or in the failure
  list.
- **Letting Excel eat identifiers.** Account numbers, GST and VAT ids, phone numbers, anything with
  a leading zero — text, not numbers.
- **Forcing prose into a grid.** Offer the document form and explain the trade in one sentence.
- **OCRing when you do not need to.** It is roughly 6 seconds a page at 300 DPI and always less
  accurate than a real text layer. Only when triage says there is no text.
- **Trusting OCR silently.** It misreads digits — 0/O, 1/l, 5/S, 8/B. On anything financial, say
  the figures came from OCR and should be spot-checked.

## Reference files

- `references/pdf-types.md` — the classification in depth, what each type needs, and how to handle
  encryption, XFA forms, damaged files and renamed files.
- `references/tables-and-layout.md` — read when tables come out wrong: multi-page tables, merged
  cells, wrapped records, rotated pages, multi-column layouts.
- `references/ocr.md` — read for any `SCANNED` or `MIXED` file: DPI, preprocessing, languages,
  accuracy expectations and where OCR must not be trusted.
- `references/output-shaping.md` — read before writing the output: choosing the target, one row
  per document versus per line item, batch schemas, and getting types right.
