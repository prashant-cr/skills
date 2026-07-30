#!/usr/bin/env python3
"""Classify a PDF before trying to extract from it, and name the route that works.

This exists because the most common PDF extraction failure is silent. Point a
text extractor at a scanned document and it returns an empty string -- not an
error. The natural conclusion is "the file is corrupt" or "the library is
broken", when in fact the file contains no text at all, only pictures of text.
Ten minutes get spent debugging the wrong thing.

So classify first. It costs milliseconds, needs nothing installed, and it turns
an invisible failure into a stated fact.

    python3 pdf_triage.py file.pdf
    python3 pdf_triage.py folder/ --batch
    python3 pdf_triage.py file.pdf --json

Standard library only -- no pypdf, no pdfplumber, nothing to install. It reads
the PDF's own object structure and inflates the streams with zlib, which is
enough to tell text from images from forms from encryption.
"""

import argparse
import json
import pathlib
import re
import shutil
import sys
import zlib

# Text-showing operators. Tj/TJ show strings; ' and " show a string and move to
# the next line. If a page has none of these, nothing on it is selectable text.
TEXT_OPS = re.compile(rb"(?:^|[\s\]>)])(Tj|TJ|'|\")(?=[\s\[<(/]|$)")
POS_OPS = re.compile(rb"(?:^|[\s\]>)])(Td|TD|Tm|T\*)(?=[\s\[<(/]|$)")

# The operators above only say *that* text was drawn. What matters is how much,
# and in what shape, so pull the actual strings out too. A PDF string is either
# (literal, with backslash escapes) or <hexadecimal>.
PDF_STR = re.compile(rb"\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]*>")
# One logical run: a single string shown with Tj, or a whole array shown with TJ
# (kerning splits one visual word across many strings, so the array is the run).
RUN = re.compile(rb"\[(?:[^\[\]\\]|\\.)*\]\s*TJ|"
                 rb"(?:\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]*>)\s*(?:Tj|'|\")", re.DOTALL)


def str_len(tok, hex_bytes_per_char=1):
    """Approximate character count of one PDF string token.

    hex_bytes_per_char is 2 for documents using Identity-H CID fonts, where each
    glyph is a two-byte code. Assuming one byte there doubles the count, which
    showed up as a 2.3x overestimate against pdftotext on real files.
    """
    if tok.startswith(b"<"):
        digits = len(re.sub(rb"\s", b"", tok[1:-1]))
        return digits // (2 * hex_bytes_per_char)
    body = tok[1:-1]
    body = re.sub(rb"\\[0-7]{1,3}", b"X", body)  # octal escapes are one char
    body = re.sub(rb"\\.", b"X", body)           # \( \) \\ \n etc are one char
    return len(body)


BT_TOKEN = re.compile(rb"(?:^|[\s>\]])BT(?=[\s/\[<(]|$)")
TF_TOKEN = re.compile(rb"(?:^|[\s>\]])Tf(?=[\s/\[<(]|$)")
PRINTABLE = bytes(range(32, 127)) + b"\t\r\n"


def is_content_stream(data):
    """True only for a page-description stream that actually draws text.

    Content streams are ASCII sequences of operators. Binary blobs -- inflated
    image data, font programs, colour profiles -- contain the bytes "BT" by
    coincidence often enough that a substring test passes on them, and then any
    parenthesis in the noise gets counted as a text string. That invents text in
    files which have none, which is the single worst thing this script could do,
    since it turns "needs OCR" into "extract directly" and the user gets nothing.
    So require the operator tokens *and* an ASCII-dominant body.
    """
    if not data:
        return False
    sample = data[:65536]
    printable = sum(1 for b in sample if b in PRINTABLE)
    if printable / len(sample) < 0.85:
        return False
    return bool(BT_TOKEN.search(data)) and bool(TF_TOKEN.search(data))


def measure_text(content, hex_bytes_per_char=1):
    """Return (estimated chars, list of logical run lengths) for a content stream."""
    chars, runs = 0, []
    for m in RUN.finditer(content):
        n = sum(str_len(t, hex_bytes_per_char) for t in PDF_STR.findall(m.group(0)))
        if n:
            runs.append(n)
            chars += n
    return chars, runs

OBJ = re.compile(rb"(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj", re.DOTALL)
STREAM = re.compile(rb"\bstream\r?\n?(.*?)\r?\n?\bendstream", re.DOTALL)

