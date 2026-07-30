# OCR

Read this for any file triage classifies `SCANNED`, or `MIXED` where the text layer proved to be a
fragment.

## Contents

- [Set expectations first](#set-expectations-first)
- [The pipeline](#the-pipeline)
- [Resolution](#resolution)
- [Preprocessing that helps](#preprocessing-that-helps)
- [Languages](#languages)
- [Page segmentation](#page-segmentation)
- [Tables from OCR](#tables-from-ocr)
- [Errors OCR actually makes](#errors-ocr-actually-makes)
- [Verifying the output](#verifying-the-output)

## Set expectations first

OCR is recognition, not extraction. It produces a best guess with an error rate, and the error rate
is never zero. On clean 300 DPI printed text tesseract is very good — well above 98% on characters.
On a phone photo of a crumpled receipt it may be near useless.

Two consequences worth stating to the user rather than discovering later:

- **It costs time.** Roughly 6 seconds a page at 300 DPI on a normal machine, measured. A 200-page
  scan is 20 minutes, so warn before starting and consider `--pages` on a sample first.
- **Digits are the weak point**, and digits are usually the reason someone is parsing a financial
  document. Say the figures came from OCR and should be spot-checked. Presenting OCR'd amounts as
  if they were extracted is the one genuinely misleading thing you can do here.

## The pipeline

Rasterise, then recognise:

```bash
pdftoppm -r 300 -png file.pdf /tmp/pg          # one PNG per page
tesseract /tmp/pg-01.png stdout -l eng --psm 6
```

`pdf_extract.py` does both and stitches the pages. It needs `tesseract` plus a rasteriser —
`pdftoppm` from poppler, or PyMuPDF as a fallback. Triage names whichever is missing.

Install, if absent:

```bash
brew install tesseract poppler                      # macOS
sudo apt install tesseract-ocr poppler-utils        # Debian/Ubuntu
```

There is no pure-Python OCR worth substituting here. If tesseract cannot be installed, say the file
cannot be read and why, rather than returning an empty parse.

## Resolution

The single biggest lever, and the most common mistake is going too low.

- **300 DPI** is the right default for printed body text.
- **400-600 DPI** for small print, dense tables, or footnote-sized text.
- **Below 250 DPI accuracy falls off sharply.** Rendering at 150 to save time is a false economy —
  you spend the time again cleaning the output, or you ship wrong numbers.

Higher is not monotonically better: past about 600 DPI you get slower runs and no accuracy gain, and
scanning artefacts start being resolved as detail.

## Preprocessing that helps

Only worth doing when a first pass is poor:

- **Deskew.** Even 2 degrees of rotation hurts line detection badly. `tesseract` handles small skew;
  ImageMagick `-deskew 40%` handles more.
- **Greyscale and increase contrast.** Colour adds nothing and can hurt. `-colorspace Gray
  -normalize`.
- **Binarise** for clean printed text, but not for faint or uneven scans, where thresholding
  destroys strokes. Tesseract's internal Otsu is usually good enough.
- **Remove speckle** on faxes and photocopies — `-despeckle`.
- **Crop the region you need.** Both faster and more accurate, because page furniture stops
  competing with the content.

Skip all of it when the scan is clean. It is easy to spend more effort on preprocessing than the
errors cost.

## Languages

`-l eng` is the default and wrong for a lot of documents.

```bash
tesseract page.png stdout -l eng+hin        # English plus Hindi
tesseract --list-langs                      # what is installed
```

Combine languages when a document genuinely mixes scripts, which is common in Indian, Arabic and
CJK business documents where headings and numbers are Latin and body text is not. Do not stack many
languages speculatively — each one added slows recognition and can pull characters toward the wrong
script.

Install extra language data as `tesseract-lang` (brew) or `tesseract-ocr-hin` style packages (apt).
`pdf_extract.py` takes `--lang` and passes it through.

## Page segmentation

`--psm` tells tesseract what kind of layout to expect, and it matters more than most options:

| Mode | Use for |
| --- | --- |
| `6` | A single uniform block. The best default for statements, tables and forms. |
| `3` | Fully automatic. Tesseract's default; better on mixed magazine-like layouts. |
| `4` | Variable-size text in a single column. |
| `11` / `12` | Sparse text, finding as much as possible in no particular order. |

`pdf_extract.py` uses `6`, because financial and tabular documents dominate this use case and
automatic segmentation tends to break their column alignment. If a page is a complex mixed layout
and mode 6 scrambles it, try `3`.

## Tables from OCR

Harder than tables from a text layer, because column alignment now depends on recognition accuracy
too. What works:

- **`--psm 6`** to keep the block structure, then the same whitespace column detection as any other
  layout text.
- **Higher DPI than you would otherwise use.** Column drift usually traces back to resolution.
- **TSV output** when you need coordinates: `tesseract page.png out tsv` gives a word-level box per
  line, which you can cluster into columns yourself. More work, much more robust for messy scans.
- **OCR the table region only.** Cropping removes the page furniture that confuses segmentation.

Expect to verify a table from OCR row by row against the page, at least in a sample. Do not skip
this on anything financial.

## Errors OCR actually makes

Knowing the specific confusions lets you target the checks:

- **`0` / `O` / `o`**, **`1` / `l` / `I` / `|`**, **`5` / `S`**, **`8` / `B`**, **`2` / `Z`**,
  **`6` / `b`**, **`rn` / `m`**. In amounts and reference numbers these are the ones that bite.
- **Decimal points lost or invented** — `1234.56` becoming `123456`. Catastrophic and easy to miss.
- **Thousands separators** read as periods and vice versa.
- **Minus signs and parenthesised negatives** dropped, flipping the sign of a figure.
- **Table rules read as characters** — stray `|`, `l` or `-` at cell edges.
- **Merged or split words** at column boundaries.

## Verifying the output

Cheap checks that catch most real damage:

- **Reconcile a total.** If the document has a sum, add the extracted rows and compare. This single
  check catches decimal errors, dropped rows and sign flips at once, and it is the highest-value
  thing you can do.
- **Count rows against a stated count.** Statements usually declare a number of transactions.
- **Range-check every number.** A transaction of 1,234,567.00 among values in the hundreds is
  probably a lost decimal point.
- **Check dates fall in the expected period.** A statement for July should not contain March.
- **Confirm the character set.** Latin letters inside what should be a pure-digit field indicate a
  confusion pair.
- **Re-OCR a sample at higher DPI** and compare. Where the two runs disagree is where the errors
  are, which is a fast way to locate them without reading everything.

Report what you checked. "Totals reconcile to the stated closing balance" earns far more trust than
a clean-looking table with no evidence behind it — and when they do not reconcile, that is the most
important thing you can tell the user.
