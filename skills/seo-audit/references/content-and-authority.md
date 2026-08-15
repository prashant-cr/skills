# Content and authority

The two slowest-paying and highest-ceiling parts of the plan. Read when writing
the content or link portion.

- [Fix what exists before writing more](#fix-what-exists-before-writing-more)
- [Content briefs](#content-briefs)
- [On-page essentials](#on-page-essentials)
- [Titles and descriptions](#titles-and-descriptions)
- [Refreshing decayed content](#refreshing-decayed-content)
- [Internal linking](#internal-linking)
- [E-E-A-T](#e-e-a-t)
- [Links that still work](#links-that-still-work)
- [AI overviews and LLM traffic](#ai-overviews-and-llm-traffic)

## Fix what exists before writing more

The instinct on receiving an SEO plan is to commission new content. It is
usually the worst available use of the first month.

An existing page ranking at position 12 has already proved relevance and earned
impressions. Improving it can reach page one in weeks. A new page starts from
nothing and takes months to be crawled, assessed and trusted. The ordering
follows:

1. Pages at positions 4-20 — improve them (highest return, weeks)
2. Pages ranking with poor click-through — rewrite titles and descriptions (days)
3. Pages that cannibalise each other — consolidate (days)
4. Pages that rank for nothing despite targeting something — diagnose: wrong
   intent, too thin, or no internal links
5. Only then: new content for gaps nothing covers

## Content briefs

A brief exists so the writer does not have to redo the research. It should
contain:

- **The target query and its intent**, read off the SERP, not assumed.
- **The page type the SERP demands** — guide, comparison, product, tool.
- **What the top five results cover**, as a list of subtopics. This is the floor:
  a page missing what all five include will not compete.
- **What none of them cover.** The reason for the page to exist. Original data,
  first-hand experience, a calculator, a clearer explanation, current
  information where theirs is stale.
- **Questions to answer**, from "people also ask" and related searches.
- **Internal links in and out** — which existing pages should link to this, with
  what anchor text, and which this should link to.
- **The primary term and natural variants.** Not a density target: use the term
  in the title, the H1, the opening, and where it genuinely belongs. Keyword
  density has not been a meaningful factor for many years, and writing to a
  ratio produces text that reads badly and ranks worse.

Length follows from covering the topic, not from a target. Match the depth of
what ranks, then add the thing they lack. Padding to reach a word count is
visible to readers and to Google.

## On-page essentials

Ordered by how much they matter:

1. **Title tag** — the strongest on-page signal, and the thing people click.
2. **Content that matches intent** — the actual determinant.
3. **H1** — one per page, describing the page, close to the title but not
   necessarily identical.
4. **URL** — short, readable, keyword-bearing. Not worth changing on an existing
   ranking page; the redirect costs more than the gain.
5. **Internal links in** — with descriptive anchor text.
6. **Headings** — a real outline, because they structure both reading and
   featured-snippet extraction.
7. **Meta description** — no direct ranking effect, real click-through effect.
8. **Image alt text** — accessibility first, image search second.
9. **Structured data** — rich result eligibility.

## Titles and descriptions

The cheapest win in SEO, and the most neglected. A page at position 3 with a
weak title loses most of its available clicks, and no amount of link building
fixes that.

**Titles.** Around 60 characters, or roughly 580 pixels — Google truncates on
width, so capital letters cost more. Front-load the term that matters. Make each
one distinct across the site; duplicates mean pages compete for the same query.
Include the brand only where it earns the space, usually on commercial pages.
Write for the click as well as the crawler: a specific number, year, or promise
outperforms a bare keyword. Google rewrites titles it finds unhelpful, and a
rewritten title is a signal your title was poor.

**Descriptions.** Around 155 characters. Treat it as ad copy — it does not
affect ranking and it does affect click-through. Include the query terms, since
Google bolds matches. Write one per page; a templated description across a
section wastes the slot entirely.

When Search Console shows a page ranking well with poor CTR, this is nearly
always the fix, and it takes minutes.

## Refreshing decayed content

Pages lose rankings gradually as competitors publish better versions and the
content ages. Refreshing beats writing new almost every time.

Find candidates by comparing two Search Console exports (`gsc_opportunities.py
--compare`), looking for pages declining in position or clicks.

A refresh that works: update facts, figures and dates; add the subtopics
competitors now cover and you do not; remove what is no longer true; improve the
title; add internal links from newer pages; and republish with an updated date
only if the content genuinely changed. Changing the date alone is transparent
and achieves nothing.

A refresh that does not work: reshuffling paragraphs, adding filler, or
appending a "2026 update" heading to unchanged text.

## Internal linking

The most under-used lever available, because it costs nothing and needs nobody's
permission.

- **Link from strong pages to pages that need help.** Authority flows along
  internal links. The homepage and best-linked pages have the most to give.
- **Use descriptive anchor text.** "Running shoes for flat feet" tells Google
  what the target is about; "click here" tells it nothing. Vary the phrasing
  naturally rather than repeating one string.
- **Link from within the content**, not only from navigation. Contextual links
  carry more weight than sitewide boilerplate — which is why the crawler flags
  pages that have only the latter.
- **Keep money pages shallow.** Three clicks from the homepage at most.
- **Build the cluster.** Sub-pages link to the pillar, the pillar links to each
  sub-page, and related sub-pages link to each other.
- **Fix orphans.** A page nothing links to cannot rank, and it is invisible to
  everyone including the people who wrote it.

When a page needs to rank and the content is already good, adding three or four
contextual internal links from relevant pages is often enough to move it, and it
takes an hour.

## E-E-A-T

Experience, Expertise, Authoritativeness, Trust. Not a ranking factor with a
score — a description of what Google's quality raters assess, which shapes what
the algorithms try to approximate. It matters most for YMYL topics (health,
finance, legal, safety), where thin anonymous content struggles regardless of
technical quality.

What demonstrates it in practice: named authors with real credentials and
biographies; first-hand experience visible in the writing — original photographs,
tested results, specific detail nobody could reproduce from other articles;
citations to primary sources; a real About page, address and contact details;
being cited by others in the field; and visible maintenance dates.

For a business site the cheapest wins are usually the dullest: put real names on
articles, publish credentials, make the company verifiably real.

## Links that still work

Links remain a major ranking factor. Most link building is a waste of money, and
some of it causes penalties.

**Worth the effort:**

- **Digital PR** — original research, surveys or data journalists will cite.
  Highest ceiling; needs something genuinely newsworthy.
- **The linkable asset** — a free tool, calculator, dataset or definitive
  reference that people cite because it is useful.
- **Being the source** — respond to journalist requests, contribute expert
  commentary.
- **Partners, suppliers, associations, sponsorships** — unglamorous, legitimate,
  and usually available immediately.
- **Genuine guest contributions** to publications with real audiences.
- **Unlinked mentions** — find where the brand is named without a link and ask.
  The highest conversion rate of any outreach.
- **Broken link building** — find dead pages others link to, publish the
  replacement, tell them.

**Not worth it, or actively harmful:** bought links from vendors, link exchanges
at scale, private blog networks, mass directory submissions, comment and forum
spam, and low-quality guest posting on sites that exist to host guest posts.
These violate Google's spam policies; the realistic outcomes are wasted money or
a manual action.

**Judge a prospective link** by whether the site has real traffic and a real
audience, whether the page would exist without SEO, and whether a reader could
plausibly click it. Relevance beats raw authority: one link from a respected
site in the exact niche beats ten from unrelated high-authority domains.

For a new site, expect links to be the binding constraint. Content can be
excellent immediately; authority cannot.

## AI overviews and LLM traffic

Two shifts worth reflecting in any current plan.

**AI overviews absorb clicks**, most heavily on informational queries with
simple answers. A term whose answer fits in a sentence may deliver little
traffic even at position 1. This is a reason to weight commercial and
transactional intent more heavily, and to favour queries needing depth,
judgement, comparison or current data — where a summary cannot substitute for
the page.

**LLM assistants are becoming a referral source.** What appears to help: clear
factual statements near the top of the page, clean semantic HTML, structured
data, being cited by sources the models already trust, and content that is
server-rendered rather than assembled by JavaScript. Much of this is ordinary
good SEO, which is convenient. Where a claim about optimising for LLM retrieval
goes beyond that, treat it as untested — the field is young and confident advice
about it is mostly speculation. Say so rather than presenting it as established.
