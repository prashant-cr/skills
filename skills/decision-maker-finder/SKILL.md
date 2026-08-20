---
name: decision-maker-finder
license: MIT
description: Finds the person at a named company who can actually approve what you are selling, plus the champion who will push it and the gatekeeper who can kill it. Works out who decides from deal size, category and company size instead of defaulting to the CEO, grades every name by the evidence and its date because a confidently wrong name burns the one cold approach you get, and infers then verifies a work email rather than guessing one. Deep on India, where statutory MCA directors and a generic info@ address routinely hide the real buyer. Use whenever the user asks who the decision maker is, wants a lead, contact or the right person at a company, mentions cold outreach, prospecting, B2B sales, sales navigator, finding someone's email or phone, who to pitch, who signs off, who owns the budget, or getting past the gatekeeper — including bare asks like "who do I talk to at Acme" or a pasted company website.
---

# Decision maker finder

The user has a company they want to sell to. This finds **who to contact**, why
that person and not the obvious one, who else has to agree, and how to reach
them — with the evidence for each name and how fresh it is.

If the user has not yet decided which companies to target, this is the wrong
job. Building a target list from an ideal-customer profile is prospecting;
this starts once a company is named.

## Why "the CEO" is usually the wrong answer

Searching a company name and returning whoever holds the grandest title feels
like the task. It fails three ways, and all three are expensive.

- **Title is not authority.** The person who can approve a purchase is a
  function of **what you sell, what it costs, and how big the company is** —
  not a fixed rung on the org chart. A ₹40,000/year tool is approved by a team
  manager; a ₹40 lakh implementation needs a CXO and finance. Aim too senior
  and you are forwarded into a void. Aim too junior and you spend two months
  coaching someone who never had budget.

- **There is no "the" decision maker.** B2B purchases clear a committee. Miss
  the security reviewer or procurement and the deal does not get rejected — it
  stalls at week six with nobody willing to say why. The person who can say
  **yes** and the people who can say **no** are usually different people, and
  you need both before you write the first email.

- **The information is stale by default.** Titles lag reality by months,
  people leave, and the contact databases everyone pays for are full of roles
  that ended two years ago. A confident wrong name does more damage than an
  honest gap, because cold outreach is close to a single-shot channel — a
  misaddressed first email is rarely survived by a second.

There is a fourth, specific to India and covered in `references/india.md`:
**a director on the MCA filing is often not a decision maker**, and the person
who decides often holds no directorship at all.

## Names you may and may not state

Every person, title and contact detail you report is either **retrieved this
session, with the source and its date**, or it is marked as inference. There is
no third category.

Never supply a name from memory. Who runs marketing at a mid-size company is
exactly the fact that changes without any public announcement, and a
remembered one is wrong in the way that costs the most: it is specific,
plausible, and it sends a personalised email to someone who left.

When you cannot establish a name, **say the seat is unfilled in your research
and name the seat**. "The person who owns this is the VP Engineering; I could
not confirm who currently holds it, here is where to look" is a usable answer.
An invented name is not.

Grade every identification, and put the grade next to the name:

| Grade | What backs it |
| --- | --- |
| **Confirmed** | The person or their current employer states the role, dated within ~6 months |
| **Probable** | Two independent secondary sources agree, or one strong source older than 6 months |
| **Inferred** | Derived from org structure or pattern; no direct evidence for this individual |

## How the name may be obtained

The method constrains the result, so settle it before searching. All of this
works on **public and professional-capacity information**, which is what B2B
prospecting legitimately runs on.

Do not do these, and do not help build them:

- **Pretexting.** Calling a receptionist pretending to be a courier, a
  candidate, or an existing customer to extract a direct line. It is deception,
  it is the fastest way to get a company to blacklist a domain, and in several
  jurisdictions it is unlawful.
- **Scraping LinkedIn.** Their terms forbid it and they enforce. Read profiles
  normally, use Sales Navigator if the user has it — do not write a crawler.
- **Buying scraped-database dumps** of unclear provenance, or anything sold as
  "verified personal mobile numbers".
- **Personal contact details.** Personal email, home address and personal
  mobile are out of scope even when findable. Work identity, work channels.
- **Circumventing an opt-out.** Someone who has unsubscribed or asked not to be
  contacted is done, through every channel, permanently.

`references/compliance.md` covers what each region actually requires — India's
DPDP Act, GDPR's legitimate-interest basis for B2B, CAN-SPAM, CASL, and the
TRAI DND registry for Indian calls and SMS. Read it before advising on
outreach in the EU, Canada or India, where the rules bite hardest.

