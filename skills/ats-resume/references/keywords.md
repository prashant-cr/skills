# Using a job description honestly

Read this when the candidate supplies a posting.

## What keywords actually do

Not a match percentage that gates your application. What they do is make the candidate findable:
a recruiter with 400 applications runs a search — `Kubernetes AND Terraform`, or the requisition's
own required-skills filter — and works through what comes back. The candidate whose resume never
contained the string is not rejected; they are absent.

That reframes the job. You are not trying to hit a threshold. You are trying to ensure that every
term a recruiter might plausibly search, which the candidate can genuinely back, appears
somewhere in the document in a form that matches.

Three practical consequences:

- **Match is mostly exact-string.** A resume saying "K8s" does not answer a search for
  "Kubernetes". Write the full term, with the short form alongside it: `Kubernetes (K8s)`,
  `Search Engine Optimization (SEO)`, `Certified Public Accountant (CPA)`.
- **Nouns matter more than verbs.** Recruiters search tools, technologies, certifications,
  methodologies and domain terms — not "collaborated" or "spearheaded".
- **Placement matters less than presence, but not none.** A term appearing only in a skills list
  is weaker to a human than the same term inside a bullet showing what was done with it. Aim for
  both where it is true.

## The workflow

Run the checker with the posting attached:

```bash
python3 scripts/ats_check.py resume.docx --jd job_description.txt
```

It reports the terms the posting repeats, which of them appear in the resume, and which do not.
Then sort the missing terms into three piles — this sorting is the entire job, and it is
judgement you cannot delegate to the tool:

**1. Present but phrased differently.** The candidate has it; the words do not match. This is
free and you should always fix it. Their "AWS" against the posting's "Amazon Web Services"; their
"CI/CD pipelines" against "continuous integration". Write the posting's term, keeping theirs
where it reads naturally: `Amazon Web Services (AWS)`.

**2. Genuinely theirs, but buried or missing.** They have done it, and it is somewhere in a
project or an old role, or nowhere at all because they did not think it mattered. Surface it.
This is the most valuable pile and the reason to read the posting carefully — candidates
systematically omit things they consider unremarkable.

**3. They do not have it.** It does not go in. This is the pile that separates honest work from
the alternative, and it goes back to the candidate as a question:

> The posting leans hard on Terraform and I did not find it anywhere in your history. If you have
> used it — even on a side project or briefly at Swiggy — tell me where and I will place it. If
> not, that is worth knowing: it is a stated requirement, so expect it to come up.

Sometimes the answer is "yes, for a year, I forgot to mention it". Sometimes it is a real gap
they now know about before the interview. Both outcomes are useful; silently inserting the term
produces neither.

## Why stuffing loses

The tricks circulate constantly — a block of keywords in white text, a 1pt paragraph of skills at
the bottom, terms hidden behind an image, the whole job description pasted in invisible text.

They fail on their own terms, before you get to the ethics:

- **Extraction ignores formatting.** White 1pt text comes out identical to body text. That is the
  entire mechanism these tricks depend on, and it is the mechanism that exposes them: the parsed
  profile the recruiter reads shows the keyword block in plain view, at the bottom, with no
  context. It looks exactly like what it is.
- **It is a known pattern.** Recruiters have seen it. Several large ATS flag it, and some
  employers keep a permanent internal note on the candidate.
- **Winning is losing.** A term that gets someone into a screen for a skill they do not have
  costs them an hour and costs the recruiter one, and it makes the next application to that
  company harder.

If a candidate asks for it directly, do not moralise — explain the extraction mechanism, show
them what the parsed text looks like, and offer the version that works. Usually they were told it
was standard practice by someone confident.

## Tailoring per application

If the candidate is applying to several roles, do not build one resume that covers all of them —
that produces a document optimised for nothing, with a skills list nobody believes.

Keep one full master version with everything, and cut down from it per posting: reorder the
skills groups so the relevant ones lead, expand the bullets on the most relevant role and trim
the least relevant, adjust the summary's last line to the target. The history never changes; the
emphasis does.

This is also the point at which file naming earns its keep — `Priya_Sharma_Resume_Stripe.docx`
saves the candidate from sending the wrong tailored version, which is a much more common
self-inflicted wound than any parsing failure.

## A note on the "match score" tools

Candidates often arrive having run their resume through a free scanner that gave them a number,
frequently a low one, and they want that number moved. Worth saying plainly: those scores are
computed by the scanner's own weighting, not by the employer's ATS, and two scanners will
disagree wildly about the same resume. They are useful as a checklist and meaningless as a
verdict.

What can be said honestly is what this skill's own checker measures — whether the file parses
correctly — and which terms from this specific posting are present or absent. Both are facts.
Neither is a probability of getting an interview, and offering one would be inventing a number,
which is the thing this skill exists not to do.
