#!/usr/bin/env python3
"""Write a real multi-sheet .xlsx from CSV or JSON, using only the standard library.

An .xlsx file is a zip of XML parts, so it can be written without openpyxl,
pandas or anything else installed. That matters here because the machine that
needs a spreadsheet is often the one where pip install is not an option -- and
handing someone a .csv when they asked for Excel is a worse answer than it looks:
CSV loses the sheet-per-table structure, and Excel mangles long digit strings and
date-like values on import.

    python3 to_workbook.py out.xlsx data.csv
    python3 to_workbook.py out.xlsx t1.csv t2.csv --names Invoices,Lines
    python3 to_workbook.py out.xlsx extract.json      # pdf_extract.py --json output
    python3 to_workbook.py out.xlsx data.csv --text-columns 1,3

Numeric-looking cells become real numbers so they can be summed. Anything that
would be corrupted by that -- account numbers, invoice references, phone numbers,
codes with leading zeros -- stays text; see keep_as_text().
"""

import argparse
import csv
import json
import pathlib
import re
import sys
import zipfile

INVALID_SHEET = re.compile(r"[\[\]:*?/\\]")
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
NUMERIC = re.compile(r"^-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$")


def esc(s):
    s = CONTROL.sub("", str(s))
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def col_ref(n):
    """0 -> A, 25 -> Z, 26 -> AA."""
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def keep_as_text(v):
    """True when converting to a number would destroy information.

    Leading zeros vanish, long digit strings turn into scientific notation, and
    anything Excel reads as a date is rewritten silently. These are exactly the
    fields people most need intact from a PDF -- account numbers, invoice refs,
    GST/VAT ids, phone numbers -- so they stay as text.
    """
    if len(v) > 15:
        return True
    if len(v) > 1 and v[0] == "0" and v[1] not in ".,":
        return True
    return False


def as_number(v):
    if not NUMERIC.match(v) or keep_as_text(v):
        return None
    try:
        f = float(v.replace(",", ""))
    except ValueError:
        return None
    return f


def sheet_xml(rows, text_cols=()):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
           "<sheetData>"]
    for r, row in enumerate(rows, 1):
        out.append(f'<row r="{r}">')
        for c, val in enumerate(row):
            val = "" if val is None else str(val)
            if not val.strip():
                continue
            ref = f"{col_ref(c)}{r}"
            num = None if (c in text_cols or r == 1) else as_number(val.strip())
            if num is not None:
                out.append(f'<c r="{ref}"><v>{num:g}</v></c>')
            else:
                out.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">'
                           f"{esc(val)}</t></is></c>")
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def safe_name(name, used):
    name = INVALID_SHEET.sub("_", str(name)).strip() or "Sheet"
    name = name[:31]
    base, i = name, 2
    while name.lower() in used:
        suffix = f"_{i}"
        name = base[:31 - len(suffix)] + suffix
        i += 1
    used.add(name.lower())
    return name


def write_xlsx(path, sheets, text_cols=()):
    """sheets: list of (name, rows)."""
    used = set()
    named = [(safe_name(n, used), rows) for n, rows in sheets]

    ct = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>']
    for i in range(len(named)):
        ct.append(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
                  'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    ct.append("</Types>")

    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>")

    wb = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
          "<sheets>"]
    wbr = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i, (name, _rows) in enumerate(named, 1):
        wb.append(f'<sheet name="{esc(name)}" sheetId="{i}" r:id="rId{i}"/>')
        wbr.append(f'<Relationship Id="rId{i}" '
                   'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                   f'Target="worksheets/sheet{i}.xml"/>')
    wb.append("</sheets></workbook>")
    wbr.append("</Relationships>")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(ct))
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", "".join(wb))
        z.writestr("xl/_rels/workbook.xml.rels", "".join(wbr))
        for i, (_name, rows) in enumerate(named, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows, text_cols))
    return [n for n, _ in named]


def read_csv(p):
    with open(p, newline="", encoding="utf-8-sig") as fh:
        return [row for row in csv.reader(fh)]


def sheets_from_extract_json(data):
    """Build sheets from pdf_extract.py --json output."""
    sheets = []
    records = data if isinstance(data, list) else [data]

    fielded = [r for r in records if r.get("fields")]
    if fielded:
        keys = []
        for r in fielded:
            for k in r["fields"]:
                if k not in keys:
                    keys.append(k)
        rows = [["source_file"] + keys]
        for r in fielded:
            rows.append([pathlib.Path(r["file"]).name]
                        + [r["fields"].get(k, "") for k in keys])
        sheets.append(("Fields", rows))

    for r in records:
        stem = pathlib.Path(r.get("file", "doc")).stem[:20]
        for i, t in enumerate(r.get("tables", []), 1):
            label = f"{stem}_p{t['page']}_{i}"
            rows = list(t["rows"])
            if len(records) > 1:
                rows = [row + [pathlib.Path(r["file"]).name] for row in rows]
                rows[0][-1] = "source_file"
            sheets.append((label, rows))

    failed = [r for r in records if r.get("error")]
    if failed:
        rows = [["file", "type", "reason"]]
        rows += [[pathlib.Path(r["file"]).name, r.get("type", ""), r["error"]]
                 for r in failed]
        sheets.append(("Failed", rows))
    return sheets


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("output", help="path to the .xlsx to write")
    ap.add_argument("inputs", nargs="+", help="CSV files, or one JSON from pdf_extract")
    ap.add_argument("--names", help="comma-separated sheet names, in input order")
    ap.add_argument("--text-columns", help="0-based columns to force to text, e.g. 0,4")
    args = ap.parse_args()

    text_cols = set()
    if args.text_columns:
        text_cols = {int(x) for x in args.text_columns.split(",") if x.strip().isdigit()}

    paths = [pathlib.Path(p).expanduser() for p in args.inputs]
    for p in paths:
        if not p.exists():
            raise SystemExit(f"error: {p} does not exist")

    if len(paths) == 1 and paths[0].suffix.lower() == ".json":
        sheets = sheets_from_extract_json(json.loads(paths[0].read_text()))
        if not sheets:
            raise SystemExit("error: nothing tabular in that JSON -- no tables, "
                             "fields or failures to write")
    else:
        names = args.names.split(",") if args.names else [p.stem for p in paths]
        if len(names) != len(paths):
            raise SystemExit(f"error: {len(names)} names for {len(paths)} inputs")
        sheets = [(n, read_csv(p)) for n, p in zip(names, paths)]

    out = pathlib.Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    written = write_xlsx(out, sheets, text_cols)
    total = sum(len(rows) for _n, rows in sheets)
    print(f"{out}  --  {len(written)} sheet(s), {total:,} rows")
    for name, rows in zip(written, [r for _n, r in sheets]):
        print(f"   {name:32} {len(rows):>6} rows x {max((len(r) for r in rows), default=0)} cols")
    return 0


if __name__ == "__main__":
    sys.exit(main())
