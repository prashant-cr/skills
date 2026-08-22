# Writing clinical documents in India

Conventions, notation, and the requirements that decide whether a claim is paid
or a record survives an audit.

## Contents

- [Dosing notation](#dosing-notation)
- [Abbreviations that are genuinely ambiguous](#abbreviations-that-are-genuinely-ambiguous)
- [NABH documentation requirements](#nabh-documentation-requirements)
- [PMJAY and TPA claims](#pmjay-and-tpa-claims)
- [Language and the patient copy](#language-and-the-patient-copy)
- [DPDP and patient data](#dpdp-and-patient-data)
- [Medico-legal points](#medico-legal-points)

---

## Dosing notation

Indian prescriptions use a compact notation that is near-universal in the
country and opaque outside it. Preserve the clinician's notation in the record,
but expand it in anything the patient reads.

| | |
| --- | --- |
| **OD** | once daily |
| **BD / BID** | twice daily |
| **TDS / TID** | three times daily |
| **QID / QDS** | four times daily |
| **HS** | at night (hora somni) |
| **OM / mane** | in the morning |
| **SOS** | as required |
| **STAT** | at once, single dose |
| **Q4H / Q6H / Q8H** | every 4 / 6 / 8 hours |
| **1-0-1** | morning – afternoon – night grid; here, morning and night |
| **0-0-1** | night only |
| **x 5 days** | for 5 days |

**The 1-0-1 grid is the one to read carefully.** 1-0-1 is two doses; 1-1-1 is
three. Half doses appear as 0.5 or ½. Miscounting it changes the daily dose
silently, which is why `scripts/parse_med_list.py` in the `medication-review`
skill normalises it explicitly rather than by eye.

Also common: **"Tab" / "T." / "Cap" / "Inj" / "Syp"** prefixes for the dosage
form, and strengths written without a unit — "Ecosprin 75" means 75mg. Do not
add a unit that was not written; flag it.

## Abbreviations that are genuinely ambiguous

Do not expand these by guessing — the same string means different things by
speciality, and the wrong expansion changes the record:

| Abbreviation | Could be |
| --- | --- |
| **PID** | pelvic inflammatory disease, or prolapsed intervertebral disc |
| **MR** | mitral regurgitation, modified release, or mental retardation (obsolete) |
| **CVA** | cerebrovascular accident, or costovertebral angle |
| **DOA** | date of admission, or dead on arrival |
| **PT** | prothrombin time, physiotherapy, or patient |
| **BD** | twice daily, or bipolar disorder |
| **RA** | rheumatoid arthritis, right atrium, or room air |
| **HS** | at night, or heart sounds |
| **AF** | atrial fibrillation, or amniotic fluid |
| **OD** | once daily, or right eye (oculus dexter) |
| **IU** | international units, or intrauterine |

**OD is the dangerous one**: "Prednisolone OD" and "drops OD" mean different
things, and in ophthalmology the eye reading is standard. Where context does not
settle it, ask.

## NABH documentation requirements

For accredited hospitals, the discharge summary is an audited document. What
assessors look for:

- **A copy given to the patient**, and that recorded
- **Identification** — name, registration number, admission and discharge dates
- **Reason for admission**, diagnoses, and comorbidities
- **Significant findings**, investigations and procedures
- **Discharge medication with dosage and duration**, clearly stated
- **Follow-up instructions**, including when and where
- **Instructions on when to obtain urgent care** — safety netting, explicitly
  required, and the most common gap found in audits
- **Signature and registration number** of the treating clinician
- For a death: the cause, and that the family was informed

The pattern to notice is that NABH requires exactly the sections clinicians most
often compress: medication with duration, follow-up specifics, and urgent-care
instructions.

## PMJAY and TPA claims

Claim rejections are usually documentation failures, not clinical ones.

**What claims turn on:**

- **Diagnosis coded to the package**, with the primary diagnosis matching the
  procedure claimed
- **Secondary diagnoses and comorbidities documented** — these determine package
  tier, and an omitted comorbidity is money left on the table that was clinically
  present
- **Dates consistent everywhere** — admission, procedure, discharge. A mismatch
  between the summary and the claim form triggers a query
- **Length of stay justified by the recorded course.** A stay longer than the
  package norm needs the clinical reason visible in the notes
- **Investigations and procedures listed with dates**
- **Implant details** — make, model, and lot number for implant packages
- **Pre-authorisation number** where the scheme required one

**The integrity line, stated plainly.** Documenting a comorbidity that was
present and treated is correct and is the clinician's job. Adding one that was
not, upgrading a provisional diagnosis to a confirmed one, or adjusting a date to
fit a waiting period, is fraud — regardless of who in the billing chain asks for
it. If the notes are incomplete, complete them accurately from the source. Never
write toward the claim.

## Language and the patient copy

Many patients cannot read English, and a discharge summary they cannot read is
a discharge summary that does not work.

- The clinical document stays in English for the next clinician.
- The **patient-facing sections** — medications, follow-up, safety netting — are
  the ones worth producing in the patient's language.
- This is a **rewrite at a lower reading level, not a translation.** Translating
  "monitor for signs of decompensation" produces something equally unusable in
  Hindi. Write the meaning as actions first, then render it.
- **Numerals and dosing schedules travel better than words.** A simple grid with
  the tablet, the times of day, and before/after food is understood across
  literacy levels better than any prose.
- Keep drug names in the Latin script the strip uses, so the patient can match
  what you wrote against the packet.

## DPDP and patient data

The **Digital Personal Data Protection Act 2023** treats health data as personal
data under a consent regime. The treating hospital or clinician is the data
fiduciary; a tool is a processor at most.

Practically, for a clinician using this:

- Strip identifiers before pasting a record into any external tool, and
  re-insert them in the hospital system afterwards.
- The patient's consent to treatment is not consent for their record to be
  processed elsewhere.
- Data-principal rights include correction and erasure, which is a reason not to
  scatter copies of a record across drafts and downloads.

The **Digital Information Security in Healthcare Act** has been long-pending; do
not cite it as being in force. **Telemedicine Practice Guidelines** (2020) govern
remote consultations and carry their own record-keeping requirements.

## Medico-legal points

- **Records must be retained** — commonly 3 years for outpatient records under
  NMC regulations, longer for inpatient and medico-legal cases and for minors.
  Institutional policy usually sets a longer period; follow it.
- **The patient is entitled to their records**, and NMC regulations require them
  to be supplied on request within 72 hours.
- **Medico-legal cases (MLC)** — assault, road traffic accidents, poisoning,
  burns, suspected suicide — carry mandatory police intimation and stricter
  record-keeping. Flag the MLC status in the document; do not omit it.
- **Corrections are struck through, initialled and dated, never erased or
  overwritten.** An altered record is worse than a wrong one in any subsequent
  proceeding.
- **Never backdate anything**, and where an entry is written late, record it as
  a late entry with the actual time of writing.
