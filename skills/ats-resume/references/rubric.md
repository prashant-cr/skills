# The rubric: what `ats_check.py` measures and why

Read this when a check fails and the fix is not obvious, or when a candidate asks why something
is on the list.

Two categories. **Blocking issues** are not point deductions — they are reasons the file does
not survive a parser at all, and no score is meaningful until they are gone. **Scored checks**
total 100 points; the pass mark is 90.

## Contents

- [Blocking issues](#blocking-issues)
- [Contact block (16 points)](#contact-block-16-points)
- [Sections (18 points)](#sections-18-points)
- [Employment entries (20 points)](#employment-entries-20-points)
- [Dates (10 points)](#dates-10-points)
- [Bullets (12 points)](#bullets-12-points)
- [Skills (10 points)](#skills-10-points)
- [File and hygiene (14 points)](#file-and-hygiene-14-points)
- [What this does not measure](#what-this-does-not-measure)

## Blocking issues

### `no_extractable_text` / `image_only_pdf`

Under 300 characters came out of the file. The resume is an image: a scan, or — far more often —
a Canva, Figma or Illustrator export where the text was converted to outlines. To a parser this
is a blank document.

Nothing can be fixed by editing. The candidate needs the editable source, or the content retyped.
Detect this first; it is the most expensive thing to miss because every other observation you
make about the file is irrelevant.

### `multi_column_layout`

Two or more newspaper-style columns. The parser reads the underlying text stream, which crosses
column boundaries in an order nobody intended — a skills sidebar ends up spliced through the job
history, and a job title can end up attached to the wrong employer.

Fix: one column. This is not negotiable and not stylistic; there is no reliable way to make two
columns parse.

### `contact_in_header_footer`

Email or phone lives in the page header or footer region. Several ATS — Taleo is the notorious
one — never read that region. The result is a candidate record with no way to contact the
candidate, which fails silently and completely.

Fix: move contact details into the body, at the top.

### `text_in_textboxes`

Text boxes are a separate story in the file format, not part of the main text flow. Parsers
routinely drop them entirely.

Fix: move the content into ordinary paragraphs.

### `table_based_layout`

More than 40% of paragraphs sit inside tables. Table cells get flattened, commonly row-first,
splicing unrelated lines together — a date column merges into a description column and neither
survives.

Fix: remove the table scaffolding. A table used purely to align dates against titles is the most
common offender, and the alignment it buys is worth nothing compared to what it costs.

## Contact block (16 points)

| Check | Points | Why |
| --- | --- | --- |
| Email in body text | 5 | The primary key of the candidate record. Without it there is nothing to reply to. |
| Phone, machine-readable | 4 | Most ATS treat it as required and some portals reject the application without it. |
| Location near the top | 3 | Recruiters filter on it constantly. "Remote" counts, if that is the truth. |
| Links written as full addresses | 4 | A hyperlink whose visible text reads "LinkedIn" loses the address the moment the file becomes text. Write `linkedin.com/in/name`. |

## Sections (18 points)

| Check | Points | Why |
| --- | --- | --- |
| Experience under a standard heading | 7 | Parsers map sections by name. An unrecognised heading means the jobs never reach the work-history field, so the candidate appears to have no experience. |
| Education under a standard heading | 5 | Same mechanism; degree filters are common. |
| Skills under a standard heading | 4 | This is the section keyword search leans on hardest. |
| No creative headings | 2 | "Where I've Made an Impact" is charming and unparseable. |

Headings that parse reliably: `Summary`, `Experience` / `Work Experience` / `Professional
Experience`, `Skills` / `Technical Skills`, `Education`, `Projects`, `Certifications`.

The cost of a plain heading is zero — nobody was ever hired for naming a section well — so this
is the cheapest set of points on the sheet.

## Employment entries (20 points)

| Check | Points | Why |
| --- | --- | --- |
| Every role carries a parseable date range | 10 | Tenure and recency drive both search ranking and the recruiter's first judgement. An undated role reads as a gap. |
| Every role names a title and an employer | 10 | These are separate database fields. A header collapsing them into one unpunctuated phrase populates one and blanks the other. |

The format that parses most reliably:

```
Senior Data Engineer | Razorpay | Bengaluru, India | Mar 2022 - Present
```

Title first, then employer, then location, then dates, separated by pipes — and applied
identically to every role. Inconsistency between entries is itself a failure: a parser that
infers "title comes first" from your first job will mis-assign the second one if you reverse it
there.

## Dates (10 points)

| Check | Points | Why |
| --- | --- | --- |
| Formats parsers resolve | 6 | `Mar 2022 - Present` and `03/2022 - 05/2024` resolve. `'19 - '22`, `2015-19`, `Since 2019` and `3 yrs at Infosys` do not. |
| Consistent format throughout | 4 | Mixing month-name and numeric styles halves the reliability of the inference. |

`Present` for a current role parses; so do `Current` and `Now`. Never leave the end date blank.

A note on gaps: ambiguity is a worse strategy than honesty here. Vague dates do not hide a gap
from a recruiter — they just stop the role from parsing, which turns a six-month gap into an
apparently missing job.

## Bullets (12 points)

| Check | Points | Why |
| --- | --- | --- |
| Achievements as bullets | 4 | Dense paragraphs bury the evidence and get skimmed past by humans, whatever the parser does. |
| Standard bullet character | 3 | Wingdings and decorative arrow glyphs extract as garbage characters or vanish. `•` is safe. |
| Bullets open with an action | 5 | "Responsible for", "Worked on", "Helped with" and "Duties included" describe a job description, not a person. The bullet reads as a list of what was assigned rather than what was accomplished. |

See `bullets.md` for how to rewrite these without inventing outcomes.

## Skills (10 points)

| Check | Points | Why |
| --- | --- | --- |
| Plain comma-separated skills | 6 | Full marks around a dozen concrete skills. Grouped labels — `Languages: Python, SQL` — read well and parse fine. |
| No graphical ratings | 2 | Dot and star proficiency meters carry no text; they extract as nothing, or as a run of identical symbols. They also assert a precision nobody can defend — what distinguishes 4/5 from 5/5 in Python? |
| Acronyms paired with expansions | 2 | Search is largely exact-string. Someone searching "Search Engine Optimization" misses a resume saying only "SEO". Write `Search Engine Optimization (SEO)` and one string matches both. |

List tools and technologies, not qualities. "Team player" and "hard-working" match nothing a
recruiter searches for and cost space that a real skill would use better.

## File and hygiene (14 points)

| Check | Points | Why |
| --- | --- | --- |
| Format ATS parse reliably | 4 | `.docx` is the safest. `.pdf` is usually fine *if* it has a real text layer — verify rather than assume. `.doc`, `.pages` and `.rtf` cause avoidable trouble. |
| File name identifies the candidate | 2 | `Priya_Sharma_Resume.docx`, not `resume_final_v3.docx`. Recruiters download hundreds of files into one folder. |
| No images or logos | 3 | They contribute nothing to a parser. A photo additionally invites bias screening in markets where photos are not customary, and some employers discard photo-bearing resumes for exactly that reason. |
| No irrelevant personal details | 3 | Date of birth, marital status, father's name, nationality, religion, gender, passport number. Conventional on Indian resumes; in most ATS-driven hiring they are noise at best and a legal problem for the employer at worst. See `market-conventions.md` before removing them — the candidate's target market decides. |
| No declaration block | 2 | "I hereby declare that the above information is true" is a legacy convention that consumes space and parses as stray text. A signature line has the same problem. |

## What this does not measure

Be straight with the candidate about the boundary. The scorer answers one question: will a
machine reading this file recover the candidate's history correctly? It does not measure:

- whether the writing is any good, or the achievements impressive
- whether the candidate is a fit for the role
- how a recruiter will react to a career gap, a short tenure, or a career change
- any particular vendor's behaviour — parsers differ, and the checks here are the intersection
  of what is known to break across the common ones

So a 95 means the resume will be read as intended. It does not mean it will get a call. Say that
plainly rather than letting a number carry more weight than it earns.
