#!/usr/bin/env python3
"""Build an ATS-clean .docx (and the .txt a parser sees) from a resume JSON file.

Stdlib only -- a .docx is a zip of XML, so nothing needs installing. That
matters because this skill runs on other people's machines.

    python3 build_resume_docx.py resume.json --out out/Priya_Sharma_Resume.docx

The document it emits is deliberately plain: one column, no tables, no text
boxes, no images, no header or footer, one standard font, literal bullet
characters. Every one of those is a thing that breaks parsers, and none of them
is what gets someone hired -- the words do.

Input JSON (every key optional except name, contact and experience):

{
  "name": "Priya Sharma",
  "headline": "Senior Data Engineer",
  "contact": {"email": "...", "phone": "+91 ...", "location": "Bengaluru, India",
              "links": ["linkedin.com/in/priyasharma", "github.com/priyasharma"]},
  "summary": "Two or three lines, no first person, no adjectives you cannot evidence.",
  "skills": [{"group": "Languages", "items": ["Python", "SQL"]},
             {"group": "Cloud", "items": ["AWS", "Terraform"]}],
  "experience": [{"title": "Senior Data Engineer", "company": "Acme",
                  "location": "Bengaluru, India", "start": "Jan 2021", "end": "Present",
                  "bullets": ["..."]}],
  "projects": [{"name": "...", "detail": "...", "bullets": ["..."]}],
  "education": [{"degree": "B.Tech, Computer Science", "institution": "NIT Trichy",
                 "location": "Trichy, India", "start": "2015", "end": "2019",
                 "detail": "CGPA 8.7/10"}],
  "certifications": ["AWS Certified Solutions Architect - Associate, 2024"],
  "extras": [{"heading": "Publications", "items": ["..."]}]
}
"""

import argparse
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BODY_PT = 21          # half-points -> 10.5pt
NAME_PT = 32          # 16pt
HEAD_PT = 24          # 12pt section headings
FONT = "Calibri"
PAGE = {"letter": (12240, 15840), "a4": (11906, 16838)}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def clean(s):
    """Strip characters that survive badly through text extraction."""
    if s is None:
        return ""
    s = str(s)
    repl = {"‘": "'", "’": "'", "“": '"', "”": '"',
            "–": "-", "—": "-", "ﬁ": "fi", "ﬂ": "fl",
            " ": " ", "•": "", "​": ""}
    for k, v in repl.items():
        s = s.replace(k, v)
    return re.sub(r"[ \t]+", " ", s).strip()


def run(text, bold=False, italic=False, size=BODY_PT, caps=False):
    rpr = ["<w:rFonts w:ascii=\"%s\" w:hAnsi=\"%s\" w:cs=\"%s\"/>" % (FONT, FONT, FONT)]
    if bold:
        rpr.append("<w:b/>")
    if italic:
        rpr.append("<w:i/>")
    if caps:
        rpr.append("<w:caps/>")
    rpr.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    return (f'<w:r><w:rPr>{"".join(rpr)}</w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r>')


def para(runs_xml, before=0, after=40, indent=None, hanging=None, border=False,
         keep_next=False):
    ppr = ["<w:spacing w:before=\"%d\" w:after=\"%d\" w:line=\"252\" "
           "w:lineRule=\"auto\"/>" % (before, after)]
    if indent is not None:
        h = f' w:hanging="{hanging}"' if hanging else ""
        ppr.append(f'<w:ind w:left="{indent}"{h}/>')
    if border:
        ppr.append('<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" '
                   'w:color="808080"/></w:pBdr>')
    if keep_next:
        ppr.append("<w:keepNext/>")
    return f'<w:p><w:pPr>{"".join(ppr)}</w:pPr>{runs_xml}</w:p>'


def heading(text):
    return para(run(text, bold=True, size=HEAD_PT, caps=True),
                before=200, after=60, border=True, keep_next=True)


def bullet(text):
    # A literal bullet plus a hanging indent, rather than Word list numbering:
    # numbering lives in a separate part that some extractors ignore, which
    # turns an achievement list into an undifferentiated wall of text.
    return para(run("•") + '<w:r><w:tab/></w:r>' + run(clean(text)),
                after=20, indent=288, hanging=288)


def joined(*parts, sep=" | "):
    return sep.join(clean(p) for p in parts if clean(p))


def date_range(start, end):
    s, e = clean(start), clean(end) or "Present"
    if not s:
        return ""
    return f"{s} - {e}"


