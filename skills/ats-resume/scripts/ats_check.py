#!/usr/bin/env python3
"""Score a resume on how reliably an applicant tracking system will parse it.

Stdlib only. Works on .docx, .pdf, .txt and .md.

    python3 ats_check.py resume.docx
    python3 ats_check.py resume.docx --json
    python3 ats_check.py resume.docx --jd job_description.txt

Exit code is 0 when the resume scores at least the threshold (default 90) with
no blocking issue, and 1 otherwise, so this can gate a rewrite instead of being
advisory.

What it does and does not measure: this scores *parseability* -- whether a
machine reading the file recovers the contact details, the employment history
with dates, the education and the skills. It deliberately does not pretend to
predict a recruiter's opinion, and it does not score writing quality. A resume
can pass every check here and still be a weak application; it just will not be
weak because a parser mangled it.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_resume_text import extract  # noqa: E402

DEFAULT_THRESHOLD = 90

MONTH = (r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
         r"(?:uary|ruary|ch|il|e|y|ust|tember|ober|ember)?\.?")
NOW = r"(?:present|current(?:ly)?|now|to\s*date|till\s*date|ongoing)"
DASH = r"(?:-{1,2}|–|—|to|until|through)"
YEAR = r"(?:19|20)\d{2}"
DATE_ONE = (rf"(?:{MONTH}\s*[,.]?\s*{YEAR}"
            rf"|\d{{1,2}}[/.-]{YEAR}"
            rf"|{YEAR}[/.-]\d{{1,2}}"
            rf"|{YEAR})")
DATE_RANGE = re.compile(rf"\b{DATE_ONE}\s*{DASH}\s*(?:{DATE_ONE}|{NOW})\b", re.I)
BAD_DATE = re.compile(
    rf"(?:'\d{{2}}\s*{DASH}|\b{YEAR}\s*{DASH}\s*\d{{2}}\b(?!\d)"
    rf"|\bsince\s+{YEAR}\b|\b\d+\+?\s*(?:yrs?|years?)\s+(?:at|with|in)\b)",
    re.I)

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")
# Deliberately permissive: international formats vary wildly and a false
# "missing phone" is worse than a false pass.
PHONE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
URL = re.compile(r"(?:https?://|www\.)?(?:linkedin\.com|github\.com|gitlab\.com|"
                 r"behance\.net|dribbble\.com|medium\.com|kaggle\.com|[\w-]+\.[a-z]{2,})"
                 r"/[\w./%+-]+", re.I)

SECTIONS = {
    "experience": [r"work\s+experience", r"professional\s+experience", r"experience",
                   r"employment(?:\s+history)?", r"career\s+history", r"work\s+history"],
    "education": [r"education", r"academic\s+(?:background|qualifications?)",
                  r"qualifications?"],
    "skills": [r"(?:technical\s+|core\s+|key\s+)?skills", r"technical\s+competenc(?:y|ies)",
               r"areas?\s+of\s+expertise", r"technologies", r"tech\s+stack"],
    "summary": [r"(?:professional\s+|career\s+|executive\s+)?summary", r"profile",
                r"objective", r"about(?:\s+me)?"],
    "projects": [r"projects?", r"selected\s+projects?", r"personal\s+projects?"],
    "certifications": [r"certifications?", r"licen[cs]es?(?:\s*&?\s*certifications?)?",
                       r"courses?(?:\s*&?\s*certifications?)?"],
}
# Headings a human likes and a parser cannot classify.
CREATIVE_HEADINGS = re.compile(
    r"^(?:where\s+i|what\s+i|my\s+(?:journey|story|impact|toolkit|arsenal)|"
    r"things\s+i|the\s+work|career\s+so\s+far|hustle|adventures|"
    r"bragging\s+rights|superpowers?|weapons?\s+of\s+choice)", re.I)

# Personal details that are conventional in some markets but are noise or a
# discrimination-law problem in most ATS-driven hiring, and never help parsing.
PERSONAL_NOISE = re.compile(
    r"\b(?:date\s+of\s+birth|d\.?o\.?b\.?|marital\s+status|father'?s?\s+name|"
    r"mother'?s?\s+name|nationality|religion|caste|gender|sex|blood\s+group|"
    r"passport\s+(?:no|number)|aadha?ar|languages\s+known\s*:\s*$)", re.I)
DECLARATION = re.compile(r"^\s*declaration\b|i\s+hereby\s+declare", re.I)

WEAK_OPENERS = re.compile(
    r"^(?:responsible\s+for|worked\s+on|helped\s+(?:with|to)|assisted\s+(?:with|in)|"
    r"tasked\s+with|duties\s+included|involved\s+in|part\s+of\s+(?:a\s+)?team)", re.I)
BULLET_CHARS = "•●○▪■‣⁃-*·∙➢➜➔"
DECORATIVE_BULLETS = re.compile(r"^\s*[➢➜➔❖✦★♦⮚☞]")
SYMBOL_FONTS = {"wingdings", "wingdings 2", "wingdings 3", "webdings", "symbol",
                "zapf dingbats", "zapfdingbats"}
RATING_GRAPHICS = re.compile(r"(?:[⬤●○■□★☆]\s*){3,}")

STOPWORDS = set("""a an the and or but for with without to of in on at by from as is are was were be
been being this that these those it its we our you your they their he she his her i me my will would
can could should shall may might must have has had do does did not no if then than so such very more
most other others new using use used across within into over under about per etc via each any all both
who whom which what when where why how""".split())

# Words every job posting contains, which therefore tell you nothing about the
# posting. Without this list the "top terms" are "experience", "strong" and
# "requirements" -- true, useless, and crowding out the terms that matter.
JD_BOILERPLATE = set("""experience experienced required require requires requirement requirements
strong excellent proven solid essential preferred plus nice must should ideal ideally looking
seeking join joining role roles position positions job jobs opportunity candidate candidates
applicant team teams company companies work working works ability able skills skill knowledge
understanding familiarity familiar background year years month months senior junior lead mid level
responsibilities responsible duties tasks day days daily including include includes well good
great high highly deep hands hand plus bonus benefits salary apply application applications
looking want wants need needs help helping ensure ensuring drive driving support supporting
partner partnering collaborate collaborating stakeholders stakeholder business customer customers
environment culture fast paced growth grow growing world class best practices practice
qualifications degree bachelor master phd equivalent field related relevant minimum least
plus we you your our us their them who what""".split())


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def is_heading(line):
    """Headings are short, unpunctuated, and set apart. Bullets never are.

    The subtle case this has to get right is a labelled content line such as
    "Languages: Python, SQL, Scala" -- short and title-cased like a heading, but
    it carries content. Treating it as a heading orphans the skills list into a
    section nothing recognises, so a label followed by content disqualifies.
    """
    t = norm(line)
    if not t or len(t) > 60:
        return False
    if t[0] in BULLET_CHARS and t[0] != "-":
        return False
    if t.endswith((".", ",", ";", ":")):
        t = t.rstrip(".,;:")
    if re.search(r":\s*\S", t) or "," in t or "|" in t or "@" in t:
        return False
    if re.search(rf"\d{{4}}|{MONTH}\s", t, re.I):
        return False
    if len(t.split()) > 6:
        return False
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    titleish = all(w[0].isupper() for w in t.split() if w and w[0].isalpha())
    return upper_ratio > 0.8 or titleish


def classify_heading(line):
    t = norm(line).rstrip(".,;:").lower()
    t = re.sub(r"^[^\w]+|[^\w]+$", "", t)
    for key, pats in SECTIONS.items():
        for p in pats:
            if re.fullmatch(rf"(?:{p})", t, re.I):
                return key
    return None


def split_sections(lines):
    """Return {section_key: [lines]} plus the list of heading lines seen."""
    sections, headings = {}, []
    current = "_preamble"
    sections[current] = []
    seen_content = 0
    for line in lines:
        if not norm(line):
            continue
        seen_content += 1
        # The name and the headline sit at the top and look exactly like
        # headings; they are the contact block, not a section boundary.
        if seen_content <= 2 and not classify_heading(line):
            sections[current].append(line)
            continue
        if is_heading(line):
            headings.append(line)
            key = classify_heading(line)
            if key:
                current = key
                sections.setdefault(current, [])
                continue
            if len(norm(line)) <= 45:
                current = "_other:" + norm(line).lower()
                sections.setdefault(current, [])
                continue
        sections.setdefault(current, []).append(line)
    return sections, headings


def jd_keywords(text, top=30):
    """The terms a recruiter would actually type into a search box.

    Three things make this useful rather than noise. Candidate terms are built
    only within punctuation-delimited segments, so a phrase can never straddle
    a sentence boundary ("SQL required. Experience" is not a skill). Job-posting
    boilerplate is dropped, because "strong", "required" and "responsibilities"
    appear in every posting and discriminate nothing. And a term capitalised
    mid-sentence in the original is boosted, since that is what technology and
    product names look like -- Kafka, Terraform, Snowflake -- and those are
    exactly the strings recruiters search on.
    """
    segments = re.split(r"[.;:,\n()\[\]/|•]+", text)
    counts, proper = {}, set()
    for seg in segments:
        words = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]*", seg)
        for i, w in enumerate(words):
            # Capitalised but not sentence-initial: a name, not grammar.
            if i > 0 and (w[0].isupper() or (len(w) > 1 and w[1:].lower() != w[1:])):
                proper.add(w.lower())
        low_words = [w.lower() for w in words]
        for n in (1, 2):
            for i in range(len(low_words) - n + 1):
                gram = low_words[i:i + n]
                if any(g in STOPWORDS or g in JD_BOILERPLATE for g in gram):
                    continue
                if any(len(g) < 2 or g.isdigit() for g in gram):
                    continue
                ph = " ".join(gram)
                counts[ph] = counts.get(ph, 0) + 1

    def rank(item):
        ph, n = item
        bonus = 2 if any(w in proper for w in ph.split()) else 0
        # Shorter terms win ties: "kafka" is searched, "kafka pipelines" is not.
        return (-(n + bonus), len(ph.split()), len(ph))

    ranked = sorted(counts.items(), key=rank)
    out, covered = [], set()
    for ph, n in ranked:
        # Drop a two-word term whose halves are both already listed; it adds no
        # new search string and crowds out a real one.
        parts = ph.split()
        if len(parts) == 2 and all(p in covered for p in parts):
            continue
        out.append((ph, n))
        covered.update(parts)
        if len(out) >= top:
            break
    return out


def contains_term(haystack, term):
    """Word-boundary match, so 'aws' does not match inside 'laws'."""
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", haystack) is not None


class Report:
    def __init__(self):
        self.checks = []
        self.blockers = []

    def add(self, name, earned, possible, detail=""):
        self.checks.append({"check": name, "earned": round(earned, 2),
                            "possible": possible, "detail": detail})

    def block(self, name, detail):
        self.blockers.append({"issue": name, "detail": detail})

    @property
    def score(self):
        possible = sum(c["possible"] for c in self.checks) or 1
        return round(100.0 * sum(c["earned"] for c in self.checks) / possible, 1)


def audit(path, jd_path=None, threshold=DEFAULT_THRESHOLD):
    data = extract(path)
    text = data["text"]
    flags = data["flags"]
    lines = [l for l in (p["text"] for p in data["paragraphs"])]
    nonempty = [norm(l) for l in lines if norm(l)]
    body = "\n".join(nonempty)
    low = body.lower()
    r = Report()

    # ---------- blocking issues: these are not point deductions, they are
    # reasons the file will not survive a parser at all ----------
    if len(body.strip()) < 300:
        r.block("no_extractable_text",
                f"Only {len(body.strip())} characters came out. The resume is probably an "
                "image, or text converted to outlines (common with Canva/Illustrator "
                "exports). A parser sees a blank document.")
    if flags.get("likely_image_only"):
        r.block("image_only_pdf", "No usable text layer in this PDF.")
    if flags.get("max_columns", 1) > 1:
        r.block("multi_column_layout",
                f"{flags['max_columns']} newspaper-style columns. Text is read in an order "
                "no reader intended, interleaving the sidebar into the job history.")
    header_footer = " ".join(flags.get("header_text", []) + flags.get("footer_text", []))
    if EMAIL.search(header_footer) or PHONE.search(header_footer):
        r.block("contact_in_header_footer",
                "Email or phone sits in the page header/footer. Several ATS (Taleo among "
                "them) discard that region entirely, producing a candidate record with no "
                "way to contact the candidate.")
    if flags.get("textbox_count", 0) and any(
            EMAIL.search(t) or len(t) > 40 for t in flags.get("textbox_text", [])):
        r.block("text_in_textboxes",
                f"{flags['textbox_count']} text box(es) carry real content. Text boxes are a "
                "separate story in the file and are routinely dropped.")
    para_in_tables = flags.get("paragraphs_in_tables", 0)
    total_paras = max(1, len([p for p in data["paragraphs"] if norm(p["text"])]))
    if para_in_tables / total_paras > 0.4:
        r.block("table_based_layout",
                f"{para_in_tables} of {total_paras} paragraphs are inside tables. Table cells "
                "are commonly flattened row-first, splicing unrelated lines together.")

    # ---------- contact block (16) ----------
    head = "\n".join(nonempty[:12])
    emails = EMAIL.findall(body)
    r.add("Email address present in the body text", 5 if emails else 0, 5,
          emails[0] if emails else "No email found outside the header/footer.")
    phones = [p for p in PHONE.findall(head) if len(re.sub(r"\D", "", p)) >= 8]
    if not phones:
        phones = [p for p in PHONE.findall(body) if len(re.sub(r"\D", "", p)) >= 8]
    r.add("Phone number present and machine-readable", 4 if phones else 0, 4,
          norm(phones[0]) if phones else "No phone number found.")
    has_loc = bool(re.search(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*(?:[A-Z]{2}\b|[A-Z][a-z]+)", head)) \
        or bool(re.search(r"\b(?:remote|bengaluru|bangalore|mumbai|delhi|hyderabad|pune|chennai|"
                          r"gurgaon|gurugram|noida|kolkata|london|singapore|dubai|new york|"
                          r"san francisco|berlin|toronto)\b", head, re.I))
    r.add("Location stated near the top", 3 if has_loc else 0, 3,
          "" if has_loc else "No city/region in the contact block; many ATS filter on location.")
    urls = URL.findall(head) or URL.findall(body)
    bare_link_word = re.search(r"\b(?:linkedin|github|portfolio)\b(?!\s*[:.]?\s*(?:https?|www|\w+\.))",
                               head, re.I) and not urls
    r.add("Profile links written out as full addresses", 4 if urls else (1 if not bare_link_word else 0), 4,
          urls[0] if urls else "A link labelled only 'LinkedIn' loses its address when the "
                               "file is converted to text; write the address itself.")

    # ---------- sections (18) ----------
    sections, headings = split_sections(lines)
    found = {k: k in sections and any(norm(l) for l in sections[k]) for k in SECTIONS}
    r.add("Work experience section under a standard heading", 7 if found["experience"] else 0, 7,
          "" if found["experience"] else
          "No heading a parser recognises as employment history. It maps sections by name; "
          "an unrecognised heading means the jobs never reach the work-history field.")
    r.add("Education section under a standard heading", 5 if found["education"] else 0, 5,
          "" if found["education"] else "No recognisable education heading.")
    r.add("Skills section under a standard heading", 4 if found["skills"] else 0, 4,
          "" if found["skills"] else "No recognisable skills heading; keyword search relies on it.")
    creative = [norm(h) for h in headings if CREATIVE_HEADINGS.match(norm(h))]
    r.add("No unparseable creative section headings", 0 if creative else 2, 2,
          "; ".join(creative) if creative else "")

    # ---------- employment entries (20) ----------
    exp_lines = [norm(l) for l in sections.get("experience", []) if norm(l)]
    anchors = [l for l in exp_lines if DATE_RANGE.search(l)]
    # A dated line that is not a bullet is an entry header.
    entry_lines = [l for l in anchors if not (l[0] in BULLET_CHARS and l[0] != "-")]
    n_entries = len(entry_lines)
    if not exp_lines:
        r.add("Every role carries a parseable date range", 0, 10,
              "No experience section content to check.")
        r.add("Every role names a title and an employer", 0, 10,
              "No experience section content to check.")
    else:
        # Count role headers as lines that look like a job header: dated, or
        # immediately above/below a dated line and containing a separator.
        idx = {l: i for i, l in enumerate(exp_lines)}
        undated = []
        for i, l in enumerate(exp_lines):
            if l[0] in BULLET_CHARS and l[0] != "-":
                continue
            if DATE_RANGE.search(l):
                continue
            neighbours = exp_lines[max(0, i - 1):i + 2]
            if any(DATE_RANGE.search(n) for n in neighbours if n != l):
                continue
            if re.search(r"\b(?:at|@|\||–|,|-)\s*\w", l) and len(l) < 90 and len(l.split()) <= 12:
                undated.append(l)
        dated_ratio = n_entries / max(1, n_entries + len(undated))
        r.add("Every role carries a parseable date range", 10 * dated_ratio, 10,
              f"{n_entries} dated role header(s)." +
              (f" Undated role-looking line(s): {'; '.join(undated[:3])}" if undated else ""))

        with_org = 0
        for l in entry_lines:
            stripped = DATE_RANGE.sub("", l).strip(" |,–-\t")
            i = idx.get(l, 0)
            neighbour = ""
            for j in (i - 1, i + 1):
                if 0 <= j < len(exp_lines):
                    c = exp_lines[j]
                    if c and (c[0] not in BULLET_CHARS or c[0] == "-") and len(c) < 90 \
                            and not DATE_RANGE.search(c):
                        neighbour = c
                        break
            combined = f"{stripped} {neighbour}".strip()
            # Needs two distinct pieces of information: a role and an employer.
            if re.search(r"[|–,]|\bat\b|•", combined) and len(combined.split()) >= 3:
                with_org += 1
            elif len(stripped.split()) >= 4:
                with_org += 0.5
        r.add("Every role names a title and an employer", 10 * (with_org / n_entries) if n_entries else 0,
              10, f"{with_org:g}/{n_entries} role header(s) expose both a title and an employer.")

    # ---------- dates (10) ----------
    all_ranges = DATE_RANGE.findall(body)
    bad = BAD_DATE.findall(body)
    if not all_ranges:
        # Report the ambiguous forms even here: "no parseable dates" is usually
        # caused by dates that exist but are written as "'19 - '22", and saying
        # so is far more useful than reporting their absence.
        r.add("Dates written in a format parsers resolve", 0, 6,
              "No date range a parser can resolve." +
              (f" Ambiguous forms present: {sorted(set(x.strip() for x in bad))[:4]}"
               if bad else " No dates found at all."))
        r.add("Date format is consistent throughout", 0, 4, "")
    else:
        r.add("Dates written in a format parsers resolve",
              6 if not bad else max(0, 6 - 2 * len(set(bad))), 6,
              "" if not bad else f"Ambiguous forms: {sorted(set(x.strip() for x in bad))[:4]}")
        # consistency: month-year vs bare-year mixing
        month_year = len(re.findall(rf"{MONTH}\s*[,.]?\s*{YEAR}", body, re.I))
        slash = len(re.findall(rf"\d{{1,2}}[/.-]{YEAR}", body))
        styles = sum(1 for n in (month_year, slash) if n)
        r.add("Date format is consistent throughout", 4 if styles <= 1 else 2, 4,
              "" if styles <= 1 else "Month-name and numeric date styles are mixed.")

    # ---------- bullets (12) ----------
    bullets = [l for l in nonempty if l and l[0] in BULLET_CHARS and l[0] != "-"] or \
              [l for l in nonempty if re.match(r"^[-*]\s+\S", l)]
    if not bullets:
        r.add("Achievements written as bullet points", 0, 4,
              "No bullet points found. Dense paragraphs bury the evidence and are skimmed past.")
        r.add("Bullets use a standard bullet character", 0, 3, "")
        r.add("Bullets open with an action, not 'responsible for'", 0, 5, "")
    else:
        r.add("Achievements written as bullet points", 4, 4, f"{len(bullets)} bullets.")
        decorative = [b for b in bullets if DECORATIVE_BULLETS.match(b)]
        symbol_font_used = {f.lower() for f in flags.get("fonts", [])} & SYMBOL_FONTS
        ok_bullets = not decorative and not symbol_font_used
        r.add("Bullets use a standard bullet character", 3 if ok_bullets else 0, 3,
              "" if ok_bullets else
              f"Decorative or symbol-font bullets ({sorted(symbol_font_used) or 'arrow/star glyphs'}) "
              "extract as garbage characters or vanish.")
        stripped = [b.lstrip(BULLET_CHARS + " \t") for b in bullets]
        weak = [b for b in stripped if WEAK_OPENERS.match(b)]
        weak_ratio = len(weak) / len(stripped)
        r.add("Bullets open with an action, not 'responsible for'",
              round(5 * (1 - min(1.0, weak_ratio * 2)), 2), 5,
              f"{len(weak)}/{len(stripped)} start with a passive opener." if weak else "")

    # ---------- skills (10) ----------
    skill_lines = [norm(l) for l in sections.get("skills", []) if norm(l)]
    skill_blob = " ".join(skill_lines)
    n_skills = len([s for s in re.split(r"[,;|•\n]", skill_blob) if len(s.strip()) > 1])
    r.add("Skills listed as plain, comma-separated text",
          min(6, n_skills / 2.0) if skill_lines else 0, 6,
          f"{n_skills} skill tokens." if skill_lines else "No skills section content.")
    # Scan the whole document, not just the skills section: a proficiency meter
    # usually sits under a heading like "My Toolkit" that never parses as
    # skills, so a section-scoped check would miss exactly the resumes that
    # have the problem.
    graphic = RATING_GRAPHICS.search(body)
    r.add("No graphical skill ratings", 0 if graphic else 2, 2,
          "Dot/star proficiency meters carry no text and vanish on extraction."
          if graphic else "")
    acro = re.findall(r"\b[A-Z]{2,6}\b", skill_blob)
    paired = re.findall(r"\w+\s*\([A-Z]{2,6}\)|\b[A-Z]{2,6}\s*\([\w\s]+\)", skill_blob)
    r.add("Acronyms paired with their spelled-out form", 2 if (paired or not acro) else 1, 2,
          "" if paired or not acro else
          "Recruiters search either the acronym or the full phrase; write 'Search Engine "
          "Optimization (SEO)' so one string matches both.")

    # ---------- file & hygiene (14) ----------
    ext = os.path.splitext(path)[1].lower()
    r.add("Saved in a format ATS parse reliably", 4 if ext == ".docx" else (3 if ext == ".pdf" else 1), 4,
          "" if ext in (".docx", ".pdf") else f"{ext} is not a format most ATS accept.")
    fname = os.path.basename(path)
    good_name = bool(re.match(r"^[A-Za-z]+[ _-][A-Za-z]+.*(?:resume|cv)", fname, re.I)) or \
        bool(re.search(r"(?:resume|cv)", fname, re.I) and re.match(r"^[A-Za-z]{2,}[ _-]", fname))
    r.add("File name identifies the candidate", 2 if good_name else 0, 2,
          "" if good_name else f"'{fname}' -- use Firstname_Lastname_Resume.docx; recruiters "
                               "download hundreds of files into one folder.")
    r.add("No images or logos in the document", 3 if not flags.get("image_count") else 0, 3,
          "" if not flags.get("image_count") else
          f"{flags['image_count']} image(s). A photo also invites bias screening in markets "
          "where it is not customary.")
    noise = sorted({norm(m.group(0)) for m in PERSONAL_NOISE.finditer(body)})
    r.add("No irrelevant personal details", 3 if not noise else max(0, 3 - len(noise)), 3,
          "" if not noise else f"Found: {noise[:5]}")
    decl = bool(DECLARATION.search(body))
    r.add("No signature/declaration block", 2 if not decl else 0, 2,
          "" if not decl else "The 'I hereby declare' block is a legacy convention that "
                              "consumes space and parses as stray text.")

    # ---------- keyword alignment against the JD (bonus, reported separately) ----------
    keyword_report = None
    if jd_path:
        with open(jd_path, "r", encoding="utf-8", errors="replace") as fh:
            jd = fh.read()
        kws = jd_keywords(jd)
        present = [(k, n) for k, n in kws if contains_term(low, k)]
        missing = [(k, n) for k, n in kws if not contains_term(low, k)]
        keyword_report = {
            "match_rate": round(100.0 * len(present) / max(1, len(kws)), 1),
            "matched": [k for k, _ in present][:25],
            "missing": [k for k, _ in missing][:25],
        }

    passed = r.score >= threshold and not r.blockers
    return {
        "file": path,
        "score": r.score,
        "threshold": threshold,
        "passed": passed,
        "blockers": r.blockers,
        "checks": r.checks,
        "keyword_report": keyword_report,
        "extraction": {k: v for k, v in flags.items() if k != "textbox_text"},
        "extracted_chars": len(body),
    }


def render(res):
    out = []
    verdict = "PASS" if res["passed"] else "FAIL"
    out.append(f"ATS parseability: {res['score']}/100  (threshold {res['threshold']}) -> {verdict}")
    out.append(f"file: {res['file']}   extracted {res['extracted_chars']} chars")
    if res["blockers"]:
        out.append("\nBLOCKING -- fix these before anything else:")
        for b in res["blockers"]:
            out.append(f"  [X] {b['issue']}: {b['detail']}")
    out.append("\nChecks:")
    for c in res["checks"]:
        mark = "ok  " if c["earned"] >= c["possible"] else ("part" if c["earned"] > 0 else "MISS")
        out.append(f"  [{mark}] {c['earned']:>5}/{c['possible']:<3} {c['check']}")
        if c["detail"] and c["earned"] < c["possible"]:
            out.append(f"          -> {c['detail']}")
    kr = res.get("keyword_report")
    if kr:
        out.append(f"\nJob-description overlap: {kr['match_rate']}% of the terms the posting "
                   f"repeats appear in the resume.")
        out.append(f"  present: {', '.join(kr['matched'][:12])}")
        out.append(f"  absent : {', '.join(kr['missing'][:12])}")
        out.append("  Absent terms are a question for the candidate, not a list to paste in. "
                   "Add only what they can defend in an interview.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("resume")
    ap.add_argument("--jd", help="job description file, for keyword overlap")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(args.resume):
        raise SystemExit(f"No such file: {args.resume}")
    res = audit(args.resume, args.jd, args.threshold)
    if args.json:
        json.dump(res, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        print(render(res))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
