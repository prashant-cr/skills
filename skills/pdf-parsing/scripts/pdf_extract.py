#!/usr/bin/env python3
"""Extract text, tables and form fields from a PDF, using whatever is installed.

Routes itself from pdf_triage's classification, because the right extractor
depends entirely on what the PDF is: a text-layer document wants layout-preserving
text extraction, a scan wants OCR, a form wants its field values read directly.
Using the wrong one produces empty or scrambled output rather than an error.

    python3 pdf_extract.py file.pdf                 # text + tables to stdout summary
    python3 pdf_extract.py file.pdf -o out/         # write text, tables as CSV, JSON
    python3 pdf_extract.py folder/ --batch -o out/  # every PDF, plus a failure list
    python3 pdf_extract.py file.pdf --pages 2-5

Table detection is deliberately simple and dependency-free: it reads
layout-preserved text and finds the character columns that are blank on every
line of a block. Those are the gaps between real columns. It handles the common
case well and will not pretend to handle merged cells -- check its output.
"""

import argparse
import csv
import json
import pathlib
import re
import shutil
import statistics
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pdf_triage import analyse  # noqa: E402

MIN_TABLE_ROWS = 3
MIN_TABLE_COLS = 2
MIN_GAP = 2          # a column separator is at least this many blank characters
MIN_COL_FILL = 0.6   # every column must carry data on this share of rows
OCR_DPI = 300        # below ~250 OCR accuracy falls off sharply for body text


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# --------------------------------------------------------------------------
# text
# --------------------------------------------------------------------------

def text_via_pdftotext(path, first=None, last=None, layout=True):
    cmd = ["pdftotext", "-q"]
    if layout:
        cmd.append("-layout")
    if first:
        cmd += ["-f", str(first)]
    if last:
        cmd += ["-l", str(last)]
    cmd += [str(path), "-"]
    p = run(cmd)
    return p.stdout if p.returncode == 0 else None


def text_via_pdfplumber(path, first=None, last=None):
    try:
        import pdfplumber
    except Exception:
        return None
    out = []
    with pdfplumber.open(str(path)) as pdf:
        pages = pdf.pages[(first - 1 if first else 0):(last if last else None)]
        for pg in pages:
            out.append(pg.extract_text(layout=True) or "")
    return "\f".join(out)


def text_via_pypdf(path, first=None, last=None):
    try:
        from pypdf import PdfReader
    except Exception:
        return None
    reader = PdfReader(str(path))
    pages = reader.pages[(first - 1 if first else 0):(last if last else None)]
    # No layout mode here, so columns will not survive. Last resort only.
    return "\f".join((pg.extract_text() or "") for pg in pages)


def text_via_ocr(path, first=None, last=None, dpi=OCR_DPI, lang="eng"):
    """Rasterise then OCR. Requires pdftoppm (or PyMuPDF) plus tesseract."""
    if not shutil.which("tesseract"):
        return None, "tesseract not installed"
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        if shutil.which("pdftoppm"):
            cmd = ["pdftoppm", "-r", str(dpi), "-png"]
            if first:
                cmd += ["-f", str(first)]
            if last:
                cmd += ["-l", str(last)]
            cmd += [str(path), str(tmp / "pg")]
            p = run(cmd)
            if p.returncode != 0:
                return None, f"pdftoppm failed: {p.stderr.strip()[:200]}"
        else:
            try:
                import fitz
            except Exception:
                return None, "no rasteriser: install poppler (pdftoppm) or PyMuPDF"
            doc = fitz.open(str(path))
            rng = range((first - 1 if first else 0), (last if last else doc.page_count))
            for i in rng:
                pix = doc[i].get_pixmap(dpi=dpi)
                pix.save(str(tmp / f"pg-{i + 1:04d}.png"))

        images = sorted(tmp.glob("pg*.png")) or sorted(tmp.glob("pg*.ppm"))
        if not images:
            return None, "rasteriser produced no images"
        pages = []
        for img in images:
            # -psm/--psm 6 assumes a uniform block, which suits statements and
            # tables far better than the default page segmentation.
            p = run(["tesseract", str(img), "stdout", "-l", lang, "--psm", "6"])
            pages.append(p.stdout if p.returncode == 0 else "")
        return "\f".join(pages), None