## Workflow

### 1. Pin what is being sold, and for how much

This is the input that decides everything downstream, and it is the one users
skip. Ask these together in one message, then proceed:

1. **What are you selling?** The category sets which function owns the budget.
2. **Roughly what does it cost per year?** Sets the seniority. A range is fine.
3. **Who is it for — whose job changes?** That person is your champion, and
   they are usually not the buyer.
4. **Is this a new line item or replacing something?** Replacements have an
   incumbent, and the incumbent's owner is either your champion or your blocker.
5. **Do you have any existing connection?** A customer, an investor, an alum,
   an ex-colleague. A warm path beats a perfect cold email, and this is the
   only question whose answer can end the search early.

If the user does not answer, **state the assumption and continue.** Deliver the
map with assumptions visible rather than blocking. Guessing a mid-market deal
size and saying so is far more useful than a question they answer tomorrow.

### 2. Map the company before naming anyone

You cannot pick the right seniority without knowing the shape of the company.
Establish, from live sources: headcount band, revenue band if disclosed,
funding stage and last raise, whether it is founder-run or professionally
managed, group or subsidiary structure, and how centralised buying looks.

Two structural facts change the answer more than anything else:

- **A subsidiary may not buy for itself.** In Indian conglomerates and global
  groups, IT, HR and marketing spend is often decided at the parent. Selling
  into the subsidiary that has no budget is a common dead end.
- **Founder-run companies below roughly 200 people concentrate approval at the
  founder** regardless of what the titles say. Above that, real delegation
  usually exists. This threshold moves, but the direction is reliable.

**Check for a live regulatory filing before anything else.** A company that has
filed for an IPO, or files annual reports, has just published a document written
under legal liability that names its senior management with exact titles and
joining dates. A DRHP, prospectus or annual report converts an opaque private
company into the best source available in any market, and it will contain things
no directory has: the real group structure, segment leadership, headcount by
function, and often the product roadmap. It is worth searching for specifically —
"company name DRHP", "prospectus", "annual report", the exchange filing archive —
before falling back on aggregators. This single check has repeatedly been the
difference between a sourced answer and a plausible one.

**Establish which legal entity actually signs.** The brand and the contracting
party are frequently different, and the entity on the purchase order is the one
that matters for the MSA, the GST invoice and the security review. Consumer
brands in particular often trade under a name that appears in no filing. Get the
registered name and, in India, the CIN.

### 3. Build the buying committee, not a contact

Name the seats before you name people. Five roles matter:

| Role | What they do | Failure if you miss them |
| --- | --- | --- |
| **Economic buyer** | Controls the budget, can say yes | You have enthusiasm and no purchase order |
| **Champion** | Feels the pain, sells it internally | Nothing moves between your meetings |
| **Technical / security evaluator** | Can say no — IT, InfoSec, DPO | Killed at review, after you have invested |
| **Procurement / finance** | Owns contract and terms | Stalls for a quarter, then re-opens pricing |
| **End user** | Whose day changes | Adopted on paper, unused in practice |

**Then split those seats in two, because they are not the same kind of problem.**
Some are people you must *convince*; the rest are checkpoints you must *clear*.
Procurement and security review rarely need selling — they need scheduling, and
the questionnaire answered early. Treating a gate as a stakeholder is how a
three-week deal becomes a three-month one, and it is the standard way a small
purchase at a large company gets over-engineered.

This matters most in the case people get wrong in both directions: **a small
deal at a big company.** A ₹9 lakh tool at a company doing ₹15,000 crore is
approved by one operator — there is no committee to sell. But it still passes
vendor onboarding, so the gate is real even though the decision is not shared.
Say which is which; do not present five seats as five people to win over.

```bash
python3 scripts/buying_committee.py --category saas --acv 1200000 --currency INR --headcount 400 --founder-run no
```

The script maps deal size, category and headcount onto the likely seats,
names the function that owns each, and flags which one is the entry point. Use
it to decide **who to approach first** — that is rarely the economic buyer.
The usual best opening is the champion, because they will tell you who the
economic buyer actually is, and that beats any external research.

### 4. Name the people, with evidence and a date

Work the sources in reliability order — `references/sources.md` has the full
hierarchy and what each is good and bad at. In short: company sources and the
person's own statements beat directories; anything undated is weak.

For each seat, record the name, exact current title, how long in role, the
source URL, and the date that source reflects. **Note when a source is more
than a year old** — that is the difference between a name you can use and a
name you must re-check.

Check for departure signals before you commit to a name: a title change, a
"formerly" phrasing, an updated leadership page that dropped them, a
replacement announced. People leave quietly and the internet updates slowly.

