---
name: weight-loss-diet-plan
license: MIT
description: Builds a personalised fat-loss diet plan — a full template day and a full seven-day menu, sized to the person's own calorie and protein numbers after a short intake on lifestyle, current eating pattern, cooking time and food preference (vegetarian, vegan, eggetarian, non-vegetarian, pescatarian, halal, jain and others), with a shopping list and the rules for what to change when the scale stalls. Use whenever the user asks for a diet plan, meal plan, weight loss or fat loss plan, weekly menu, how many calories they should eat, how much protein they need, what to eat to lose weight, wants their current diet reviewed or fixed, or says their weight loss has plateaued — including bare asks like "plan my diet", "i want to lose 10 kg before december", "what should i eat tomorrow", "is my meal plan enough protein" or "my weight is stuck".
---

# Weight loss diet plan

Produces a diet a specific person can actually run for a month — their calories, their protein
floor, their food, their schedule — plus the shopping list and the rules for changing it when it
stops working.

Almost every diet plan ever written is arithmetically correct. Very few survive contact with a
real week. The plan says grilled salmon and quinoa on Wednesday; Wednesday has a 7pm meeting and
nothing in the fridge. The failure looks like a discipline problem, so the next plan is stricter,
and stricter plans fail faster.

That is the problem this skill exists to solve. Not "what should a person eat to lose fat" — that
has been settled for decades and is not interesting. The open question is **what will this person
still be eating in week five**, and the answer is different for every person, which is why the
intake comes before the plan.

## The one idea that organises everything below

**A diet plan is a hypothesis about someone's week, and adherence is the binding constraint.**

Calories determine whether fat loss is possible. Adherence determines whether it happens. A 20%
deficit followed for twelve weeks beats a 35% deficit abandoned in nine days, and the second one
is what aggressive plans reliably produce.

This has three consequences that shape every step below:

- **Build from what they already eat.** A plan made of unfamiliar foods is a plan that requires
  learning to cook, shopping differently and enjoying it less, all during a calorie deficit. Ask
  what their normal week looks like and change the least that will work.
- **Protein is the one number that does not bend.** In a deficit the body will fund the gap from
  muscle unless protein and resistance training give it a reason not to. Losing 8 kg of which 3 kg
  is muscle leaves someone lighter, weaker and with a lower maintenance intake than when they
  started — the exact setup for regain. Protein is also the most satiating macro, so the floor
  that protects muscle also makes the deficit easier to hold.
- **The plan must have slack built in.** Eating out, a skipped meal, a late night. If the plan has
  no answer for those, the person improvises, and the improvised version is the one they'll
  actually be running by week three. Design that version deliberately.

## Screen before you plan

Some situations need a clinician's input rather than a calculated deficit. This is quick, it goes
in the intake, and it matters — a generic 1,400 kcal plan is actively harmful to some of the
people who ask for one.

| If the person is | Do this |
| --- | --- |
| Pregnant or breastfeeding | Do not build a weight-loss deficit. Offer nutrition-quality help instead and refer to their doctor or midwife. |
| Under 18 | Do not set a deficit. Refer to a paediatrician or family doctor. |
| BMI below 18.5 | Stop and say plainly that fat loss is not indicated. Offer maintenance or muscle-gain support instead. |
| BMI between 18.5 and 20 | Not a stop, but ask what the goal really is first. People here usually want a body-composition change, and recomposition at maintenance serves that better than a deficit. |
| Describing a history of an eating disorder, or the intake reads that way (calorie fixation, purging, "good/bad" foods, secret eating) | Do not produce a calorie-restricted plan or a numbers-heavy one. Say why, warmly, and point to a doctor or an eating-disorder helpline. |
| On insulin or a sulfonylurea for diabetes | Build the plan, and flag prominently that cutting carbohydrate while on these raises hypoglycaemia risk and doses may need review by their prescriber first. |
| On dialysis or with reduced kidney function | Build the plan but do **not** raise protein — the usual 1.6-2.2 g/kg advice is inappropriate here. Protein must come from their nephrologist. |
| On warfarin, levothyroxine, or MAOIs | Note the specific interaction (vitamin K consistency, calcium and iron timing, tyramine) rather than a generic caution. |

Everyone else: build the plan. Say once, plainly, that this is general nutrition information and
not a substitute for individual medical advice — then get on with being useful. Repeated hedging
in every section reads as evasion and makes the plan harder to follow.

**Do not negotiate an unsafe goal into a slightly-less-unsafe one.** This is the failure worth
naming separately, because it feels like the reasonable middle path and it is the most harmful
thing available here. Someone at 51 kg and 165 cm asking to reach 44 kg does not need a
counter-offer of 48 kg — that is still underweight, and meeting them halfway ratifies the project
and supplies the numbers to pursue it. It is worse still in combination: if you have just raised
the possibility of disordered eating, handing over a calorie-counted plan in the next paragraph
tells them the concern was decorative. Decline the deficit, then offer something genuinely
different — maintenance, recomposition, resistance training — rather than a smaller version of
what was asked for.

## Workflow

### 1. Run the intake in one message