def extract_text(path, kind, first=None, last=None, lang="eng"):
    """Returns (text, method, warning)."""
    if kind in ("SCANNED", "NO_TEXT_LAYER"):
        txt, err = text_via_ocr(path, first, last, lang=lang)
        return txt, "ocr", err

    for fn, name in ((text_via_pdftotext, "pdftotext -layout"),
                     (text_via_pdfplumber, "pdfplumber"),
                     (text_via_pypdf, "pypdf (no layout)")):
        txt = fn(path, first, last)
        if txt and txt.strip():
            warn = None
            if kind == "MIXED":
                warn = ("MIXED document: this is the text layer only. Compare the "
                        "character count against what you can see on the page -- if "
                        "most of the content is in the images, OCR as well "
                        "(--force-ocr).")
            return txt, name, warn

    # A text-layer PDF that yields nothing usually means unmappable glyphs.
    txt, err = text_via_ocr(path, first, last, lang=lang)
    if txt:
        return txt, "ocr (fallback)", (
            "Text extractors returned nothing despite a text layer -- typically "
            "fonts with no ToUnicode mapping. OCR was used instead.")
    return None, None, err or "no extractor available"


# --------------------------------------------------------------------------
# tables, from layout-preserved text
# --------------------------------------------------------------------------

def blocks_of(lines):
    """Group consecutive non-blank lines."""
    block, out = [], []
    for ln in lines:
        if ln.strip():
            block.append(ln)
        else:
            if len(block) >= MIN_TABLE_ROWS:
                out.append(block)
            block = []
    if len(block) >= MIN_TABLE_ROWS:
        out.append(block)
    return out


def column_gaps(block):
    """Character positions blank on every line -- the gaps between columns."""
    width = max(len(l) for l in block)
    padded = [l.ljust(width) for l in block]
    blank = [all(row[i] == " " for row in padded) for i in range(width)]

    gaps, start = [], None
    for i, b in enumerate(blank):
        if b and start is None:
            start = i
        elif not b and start is not None:
            if i - start >= MIN_GAP:
                gaps.append((start, i))
            start = None
    if start is not None and width - start >= MIN_GAP:
        gaps.append((start, width))
    return gaps, width


def block_to_rows(block):
    gaps, width = column_gaps(block)
    # Leading/trailing gaps are margins, not separators.
    inner = [g for g in gaps if g[0] > 0 and g[1] < width]
    if not inner:
        return None
    bounds = [0] + [g[0] for g in inner] + [width]
    rows = []
    for line in block:
        padded = line.ljust(width)
        cells = [padded[bounds[i]:bounds[i + 1]].strip() for i in range(len(bounds) - 1)]
        if any(cells):
            rows.append(cells)
    ncols = len(bounds) - 1
    if len(rows) < MIN_TABLE_ROWS or ncols < MIN_TABLE_COLS:
        return None

    # Guard against prose. Wrapped paragraph text often has a character column
    # that happens to be blank on every line, which splits it into a "table"
    # whose second column is empty on most rows. A real table fills its cells.
    # Without this check a plain contract yields dozens of 3x2 phantom tables,
    # and that noise is worse than reporting no tables at all.
    fill = [sum(1 for r in rows if r[c].strip()) / len(rows) for c in range(ncols)]
    med = statistics.median(fill)
    mean = sum(fill) / len(fill)
    # Coefficient of variation across columns. Measured on real documents, this
    # separates the two cases cleanly: genuine tables fill their columns evenly
    # (CV 0.07-0.55) while a paragraph split at a coincidental blank strip is
    # lopsided -- one full column against one mostly empty (CV 0.50-0.90).
    cv = (statistics.pstdev(fill) / mean) if mean else 99.0
    widths = [max(len(r[c]) for r in rows) for c in range(ncols)]

    if ncols == 2:
        # Two columns is where the false positives live, because wrapped prose
        # produces them constantly and real two-column tables are uncommon. Demand
        # even, well-filled, narrow cells before believing it.
        if med < MIN_COL_FILL or cv > 0.35 or max(widths) > 55:
            return None
        confidence = "medium"
    else:
        confidence = "high" if med >= 0.5 else "low"

    # Low but *even* fill across three or more columns is the signature of a table
    # whose records wrap over several physical lines, or of a multi-column page
    # layout. Real data, but not one-record-per-row, so say so rather than handing
    # over sparse rows that look clean.
    sparse = med < 0.5
    if sparse and cv > 0.6:
        return None
    return rows, confidence, sparse


