---
name: clinical-note-writer
license: MIT
description: Turns messy consultation, ward-round or operative notes into a finished clinical document — discharge summary, referral letter, operative note or death summary — and reports every gap rather than filling it with plausible clinical detail, because an invented observation in a medical record is a fabricated legal document that the next doctor will read as fact. Reconciles what actually changed on the medication list, writes the follow-up plan and the return-if red flags that most summaries omit, and strips patient identifiers before anything is processed. Knows Indian conventions — NABH requirements, what PMJAY and TPA claims need, OD/BD/TDS notation. Use whenever the user mentions a discharge summary, referral or transfer letter, operative note, death summary, case sheet, handover or sick note, asks to write up, tidy or format clinical notes, pastes ward notes or a case, or says they have documentation or paperwork to finish.
---

# Clinical note writer

Takes what the clinician actually recorded and produces the document the next
reader needs — with **every gap named rather than filled**.

The output is a draft for a qualified clinician to check and sign. It is not a
clinical decision, and it must never contain a finding, value or event that was
not in the source.

## The one rule that matters

**Never write a clinical fact that was not in the input.**

This is not a style preference. A discharge summary is a legal document and a
handover to the next clinician, who has no way to tell your prose from the
author's. "Vitals stable at discharge" written where no vitals were recorded is
a fabricated observation that will be read, trusted, and acted on. Add up a
few of those and the record describes a patient who does not exist.

The failure is seductive because the model is *good* at clinical prose. Filling
"Systemic examination: CVS - S1S2 normal, RS - bilateral air entry equal" from
pattern rather than from source produces a paragraph that reads perfectly and
is entirely invented. Watch for that specific reflex.

So the deliverable has two halves, and **the second half is the valuable one**:

1. The document, containing only what was recorded.
2. **The gap report** — what is missing, why it matters, and who must supply it.

A document that looks complete is more dangerous than one with visible blanks.
Blanks get filled by the person who was there. Smooth prose gets signed.

## De-identify before anything else

Run this first, before drafting, and tell the user what was found:

```bash
python3 scripts/deidentify.py --file notes.txt
```

It flags Indian identifiers specifically — Aadhaar, UHID/MRN patterns, 10-digit
mobiles, PIN codes, email, names following Mr/Mrs/Dr titles, and full dates of
birth.

Then keep them out of your working text. Refer to the patient by **age and sex**
("a 62-year-old man"), never by name, in everything you generate.

Two reasons this matters beyond privacy law. Identifiers in a shared context can
be copied into the wrong record, which is how a note ends up filed under the
wrong patient. And under India's **DPDP Act 2023** health data is personal data
with a consent regime attached — the treating institution is the data fiduciary,
and a clinician pasting a full record into an external tool may be acting
outside what the patient consented to.

The clinician re-inserts identifiers into their own hospital system at the end.
Say so, so they do not forget.

## Establish the document and its reader

Ask, or infer from the input, and state which you did:

1. **Which document?** Discharge summary, referral letter, transfer note,
   operative note, death summary, sick/fitness certificate, insurance summary.
2. **Who reads it, and what must they do next?** This is the question that
   changes the writing most and is almost never asked. A referral letter is read
   by a specialist deciding *how urgently to see this patient* — so the reason
   for referral and the urgency go at the top, not the history. A discharge
   summary is read by a GP resuming care, and by the patient at home.
3. **Language.** Patient-facing sections may need a language other than English,
   and a plain-language version of the same content is not a translation job —
   it is a rewrite at a different reading level.

`references/document-types.md` has the structure and purpose of each type. Read
it for the one you are writing rather than all of them.

## Workflow

### 1. Extract, do not compose

Go through the source and pull out only what is stated: presenting complaint,
history, examination findings, investigations with values and dates, procedures,
course, medications, plan. Keep the clinician's own numbers exactly — do not
round, convert units, or tidy a value into a normal range.

Where the source is ambiguous ("BP low on admission"), carry the ambiguity
through rather than resolving it into a number. Then list it as a gap.

### 2. Reconcile the medications, showing what changed

The medication section is the most-used part of a discharge summary and the most
common source of post-discharge harm. A list of what the patient leaves on is
half the job. The reader needs to know **what changed and why**:

| | |
| --- | --- |
| **Continued** | Was on it, still on it |
| **New** | Started this admission — and the indication |
| **Changed** | Dose or frequency altered — and from what |
| **Stopped** | Discontinued — and why, so nobody restarts it |
| **Time-limited** | Stop date for the antibiotic, the steroid taper, the anticoagulant |

