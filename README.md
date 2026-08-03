# Skills

Open [Agent Skills](https://skills.sh) — self-contained instruction packages that teach coding
agents to do a specific job well.

A skill is Markdown an agent reads at runtime, plus any scripts and reference material it needs.
Install one and your agent gains a capability it keeps: it knows when to reach for it, what steps
to follow, and what to check before claiming it worked.

Works with Claude Code, Cursor, GitHub Copilot, Codex, Gemini CLI, Windsurf and 20+ other agents.

```bash
# see what's here
npx skills add prashant-cr/skills --list

# install just the one you want
npx skills add prashant-cr/skills --skill stock-deep-dive
```

Skills are independent — take one, take all twelve. See [Installing](#installing) for the difference
between picking one and taking the lot.

## Available skills

### Web scraping & data extraction

| Skill | What it does |
| --- | --- |
| [`scrape-feasibility-audit`](skills/scrape-feasibility-audit) | Audits a site **before** you build a scraper — bot-detection vendor, CAPTCHA type, robots.txt rules, server- or client-rendered — then recommends tooling proportionate to what it actually found. |
| [`structured-data-extraction`](skills/structured-data-extraction) | Extracts data **without CSS selectors**, by reading what a page already publishes: JSON-LD, microdata, Open Graph, embedded state JSON, tables and feeds. Find a field by name, get a JSON path. |
| [`fix-broken-scraper`](skills/fix-broken-scraper) | Diagnoses **why** a scraper broke and repairs it one verified step at a time — separating stale selectors from real blocking, changed routing, and content that moved into embedded JSON. |
| [`proxy-finder`](skills/proxy-finder) | Works out what proxy or scraping infrastructure a site actually needs and what it will really cost. **Measures before it recommends** — probes the target, checks robots.txt for your paths, weighs the pages — because the most expensive mistake here is silent: residential proxies work on everything, so nobody discovers the tier at a tenth the price would have worked too. Prices every route including the non-proxy ones on **total cost with retries and engineering time**, and refuses to rank a price it couldn't verify. |

Together they cover the life of a scraping project: audit before you build, cost the
infrastructure, extract without brittle selectors, diagnose when something breaks.

### Markets & research

| Skill | What it does |
| --- | --- |
| [`news-stock-impact`](skills/news-stock-impact) | Turns today's news into a ranked shortlist of listed companies genuinely **exposed** to it — the event, the transmission mechanism to a revenue or cost line, how much the stock has *already* moved, and what would invalidate the idea. Any market, any cap. |
| [`stock-deep-dive`](skills/stock-deep-dive) | Full fundamental analysis of one company — business, moat, earnings quality, management, and **what the current price already implies** — scored 0–10 across six dimensions, with bull/base/bear scenarios and separate verdicts for the long term and the next year. |
| [`ipo-rating`](skills/ipo-rating) | Rates an IPO and says whether to apply — scoring the business, valuation against listed peers, and the fresh-issue vs offer-for-sale split. Gives **two separate verdicts**, listing-day gain and long-term hold, because they often disagree. Reads grey market premium and subscription data, and maps the lock-in expiries. |
| [`crypto-rating`](skills/crypto-rating) | Rates a crypto asset **on live data only** — it fetches and cross-checks the price against three venues and refuses to proceed on a stale feed, because a remembered crypto price is wrong by a multiple, not by a little. Screens new or thin tokens for rug patterns *before* rating anything, does the dilution and unlock arithmetic, then turns **your** capacity for loss into a maximum position size with the crash shown in money. Two verdicts, hold and entry, because they disagree. |

### Documents

| Skill | What it does |
| --- | --- |
| [`pdf-parsing`](skills/pdf-parsing) | Turns a PDF into data you can compute on. **Classifies the file first** — text layer, scanned, fillable form, encrypted — because pointing a text extractor at a scan returns an empty string rather than an error, and that silence is the bug people spend an afternoon on. Extracts text, tables and form fields with whatever toolchain is installed, OCRs when there's no text layer, and writes real multi-sheet `.xlsx` **with only the standard library**. One file or a whole folder, with every input accounted for in the data or in a failure list. |

### Careers

| Skill | What it does |
| --- | --- |
| [`ats-resume`](skills/ats-resume) | Makes a resume survive applicant tracking systems, and **proves it with a scorer** that must read back ≥90/100 before anything is handed over. Reads the file the way a parser does, not the way it looks — which is what catches the failures that actually sink applications: two-column layouts, table scaffolding, text boxes, and contact details in the page header where several ATS discard them. **Never invents a metric** — asks for the numbers it's missing and writes scope instead, because a fabricated 35% has to be defended at interview. Reports keyword gaps as questions rather than pasting them in, and emits a clean `.docx` plus the plain text a parser recovers. Stdlib only. |

### Shopping

| Skill | What it does |
| --- | --- |
| [`value-for-money`](skills/value-for-money) | Finds what's actually worth buying for **one person's use** — asks what the thing is for, then ranks on **cost of ownership**, not sticker price, because the cheap printer is the expensive one. Confidence-adjusts ratings for review count (a 4.3 from 4,000 beats a 4.8 from 60) and **excludes manufactured-looking review distributions** instead of rewarding them. Willing to answer *last year's model*, *refurbished*, *wait for the sale*, or *don't buy*. Knows Indian retail — seller warranty, GST invoice, grey imports, festive cycles. |

### Health & nutrition

| Skill | What it does |
| --- | --- |
| [`weight-loss-diet-plan`](skills/weight-loss-diet-plan) | Builds a fat-loss diet someone will still be eating in week five — **intake first**, then computed calorie and protein targets, a template day, a full seven-day menu, and the shopping list. Handles vegetarian, vegan, eggetarian and other patterns honestly, including the protein arithmetic that quietly sinks most plant-based plans. Ships the **adjustment rules** for when the scale stalls, because that is where plans actually fail. |

## See one in action

`structured-data-extraction` surveys what a page publishes, then locates a field by name:

```console
$ python3 extract.py https://github.com/orgs/vercel/repositories --find starsCount

Keys matching 'starsCount':
  json_blocks[5].data.payload.orgReposPageRoute.repositories[0].starsCount = 30801
  json_blocks[5].data.payload.orgReposPageRoute.repositories[1].starsCount = 2264
  json_blocks[5].data.payload.orgReposPageRoute.repositories[2].starsCount = 15996
  json_blocks[5].data.payload.orgReposPageRoute.repositories[3].starsCount = 4163
  json_blocks[5].data.payload.orgReposPageRoute.repositories[4].starsCount = 25874
  json_blocks[5].data.payload.orgReposPageRoute.repositories[5].starsCount = 141153
```

A JSON path and an exact value, with no DOM inspection. That last one is the argument for this
approach: the page *renders* it as `141k`, so scraping the markup silently loses three digits and
looks perfectly fine doing it. (Counts drift — that was a real run.)

## What a skill here has to earn

Anyone can write instructions an agent will nod along to. These aim higher:

- **Runnable tools, not just prose.** Deterministic work belongs in a script the agent executes
  rather than reasoning through. The bundled scripts use the standard library only — nothing to
  install, nothing to break.
- **Claims are verified, not asserted.** Where a skill says a site behaves a certain way, that was
  checked against the live target. Where a claim turned out to be wrong, it was removed rather
  than softened.
- **Tested against real prompts.** Each skill carries eval cases in `evals/` written the way users
  actually ask — including prompts whose premise is wrong, because the valuable answer is often
  the one that corrects the question.
- **Honest about scope.** A skill that says where it stops is worth more than one that improvises
  past the edge of what it knows.
- **The least powerful tool that works.** Recommending a headless browser for a job a plain HTTP
  request handles is a failure, not caution.

## Installing

**Just one skill** — the common case, since the skills are independent and span different domains:

```bash
npx skills add prashant-cr/skills --skill stock-deep-dive
```

Several at once — repeat the flag. A comma-separated list is **not** accepted and
fails with `No matching skills found`, which reads like the skills are missing:

```bash
npx skills add prashant-cr/skills --skill stock-deep-dive --skill news-stock-impact
```

**Everything**, to every detected agent, without prompts:

```bash
npx skills add prashant-cr/skills --all
```

One thing worth knowing, because it surprises people: **the bare command is not a "browse" command.**

```bash
npx skills add prashant-cr/skills     # <- installs ALL twelve when run inside a coding agent
```

Run in a plain terminal it prompts you to choose. But run inside a coding agent it detects that,
prints `Agent detected — installing non-interactively`, and installs every skill in the repo to
every agent it finds — no picker, no confirmation. Use `--skill` when you want one, and `--list`
when you only want to look.

Skills land in `./.agents/skills/` in the current project, with symlinks into each agent's own
directory. Add `-g` to install user-level in `~/.agents/skills/` instead.

| Flag | Effect |
| --- | --- |
| `-g, --global` | Install user-level (`~/.agents/skills/`) instead of into the current project |
| `-s, --skill <name>` | Install one skill. Repeat the flag for several; commas do not work. `'*'` for all |
| `-a, --agent <agents>` | Target specific agents (`'*'` for all) |
| `-l, --list` | List the skills in this repo without installing |
| `-y, --yes` | Skip confirmation prompts |
| `--copy` | Copy files instead of symlinking into agent directories |
| `--all` | Shorthand for `--skill '*' --agent '*' -y` |

Try a skill without installing it:

```bash
npx skills use prashant-cr/skills --skill <skill-name>
```

Update and remove:

```bash
npx skills update
npx skills remove <skill-name>
```

## Repository layout

```
skills/
  <skill-name>/           # flat: skills/my-skill/SKILL.md
    SKILL.md              # required: frontmatter + instructions
    scripts/              # optional: executable helpers
    references/           # optional: docs loaded on demand
    evals/                # optional: test cases for the skill
    assets/               # optional: templates, images, fonts
  <category>/<skill-name>/  # or catalogued: skills/web-scraping/my-skill/SKILL.md
template/
  SKILL.md.template       # starting point for a new skill (not itself a skill)
scripts/                  # repo tooling
```

The CLI discovers skills at exactly those two depths. Anything deeper is invisible without
`--full-depth`.

Two traps worth knowing if you fork this:

- There is deliberately **no `SKILL.md` at the repository root**. A shallower `SKILL.md` wins, so
  one there makes the CLI treat the whole repo as a single skill and hides everything under
  `skills/`.
- The template is named `SKILL.md.template`, not `SKILL.md`. Being outside `skills/` is not enough
  to hide it — the CLI scans sibling directories too, and a `template/SKILL.md` gets published as
  an installable placeholder skill.

## Adding a skill

```bash
mkdir -p skills/my-new-skill
cp template/SKILL.md.template skills/my-new-skill/SKILL.md
python3 scripts/validate_skills.py
```

The `name` in the frontmatter must match the directory name. The `description` is the entire
triggering mechanism — it is the only part of a skill always resident in an agent's context, so it
has to say both what the skill does *and* the concrete phrases that should summon it. Agents
systematically under-trigger skills; a vague description is the usual reason.

## Validate

```bash
python3 scripts/validate_skills.py            # all skills
python3 scripts/validate_skills.py skills/my-new-skill
```

No dependencies required. Exits non-zero on any problem.

## Publishing

Installability and discoverability are different things, and only the first is automatic.

Push to a public GitHub repo and the skills are immediately installable by `owner/repo` — the CLI
reads GitHub directly, with no registry in between, no submission form and no approval queue.

Appearing in `npx skills find` or on the skills.sh leaderboard is separate, and is driven purely by
anonymous install telemetry from the CLI. Nothing in a repository changes that ranking; only real
installs do.

## License

MIT
