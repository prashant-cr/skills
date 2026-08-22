---
name: medication-review
license: MIT
description: Reviews a patient's medication list for interactions, duplication, renal and hepatic dosing, and drugs that should be stopped — ranked by what actually needs acting on rather than returning forty alerts a clinician will scroll past. Resolves every brand and fixed-dose combination to its molecules first, because in India four brand names routinely hide nine ingredients and the commonest duplication is one molecule appearing twice under different labels. Fetches every dose and interaction rather than recalling it, since a remembered renal adjustment is specific, plausible and wrong. Computes creatinine clearance the way drug labels actually define it. Use whenever the user pastes a medication or prescription list, asks about drug interactions, dose adjustment in kidney or liver disease, polypharmacy, deprescribing, Beers or STOPP criteria, whether two drugs can be given together, or safety in elderly, pregnant or paediatric patients.
---

# Medication review

Takes a patient's medication list and returns **the few things that need acting
on**, in order, with the evidence for each.

The output supports a prescriber's decision. It does not make one, and no
medication should be started, stopped or changed on the strength of it alone.

## Doses you may and may not state

Every dose, interaction, contraindication and adjustment threshold you report is
either **retrieved this session, with the source named**, or it is not stated as
fact.

Never supply a dose or a renal cut-off from memory. This is the highest-harm
version of a failure mode you can otherwise get away with: a recalled adjustment
is *specific*, *plausible* and *confidently wrong* — "reduce to 50% if eGFR
below 30" has the exact shape of a real recommendation, and nothing about it
looks uncertain to the reader.

When you cannot retrieve it, say which drug you could not verify and where to
check — the product's own label, the national formulary, the hospital's
antimicrobial policy. **A named gap sends the clinician to the source. A
plausible number stops them looking.**

The same applies to interaction severity. "Moderate" is a graded claim from a
specific database, not an adjective.

## Why the forty-alert list is the problem

Run a list through a standard checker and it returns thirty or forty hits.
Almost all are theoretical, and the clinician learns within a week to dismiss the
whole panel — including the two that would have changed management. Alert
fatigue is not a UI complaint; it is the mechanism by which real warnings stop
being read.

So the job is **triage, not detection**. For every finding ask: does this change
what the prescriber does today? If not, it goes below the fold or not at all.

Rank on three things together:

- **Severity** — what happens if it is missed
- **Likelihood** — does it occur at these doses, in this patient
- **Actionability** — is there something to do about it

A theoretically severe interaction with no action available ranks below a
moderate one with a clear fix.

## De-identify first

```bash
python3 scripts/deidentify.py --file meds.txt
```

Prescriptions carry the patient's name, UHID, and often the prescriber's
registration number. Strip them before working, refer to the patient by age and
sex, and keep them out of the output. Under India's **DPDP Act 2023** health
data is personal data with a consent regime, and the treating institution — not
the tool — is the data fiduciary.

## Workflow

### 1. Resolve everything to molecules — before anything else

This step finds more real problems than the interaction check does, and it is
the one most reviews skip.

An Indian prescription is usually brand names, and many of those brands are
**fixed-dose combinations**. Four brands can be nine molecules. Until every line
is resolved to its ingredients, an interaction check is running on the wrong
list, and the commonest error of all — **the same molecule arriving twice under
two labels** — is invisible.

```bash
python3 scripts/parse_med_list.py --file meds.txt
```

The parser normalises the frequency notation Indian prescriptions actually use
(OD, BD, TDS, QID, HS, SOS, STAT, Q6H, 1-0-1) into explicit daily dosing, splits
dose from unit, and flags every line it could not parse confidently rather than
guessing. Ambiguity here propagates into every later step, so resolve the
flagged lines before continuing.

Then look up each brand to get its molecules. Do not rely on recall for brand
composition — Indian brand names are reused across very different formulations,
and the same brand can be a different molecule in a different strength.

`references/india-formulary.md` covers FDCs, the banned-FDC list, Schedule H/H1
and X, NLEM, and why brand-to-molecule resolution is harder here than elsewhere.

### 2. Duplication and class overlap

With the molecule list in hand:

- **Same molecule twice** — usually via two FDCs, or a brand plus its generic
- **Same class twice** — two NSAIDs, two PPIs, an ACE inhibitor with an ARB,
  two benzodiazepines
- **Additive effect without shared class** — three drugs each with modest
  anticholinergic activity, or several serotonergic agents
- **Paracetamol across products**, which is the classic FDC hazard: an
  analgesic FDC plus a cold preparation plus PRN paracetamol can exceed the
  daily ceiling without any single line looking wrong

### 3. Interactions that change management

Check the resolved list, then triage as above. Some combinations warrant a
specific look every time because the consequence is severe and the mechanism is
common — QT prolongation from stacked agents, serotonin syndrome, additive
bleeding risk, drugs that raise or lower another's levels through CYP or P-gp,
and potassium-raising combinations in a patient with any renal impairment.

`references/interactions.md` has the always-check list and how to grade
significance defensibly.

### 4. Renal and hepatic dosing

This is where dosing errors concentrate, and where a wrong recalled number does
the most damage.

