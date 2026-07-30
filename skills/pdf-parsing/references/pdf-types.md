# PDF types and what each one needs

Read this when triage returns anything other than a plain `TEXT`, or when a file behaves oddly.

## Contents

- [Why the type decides everything](#why-the-type-decides-everything)
- [TEXT](#text)
- [SCANNED](#scanned)
- [MIXED](#mixed)
- [FORM and XFA_FORM](#form-and-xfa_form)
- [ENCRYPTED](#encrypted)
- [NO_TEXT_LAYER](#no_text_layer)
- [NOT_A_PDF and damaged files](#not_a_pdf-and-damaged-files)
- [How the classifier decides](#how-the-classifier-decides)

## Why the type decides everything

A PDF stores drawing instructions, not content. Two documents that look identical in a viewer can
be a text-layer file and a photograph of a printout, and no amount of inspecting the rendering
tells them apart. The only reliable signal is inside the file, which is what `pdf_triage.py` reads.

Getting this wrong is not a small inefficiency — the failures are silent. A text extractor on a
scan returns `""`. Plain extraction on a table returns real text with the columns destroyed. Both
look like success to a caller checking only for exceptions.

## TEXT

A real text layer: glyphs with a character mapping, so text can be selected and extracted exactly.

Extract with layout preserved. `pdftotext -layout` is the strongest general-purpose option and it
is very widely installed; `pdfplumber` is better when you need per-character coordinates for
difficult tables; `pypdf` has no layout mode and should be a last resort for anything tabular.

One trap worth knowing: **a TEXT file can still yield nothing.** Fonts embedded without a
`ToUnicode` map produce glyphs that render correctly and extract as mojibake or empty. If triage
says there is text and extraction returns garbage, this is usually why, and OCR is the workaround.
`pdf_extract.py` falls back to OCR automatically in this case and tells you it did.

## SCANNED

No text layer. The page is an image, so there is nothing to extract and OCR is the only route.
`pdftotext` returning empty here is correct behaviour, not a bug — say that plainly rather than
reporting "no data found", which sounds like the document was empty.

Read `references/ocr.md` before running it. The headline points: 300 DPI, expect roughly 6 seconds
a page, and never present OCR'd financial figures without saying they came from OCR.

## MIXED

Images with a thin text layer. Three quite different documents land here:

- **Already-OCR'd scans.** Someone ran OCR and saved the text as an invisible layer. Extract it —
  it is free and usually decent — but it inherits every OCR error, and you cannot see them.
- **Designed documents** — catalogues, brochures, annual report front sections — where much of the
  text is baked into artwork. The text layer is real but partial.
- **Text-layer documents with heavy imagery**, where the classification is simply conservative.

The action is the same: extract the text layer, then **check whether what you got is a plausible
fraction of what is on the page**. Compare the character count to the page count and to what a
rendered page looks like. If most content is in the images, OCR as well with `--force-ocr` and
merge. Do not silently return the fragment.

## FORM and XFA_FORM

**AcroForm** is the common fillable PDF. Field values live in the document structure as name/value
pairs, and reading them is far more reliable than reading page text, because field names are stable
while the visual position of a label is not. `pdf_extract.py` returns them as JSON.

Two cautions. Field names are frequently unhelpful (`Text1`, `undefined_3`), so map them to
meaningful names using the visible labels and confirm the mapping with the user. And a form may
have **both** filled fields and printed text; if the values look shifted relative to what the page
shows, check whether appearance streams were flattened separately from the field values.

**XFA** (Adobe LiveCycle) is a different animal: the real data is an embedded XML packet, and page
content may be a "please open in Adobe Reader" placeholder. Extract the XFA XML and parse that.
Text extraction on an XFA form typically returns the placeholder message, which is a confusing
result if you do not know to expect it.

## ENCRYPTED

Distinguish two cases, because they are not the same request:

- **Owner password with an empty user password.** Extremely common on bank statements and reports —
  the file opens for reading without any password and only restricts printing or copying.
  `qpdf --decrypt --password= in.pdf out.pdf` handles it, and `pdf_extract.py` tries this
  automatically before giving up.
- **A genuine user password.** The content is cryptographically protected. Ask the user for the
  password. Do not attempt to break or brute-force it — that is the one thing not to do here, and
  it is also almost never what the user wants.

If a user supplies a password, pass it through rather than storing it anywhere.

## NO_TEXT_LAYER

Neither meaningful text nor page-sized images. Possibilities: text drawn as vector paths (some
design tools do this, and it is genuinely unextractable without OCR), a file that is only a cover
sheet, or damage.

Render a page and look at it before deciding — `pdftoppm -r 150 -png -f 1 -l 1 file.pdf page`.
Guessing without looking wastes more time than the render costs.

## NOT_A_PDF and damaged files

Triage sniffs the magic bytes and tells you what the file actually is. A `.pdf` that is really a
`.docx`, an image, or an HTML error page saved by a failed download is a routine occurrence,
especially with files pulled from a portal.

For genuine damage — truncated downloads, bad byte ranges — `qpdf --check file.pdf` reports what is
wrong and `qpdf --qdf --object-streams=disable in.pdf out.pdf` often rebuilds a readable file. If a
file is truncated, note that the *tail* is missing, which in a statement or report is usually the
totals.

## How the classifier decides

Useful to know so you can judge when to override it.

It walks the PDF's objects, inflates every stream it can with zlib, and then measures **only page
content streams** — identified by requiring the `BT` and `Tf` operator tokens plus an
ASCII-dominant body. That filter matters more than it sounds: object streams, XMP metadata and
embedded font programs are full of strings, and counting those invents text in files that have
none. Inflated binary also contains the bytes `BT` by coincidence often enough that a naive
substring test passes on it, after which any parenthesis in the noise counts as a text string.
Both bugs turn "needs OCR" into "extract directly", which is the worst error available.

From the surviving content streams it counts the characters inside text-showing operators, halving
hex-string counts for `Identity-H` CID fonts where each glyph is two bytes. Validated against
`pdftotext` on real documents, the estimate lands within about 1.0-1.3x — close enough to separate
the classes, and not a substitute for actual extraction.

Then:

- under ~50 chars/page **and** roughly one image per page → `SCANNED`
- under ~50 chars/page without the images → `NO_TEXT_LAYER`
- under ~350 chars/page with substantial images → `MIXED`
- fillable fields present → `FORM`
- otherwise → `TEXT`

Override it when you have better information. If it says `MIXED` and a rendered page is clearly all
live text, trust the page.