TOOLS = {
    "pdftotext": "poppler -- best general text and layout extraction",
    "pdftoppm": "poppler -- renders pages to images for OCR",
    "pdfinfo": "poppler -- metadata and page count",
    "tesseract": "OCR engine for scanned pages",
    "qpdf": "repairs damaged PDFs, removes owner passwords you hold",
}


def available_tools():
    return {name: shutil.which(name) is not None for name in TOOLS}


def python_libs():
    libs = {}
    for mod in ("pypdf", "pdfplumber", "fitz", "openpyxl", "pandas", "docx"):
        try:
            __import__(mod)
            libs[mod] = True
        except Exception:
            libs[mod] = False
    return libs


def inflate(payload):
    """Try the two deflate framings PDFs actually use. Returns None if neither."""
    for wbits in (15, -15):
        try:
            return zlib.decompressobj(wbits).decompress(payload)
        except Exception:
            continue
    return None


def analyse(path):
    raw = path.read_bytes()
    r = {
        "file": str(path),
        "size_bytes": len(raw),
        "valid_pdf": raw[:5] == b"%PDF-",
        "pdf_version": raw[5:8].decode("latin-1", "replace") if len(raw) > 8 else "?",
    }
    if not r["valid_pdf"]:
        # Worth checking, because "my PDF won't parse" is sometimes a renamed file.
        sniff = {b"PK\x03\x04": "a zip (maybe .docx/.xlsx renamed)",
                 b"\xd0\xcf\x11\xe0": "a legacy Office file (.doc/.xls)",
                 b"\x89PNG": "a PNG image", b"\xff\xd8\xff": "a JPEG image"}
        r["actually"] = next((v for k, v in sniff.items() if raw.startswith(k)),
                            "not a recognised format")
        r["type"] = "NOT_A_PDF"
        r["route"] = f"This file is {r['actually']}, not a PDF. Handle it as that instead."
        return r

    # --- walk objects, inflating what we can -----------------------------
    # Two-byte glyph codes if the document uses Identity-H CID fonts.
    hex_w = 2 if re.search(rb"/Identity-H|/Identity\s*-\s*H", raw) else 1
    text_ops = pos_ops = 0
    image_objs = 0
    inflated_total = 0
    est_chars = 0
    runs = []
    searchable = bytearray(raw)

    for match in OBJ.finditer(raw):
        body = match.group(3)
        dict_part = body.split(b"stream", 1)[0]
        is_image = b"/Image" in dict_part
        if is_image:
            image_objs += 1
        m = STREAM.search(body)
        if not m:
            continue
        out = inflate(m.group(1))
        if out is None:
            continue
        inflated_total += len(out)
        # Object streams hold other objects' dictionaries; appending them makes
        # /AcroForm, /FT and page markers findable in modern compressed PDFs.
        searchable += out
        # Only *page content* streams describe what a reader sees. Object streams,
        # XMP metadata and embedded font programs are full of strings too, and
        # counting them invents text that no extractor will ever return -- which
        # is exactly how a scanned file gets mistaken for one containing text.
        if is_image or any(k in dict_part for k in
                           (b"/ObjStm", b"/Metadata", b"/FontFile", b"/Type/Font",
                            b"/Type /Font", b"/XML")):
            continue
        if not is_content_stream(out):
            continue
        text_ops += len(TEXT_OPS.findall(out))
        pos_ops += len(POS_OPS.findall(out))
        c, rr = measure_text(out, hex_w)
        est_chars += c
        runs.extend(rr)

    # Uncompressed content streams still exist in older/simpler PDFs.
    if text_ops == 0:
        for m in STREAM.finditer(raw):
            body = m.group(1)
            if not is_content_stream(body):
                continue
            text_ops += len(TEXT_OPS.findall(body))
            pos_ops += len(POS_OPS.findall(body))
            c, rr = measure_text(body, hex_w)
            est_chars += c
            runs.extend(rr)

    blob = bytes(searchable)
    image_objs = max(image_objs, len(re.findall(rb"/Subtype\s*/Image", blob)))
    pages = len(re.findall(rb"/Type\s*/Page(?![s/])", blob))
    if pages == 0:
        counts = [int(x) for x in re.findall(rb"/Count\s+(\d+)", blob)]
        pages = max(counts) if counts else 1
    form_fields = len(re.findall(rb"/FT\s*/(?:Tx|Btn|Ch|Sig)", blob))

    r.update({
        "pages": pages,
        "text_show_ops": text_ops,
        "position_ops": pos_ops,
        "image_objects": image_objs,
        "form_fields": form_fields,
        "encrypted": bool(re.search(rb"/Encrypt\b", raw)),
        "has_acroform": b"/AcroForm" in blob,
        "has_xfa": b"/XFA" in blob,
        "inflated_bytes": inflated_total,
        "tools": available_tools(),
        "python_libs": python_libs(),
    })

    ops_per_page = text_ops / max(pages, 1)
    chars_per_page = est_chars / max(pages, 1)
    r["text_ops_per_page"] = round(ops_per_page, 1)
    r["est_chars"] = est_chars
    r["est_chars_per_page"] = round(chars_per_page)
    # Run-length shape separates tables from prose better than operator counts do.
    # A table cell is its own short run; a paragraph line is one long run.
    if runs:
        r["mean_run_len"] = round(sum(runs) / len(runs), 1)
        r["short_run_share"] = round(sum(1 for n in runs if n <= 12) / len(runs), 2)
    else:
        r["mean_run_len"] = 0.0
        r["short_run_share"] = 0.0

    # --- classify ---------------------------------------------------------
    if r["encrypted"]:
        r["type"] = "ENCRYPTED"
        r["route"] = (
            "Encrypted. If you have the password, decrypt first "
            "(qpdf --decrypt --password=PW in.pdf out.pdf). Many PDFs carry an "
            "owner password with an empty user password, which qpdf opens with no "
            "password at all -- try that before asking the user for one. Do not "
            "attempt to defeat a password you were not given."
        )
    elif r["has_xfa"]:
        r["type"] = "XFA_FORM"
        r["route"] = ("XFA (LiveCycle) form -- the data lives in embedded XML, not "
                      "page content. Extract the XFA XML packet rather than the text.")
    elif chars_per_page < 50 and image_objs >= max(pages, 1) * 0.8:
        # Judged on characters, not operators. A scan often carries a handful of
        # stray text ops -- a stamp, an annotation, an empty run -- which are
        # enough to fail an "ops == 0" test while yielding no readable text at all.
        r["type"] = "SCANNED"
        r["route"] = (
            "Effectively no text layer -- this is pictures of text. Every text "
            "extractor will return empty or near-empty output, which is correct "
            "behaviour, not a bug. OCR is the only route."
        )
    elif chars_per_page < 50:
        r["type"] = "NO_TEXT_LAYER"
        r["route"] = ("Almost no extractable text and few images. Possibly "
                      "vector-drawn text, a cover-only file, or damaged. Render a "
                      "page and look at it before assuming anything; try qpdf "
                      "--check to test for damage.")
    elif chars_per_page < 350 and image_objs >= max(pages, 1) * 0.5:
        r["type"] = "MIXED"
        r["route"] = (
            "Mostly images with a thin text layer -- often a scanned document "
            "someone already OCR'd, or a designed catalogue with text in the "
            "artwork. Extract the text layer, then check whether what came out is "
            "a real fraction of what is on the page. If not, OCR as well."
        )
    elif form_fields > 0:
        r["type"] = "FORM"
        r["route"] = ("AcroForm with fillable fields. Read the field values as "
                      "key/value pairs -- far more reliable than reading page text, "
                      "since field names are stable and labels move.")
    else:
        r["type"] = "TEXT"
        r["route"] = "Has a real text layer. Extract directly, no OCR needed."

    if r["type"] in ("TEXT", "FORM", "MIXED"):
        if r["short_run_share"] >= 0.6:
            r["layout_hint"] = (
                f"{r['short_run_share']:.0%} of text runs are 12 characters or fewer "
                f"(mean {r['mean_run_len']}) -- that is cell-shaped, not "
                "sentence-shaped. Treat as tabular and extract with layout "
                "preserved, or the columns will collapse into one another."
            )
        elif r["short_run_share"] >= 0.35:
            r["layout_hint"] = (
                f"Mixed shape ({r['short_run_share']:.0%} short runs, mean "
                f"{r['mean_run_len']}) -- likely prose with tables in it, or a form "
                "layout. Extract with layout preserved and inspect before shaping."
            )
        else:
            r["layout_hint"] = (
                f"Mean run length {r['mean_run_len']} with only "
                f"{r['short_run_share']:.0%} short runs -- flowing prose. Plain text "
                "extraction is fine; a spreadsheet is probably the wrong target."
            )

    r["blockers"] = blockers(r)
    return r