The "stopped, and why" row is the one that prevents the GP helpfully restarting a
drug that caused the admission. The "time-limited" row is what prevents a
seven-day antibiotic becoming a repeat prescription.

If the source does not say why something was stopped or how long the course
runs, that is a gap, not something to infer.

### 3. Write the follow-up and the safety net

Most summaries end at "review in OPD after 1 week", which tells the patient and
the GP almost nothing. A usable plan states:

- **Who** — which department or named clinician
- **When** — a date or interval, and what to do if the appointment slips
- **What for** — the specific question the review answers, and which results are
  still pending and need chasing
- **What must be checked** — bloods before the next dose, INR, renal function
  after starting an ACE inhibitor

Then the part most often missing entirely: **safety netting — the red flags that
mean return now, not at the appointment.** Specific to this patient's condition,
written so a frightened person at home at 2am can act on them.

If the source does not specify these, they go in the gap report at the top, as
things the clinician must add. `references/discharge-essentials.md` covers all
three sections and why each is the one that gets omitted.

### 4. Check completeness against the document type

```bash
python3 scripts/note_completeness.py --type discharge --file draft.md
```

Reports required fields absent from the draft, graded by consequence. Use it as
a backstop, not a substitute for reading — it checks presence, not truth.

### 5. Deliver the gaps first

Lead with what is missing. The clinician is going to sign this, and the fastest
version of their job is a list of what to fill in — not a hunt through prose for
what you quietly left out.

Grade each gap by consequence:

| Grade | Meaning |
| --- | --- |
| **Blocks sign-off** | Cannot go out — no discharge diagnosis, no discharge medication list, no follow-up |
| **Clinically important** | Should be added — indication for a new drug, pending results, allergy status |
| **Completeness** | Worth adding — occupation, immunisation status |

## Report structure

```markdown
## Gaps to fill before signing
**Blocks sign-off**
- [what is missing, and who has it]
**Clinically important**
**Completeness**

## Identifiers removed
[what was stripped and where to re-insert]

---

# [DOCUMENT TYPE]
[structured per references/document-types.md]

## Medications on discharge
| Drug | Dose | Route | Frequency | Duration | Status | Reason |

## Follow-up
## Return immediately if
```

## Failure modes

**Composing the examination.** The single most likely error. If the note says
"chest clear", write "chest clear" — not a systemic examination paragraph.

**Normalising values.** A potassium of 3.1 stays 3.1. Do not convert units,
round, or describe it as "mildly low" unless the clinician did.

**Inventing dates.** Admission and discharge dates drive insurance claims and
medico-legal timelines. Absent means absent.

**Smoothing an ambiguity.** "Sats were low" must not become "SpO2 88%".

**Writing a diagnosis the clinician did not commit to.** A working or
provisional diagnosis stays labelled as one. Upgrading "?LRTI" to "Lower
respiratory tract infection" changes the record and can change a claim.

**Losing negatives.** "No chest pain, no fever" is clinical information. A
recorded negative is a finding, not filler.

**Copying identifiers into the output** after stripping them from the input.

## Judgement calls

**When the source is too thin, say so and stop.** Three lines of ward notes do
not become a discharge summary. Produce the skeleton with gaps marked and tell
the clinician what to retrieve — that is more useful, and far safer, than a
plausible document.

**Abbreviations.** Expand on first use in anything leaving the institution, but
keep the clinician's meaning. Do not guess: `PID` is pelvic inflammatory disease
or prolapsed intervertebral disc depending on who wrote it, and guessing wrong
changes the record. Ask, or flag it.

**Do not upgrade certainty anywhere.** "Likely", "suspected", "cannot rule out"
carry clinical and legal weight. Preserve the hedge exactly.

**Patient-facing text is a different document.** If the patient gets a copy,
write their section at a genuinely lay reading level — no abbreviations, no
Latin, and instructions as actions.

## References

- `references/document-types.md` — read for the document you are writing:
  structure, purpose, and what its specific reader needs.
- `references/discharge-essentials.md` — read when writing any discharge or
  transfer document: medication reconciliation, follow-up, safety netting.
- `references/india.md` — read for Indian settings: NABH requirements, PMJAY and
  TPA claim needs, OD/BD/TDS notation, language and DPDP considerations.

## What this is not

A drafting aid for a qualified clinician who reads, corrects and signs. It does
not decide diagnoses, choose treatment, or determine fitness for discharge, and
nothing it produces should reach a patient record unreviewed.

It also does not certify anything. Fitness certificates, disability assessments
and cause-of-death statements are attestations by a named clinician about facts
they personally verified — draft the structure, never the attestation.
