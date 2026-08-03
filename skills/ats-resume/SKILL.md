---
name: ats-resume
license: MIT
description: Makes a resume survive applicant tracking systems, and proves it with a scorer that must read back at least 90 out of 100 before anything is handed over. Reads the resume the way a parser does rather than the way it looks, which is what catches the failures that actually sink applications - two-column layouts, table scaffolding, text boxes, and contact details sitting in the page header where several ATS discard them. Asks the candidate for the numbers it is missing instead of inventing achievements, reports keyword gaps as questions rather than pasting them in, and emits a clean .docx alongside the plain text a parser recovers. Use whenever the user mentions ATS, applicant tracking systems, resume screening, or resume keywords, asks to make a resume or CV ATS-friendly, wants a resume checked, scored, fixed, reformatted, or tailored to a job description, says their resume gets no callbacks or is auto-rejected, or asks whether a template or a PDF will pass automated screening.
---

# ATS resume

Makes a resume parse correctly, then says out loud what it could not verify.

## The one idea that organises everything below

**Almost every "the ATS rejected me" story is a parsing failure, not a scoring failure.**

The popular model — a machine reads your resume, computes a match percentage, and bins you
below 75% — is mostly folklore. What actually happens in Workday, Greenhouse, Lever, Taleo and
iCIMS is duller and more brutal: the file is parsed into database fields (name, email, employer,
title, start date, end date, school, skills), and a recruiter then *searches* that database.

So the damage is done silently, before anyone judges anything. A two-column layout interleaves
the sidebar into the job history. A table splices unrelated cells together. Contact details in
the page header get dropped by the parser, producing a candidate record nobody can reply to. The
resume was never rejected — it was never legible, so it never appeared in the search that would
have surfaced it.

This reorders the work. Formatting is not the cosmetic step you do at the end; it is the step
that decides whether the words are read at all. And keywords are worth much less than people
think, because a keyword in a document that failed to parse is in no index.

Two consequences worth holding onto:

- **A resume that scores 95% on "keyword match" and parses into an empty work history is worse
  than a plain one that parses.** Check parsing first, always.
- **Length is a human convention, not a machine constraint.** No ATS penalises a second page.
  The one-page rule comes from recruiters' attention, not from software — so argue it on those
  grounds or not at all.

## The rule that matters more than any formatting fix

**Never invent a number, a title, a date, or a technology.**

This is the characteristic failure of automated resume rewriting: a bullet that said "worked on
the billing module" comes back as "reduced billing errors by 35%, saving $200K annually". It
reads beautifully, it lifts every score, and it is a fabrication the candidate now has to defend
in an interview — or worse, does not discover until a reference check.

Two things follow, and both are non-negotiable because the cost falls on the candidate, not on
you:

- If the candidate has not given you a number, **write scope instead of results**. "Owned the
  billing module for 40,000 monthly invoices" is honest and specific; it needs no invention.
  `references/bullets.md` shows the patterns for writing strong bullets without fabricating.
- If a number would clearly strengthen a bullet, **ask for it**. Collect the questions and ask
  them in one block rather than one at a time.

The same holds for keywords. A skill the candidate cannot demonstrate does not go in the skills
list because a job posting mentioned it — it goes on the list of gaps you hand back to them.

## Workflow

### 1. Read what the parser sees, before you read the resume

```bash
python3 scripts/extract_resume_text.py <resume> --json
```

Do this first, and read the extracted text before opening the original. Judging a resume by how
it looks in a PDF viewer is precisely how a layout that interleaves into nonsense gets approved —
the visual document and the parsed document are two different things, and only one of them gets
a job.

The `flags` in the output name the hazards directly: `max_columns`, `table_count`,
`textbox_count`, `header_text`, `footer_text`, `image_count`, `hyperlink_count`.

If almost no text comes out, the resume is an image — usually a Canva or Illustrator export
with text converted to outlines, or a scan. No rewriting helps; the candidate needs the source
file or a retype. Say so plainly, because this is the single most expensive thing to miss.

Confirm that diagnosis rather than resting on an empty extraction, because *why* the file is
empty changes what you tell the candidate. On a PDF, `pdffonts file.pdf` listing no fonts is
conclusive: a page cannot draw a glyph without a font, so no fonts means no text, and the
"characters" are vector outlines. `strings file.pdf | grep -c ' Tj\| TJ'` returning zero says
the same thing from the other direction — those are the operators that draw text. A file that
does have fonts but still extracts nothing is more likely encrypted or damaged, which is a
different conversation and a recoverable one.

Give the candidate a check they can run themselves: open the PDF and press Ctrl+F / Cmd+F for
their own surname. No match means no ATS can read it either. That single test tends to land
harder than any score, because they can repeat it on the next version.

The `pdf-parsing` skill in this repository handles scanned documents if you need to recover
content from one.

### 2. Score the original, so the candidate can see the change

```bash
python3 scripts/ats_check.py <resume> --jd <job_description.txt>
```

The score is out of 100, and it exits non-zero below 90. Keep this baseline number — the
before-and-after is the most convincing thing you will show the candidate, and it stops the
rewrite from being a matter of taste.

`--jd` is optional and adds a keyword overlap section. Treat that list as a set of questions for
the candidate, never as a list to paste in. `references/keywords.md` covers how to use it
honestly and why stuffing backfires.