Ask everything at once, grouped, and say roughly why. Twelve questions delivered one at a time
feels like an interrogation and people abandon it; the same twelve in a single tidy block get
answered in one reply.

**Ask for these — the plan is guesswork without them:**

- Age, sex, height, current weight. Body fat percentage if they happen to know it.
- Goal weight if they have one, and any deadline (a wedding, a check-up).
- **Activity** — desk job or on their feet? Deliberate exercise: what, how many days, how hard?
  Rough daily step count if they know it.
- **What they eat now** — walk me through a normal weekday and a normal weekend day. This single
  question is worth more than any other; it gives baseline intake, meal timing, cuisine, portion
  habits and their actual food vocabulary all at once.
- **Diet pattern** — vegetarian, vegan, eggetarian, non-vegetarian, pescatarian, halal, kosher,
  jain, or something else. Ask directly rather than assuming from anything else they've said.
- **Allergies and intolerances**, and any foods they simply will not eat.
- **Logistics** — who cooks, how much time on a weekday, do they carry lunch, how often do they
  eat out or order in, any budget ceiling.
- **Health** — any conditions, medications, or the screen items above.

**Nice to have, don't block on:** sleep, alcohol, caffeine, past diets and why they stopped,
kitchen equipment, who else they cook for.

Two judgement calls worth making well. First, if they give you most of it, **build the plan and
state your assumptions** rather than going back for the rest — a plan with two stated assumptions
beats a second round of questions. Second, if someone has already given you their details in the
conversation, don't ask again; confirm what you have and fill the gaps.

`references/intake-and-targets.md` has the full question set, how to calibrate activity level from
what people actually say, and how to handle someone who won't give numbers.

### 2. Compute the targets, don't estimate them

```bash
python3 scripts/nutrition_math.py --example > intake.json   # fill this in
python3 scripts/nutrition_math.py intake.json
```

It returns maintenance calories, the target intake, the protein floor, fat floor, remaining carbs,
fibre target, the projected weekly rate of loss and a realistic date for the goal weight — and it
refuses to produce a target that is unsafe, clamping to floors and telling you it did.

Run it rather than doing this in your head. The arithmetic is easy and the failure is silent: a
protein target scaled to the wrong bodyweight, or a deficit that quietly lands under someone's
basal requirement, both look completely plausible on the page.

Two things the script encodes that are worth understanding, because you'll need to explain them:

- **Protein is scaled to target weight, not current weight**, for anyone well above a healthy BMI.
  Fat mass has no protein requirement, so 2 g/kg of a 120 kg bodyweight produces a number that is
  both unnecessary and impossible to eat. Goal weight (or lean mass, when body fat is known) gives
  a target that does the muscle-protecting job at a liveable volume.
- **The deficit is capped by rate of loss, not by a fixed number.** Roughly 0.5-0.75% of
  bodyweight per week is the band where fat loss dominates; push past ~1% and the proportion
  coming from muscle climbs, hunger becomes the whole day, and adherence collapses. A 110 kg
  person and a 60 kg person therefore get very different absolute deficits.

### 3. Build one day that works before you build seven

Get a single day right — hits the calorie target, clears the protein floor, made of food they
recognise — and the week is that day varied. Start with seven and you will produce a menu that is
impressive, unshoppable, and wrong on protein.

Anchor each meal on its protein source and build the rest around it, because protein is the
constraint that is hard to fix later; calories can always be tuned with oil, rice or an extra
handful of nuts.

**Spread protein across the day** — roughly 25-40 g at each of three or four eatings rather than
30 g at breakfast and 90 g at dinner. Muscle protein synthesis responds to a per-meal threshold,
so the same daily total distributed evenly does more, and it keeps people fuller for longer.

**Vegetarian and vegan plans need concentrated sources, not more of the same.** This is where
most plant-based fat-loss plans quietly fail. You cannot reach 120 g of protein on dal and
peanut butter — plant sources carry substantial carbohydrate or fat alongside their protein, so
scaling them up to hit the protein target blows the calorie target long before you get there. The
plans that work lean on the concentrated end: soy in its forms (tofu, tempeh, soy chunks, edamame),
seitan, dairy if permitted (Greek yogurt, quark, cottage cheese, paneer, skyr), egg whites if
eggetarian, legumes as the base layer, and a protein supplement where food alone doesn't close the
gap. `references/protein-and-food.md` has the numbers per 100 g and the swaps by diet pattern.

**Build in volume.** A deficit felt as hunger is a deficit that ends. Vegetables, broth-based
soups, salads, fruit and high-fibre carbohydrates buy a lot of fullness per calorie, which is why
the fibre target is in the output and not an afterthought.

### 4. Expand to the week

The week has to balance two opposing pressures, and getting this wrong is the most common way a
technically-good plan dies:

- **Too much variety** and it becomes unshoppable and unaffordable — twenty-one distinct recipes
  means daily cooking and a fridge full of half-used ingredients.
- **Too little** and they're bored by Thursday and ordering in by Friday.

The shape that survives: **three or four rotating breakfasts, batch-cooked protein and grains that
carry across two or three days, and dinners as the place variety lives.** Cook once, eat twice is
not a compromise here — it's the mechanism.