**Get the kidney function right, and use the right measure.** Most drug labels
define their adjustments against **Cockcroft-Gault creatinine clearance**, not
the CKD-EPI eGFR the lab reports. They are different numbers and they diverge
most in exactly the patients where it matters — the elderly, the very light, the
obese.

```bash
python3 scripts/kidney_function.py --creatinine 1.4 --age 74 --sex F --weight 58
```

It reports both, states which to use for drug dosing and why, and gives the CKD
stage. Where the patient's weight is unknown it says so rather than assuming
one — Cockcroft-Gault needs weight, and a guessed weight produces a confident
wrong clearance.

Then check each drug against a fetched source. Flag drugs that are contra-
indicated below a threshold separately from those merely needing a lower dose:
those are different actions.

For hepatic impairment, note that there is no equivalent of eGFR — adjustment
is qualitative, usually via Child-Pugh, and many labels simply say avoid.

### 5. The patient in front of you

Age, pregnancy and comorbidity change the answer more than the drug list does.
`references/high-risk.md` covers each; in outline:

- **Older adults** — Beers and STOPP/START flag drugs where risk usually exceeds
  benefit. Anticholinergic burden and falls risk are cumulative across the list,
  so they are properties of the whole prescription, not of any one line.
- **Pregnancy and breastfeeding** — check every drug, including ones that feel
  trivial. Say what is known rather than defaulting to "avoid", which is often
  wrong and causes untreated maternal illness.
- **Children** — dosing is per kilogram against a current weight, with ceilings.
  Never scale an adult dose down by eye.
- **Renal, hepatic and cardiac comorbidity** — already covered above, but they
  interact: a diuretic plus an ACE inhibitor plus an NSAID is the "triple
  whammy" that precipitates acute kidney injury, and each drug alone looks fine.

### 6. What could come off

Polypharmacy is itself a risk, and nobody is assigned the job of stopping
things. Worth surfacing:

- Drugs with **no documented indication** in the list you were given
- **Prescribing cascades** — a drug treating another drug's side effect
- **Indefinite courses** that were meant to be short: PPIs, steroids,
  benzodiazepines, antibiotics
- Preventive drugs whose **time-to-benefit exceeds life expectancy**

Frame these as questions for the prescriber, not instructions. Deprescribing
needs the clinical context and the patient's wishes, and often a taper — several
of these drugs cause harm if stopped abruptly, which is worth saying explicitly.

## Report structure

```markdown
# Medication review — [age], [sex]
**Kidney function:** [CrCl and eGFR, or "not supplied"]
**Resolved:** [n] products -> [m] molecules

## Act on these
| # | Finding | Why it matters | Suggested action | Source |

## Molecule list after resolving brands and FDCs
| Product | Molecules | Dose | Frequency | Daily total |

## Duplication
## Interactions — reviewed and not acted on
## Renal / hepatic dose checks
## Consider stopping
## Not verified
[every drug whose dosing or interaction data could not be retrieved]
```

## Failure modes

**Stating a dose from memory.** The one that hurts people.

**Reviewing brands instead of molecules.** Guarantees missed duplication.

**Returning everything found.** An unranked list is not a review.

**Using eGFR where the label means creatinine clearance**, or vice versa.

**Calling an interaction severe without a source.** Severity grades come from
databases and they disagree; say which one.

**Treating "no interaction found" as "safe".** It may mean nothing was checked
for that pair. Say which is which.

**Ignoring what is not on the list.** Over-the-counter analgesics, ayurvedic and
homeopathic preparations, and supplements are commonly omitted by patients and
routinely interact — St John's wort, high-dose fish oil, and heavy-metal content
in some traditional preparations all matter. Ask.

## Judgement calls

**If the user is the patient, not a clinician, change register but stay useful.**
Explain what was found in plain language and why it matters, and route them to
their doctor or pharmacist for the decision. Do not tell a patient to stop a
prescribed drug — some cause harm on abrupt withdrawal, and the prescriber has
context you do not. Telling them what to ask is the useful version.

**An incomplete list still deserves a review.** Say what is missing, review what
you have, and name what the answer would depend on.

**Do not manufacture certainty about Indian brands.** If a brand cannot be
resolved confidently, say so and ask for the strip or the composition. Guessing
a molecule from a brand name is how the whole review becomes wrong.

**Urgent findings go first, plainly.** If something on the list could cause
serious harm today, say that in the first line rather than at rank 1 of a table.

## References

- `references/india-formulary.md` — read for any Indian prescription: FDCs,
  banned combinations, schedules, NLEM, brand-resolution traps.
- `references/interactions.md` — read when checking interactions: the
  always-check list and how to grade significance.
- `references/high-risk.md` — read when the patient is elderly, pregnant,
  paediatric, or has renal, hepatic or cardiac impairment.

## What this is not

A second pair of eyes for a qualified prescriber. It is not a prescribing
decision, not a substitute for the product label or a maintained interaction
database, and not a tool for a patient to adjust their own treatment.

Nothing here overrides the clinician who has examined the patient, and where
this review and the treating team disagree, the treating team has information
this does not.