`references/rubric.md` explains every check, what it is protecting against, and how to fix each
failure.

### 3. Ask, in one block

You need things the file cannot tell you. Ask them together — six questions answered in one
reply beats twelve delivered one at a time:

- **Which country or market are they applying in?** Resume conventions differ enough to change
  the output substantially: a photo and a date of birth are normal in parts of Europe and
  routine on Indian resumes, and actively harmful for a US application. Ask rather than
  assuming, and see `references/market-conventions.md`.
- **Which role, and is there a specific posting?** Ask for the job description text. Tailoring
  to a real posting is the largest honest gain available, and without it you are optimising
  against a guess.
- **The specific numbers you are missing.** Not "do you have any metrics?" — that question gets
  "no" from people who have plenty. Ask per bullet: how many users, how large was the team, how
  long did the job take before and after, what was the budget, how many transactions.
- **Anything the file leaves ambiguous**: employment gaps, whether a role was a contract, a
  promotion inside one employer, current notice period or visa status if relevant to the market.
- **What they do not want changed.** People have reasons — a title that matches their reference,
  a project they are proud of.

If they have already supplied most of this, **state your assumptions and get on with it** rather
than interrogating them. If exactly one fact is missing and everything else is decidable, ask
only for that one.

### 4. Rewrite the content

Fix parsing hazards structurally rather than cosmetically — a table used for layout gets removed,
not restyled. Then work on the words: `references/bullets.md` for achievement bullets and the
summary, `references/keywords.md` for aligning vocabulary with the posting.

Preserve the candidate's voice and their facts. You are re-presenting their history, not
authoring a new one.

### 5. Build the document

Write the resume as JSON and build it. The builder emits a single-column .docx with no tables,
no text boxes, no images, no header or footer, one standard font and literal bullet characters —
every one of those is a parser hazard removed by construction.

```bash
python3 scripts/build_resume_docx.py resume.json --out out/Firstname_Lastname_Resume.docx
```

The JSON schema is documented at the top of the script. It refuses to build with a missing
email, phone, location, or role details unless you pass `--force`, because those gaps should
become questions to the candidate rather than blanks in a file.

It also writes a `.txt` twin, generated by reading back the `.docx` it just wrote — so it is
literally what an extractor recovers, not a hopeful rendering of the same data. Hand that to the
candidate too; seeing the parsed text is what makes the whole idea click.

Use `--page a4` outside the US and Canada.

### 6. Re-score, and iterate until it passes

```bash
python3 scripts/ats_check.py out/Firstname_Lastname_Resume.docx --jd job_description.txt
```

**Do not hand over a resume that scores below 90 or has any blocking issue.** Re-run after every
change. This is the whole point of having a scorer: it converts "looks ATS-friendly to me" into
a number that either clears the bar or does not.

When a check will not clear because information is genuinely missing — no phone number supplied,
no dates for an old role — say that explicitly instead of working around it. The honest sentence
is "this scores 86 and the four missing points are your phone number, which you have not given
me", not a quiet `--force`.

Treat a passing score as necessary, not sufficient. It measures whether a machine can read the
resume; it says nothing about whether the writing is any good. Read the result yourself.

### 7. Hand it back with the reasoning

Deliver the `.docx`, the `.txt`, and a short report:

```markdown
## ATS audit: [name]

**Parseability: [before]/100 -> [after]/100**

### What would have broken
- [issue] -> [what a parser did with it] -> [what changed]

### What I changed in the wording
- [bullet before] -> [bullet after], using the number you gave me for [X]

### What I could not verify, and needs you
- [bullet] still has no measurable outcome. If you know [specific number], it becomes much stronger.
- The posting asks for [skill]. I did not add it because nothing in your history evidences it -- if you have used it, tell me where and I will place it.

### If you need a PDF
Export from the .docx and re-run the check on the PDF -- some exporters lose the text layer.
```

The third section is the one candidates value most and the one most tools omit. It is also what
keeps this honest: the gaps get reported, not filled in.

## Handling the awkward cases

**"Just tell me if my resume is good."** Score it, report the parsing failures concretely, and
offer the rewrite. Do not rewrite unasked.

**A beautiful template they paid for.** Say what it costs them in parsing terms and let them
decide. Many people apply through both an ATS portal and direct email; keeping the designed
version for humans and a plain version for portals is a legitimate answer, not a compromise.

**"Add keywords so I get past the filter."** Explain what actually filters (see the top of this
file), then do the honest version: surface every term from the posting they can evidence, place
it where it belongs, and hand back the rest as gaps. Never white text, never a hidden keyword
block — it is visible in the extracted text, and it reads as fraud to the human who opens the
parsed profile.

**A career break or a gap.** Do not disguise it with vague date formats — ambiguous dates are a
parsing failure, so the trick costs more than the gap. Date it plainly.

## Reference files

- `references/rubric.md` — every check the scorer runs, why it exists, and how to fix a failure.
  Read when a check fails and the fix is not obvious.
- `references/bullets.md` — writing achievement bullets and summaries without inventing
  evidence, and the questions that pull real numbers out of people. Read before rewriting content.
- `references/keywords.md` — using a job description honestly, and why keyword stuffing loses.
  Read when a job description is supplied.
- `references/market-conventions.md` — what belongs on a resume in India, the US, the UK, the
  EU, Canada, Australia and the Gulf. Read once the candidate names their market.
