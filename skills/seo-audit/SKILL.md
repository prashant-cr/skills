---
name: seo-audit
license: MIT
description: In-depth SEO audit of a live website, plus a sequenced plan to reach top rankings and the keywords the site can realistically win. Crawls for indexation, technical, on-page and internal-linking faults with evidence attached to every finding, mines Search Console for striking-distance and cannibalisation wins, and judges keyword winnability from who currently ranks rather than from an invented difficulty score. Use whenever the user mentions SEO, search rankings, organic traffic, ranking on Google, keyword research, why their site is not indexed or lost traffic, meta tags, sitemaps, robots.txt, Core Web Vitals, competitor rankings, content strategy for search, or asks how to get their website to the top of Google — even if they only paste a URL and ask what is wrong with it.
---

# SEO audit and ranking plan

Produces three things: an audit of what is actually wrong with a specific site, a
shortlist of keywords that site can realistically win, and a sequenced plan that
says what to do first and why.

Most SEO advice fails in one of three ways, and all three are avoidable:

- **It is a checklist nobody checked.** "Add meta descriptions, improve page
  speed" applies to every site ever built, which is what makes it worthless.
  Every finding here carries a URL and an observed value.
- **It invents numbers.** Search volumes and difficulty scores are easy to
  produce from memory and impossible to distinguish from real ones. Someone then
  allocates a budget against them. See *Numbers you may and may not state*.
- **It targets keywords the site cannot win.** Volume says what a term is worth
  if you win it and nothing about whether you can. Recommending a head term to a
  young site burns a year.

## Numbers you may and may not state

This is the rule that keeps the rest honest, because a fabricated metric is
indistinguishable from a real one once it is in a slide.

Label every figure as one of:

- **Measured** — it came out of a script run in this session, or a file the user
  supplied. Say where. "TTFB 1,240 ms (crawl, 12 Aug)".
- **Sourced** — it came from a tool or page fetched now. Name the tool and date.
- **Estimated** — your judgement. Give a band, not a point value, and say what
  it rests on.

Never state a monthly search volume or a keyword-difficulty score as a bare
number unless it came from a tool in this session. Without one, use bands —
**head / mid / long-tail** — and say the band is a judgement. A user who wants
real volumes needs Search Console, Keyword Planner, or a paid tool, and telling
them so is more useful than a plausible invention.

Never promise a position or a date. "Rank #1 in three months" is not a
forecastable claim. Commit to the work and the leading indicators instead.

## Workflow

### 1. Establish what winning means

Ask before auditing, because the same site gets a different plan depending on
the answers, and a crawl alone cannot tell you any of them:

- What does the site sell or do, and which pages make money?
- Which country and language is the audience in?
- Who are the two or three competitors that outrank them?
- Is there Search Console or analytics access? *(This changes the audit more
  than anything else — ask explicitly, and see step 3.)*
- Anything already tried, and any recent change — a migration, redesign, or
  traffic drop with a date?

Start the crawl while waiting; it takes minutes and needs only the URL. But do
not deliver a plan built on assumed answers. If the user cannot answer, state
the assumption at the top of the report so a wrong one is visible and cheap to
correct.

**When the user asks to "rank #1 for X":** take the goal seriously, then make it
concrete. Establish what currently ranks for that term (step 4). If the top ten
are entrenched authorities and the site is new, say so plainly, in one sentence,
with the evidence — and pivot to the terms that *are* reachable, which is what
they actually wanted. That is a better answer than agreeing, and a far better
one than a lecture.

### 2. Crawl the site

```bash
python3 scripts/crawl_site.py https://example.com --max-pages 60 --delay 1.0 --json crawl.json
```

Reports per page: status and redirect chain, title, meta description, H1s, word
count, canonical, meta robots, images missing alt, structured data, internal
links and TTFB. Site-wide: robots.txt, sitemaps, HTTP/HTTPS and www
canonicalisation, and whether unknown URLs return a real 404. It then groups
findings by severity — indexation blockers first, polish last.