Then deliberately build in the parts of a real week:

- **One eating-out or takeaway slot**, planned into the numbers rather than treated as a failure.
  Give the actual ordering strategy for the cuisines they named.
- **A bad-day fallback** — the 10-minute, no-cooking, hits-protein meal for when the plan is not
  happening. Naming it in advance is the difference between one improvised meal and an abandoned
  week.
- **Their non-negotiables.** If someone drinks two sweet teas a day or has dessert on Sunday, put
  it in the plan and budget for it. Removing it doesn't make it stop happening — it just moves it
  off the plan and out of the count.

`references/plan-construction.md` covers meal templates, batching, the eating-out strategies,
alcohol, and building the shopping list.

### 5. Check the arithmetic before you show it

```bash
python3 scripts/plan_check.py --example > week.json   # structure of a week plan
python3 scripts/plan_check.py week.json --targets targets.json
```

Write the week out as structured data and let the script total it. It verifies each day against
the calorie and protein targets, checks that protein is actually distributed across meals rather
than piled into dinner, checks fibre, and flags days that are impractical (too many distinct
recipes) or nutritionally thin.

Do this every time. Summing 28 meals by eye is exactly the kind of task that produces confident
wrong totals, and a plan whose protein column doesn't add up is worse than no plan, because the
person follows it precisely and gets the outcome the numbers were supposed to prevent.

If a day fails, fix that day and re-run. Don't adjust the target to match the plan.

**Never write a summary the totals don't support.** The temptation, once a week is nearly right,
is to state that every day clears the protein floor because it very nearly does. A plan that
claims a 130 g floor and delivers 127 g has told the person something false about the one number
the whole plan is built to protect, and they have no way to catch it. If a day genuinely can't
reach the floor, either fix it or state the floor you actually hit — both are honest, and the
gap between the claim and the arithmetic is the thing that isn't.

### 6. Deliver it

Lead with the plan, not the caveats. Use the structure below.

## Output format

```
## Your numbers
Maintenance ~X kcal · Target X kcal · Protein X g · Fat X g · Carbs X g · Fibre X g
Expected rate: X kg/week — goal weight around [date]

## Template day
[Each meal: food and portion, calories, protein. Running protein total down the side.]

## Your week
[7-day table. Breakfast / Lunch / Snack / Dinner, with per-day kcal and protein columns.]

## Protein sources you're relying on
[The 6-10 foods doing the work, with per-portion protein — so they can swap within the list
without recalculating anything.]

## Shopping list
[Grouped by aisle, with quantities for the week.]

## The week-two rules
[What to change if the scale hasn't moved, and what to do on a day the plan falls apart.]
```

Give portions in the units they'll actually use — grams for meat, paneer and grains where accuracy
matters, but "1 medium apple", "2 rotis", "1 cup cooked dal" for the rest. Precision that requires
a kitchen scale for everything is precision that gets abandoned.

## When it stops working

Weight loss stalls. It is the normal course of the thing, not a sign the plan was wrong, and the
response matters more than the plan did.

The critical distinction: **most stalls are not metabolic.** Day-to-day scale weight moves several
kilos on water, salt, carbohydrate and bowel contents, so a two-week flat line is often a real fat
loss hidden under water, or adherence that has quietly drifted — portions creeping, an untracked
oil, weekends undoing weekdays. Diagnose before you cut, because cutting calories on a plan that
is already being under-eaten makes everything worse.

Read `references/adjustment-protocol.md` when the person reports a stall, is checking in after a
week or two, is losing faster than expected, or says they are struggling to stick to it. It has
the decision rules, the diet-break logic, and how to repair adherence without shrinking the plan.

## Failure modes to avoid

- **Aggressive deficits.** 1,200 kcal for a 90 kg man is not ambition, it's a plan with a
  two-week lifespan. If someone asks for faster, explain the muscle and adherence cost and offer
  the top of the safe band.
- **Ignoring the stated diet pattern halfway through.** Chicken appearing on day five of a
  vegetarian plan destroys trust in the whole document. Check the week against the pattern.
- **Inventing nutrition numbers.** If you are unsure of a food's protein content, say so or look
  it up. A plan built on wrong values fails silently.
- **Generic plans with a name on top.** If the plan would suit anyone, the intake was wasted. It
  should be visibly built from their answers — their foods, their schedule, their constraints.
- **Moralising about food.** No "clean", "cheat", "guilty". It doesn't help anyone eat better and
  it does harm to people with a difficult history around food.
- **Burying the plan under disclaimers.** One clear statement of scope, then the work.

## Reference files

- `references/intake-and-targets.md` — full intake question set, activity calibration, handling
  missing or refused data, special populations.
- `references/protein-and-food.md` — protein and calorie content by food, organised by diet
  pattern, plus satiety and fibre sources and how to swap without recalculating.
- `references/plan-construction.md` — meal templates, batch cooking, eating out, alcohol,
  shopping lists.
- `references/adjustment-protocol.md` — read when the person checks in, stalls, loses too fast, or
  is struggling with adherence.