### 5. Find and verify the contact route

Work outward from the strongest channel.

**A warm introduction outranks everything else.** Check shared investors,
customers, portfolio companies, alma mater and past employers before spending
effort on an email address.

**For work email, infer the pattern then verify — never guess and send.**
Collect two or three known-good addresses at the domain from public sources
(press releases, careers pages, conference speaker listings, open-source commit
history, PDF document metadata, WHOIS), derive the pattern, then apply it:

```bash
python3 scripts/email_pattern.py --domain acme.in --known "priya.sharma@acme.in,r.iyer@acme.in" --name "Arjun Venkataraman"
```

The script infers the dominant pattern, ranks candidates, and handles the name
forms that break naive first-dot-last logic — mononyms, initial-prefixed South
Indian names, and surnames long enough to be truncated by the mail system.

Then **verify before sending.** An unverified guess that bounces damages the
sending domain's reputation, which quietly degrades deliverability for every
future email including the ones to companies you got right. Use a legitimate
verification service; treat "accept-all" domains as unverified, because they
answer yes to everything.

**Phone.** The company switchboard and a named person is a legitimate route.
Direct lines published by the company are fair use. In India, check the TRAI
DND registry position before any call or SMS campaign — see
`references/compliance.md`.

### 6. Deliver the map, the confidence, and the opening

Give the user the committee, the entry point, the evidence grade on each name,
and a specific first approach that references something real about that person
or company. `references/outreach.md` covers what makes a first touch land and
the patterns that mark an email as bulk before it is read.

State what you could not verify. That section is not an apology — it is where
the user learns which name to double-check before it costs them the account.

## Report structure

```markdown
# <Company> — decision maker map

**Selling:** <what, at what ACV>
**Company:** <headcount, stage, structure, founder-run or professional>
**Entry point:** <name, title> — <why start here>

## The buying committee
| Role | Person | Title | Grade | Source (date) |
| Economic buyer | | | | |
| Champion | | | | |
| Technical/security | | | | |
| Procurement/finance | | | | |

## Why this person and not the CEO
## Reaching them
| Channel | Detail | Verified? |
## Warm paths
## The opening
## What I could not verify
```

## Failure modes

**Returning the most senior name.** The task is who can approve *this* purchase,
not who runs the company. If the answer is the CEO, that must be a conclusion
from deal size and company size, not a default.

**One name, no committee.** A single contact with no view of who can veto is
how a deal reaches week six and dies without explanation.

**Undated evidence.** A title with no date attached is a claim about the past
presented as the present.

**Guessing an email and calling it found.** A pattern-derived address is a
hypothesis. Unverified, it is a bounce risk to the user's own domain.

**Treating an MCA or Companies House director as the buyer.** Statutory
directorship and operational authority are different things and frequently
different people.

**Ignoring the parent company.** The budget may not sit where the user is
pointing.

## Judgement calls

**Say when the seat is empty.** Some companies genuinely have no one in the
role — early-stage companies often have no security reviewer, and no
procurement function below a few hundred people. Naming the absence is useful;
inventing an occupant is not.

**Small companies collapse the committee.** Under about 50 people, the founder
is frequently all five seats. Say so and stop constructing an org chart that
does not exist.

**Watch for the buying trigger.** A recent raise, a new hire into the relevant
seat, a compliance deadline or a competitor's public failure changes whether
anyone is listening at all. A perfect contact at the wrong moment still gets
nothing, and a new person in seat is the single best timing signal there is.

**When the trail is cold, say so early.** Some companies are genuinely opaque —
no leadership page, thin professional presence, a holding structure. Two
honest sentences and a recommendation to go through the switchboard beats
twenty minutes of searching that produces a guess.

## References

- `references/india.md` — read when the target is an Indian company: MCA and
  ROC filings, what a statutory director actually is, GST and Tofler/Zauba,
  title inflation, and why the website only lists info@.
- `references/sources.md` — read when deciding where to look: the source
  hierarchy by reliability, what each source is good and bad at, and the
  regional registries outside India.
- `references/compliance.md` — read before advising on any outreach, and always
  for the EU, UK, Canada or India.
- `references/outreach.md` — read when writing the first touch.

## What this is not

This finds who to contact and how to reach them legitimately. It does not write
bulk campaigns, build contact databases for resale, or obtain details a person
has chosen not to make available in a professional context.

Being findable in a professional capacity is not consent to be contacted
without limit. The user gets one considered approach and an easy way to be told
no — and honouring that no, permanently and across every channel, is part of
the job, not a courtesy.