def blockers(r):
    """What is missing that this specific file needs."""
    out = []
    t, tools = r["type"], r.get("tools", {})
    libs = r.get("python_libs", {})
    if t in ("SCANNED", "MIXED"):
        if not tools.get("tesseract"):
            out.append("tesseract not installed -- required to OCR this file "
                       "(macOS: brew install tesseract; Debian: apt install tesseract-ocr)")
        if not tools.get("pdftoppm") and not libs.get("fitz"):
            out.append("no page rasteriser -- install poppler (brew install poppler / "
                       "apt install poppler-utils) or PyMuPDF")
    if t in ("TEXT", "FORM", "MIXED"):
        if not tools.get("pdftotext") and not libs.get("pdfplumber") and not libs.get("pypdf"):
            out.append("no text extractor -- install poppler for pdftotext, or "
                       "pip install pdfplumber")
    if t == "ENCRYPTED" and not tools.get("qpdf"):
        out.append("qpdf not installed -- needed to decrypt (brew install qpdf)")
    return out


def render(r):
    o = []
    o.append(f"{pathlib.Path(r['file']).name}")
    if r["type"] == "NOT_A_PDF":
        o.append(f"  Type      {r['type']}  -- {r['actually']}")
        o.append(f"  Route     {r['route']}")
        return "\n".join(o)

    o.append(f"  Type      {r['type']}")
    o.append(f"  Pages     {r['pages']}     Size {r['size_bytes'] / 1024:.0f} KB"
             f"     PDF {r['pdf_version']}")
    o.append(f"  Text      {r['est_chars']:,} chars ({r['est_chars_per_page']}/page)"
             f"     Images {r['image_objects']}"
             f"     Fields {r['form_fields']}")
    o.append(f"  Runs      mean {r['mean_run_len']} chars,"
             f" {r['short_run_share']:.0%} are 12 or fewer")
    o.append("")
    o.append(f"  Route     {r['route']}")
    if r.get("layout_hint"):
        o.append(f"  Layout    {r['layout_hint']}")
    if r["blockers"]:
        o.append("")
        o.append("  MISSING")
        for b in r["blockers"]:
            o.append(f"    ! {b}")
    else:
        have = [t for t, ok in r["tools"].items() if ok]
        o.append(f"  Have      {', '.join(have) if have else 'no external tools'}")
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target", help="a PDF file, or a folder with --batch")
    ap.add_argument("--batch", action="store_true", help="classify every PDF in a folder")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    p = pathlib.Path(args.target).expanduser()
    if not p.exists():
        raise SystemExit(f"error: {p} does not exist")

    if args.batch or p.is_dir():
        files = sorted(f for f in p.rglob("*") if f.suffix.lower() == ".pdf")
        if not files:
            raise SystemExit(f"error: no PDFs found under {p}")
        results = []
        for f in files:
            try:
                results.append(analyse(f))
            except Exception as exc:
                results.append({"file": str(f), "type": "ERROR", "route": str(exc),
                                "blockers": []})
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            by_type = {}
            for r in results:
                by_type.setdefault(r["type"], []).append(r)
            print(f"{len(results)} PDFs under {p}\n")
            for t, group in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
                print(f"  {t:14} {len(group):>4}")
            print()
            # Surface only what needs a decision -- a clean TEXT file needs none.
            needs = [r for r in results
                     if r["type"] not in ("TEXT", "FORM") or r.get("blockers")]
            if needs:
                print(f"{len(needs)} need attention before extraction:\n")
                for r in needs[:40]:
                    print(f"  {r['type']:14} {pathlib.Path(r['file']).name[:58]}")
                    for b in r.get("blockers", []):
                        print(f"                 ! {b}")
                if len(needs) > 40:
                    print(f"  ... and {len(needs) - 40} more (use --json for all)")
            else:
                print("All have text layers and the tools are present. Extract directly.")
        return 0

    r = analyse(p)
    print(json.dumps(r, indent=2) if args.json else render(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
