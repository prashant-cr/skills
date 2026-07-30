# Plan construction

Read this when building the template day and expanding it to the week.

## Contents

- [Meal templates](#meal-templates)
- [The shape of a survivable week](#the-shape-of-a-survivable-week)
- [Batch cooking](#batch-cooking)
- [Eating out and ordering in](#eating-out-and-ordering-in)
- [Alcohol](#alcohol)
- [The bad-day fallback](#the-bad-day-fallback)
- [Shopping lists](#shopping-lists)
- [Presenting the plan](#presenting-the-plan)

## Meal templates

Templates beat recipes. A recipe is one meal; a template is a hundred meals with a structure that
guarantees the protein lands. Give the template, then populate it with their foods.

**The universal shape**

```
1 protein anchor      25-40 g protein — decided first, non-negotiable
+ 1 volume component  vegetables, salad, soup — as much as they want
+ 1 carbohydrate      sized to the day's remaining budget
+ 1 flavour/fat       oil, dressing, nuts, sauce — measured, this is where days leak
```

Deciding the protein anchor first is the whole trick. Everything else can be scaled up or down to
land the calories; protein cannot be recovered later in the day without effort.

**Breakfast** is where most people are 20-30 g short. The fixes, in order of how well they land:
Greek yogurt or quark with fruit and oats; eggs or an egg-white-heavy omelette; a protein smoothie
for people who don't want to eat early; savoury options built on paneer, tofu or leftover dinner
protein — there is no rule that breakfast must be breakfast food, and for people who dislike
breakfast this is often the unlock.

**Lunch** carries the constraint of being eaten at work. Batch-cooked protein plus grains plus a
salad box travels well and takes ten minutes to assemble the night before. If they buy lunch,
plan what they will buy rather than pretending they'll start carrying one.

**Dinner** is the meal families eat together and the one people most want to be normal. It is
also where variety should live, because it is the meal with the most cooking time attached. Work
with what the household already eats, adjusting the protein portion up and the oil and starch
portion down, rather than putting one person on separate food.

**Snacks** are optional. Some people do better with three meals, some with four or five. Ask.
Where snacks exist, make them protein-carrying rather than decorative: yogurt, a boiled egg,
roasted chana, edamame, cottage cheese, a shake, fruit with a protein side.

## The shape of a survivable week

The template that consistently survives contact with a real week:

- **3-4 breakfasts on rotation.** Breakfast is eaten under time pressure and benefits from being
  nearly automatic. Novelty here buys nothing.
- **2-3 lunch formats**, built from batch-cooked components rather than distinct recipes.
- **5-7 dinners**, which is where variety and enjoyment live.
- **One planned meal out**, in the numbers.
- **One fallback meal**, named in advance.

That is roughly 12-15 distinct dishes across a week, not 21. `scripts/plan_check.py` flags the
week when the distinct-food count climbs past what a normal person will shop for and cook.

Repetition is not a failure of imagination. It is how adherence is achieved in practice — people
who lose weight and keep it off eat a fairly narrow rotation of foods they like. Frame it that
way, because a plan that looks repetitive can otherwise read as lazy work.

## Batch cooking

The single highest-leverage habit, and worth writing into the plan as a scheduled task rather
than a suggestion.

**What batches well**: cooked grains (rice, quinoa, bulgur), legumes and beans, roasted vegetables,
grilled or baked chicken, mince-based dishes, dal, boiled eggs, marinated tofu or paneer, soups.

**What doesn't**: salads dressed in advance, anything fried for crispness, fish beyond a day.

**A realistic session** is 60-90 minutes on a Sunday producing: one large batch of protein, one
grain, two roasted vegetable trays, and one sauce or dressing that ties them together. That is
lunches covered and dinners half-built.

**The variation trick** is to keep the components constant and change the seasoning. The same
chicken and rice becomes a burrito bowl, a stir-fry, a curry or a salad depending on sauce and
sides. This gets variety in the eating without variety in the cooking, which is exactly the
trade-off you want.

## Eating out and ordering in

Plan it in. A person eating out twice a week for the rest of their life needs a strategy, not an
instruction to stop.

**The general moves**, which work almost anywhere: pick the protein first and ask for it grilled,
roasted, baked, steamed or tandoori rather than fried or in a cream sauce. Get sauces and
dressings on the side. Order a vegetable side deliberately. Skip either the bread basket or the
dessert, not necessarily both. Drink water alongside anything else.

**Rough per-cuisine notes**, adapted to whatever they actually eat:

- **Indian** — tandoori and grilled items, dal, chana, plain roti over naan or paratha; the
  calorie load is in the cream, ghee and butter-based gravies rather than the spice.
- **Italian** — grilled protein and salad; if pasta, a tomato or seafood base over cream, and
  expect a restaurant portion to be two to three home portions.
- **Chinese and other East Asian** — steamed rather than fried, sauce on the side, steamed rice
  over fried; broth-based soups are excellent value.
- **Fast food** — grilled chicken items, skip the large fries and the sugary drink. Most chains
  publish full nutrition data, which makes this the *easiest* place to eat to a target, not the
  hardest.
- **Buffets and weddings** — one plate, protein and vegetables first, then decide about the rest.

**The day-around adjustment**: shifting a couple of hundred calories from earlier in the day to
the meal out is reasonable planning. Skipping food all day to "save up" is not — it reliably
produces a much larger meal and a miserable afternoon.

## Alcohol

Handle it factually rather than moralistically, because the alternative is people leaving it out
of what they tell you.

7 kcal per gram, no useful nutrients, and it suppresses fat oxidation while it's being cleared.
The larger practical effect is usually second-order: it lowers restraint, and the food eaten
around drinking is where the real damage is.

If someone drinks regularly, budget for it. Spirits with a zero-calorie mixer are the cheapest
option at roughly 60-70 kcal a measure; dry wine is around 120 kcal a glass; beer runs 150-250 a
pint. Put a realistic number of drinks in the weekly plan rather than a zero that everyone knows
is fiction.

## The bad-day fallback

Name this explicitly in the plan. It is a small piece of the document that does a large amount of
work, because the alternative to a fallback is not a perfect day — it is an abandoned week.

The specification: **under ten minutes, no real cooking, at least 30 g of protein, made of things
that keep.** Some shapes — Greek yogurt with fruit and nuts; a protein shake with a banana and
peanut butter; scrambled eggs on toast; canned tuna or beans on toast with a bag of salad; a
microwaved pouch of grains with pre-cooked chicken; boiled eggs with fruit.

Say plainly that using it is following the plan, not breaking it. People who believe an imperfect
day has ruined the week tend to abandon the week.

## Shopping lists

Generate it from the plan rather than as a generic list, with quantities for the week, grouped by
where things are in a shop:

```
Produce      spinach 400 g, tomatoes 6, onions 4, apples 7, bananas 6, salad leaves 2 bags
Protein      chicken breast 1 kg, eggs 12, Greek yogurt 1 kg, firm tofu 400 g
Pantry       rolled oats 500 g, brown rice 500 g, chana dal 500 g, olive oil, spices
Frozen       peas 500 g, mixed berries 500 g
```

Two things that make it actually useful: give quantities for the household, not the individual,
if others eat the same food — and mark the two or three items that are the plan's backbone, so if
the shop is short on something they know what has to be substituted rather than skipped.

## Presenting the plan

**Lead with the plan.** Numbers, template day, week, shopping list. Caveats once, near the top,
briefly.

**Show protein per meal** in the tables. It is the number that must be hit, so it should be
visible everywhere rather than buried in a daily total.

**Use their vocabulary.** If they said "roti", write roti, not "flatbread". If they call the
evening meal dinner, don't write supper. It sounds trivial and it strongly affects whether the
document feels like it was written for them.

**Portions in usable units.** Grams where accuracy matters — meat, paneer, oil, grains — and
household measures everywhere else. Requiring a scale for lettuce is how a plan gets abandoned in
week one.

**Explain two or three choices.** Not every line, but enough that the plan teaches rather than
dictates: why breakfast changed, why protein is at each meal, why the fallback exists. Someone who
understands the reasoning can adapt the plan when life moves; someone following instructions
cannot.