Raise `--max-pages` for a fuller picture on a big site; the report says how many
URLs it discovered but did not reach, and findings only ever describe the pages
actually crawled. Say that in the report rather than implying full coverage.

Crawl **once** and pass `--json`, then read that file for the per-page detail.
Re-running the crawler to check one more thing costs the user's time and the
target's bandwidth for data already on disk.

`--delay` is politeness on someone else's server; keep it at 1s or above unless
the user owns the site. Use `--ignore-robots` only when they do.

Read the findings, do not relay them. Two judgements matter most:

**Is a "problem" deliberate?** A `noindex` on a staging path, a thin tag page, a
canonical consolidating duplicates — all correct. Flagging them as faults
destroys trust in the rest of the report. Ask, or mark as "verify intent".

**Which findings actually move traffic?** Missing alt text on 40 images and one
`noindex` on the main service page are not comparable, and a report that lists
them together gets ignored. `references/technical-seo.md` covers how to
interpret each finding, plus JavaScript rendering, canonical and hreflang
debugging, index-coverage triage and Core Web Vitals — read it when the crawl
surfaces something you need to explain or when the site is a single-page app.

### 3. Get the ground truth

Search Console is the only free record of what the site *actually* ranks for,
and skipping it in favour of guessing is the biggest single quality gap between
a real audit and a generated one. Ask the user to export
**Performance → Export → CSV** (with the page dimension if possible).

```bash
python3 scripts/gsc_opportunities.py Queries.csv --compare last-quarter.csv
```

It surfaces three things that are invisible by eye:

- **Striking distance** — queries at positions 4-20. These already have
  relevance and impressions; they need a nudge, not a new page. Cheapest wins
  on the site, and almost always the right place to start.
- **Click problems disguised as ranking problems** — a query at position 3
  taking 1% of clicks does not need links, it needs a better title. Diagnosing
  that as a ranking problem is the most expensive mistake in the discipline.
- **Cannibalisation** — two URLs alternating on one query, splitting the signal.

With no Search Console access, say clearly what that costs: no view of current
rankings, so opportunity sizing drops to judgement. Continue — a crawl-based
audit is still worth doing — but do not disguise the gap.

### 4. Find the keywords, by looking at the SERPs

Winnability is decided mostly by one thing that is free to check: **who
currently ranks**. A top ten of strong, on-intent pages from established
domains is closed for now, whatever any difficulty score says. A top ten
containing forum threads, outdated posts, or pages that miss the intent has a
door in it — and those are the terms where a small site beats a big one.

Build the candidate list from what the site already has and what its market
searches: Search Console queries at any position, competitor page titles and
navigation, autocomplete and "people also ask", the site's own search logs,
support tickets and sales objections. `references/keyword-research.md` covers
sourcing candidates without paid tools, classifying intent, and reading a SERP
for openings — read it before scoring anything.

Then **search each shortlisted term** and record what is on page one: the type
of each result (competitor, publisher, forum, thin, off-intent, marketplace),
roughly how authoritative it is, and which SERP features are present. This is
the input that cannot be reconstructed later, and guessing it produces a
confident number resting on nothing.

### 5. Score winnability

```bash
python3 scripts/keyword_fit.py --example > keywords.json   # documented format
# fill in the site's authority and the SERP evidence, then:
python3 scripts/keyword_fit.py keywords.json --json scored.json
```

Scores each term 0-100 on authority gap, openings in the SERP, existing assets,
topical depth and how many clicks survive the SERP features — then tiers them
**Now / Next / Later / Skip** with a timeline. It refuses to score any term
without SERP evidence, and says so.

Two outputs matter as much as the ranking. It names the intersection of winnable
and commercially valuable, which is the actual working set. And when nothing is
winnable inside six months, it says so — a real finding meaning the constraint
is authority, not keyword choice.

Sanity-check the tiers against what you know. The score ranks candidates against
each other *for this site*; it is not a difficulty metric and does not transfer.

### 6. Sequence the plan

Order the work by when it pays back, not by how it reads. The default sequence,
which holds for most sites:

1. **Unblock indexation.** Anything stopping pages from being indexed or
   crawled. Nothing else matters until this is done, and it is usually a
   same-day fix.
2. **Harvest striking distance.** Existing pages at positions 4-20. Fastest
   measurable traffic on the whole list, typically weeks.
3. **Fix click problems.** Titles and descriptions on pages that already rank.
   A day's work, and the results show up as soon as Google recrawls.
4. **Resolve cannibalisation and duplication.** Consolidate competing URLs.
5. **Upgrade existing pages** that target Now-tier terms but underperform.
6. **Build new content** for Now and Next terms, in clusters rather than
   scattered one-offs.
7. **Authority**: digital PR, partnerships, the genuinely linkable asset.
   Slowest to pay back, and the binding constraint on everything above once the
   site's own house is in order.

Give each item an owner-shaped effort estimate (hours, days, weeks), and state
what it depends on. If the user asked for 90 days, fit items 1-5 inside it and
put 6-7 on the horizon — a plan that front-loads new content is the standard
wrong answer, because it spends the first three months producing nothing
measurable while the cheap wins sit untouched.

`references/content-and-authority.md` covers content briefs, refreshing decayed
pages, internal linking, and which link-building approaches still work — read it
when writing the content or authority portion of the plan.

For ecommerce, local, SaaS or publisher sites, the priorities shift
substantially (facets and pagination, Google Business Profile, programmatic
pages, news indexing). Read `references/site-types.md` when the site is one of
these.

### 7. Report

```markdown
# SEO audit: <site>

**Assessment:** <one or two sentences: where the site stands and the single
biggest constraint on it>
**Audit basis:** <N pages crawled on DATE; Search Console DATE RANGE or "not
available"; assumptions made>

## What to do first
<The three highest-impact actions, each with the evidence and the expected
effect. If a reader stops here they should still have the plan's core.>

## Findings
| # | Finding | Evidence | Impact | Effort |
| - | ------- | -------- | ------ | ------ |
<Ordered by impact. Evidence is a URL and an observed value, never a
generality. Note anything that may be deliberate.>

## Keywords worth targeting
| Term | Intent | Winnable | Why | Value |
<From keyword_fit, grouped Now / Next / Later. "Why" cites the SERP —
"three forum results in the top five" — not the score.>

Terms deliberately not targeted: <the head terms they expected to see, with
one line on what would have to change first.>

## Plan
### Now (weeks 1-4)
### Next (months 2-3)
### Later (months 4+)
<Each item: action, why it is in this slot, effort, dependency.>

## How to tell if it is working
<Leading indicators with a checking cadence: impressions on target queries,
average position for the striking-distance set, indexed page count. Not
"traffic will increase".>

## What was not checked
<Honest limits: pages beyond the crawl cap, Core Web Vitals field data,
backlink profile, anything needing paid tools or access you did not have.>
```

## Judgement calls

**Traffic is not the goal.** A plan that doubles traffic to pages nobody buys
from has failed. Weight everything by commercial value; a term with a tenth the
volume and a buyer behind it wins.

**A traffic drop needs a date before a diagnosis.** Establish when it started,
then look for what changed on that date — a migration, a redesign, a robots
change, an algorithm update, a lost link. Auditing a dropped site as if it were
a fresh one buries the cause under fifty generic findings.

**Distinguish "not ranking" from "not indexed".** They look identical to the
user and need opposite responses. Check indexation first — every ranking
question is downstream of it.

**Cite Google's documented positions, not folklore.** SEO carries a large body
of confident claims that were never true or stopped being true years ago.
Where a common belief is contested — keyword density, a magic word count,
domain age as a ranking factor — say what is actually established and what is
not.

**Small sites should go narrower, not broader.** The instinct on a low-authority
site is more content on more topics. The opposite works: pick one cluster,
cover it more completely than anyone ranking, earn the topical authority, then
expand. Breadth without authority produces pages that never rank at all.

**AI overviews change what a ranking is worth.** For informational queries an
overview can take most of the clicks even at position 1. That is a reason to
weight commercial and transactional intent more heavily, and to say so when
recommending an informational term.