def build_body(d, page="letter"):
    out = []
    out.append(para(run(clean(d["name"]), bold=True, size=NAME_PT), after=20))
    if d.get("headline"):
        out.append(para(run(clean(d["headline"]), size=BODY_PT + 1), after=20))

    c = d.get("contact", {}) or {}
    links = [clean(l) for l in (c.get("links") or []) if clean(l)]
    contact = joined(c.get("email"), c.get("phone"), c.get("location"), *links)
    if contact:
        out.append(para(run(contact), after=60))

    if d.get("summary"):
        out.append(heading("Summary"))
        out.append(para(run(clean(d["summary"]))))

    if d.get("skills"):
        out.append(heading("Skills"))
        for grp in d["skills"]:
            if isinstance(grp, str):
                out.append(para(run(clean(grp)), after=20))
                continue
            items = ", ".join(clean(i) for i in (grp.get("items") or []) if clean(i))
            if not items:
                continue
            label = clean(grp.get("group"))
            xml = (run(f"{label}: ", bold=True) + run(items)) if label else run(items)
            out.append(para(xml, after=20))

    if d.get("experience"):
        out.append(heading("Experience"))
        for job in d["experience"]:
            header = joined(job.get("title"), job.get("company"), job.get("location"),
                            date_range(job.get("start"), job.get("end")))
            out.append(para(run(header, bold=True), before=80, after=20, keep_next=True))
            for b in (job.get("bullets") or []):
                if clean(b):
                    out.append(bullet(b))

    if d.get("projects"):
        out.append(heading("Projects"))
        for pr in d["projects"]:
            if isinstance(pr, str):
                out.append(bullet(pr))
                continue
            header = joined(pr.get("name"), pr.get("detail"),
                            date_range(pr.get("start"), pr.get("end")))
            out.append(para(run(header, bold=True), before=80, after=20, keep_next=True))
            for b in (pr.get("bullets") or []):
                if clean(b):
                    out.append(bullet(b))

    if d.get("education"):
        out.append(heading("Education"))
        for ed in d["education"]:
            if isinstance(ed, str):
                out.append(para(run(clean(ed)), after=20))
                continue
            header = joined(ed.get("degree"), ed.get("institution"), ed.get("location"),
                            date_range(ed.get("start"), ed.get("end")) or clean(ed.get("year")))
            out.append(para(run(header, bold=True), before=60, after=20, keep_next=True))
            if clean(ed.get("detail")):
                out.append(para(run(clean(ed["detail"])), after=20))

    if d.get("certifications"):
        out.append(heading("Certifications"))
        for cert in d["certifications"]:
            out.append(bullet(cert))

    for extra in (d.get("extras") or []):
        title = clean(extra.get("heading"))
        if not title:
            continue
        out.append(heading(title))
        for item in (extra.get("items") or []):
            out.append(bullet(item))

    w, h = PAGE.get(page, PAGE["letter"])
    out.append(
        f'<w:sectPr><w:pgSz w:w="{w}" w:h="{h}"/>'
        '<w:pgMar w:top="720" w:right="900" w:bottom="720" w:left="900" '
        'w:header="0" w:footer="0" w:gutter="0"/>'
        '<w:cols w:space="720" w:num="1"/><w:docGrid w:linePitch="360"/></w:sectPr>'
    )
    return "".join(out)


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:eastAsia="{FONT}" w:cs="{FONT}"/>
<w:sz w:val="{BODY_PT}"/><w:szCs w:val="{BODY_PT}"/><w:lang w:val="en-US"/>
</w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="40" w:line="252" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>
<w:qFormat/></w:style>
</w:styles>"""


def core_props(name):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties '
            'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f'<dc:title>{esc(name)} - Resume</dc:title>'
            f'<dc:creator>{esc(name)}</dc:creator>'
            f'<cp:lastModifiedBy>{esc(name)}</cp:lastModifiedBy>'
            '</cp:coreProperties>')


def write_docx(data, out_path, page="letter"):
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{build_body(data, page)}</w:body></w:document>'
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("docProps/core.xml", core_props(data.get("name", "Resume")))
    return out_path


def default_name(data):
    parts = re.findall(r"[A-Za-z]+", data.get("name", "Resume"))
    return "_".join(parts[:3] + ["Resume"]) + ".docx" if parts else "Resume.docx"


def validate(data):
    problems = []
    if not clean(data.get("name")):
        problems.append("name is required")
    c = data.get("contact") or {}
    if not clean(c.get("email")):
        problems.append("contact.email is required -- a record with no way to reply is dead")
    if not clean(c.get("phone")):
        problems.append("contact.phone is missing; most ATS treat it as a required field")
    if not clean(c.get("location")):
        problems.append("contact.location is missing; recruiters filter on it")
    if not data.get("experience") and not data.get("projects"):
        problems.append("no experience and no projects -- nothing to parse as history")
    for i, job in enumerate(data.get("experience") or []):
        where = f"experience[{i}]"
        for field in ("title", "company", "start"):
            if not clean(job.get(field)):
                problems.append(f"{where}.{field} is missing")
        if not (job.get("bullets") or []):
            problems.append(f"{where} has no bullets")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_file")
    ap.add_argument("--out", help="output .docx path")
    ap.add_argument("--page", choices=sorted(PAGE), default="letter")
    ap.add_argument("--no-txt", action="store_true",
                    help="skip writing the plain-text twin")
    ap.add_argument("--force", action="store_true",
                    help="build even if required fields are missing")
    args = ap.parse_args()

    with open(args.json_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    problems = validate(data)
    if problems:
        sys.stderr.write("Incomplete resume data:\n" +
                         "".join(f"  - {p}\n" for p in problems))
        if not args.force:
            sys.stderr.write("\nAsk the candidate for these rather than inventing them, "
                             "or re-run with --force.\n")
            return 2

    out = args.out or default_name(data)
    if os.path.isdir(out):
        out = os.path.join(out, default_name(data))
    write_docx(data, out, args.page)
    print(f"wrote {out}")

    if not args.no_txt:
        # The .txt is generated by re-reading the .docx, so it is literally what
        # an extractor recovers -- not a hopeful rendering of the same data.
        from extract_resume_text import extract_docx
        txt_path = os.path.splitext(out)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as fh:
            fh.write(extract_docx(out)["text"].replace("\t", " ") + "\n")
        print(f"wrote {txt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
