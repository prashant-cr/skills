# The patient changes the answer more than the drug list does

Age, pregnancy and organ function move a review further than any pair of drugs.
Read the section that applies.

## Contents

- [Older adults](#older-adults)
- [Renal impairment](#renal-impairment)
- [Hepatic impairment](#hepatic-impairment)
- [Pregnancy and breastfeeding](#pregnancy-and-breastfeeding)
- [Children](#children)
- [Deprescribing](#deprescribing)

---

## Older adults

Two published tools do most of the work, and they answer different questions.

**Beers criteria** list drugs that are potentially inappropriate in older
adults — where risk usually exceeds benefit. **STOPP/START** pairs drugs to stop
with drugs that should have been started and were not. START is the half people
skip, and under-treatment in older adults is as common as over-treatment: an
untreated osteoporosis after a fragility fracture, or a missing anticoagulant in
atrial fibrillation, are findings worth surfacing.

Neither is a rule. Both are prompts to justify a choice, and a documented reason
to continue a Beers-listed drug is a perfectly good answer.

**The burdens that are properties of the whole list, not any one drug:**

- **Anticholinergic burden.** Cumulative across the list, and the contributors
  are often not recognised as anticholinergic — older antihistamines, tricyclics,
  oxybutynin, some antipsychotics, some antispasmodics. The result is confusion,
  urinary retention, constipation, falls and dry mouth, and it is routinely
  attributed to ageing rather than to the prescription.
- **Falls risk.** Sedatives, antihypertensives, anything causing postural
  hypotension, and anticholinergics all add. A fall in an anticoagulated older
  adult is the high-consequence version.
- **Sedative load.** Benzodiazepines, Z-drugs, opioids, sedating antihistamines,
  and some antidepressants.

**Specific things worth checking every time in an older patient:**

- Benzodiazepines or Z-drugs continued far beyond a short course
- A PPI with no current indication, running for years
- NSAIDs in anyone with renal impairment, heart failure, or on an ACE inhibitor
- Long-acting sulfonylureas, with their prolonged hypoglycaemia risk
- Antipsychotics used for behavioural symptoms of dementia
- Doses never adjusted as renal function declined with age

**Kidney function falls with age even when creatinine looks normal**, because
creatinine reflects muscle mass and muscle mass falls too. A "normal" creatinine
in a frail 82-year-old can conceal a clearance in the 30s. This is precisely why
`scripts/kidney_function.py` reports Cockcroft-Gault, which uses weight.

## Renal impairment

Where dosing errors concentrate.

**Use the measure the label uses.** Most labels define adjustments against
Cockcroft-Gault creatinine clearance, not the CKD-EPI eGFR the lab reports.
They diverge most in the elderly, the very light and the obese — the patients in
whom the error matters most.

**Separate two different actions.** "Contraindicated below a threshold" and
"needs a lower dose" are not the same finding and should not sit in the same
row. Say which applies to each drug.

**Drugs that commonly need attention:** metformin, direct oral anticoagulants,
most renally-cleared antibiotics, gabapentin and pregabalin, allopurinol,
digoxin, methotrexate, and lithium.

**Drugs that worsen renal function** are worth flagging alongside dose
adjustment: NSAIDs, ACE inhibitors and ARBs during intercurrent illness,
aminoglycosides, and iodinated contrast.

**Acute versus chronic matters.** In acute kidney injury a single creatinine
lags behind real function — a rising creatinine means true clearance is already
lower than the calculation suggests, so dose for where the patient is heading.

**Dialysis is a separate question entirely.** Dosing depends on the modality and
on whether the drug is dialysed; do not extrapolate from a CKD-stage adjustment.

## Hepatic impairment

There is no eGFR equivalent. Adjustment is qualitative, usually framed by
**Child-Pugh** class, and many labels simply say avoid in severe impairment.

Points worth carrying:

- **Liver enzymes are not a measure of function.** Synthetic function — albumin,
  INR, bilirubin — is what matters for dosing.
- Drugs with high first-pass metabolism can have markedly increased
  bioavailability in cirrhosis with portosystemic shunting.
- **Paracetamol is not automatically contraindicated** in liver disease, but the
  ceiling is lower; check the current recommendation rather than assuming either
  extreme.
- NSAIDs carry particular risk in cirrhosis — renal failure and variceal
  bleeding.
- Sedatives can precipitate hepatic encephalopathy.

## Pregnancy and breastfeeding

**Check every drug, including the ones that feel trivial** — analgesics,
antiemetics, topicals, supplements.

**Do not default to "avoid".** Reflexive avoidance causes untreated maternal
illness, which frequently poses a greater risk to both than the drug does.
Untreated epilepsy, asthma, hypothyroidism, depression and infection all carry
real fetal risk. The useful output states what is known: this drug is
established in pregnancy, this one has limited data, this one has a documented
teratogenic risk with a specific alternative available.

**The old letter categories (A/B/C/D/X) have been withdrawn** by the FDA in
favour of narrative risk summaries. Do not cite a letter category as though it
were current.

**Timing matters** — first-trimester organogenesis, third-trimester effects, and
peripartum considerations are different questions about the same drug.

**Known high-risk agents to check for specifically:** isotretinoin, sodium
valproate, ACE inhibitors and ARBs, warfarin, methotrexate, and live vaccines.
Sodium valproate in a woman of childbearing age deserves a flag regardless of
current pregnancy status, given the pregnancy-prevention requirements attached
to it.

**Breastfeeding is a separate assessment from pregnancy.** A drug unsafe in
pregnancy may be perfectly compatible with breastfeeding, and the reverse is
also true — so answer them separately rather than together.

## Children

**Dosing is per kilogram against a current measured weight**, with a ceiling at
the adult dose. Never scale an adult dose down by eye, and be explicit about
which weight was used — a weight from three months ago is not a current weight
in a growing child.

Other points:

- **Neonates and infants are not small children.** Immature renal and hepatic
  clearance changes everything, and dosing intervals differ, not just amounts.
- **Formulation and concentration.** Paediatric liquids come in more than one
  strength, and a dose in millilitres without the concentration is not a dose.
  Insist on mg and the concentration.
- **Drugs to avoid in children** are worth checking for specifically: aspirin
  and Reye's syndrome, tetracyclines and dental staining, fluoroquinolones,
  codeine, and promethazine in the very young.
- **Off-label use is routine in paediatrics** and is not by itself a problem —
  but it means the label will not answer the dosing question, and a paediatric
  formulary must.

## Deprescribing

Surface these as questions for the prescriber, never as instructions. The
clinical context and the patient's own priorities decide, and neither is visible
from a drug list.

**What to look for:**

- **No documented indication.** The commonest finding, and often simply an
  incomplete list rather than an unnecessary drug — so ask rather than conclude.
- **Prescribing cascades** — a drug treating another drug's side effect. Classic
  chains: a calcium channel blocker causing oedema treated with a diuretic; an
  anticholinergic causing constipation treated with a laxative; metoclopramide
  causing extrapyramidal symptoms treated with an anti-Parkinsonian agent.
  Recognising the cascade means the fix is upstream.
- **Indefinite courses that were meant to be short** — PPIs, steroids,
  benzodiazepines, antibiotics.
- **Preventive drugs whose time-to-benefit exceeds life expectancy** — a statin
  for primary prevention in someone with advanced frailty or a terminal
  diagnosis. This needs handling with care and in conversation with the patient.
- **Duplicate therapy surviving a transition of care** — the commonest origin is
  a hospital admission where a brand and a generic of the same molecule both
  ended up on the discharge list.

**Several drugs cause harm if stopped abruptly**, and this belongs in the output
whenever you suggest stopping one: beta blockers (rebound tachycardia and
ischaemia), clonidine (rebound hypertension), corticosteroids (adrenal
insufficiency), benzodiazepines (withdrawal seizures), SSRIs and SNRIs
(discontinuation syndrome), and antiepileptics (seizures). Say that a taper is
needed rather than leaving it implied.
