# The documents, and what each reader needs

Read the section for the document you are writing. The differences between these
are not formatting — they are differences in **who reads it and what they must
do next**, and that changes what goes at the top.

## Contents

- [Discharge summary](#discharge-summary)
- [Referral letter](#referral-letter)
- [Transfer / handover note](#transfer--handover-note)
- [Operative note](#operative-note)
- [Death summary](#death-summary)
- [Sick note and fitness certificate](#sick-note-and-fitness-certificate)
- [Insurance and claim summary](#insurance-and-claim-summary)

---

## Discharge summary

**Read by:** the GP or physician resuming care, the patient and their family at
home, often an insurer, and — if anything goes wrong — a court.

That mixed audience is what makes it hard. It has to be clinically precise for
the doctor and actionable for a frightened person at home.

```
Patient          age, sex (no identifiers in your draft)
Admission / discharge dates
Discharge diagnosis        primary, then secondary
Presenting complaint       why they came
Hospital course            what happened, in order, with the reasoning
Procedures                 with dates
Key investigations         values and dates, not "labs were done"
Condition at discharge
Medications                the reconciliation table -- see discharge-essentials.md
Follow-up                  who, when, what for
Return immediately if      the red flags
Pending results            what is still awaited and who chases it
```

**The two sections that decide whether it worked** are the medication
reconciliation and the follow-up-plus-safety-net. Everything above them is
context; those two are instructions someone will act on.

**Secondary diagnoses matter more than they look.** They drive the insurance
claim, and in a PMJAY or TPA context an omitted comorbidity can reduce or reject
a package. They also tell the next doctor what else is going on.

## Referral letter

**Read by:** a specialist deciding, often in seconds, **how urgently to see this
patient**. That decision is made from the first two lines.

So the order inverts relative to a discharge summary — the ask comes first, the
history supports it:

```
Reason for referral        the specific question, in one sentence
Urgency                    and why -- what you are worried about
Relevant history           relevant, not complete
Examination findings
Investigations done        with values and dates, plus what is pending
Current medications        and allergies
What has already been tried   and how it failed
Referrer and contact       for the specialist to come back on
```

**"Please see and do the needful" is not a referral.** The specialist cannot
triage it and cannot prepare. State the question: "is this thyroid nodule
suspicious enough for FNAC?" is a referral. Name what you are worried about even
if you are not sure — that is the information that sets urgency.

**Include what has been tried and failed.** It prevents the specialist repeating
your work and tells them where the patient actually is.

## Transfer / handover note

**Read by:** the team taking over, often within the hour, often overnight.

Different job again: this is about what could go wrong in the next few hours.

```
Why transferring           and to what level of care
Current status             observations, support, lines, drains
Active problems            in priority order
What was done              in the last few hours
What to watch for          the specific deterioration you fear
Escalation plan            ceiling of care, DNR status if decided
Outstanding tasks          bloods due, results to chase, family to update
Who to call
```

**The ceiling-of-care and resuscitation status belongs here explicitly.** A team
taking over at 2am should not have to work it out, and an unstated decision is
treated as no decision.

## Operative note

**Read by:** the ward team managing recovery, the surgeon at follow-up, and
potentially a medico-legal reviewer years later. Convention is to write it
immediately after the procedure.

```
Date and time
Pre-operative diagnosis
Post-operative diagnosis   often the same; when it differs, that is the finding
Procedure performed        the full name, and side where relevant
Surgeon, assistants, anaesthetist
Anaesthesia                type and agent
Position and preparation
Findings                   what was actually seen
Steps                      approach, technique, closure
Implants or devices        with size, and lot number where required
Estimated blood loss
Specimens sent             and to which lab
Complications              including "none" explicitly
Counts                     swab and instrument counts correct
Post-operative instructions
```

**Side matters.** Left and right must be explicit in the procedure name.

**"No complications" is a finding worth stating.** Its absence reads as an
omission later, not as an uneventful case.

## Death summary

**Read by:** the family, the registrar of deaths, sometimes police or a coroner.
The most legally exposed document here — write it with that in mind.

```
Admission date and presenting condition
Clinical course              including deterioration and what was done
Resuscitation                attempted, or a documented DNR/DNAR decision
Date and time of death
Cause of death               in the WHO/MCCD structure below
Who was informed, and when
Post-mortem status
Medico-legal case status
```

**Cause of death has a required structure**, and getting it wrong is the
commonest certification error:

```
I(a) Immediate cause          the disease that directly caused death
I(b) due to                   the antecedent cause
I(c) due to                   the underlying cause that started the sequence
II   Other significant conditions contributing but not in the sequence
```

"Cardiorespiratory arrest" is a mode of dying, not a cause, and is rejected. The
underlying cause in I(c) is the one that matters statistically.

**Draft the structure; never draft the attestation.** Certification is a named
clinician's personal statement about facts they verified.

## Sick note and fitness certificate

**Read by:** an employer, a school, sometimes a court or insurer.

Short, and the constraint is what you may say. It confirms that the person was
seen, and for what period they are unfit — **not the diagnosis**, unless the
patient has explicitly consented to disclosure. Employers are not entitled to a
diagnosis.

```
That the person was examined, and on what date
The period of unfitness, or fitness to resume
Any restrictions or adjustments on return
The clinician's name, qualification and registration number
```

**Never draft a retrospective certificate for a period the clinician did not
observe**, and never draft the signature block as though verified. This is an
attestation, and a false one is a professional-conduct matter.

## Insurance and claim summary

**Read by:** a TPA or scheme processor checking the claim against a package.

The clinical content is unchanged; what changes is that omissions cost money.
See `references/india.md` for what PMJAY and private TPAs actually require.

The integrity rule is absolute and worth stating plainly: **the summary reflects
what happened.** Adding a comorbidity to reach a higher package, or shifting a
date to fit a waiting period, is fraud regardless of who asks for it. If the
record is genuinely incomplete, the fix is to complete it accurately from the
notes — never to write what the claim needs.
