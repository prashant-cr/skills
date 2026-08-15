# Keyword research without paid tools

How to build a candidate list, judge intent, and read a SERP for openings — the
inputs `keyword_fit.py` scores.

- [Where candidates come from](#where-candidates-come-from)
- [Search intent](#search-intent)
- [Reading a SERP](#reading-a-serp)
- [Judging the site's own authority](#judging-the-sites-own-authority)
- [Volume without a volume tool](#volume-without-a-volume-tool)
- [Clusters, not lists](#clusters-not-lists)
- [Common mistakes](#common-mistakes)

## Where candidates come from

Ordered by value, and the first two are free and better than anything a tool
sells:

**1. Search Console.** Every query the site has ever shown for, including the
hundreds it ranks for on page three that nobody noticed. Filter to positions
4-20 for the striking-distance set; sort by impressions with low clicks to find
demand the site is failing to convert. This is real demand from the site's real
market — it beats any keyword database because it is not a guess.

**2. The business itself.** Sales objections, support tickets, the questions
asked on every call, the site's internal search logs. These are the words
customers actually use, which routinely differ from the words the company uses.
Terms sourced this way convert far better than anything found by volume.

**3. Autocomplete and SERP furniture.** Type the seed term into Google and read
the suggestions. Then "People also ask", "Related searches" at the foot of the
page, and the autocomplete after adding a space, a question word, or each letter
of the alphabet. This is Google telling you what people search, for free.

**4. Competitors' own structure.** The pages they built are the terms they chose
to target. Read their navigation, page titles, H1s, and blog categories. A
competitor with a page you lack has found demand you have not.

**5. Communities.** Reddit, Stack Exchange, industry forums, review sites, and
Amazon question sections for products. Threads with many replies are unmet
demand, and a forum thread ranking on page one for a term is the single
strongest signal of an opening.

**6. Free tools.** Google Keyword Planner (needs an Ads account; gives broad
volume bands, and exact figures only with active spend), Google Trends (relative
interest and seasonality, never absolute volume), and Search Console's own
comparison view.

## Search intent

Intent decides page type. Ranking a product page for an informational query, or
a blog post for a transactional one, fails regardless of quality — Google has
already decided what kind of page belongs there.

- **Informational** — "how to", "what is", "best way to". Wants an article,
  guide or video. High volume, low conversion, and now the intent most exposed
  to AI overviews absorbing the click.
- **Commercial investigation** — "best X", "X vs Y", "X review", "X alternatives".
  Comparing before buying. Usually a listicle or comparison page. The sweet spot
  for most businesses: real buying intent, and reachable content formats.
- **Transactional** — "buy X", "X pricing", "X near me". Wants a product,
  pricing or booking page. Lowest volume, highest value.
- **Navigational** — a brand or product name. Only winnable if it is your brand.

**Do not guess the intent — read it off the SERP.** What Google already ranks is
its ruling on what the query means. If the top ten are all comparison listicles,
a product page will not rank there no matter how good it is. If the results are
a mix, the intent is genuinely split and both formats have a route in.

Watch for intent that is not what the words suggest. "Best running shoes" often
returns publisher listicles rather than shops, meaning Google reads it as
research and a store page cannot win it directly — the way in is the comparison
content, or being featured in someone else's.

## Reading a SERP

This is the highest-value ten minutes in keyword research, and the input
`keyword_fit.py` will not score without. For each shortlisted term, search it —
ideally in the target country, in a private window — and record:

**The type of each of the top ten results.** Classify each as:

| Class | Meaning |
| --- | --- |
| `competitor` | A direct competitor's own page. Strong. |
| `publisher` | An established media or industry site. Strong. |
| `brand` | A major recognised brand. Strong. |
| `marketplace` | Amazon, Etsy, a large aggregator. Strong, hard to displace. |
| `gov` / `edu` | Government or academic. Strong and usually immovable. |
| `forum` | Reddit, Quora, a forum thread. **An opening.** |
| `ugc` | User-generated content, listings, profiles. **An opening.** |
| `thin` | A short or low-quality page. **An opening.** |
| `off_intent` | Ranks but does not answer the query. **A strong opening.** |
| `outdated` | Visibly old, dated content. **An opening.** |
| `aggregator` | Thin directory or scraped content. **An opening.** |

**Roughly how authoritative each domain is** — `new`, `low`, `medium`, `high`,
`very_high`. Without a link index this is a judgement from brand recognition,
apparent size, and whether you have heard of it. Say that it is a judgement.

**Which SERP features are present** — ads at the top, an AI overview, a featured
snippet someone else holds, people-also-ask, shopping, local pack, video pack.
These decide how many clicks survive for organic position 1, and a term whose
clicks are already spent is worth less than its volume implies.

**What the ranking pages actually contain** — format, depth, what they cover,
what they all miss. The gap they share is the argument for your page existing.

### What an opening looks like

The reliable signals that a small site can break in:

- A forum or Reddit thread in the top five. Google could not find a good page.
- Two or more results that miss the intent.
- Visibly outdated top results on a topic that changes.
- Thin pages ranking on a query that deserves depth.
- No result covering an obvious sub-question that "people also ask" shows people
  asking.

And the reliable signals that it is closed: ten on-intent pages from
recognisable domains, all recently updated, all thorough. No amount of on-page
work wins that inside a year. Score it `SKIP` and spend the effort where there
is a door.

## Judging the site's own authority

`keyword_fit.py` needs an honest tier, since real link metrics require a paid
index. Judge from:

- **Age and history** — a domain with years of consistent publishing outranks
  its raw link count.
- **Existing ranking footprint** — how many terms it already ranks top-20 for,
  from Search Console. The most reliable proxy available for free: a site
  ranking for 500 terms has authority a site ranking for 6 does not.
- **Referring domains** — free backlink checkers give a rough count. The number
  of distinct linking domains matters far more than total links.
- **Brand search volume** — whether anyone searches the brand name at all,
  visible in Search Console.

Tiers: `new` (under a year, negligible links), `low` (established but few
links), `medium` (recognised in its niche), `high` (a leading site in its
category), `very_high` (a household name). Err downward — overstating authority
produces a keyword list the site cannot deliver, which is the exact failure this
is meant to prevent.

## Volume without a volume tool

You will not have real volume figures. Do not invent them; use bands, and be
explicit that they are judgements:

- **Head** — the generic category term. Very high volume, very high competition,
  usually broad or ambiguous intent.
- **Mid** — a qualified version of the head term. Meaningful volume, real intent.
- **Long-tail** — three or more words, specific, clear intent, low volume
  individually and large in aggregate.

Long-tail terms are where a low-authority site should start, and the reason is
not only lower competition: specific queries have clearer intent, so they
convert better, and they accumulate the topical authority that makes mid-tier
terms reachable later.

Google Trends gives relative interest and seasonality without absolute numbers,
which is enough to compare two terms and to spot a dying one. Keyword Planner
gives broad bands free. Say which you used.

## Clusters, not lists

Google ranks sites on topics, not pages on keywords. A cluster is one pillar
page on the broad topic plus several pages on specific sub-questions, all
interlinked. This works because it demonstrates depth on a subject rather than
an isolated claim, and because internal links concentrate authority on the
pillar.

Practically: group candidates by the underlying topic, then check whether each
group member deserves a separate page. Two terms belong on **one** page when
the SERPs for them return largely the same results — Google is telling you it
considers them the same question. Splitting them creates the cannibalisation
that keeps both off page one.

## Common mistakes

**Volume-first selection.** The whole reason this skill scores winnability.

**Ignoring what the site already ranks for.** Striking-distance terms in Search
Console beat new research nearly every time and cost a fraction of the effort.

**Targeting a term whose SERP shows a page type you will not build.** If the top
ten are all video, an article will not rank.

**One page per keyword variant.** "Cheap running shoes", "affordable running
shoes" and "budget running shoes" are one page. Separate pages compete with each
other.

**Assuming a competitor's ranking terms are winnable.** They rank with their
authority, not yours. Their terms are a candidate source, not a target list.

**Forgetting the brand can be defended.** Competitors bidding or ranking on your
brand name is cheap traffic to reclaim, and it is often overlooked entirely.