def find_tables(text):
    tables = []
    for pno, page in enumerate(text.split("\f"), 1):
        for block in blocks_of(page.split("\n")):
            got = block_to_rows(block)
            if not got:
                continue
            rows, confidence, sparse = got
            tables.append({"page": pno, "rows": rows, "n_rows": len(rows),
                           "n_cols": len(rows[0]), "confidence": confidence,
                           "sparse": sparse})
    return tables


# --------------------------------------------------------------------------
# form fields, straight from the PDF structure
# --------------------------------------------------------------------------

FIELD = re.compile(rb"/T\s*\((?:[^()\\]|\\.)*\)|/V\s*\((?:[^()\\]|\\.)*\)")


def form_fields(path):
    """Pull /T (name) and /V (value) pairs. Order in the file pairs them reliably
    enough for a first pass; verify against the page if the values look shifted."""
    raw = path.read_bytes()
    out, pending = {}, None
    for m in FIELD.finditer(raw):
        tok = m.group(0)
        val = tok[tok.index(b"(") + 1:-1].decode("latin-1", "replace")
        val = re.sub(r"\\([()\\])", r"\1", val)
        if tok.startswith(b"/T"):
            pending = val
        elif pending is not None:
            out[pending] = val
            pending = None
    return out


# --------------------------------------------------------------------------

def extract_one(path, args):
    tri = analyse(path)
    rec = {"file": str(path), "type": tri["type"], "pages": tri.get("pages"),
           "route": tri.get("route"), "text": None, "method": None,
           "warning": None, "tables": [], "fields": {}, "error": None}

    if tri["type"] == "NOT_A_PDF":
        rec["error"] = tri["route"]
        return rec
    if tri["type"] == "ENCRYPTED":
        # An empty user password is extremely common; try it before giving up.
        if shutil.which("qpdf"):
            tmp = path.with_suffix(".decrypted.pdf")
            p = run(["qpdf", "--decrypt", "--password=", str(path), str(tmp)])
            if p.returncode == 0 and tmp.exists():
                rec["note"] = "opened with an empty user password via qpdf"
                sub = extract_one(tmp, args)
                tmp.unlink(missing_ok=True)
                sub["file"] = str(path)
                sub["note"] = rec["note"]
                return sub
            tmp.unlink(missing_ok=True)
        rec["error"] = ("encrypted and could not be opened with an empty password. "
                        "Ask the user for the password.")
        return rec

    first = last = None
    if args.pages:
        m = re.match(r"^(\d+)(?:-(\d+))?$", args.pages)
        if not m:
            raise SystemExit("error: --pages wants N or N-M")
        first = int(m.group(1))
        last = int(m.group(2) or m.group(1))

    kind = "SCANNED" if args.force_ocr else tri["type"]
    text, method, warn = extract_text(path, kind, first, last, lang=args.lang)
    rec.update({"text": text, "method": method, "warning": warn})
    if text is None:
        rec["error"] = warn or "extraction produced nothing"
        return rec

    # Count non-whitespace, since -layout pads rows out with spaces and a raw
