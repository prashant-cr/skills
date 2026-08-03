#!/usr/bin/env python3
"""Extract a resume the way an ATS parser sees it, and report structural hazards.

Stdlib only. A .docx is a zip of XML, so no library is needed to read one, and
depending on python-docx would make this skill fail on machines that lack it.

Usage:
    python3 extract_resume_text.py resume.docx           # plain text to stdout
    python3 extract_resume_text.py resume.pdf --json     # text + structural flags

The point of running this before reading the resume yourself: the visual layout
and the parsed text are two different documents. Judging a resume by how it
looks in a PDF viewer is how a two-column layout that interleaves into nonsense
gets shipped.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
V = "{urn:schemas-microsoft-com:vml}"
WPS = "{http://schemas.microsoft.com/office/word/2010/wordprocessingShape}"


def _tag(el):
    return el.tag


def _para_text(p):
    """Concatenate the visible text of one w:p, in document order."""
    out = []
    for node in p.iter():
        t = node.tag
        if t == W + "t":
            out.append(node.text or "")
        elif t == W + "tab":
            out.append("\t")
        elif t in (W + "br", W + "cr"):
            out.append("\n")
        elif t == W + "noBreakHyphen":
            out.append("-")
    return "".join(out)


def _xml_text(data):
    """All text in a part (used for headers/footers)."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return ""
    return "\n".join(
        s for s in (_para_text(p).strip() for p in root.iter(W + "p")) if s
    )


def extract_docx(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        doc = z.read("word/document.xml")
        headers = [_xml_text(z.read(n)) for n in names if re.match(r"word/header\d*\.xml$", n)]
        footers = [_xml_text(z.read(n)) for n in names if re.match(r"word/footer\d*\.xml$", n)]
        media = [n for n in names if n.startswith("word/media/")]

    root = ET.fromstring(doc)
    body = root.find(W + "body")

    # Text inside a text box is visually part of the page but is a separate
    # story in the XML; several parsers drop it entirely.
    textbox_paras = set()
    textbox_text = []
    for tb in root.iter():
        if tb.tag.endswith("}txbxContent"):
            for p in tb.iter(W + "p"):
                textbox_paras.add(id(p))
                s = _para_text(p).strip()
                if s:
                    textbox_text.append(s)

    # Table cells: collect which paragraphs live inside a table.
    table_paras = set()
    tables = list(root.iter(W + "tbl"))
    for tbl in tables:
        for p in tbl.iter(W + "p"):
            table_paras.add(id(p))

    paragraphs = []
    for p in body.iter(W + "p") if body is not None else []:
        text = _para_text(p).rstrip()
        paragraphs.append(
            {
                "text": text,
                "in_table": id(p) in table_paras,
                "in_textbox": id(p) in textbox_paras,
            }
        )

    # Multi-column sections reorder text unpredictably on extraction.
    max_cols = 1
    for cols in root.iter(W + "cols"):
        try:
            max_cols = max(max_cols, int(cols.get(W + "num", "1")))
        except ValueError:
            pass

    fonts = set()
    for rf in root.iter(W + "rFonts"):
        for attr in ("ascii", "hAnsi", "cs"):
            val = rf.get(W + attr)
            if val:
                fonts.add(val)

    # Hyperlinks whose visible text hides the URL ("LinkedIn" instead of the
    # address) lose the address completely in text extraction.
    hyperlinks = len(list(root.iter(W + "hyperlink")))

    text = "\n".join(p["text"] for p in paragraphs)
    return {
        "source": os.path.basename(path),
        "format": "docx",
        "text": text,
        "paragraphs": paragraphs,
        "flags": {
            "table_count": len(tables),
            "paragraphs_in_tables": sum(1 for p in paragraphs if p["in_table"]),
            "textbox_count": len(textbox_text),
            "textbox_text": textbox_text,
            "image_count": len(media),
            "max_columns": max_cols,
            "header_text": [h for h in headers if h],
            "footer_text": [f for f in footers if f],
            "fonts": sorted(fonts),
            "hyperlink_count": hyperlinks,
        },
    }


def extract_pdf(path):
    text = ""
    tool = None
    if shutil.which("pdftotext"):
        # -layout keeps columns visually apart so a two-column resume is
        # recognisable as one; ATS parsers mostly do NOT do this, which is
        # exactly why two columns are dangerous.
        try:
            text = subprocess.run(
                ["pdftotext", "-layout", path, "-"],
                capture_output=True, text=True, timeout=60,
            ).stdout
            tool = "pdftotext -layout"
        except Exception:
            text = ""
    if not text.strip():
        try:
            import pypdf  # type: ignore

            text = "\n".join(pg.extract_text() or "" for pg in pypdf.PdfReader(path).pages)
            tool = "pypdf"
        except Exception:
            pass

    pages = text.count("\f") + 1 if text else 0
    return {
        "source": os.path.basename(path),
        "format": "pdf",
        "text": text,
        "paragraphs": [{"text": l, "in_table": False, "in_textbox": False}
                       for l in text.splitlines()],
        "flags": {
            "extractor": tool,
            "page_count": pages,
            "chars_per_page": round(len(text) / pages, 1) if pages else 0,
            "likely_image_only": len(text.strip()) < 200,
            "table_count": 0,
            "textbox_count": 0,
            "image_count": 0,
            "max_columns": 1,
            "header_text": [],
            "footer_text": [],
            "fonts": [],
            "hyperlink_count": 0,
        },
    }


def extract_plain(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    return {
        "source": os.path.basename(path),
        "format": os.path.splitext(path)[1].lstrip(".") or "txt",
        "text": text,
        "paragraphs": [{"text": l, "in_table": False, "in_textbox": False}
                       for l in text.splitlines()],
        "flags": {
            "table_count": 0, "textbox_count": 0, "image_count": 0,
            "max_columns": 1, "header_text": [], "footer_text": [],
            "fonts": [], "hyperlink_count": 0,
        },
    }


def extract(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return extract_docx(path)
    if ext == ".pdf":
        return extract_pdf(path)
    if ext in (".txt", ".md", ".markdown", ".rtf"):
        return extract_plain(path)
    if ext == ".doc":
        raise SystemExit(
            "Legacy .doc is not readable here and parses badly in many ATS. "
            "Ask the user to re-save as .docx, or convert with "
            "`libreoffice --headless --convert-to docx`."
        )
    raise SystemExit(f"Unsupported resume format: {ext or path}")


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    path = argv[1]
    if not os.path.exists(path):
        raise SystemExit(f"No such file: {path}")
    result = extract(path)
    if "--json" in argv:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(result["text"])
        if not result["text"].endswith("\n"):
            sys.stdout.write("\n")
        f = result["flags"]
        notable = {k: v for k, v in f.items()
                   if v not in (0, 1, [], None, False, "")
                   and k not in ("fonts", "extractor", "chars_per_page", "page_count")}
        if notable:
            sys.stderr.write("\n--- structural flags ---\n")
            sys.stderr.write(json.dumps(notable, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