# len() makes a sparse table look like a dense document.
    rec["chars"] = len(re.sub(r"\s", "", text))
    rec["tables"] = find_tables(text)
    if tri.get("form_fields"):
        rec["fields"] = form_fields(path)
    return rec


def write_outputs(rec, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", pathlib.Path(rec["file"]).stem)[:60]
    written = []
    if rec.get("text"):
        f = outdir / f"{stem}.txt"
        f.write_text(rec["text"])
        written.append(f)
    for i, t in enumerate(rec.get("tables", []), 1):
        f = outdir / f"{stem}.table{i}_p{t['page']}.csv"
        with open(f, "w", newline="") as fh:
            csv.writer(fh).writerows(t["rows"])
        written.append(f)
    if rec.get("fields"):
        f = outdir / f"{stem}.fields.json"
        f.write_text(json.dumps(rec["fields"], indent=2))
        written.append(f)
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target")
    ap.add_argument("-o", "--outdir", help="write text/CSV/JSON here")
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--pages", help="N or N-M")
    ap.add_argument("--force-ocr", action="store_true", help="OCR even if text exists")
    ap.add_argument("--lang", default="eng", help="tesseract language(s), e.g. eng+hin")
    ap.add_argument("--json", action="store_true", help="full result as JSON")
    args = ap.parse_args()

    p = pathlib.Path(args.target).expanduser()
    if not p.exists():
        raise SystemExit(f"error: {p} does not exist")
    outdir = pathlib.Path(args.outdir).expanduser() if args.outdir else None

    targets = (sorted(f for f in p.rglob("*") if f.suffix.lower() == ".pdf")
               if (args.batch or p.is_dir()) else [p])
    if not targets:
        raise SystemExit(f"error: no PDFs under {p}")

    records, failed = [], []
    for f in targets:
        try:
            rec = extract_one(f, args)
        except Exception as exc:
            rec = {"file": str(f), "type": "ERROR", "error": f"{type(exc).__name__}: {exc}",
                   "tables": [], "fields": {}}
        if rec.get("error"):
            failed.append(rec)
        records.append(rec)
        if outdir and not rec.get("error"):
            write_outputs(rec, outdir)

    if args.json:
        print(json.dumps(records, indent=2))
        return 1 if failed and len(failed) == len(records) else 0

    for rec in records:
        name = pathlib.Path(rec["file"]).name
        if rec.get("error"):
            print(f"FAIL  {name}\n        {rec['type']}: {rec['error']}")
            continue
        tbl = rec["tables"]
        shape = ", ".join(f"p{t['page']} {t['n_rows']}x{t['n_cols']}"
                          f"{'~' if t.get('sparse') else ''}" for t in tbl[:6])
        print(f"ok    {name}")
        print(f"        {rec['type']} via {rec['method']} -- {rec.get('chars', 0):,} chars, "
              f"{len(tbl)} table(s){': ' + shape if shape else ''}"
              f"{', ' + str(len(rec['fields'])) + ' fields' if rec['fields'] else ''}")
        if rec.get("note"):
            print(f"        note: {rec['note']}")
        if any(t.get("sparse") for t in tbl):
            print("        ~ marked tables are sparse -- records probably wrap over "
                  "several lines, or the page is a multi-column layout. Inspect "
                  "before treating a line as a record.")
        if rec.get("warning"):
            print(f"        ! {rec['warning']}")

    if len(records) > 1:
        print(f"\n{len(records) - len(failed)} of {len(records)} extracted"
              f"{f', {len(failed)} failed' if failed else ''}.")
    if outdir:
        print(f"Outputs in {outdir}")
        if failed:
            fp = outdir / "_failed.csv"
            with open(fp, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["file", "type", "reason"])
                for r in failed:
                    w.writerow([r["file"], r["type"], r["error"]])
            print(f"Failures listed in {fp}")
    return 1 if failed and len(failed) == len(records) else 0


if __name__ == "__main__":
    sys.exit(main())
