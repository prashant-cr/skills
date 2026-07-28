# Skills

Open [Agent Skills](https://skills.sh) — self-contained instruction packages that extend coding
agents (Claude Code, Cursor, Copilot, Codex, Gemini CLI, and 15+ others) with new capabilities.

## Know what you're up against before you write a scraper

`scrape-feasibility-audit` answers the two questions that decide a scraping project — **should we
collect this, and what will it take?** — before anyone writes code. It identifies the bot-detection
vendor, the CAPTCHA type, whether content is server- or client-rendered, and what robots.txt
actually permits, then recommends tooling proportionate to what it found.

```console
$ python3 probe_site.py https://news.ycombinator.com

Target:   https://news.ycombinator.com
Status:   200
Server:   nginx

robots.txt
  path /: allowed
  crawl-delay: 30.0s  <- pace requests at least this slowly

Bot protection
  none detected from headers, cookies, or markup

CAPTCHA
  none present on this response

Content delivery
  server-rendered: 4282 chars of text present in the initial HTML.

Assessment: TRIVIAL
```

Against a defended target it reports what is actually engaged and why:

```console
Bot protection
  Cloudflare  ENGAGED [high]
    evidence: cookie:__cf_bm, body:/cdn-cgi/challenge-platform/, header:cf-ray
  DataDome  ENGAGED [high]
    evidence: header:x-datadome, cookie:datadome

CAPTCHA
  DataDome CAPTCHA (slider puzzle)

Assessment: HARD
```

It deliberately distinguishes a vendor being **present** from **engaged** — a bare `cf-ray` header
means the site uses a common CDN, not that it fights bots. Conflating the two is the most common
way these assessments go wrong, and it produces confident "this site is hard" verdicts about sites
that are trivial.

Detects Cloudflare, Akamai, DataDome, HUMAN/PerimeterX, Kasada, Imperva, AWS WAF and F5; reCAPTCHA
v2/v3, hCaptcha, Turnstile, Arkose and GeeTest.

## Install

Install everything in this repo:

```bash
npx skills add prashant-cr/skills --all
```

Install one skill:

```bash
npx skills add prashant-cr/skills --skill <skill-name>
```

Useful flags:

| Flag | Effect |
| --- | --- |
| `-g, --global` | Install user-level (`~/.agents/skills/`) instead of into the current project |
| `-a, --agent <agents>` | Target specific agents; `'*'` for all |
| `-l, --list` | List the skills in this repo without installing |
| `-y, --yes` | Skip confirmation prompts |
| `--copy` | Copy files instead of symlinking into agent directories |

Try a skill without installing it:

```bash
npx skills use prashant-cr/skills --skill <skill-name>
```

## Available skills

<!-- Add a row per skill. Keep this table in sync with skills/. -->

| Skill | Description |
| --- | --- |
| [`scrape-feasibility-audit`](skills/scrape-feasibility-audit) | Audits a public website before you build a scraper: identifies bot-detection vendors (Cloudflare, Akamai, DataDome, HUMAN/PerimeterX, Kasada, Imperva, AWS WAF), CAPTCHA types, robots.txt rules and rendering mode, then recommends proportionate open-source tooling. |

### scrape-feasibility-audit

Answers *should we collect this, and what will it take* before anyone writes code.

```bash
npx skills add prashant-cr/skills --skill scrape-feasibility-audit
```

Bundled `scripts/probe_site.py` runs standalone with no third-party dependencies:

```bash
python3 skills/scrape-feasibility-audit/scripts/probe_site.py https://example.com/products
python3 skills/scrape-feasibility-audit/scripts/probe_site.py https://example.com --json
```

It reads robots.txt before fetching the page, declines robots-disallowed paths unless given
`--force`, paces its requests, and sends an honest User-Agent. It reports vendors as *engaged*
only when a scoring cookie or challenge script is present — a bare `cf-ray` means the site uses
a CDN, not that it fights bots.

Scope is public, unauthenticated content. It does not cover defeating CAPTCHAs that gate
content, bypassing authentication or paywalls, or evading sites that have refused automated
access; where an audit lands there, it says so and points at the sanctioned path instead.

## Repository layout

```
skills/
  <skill-name>/
    SKILL.md        # required: frontmatter + instructions
    scripts/        # optional: executable helpers
    references/     # optional: docs loaded on demand
    assets/         # optional: templates, images, fonts
template/
  SKILL.md.template # starting point for a new skill (not itself a skill)
scripts/            # repo tooling
```

There is deliberately **no `SKILL.md` at the repository root** — one there would make the CLI treat the entire repo as a single skill and hide everything under `skills/`.

The template is named `SKILL.md.template` rather than `SKILL.md` because the CLI scans `template/` too; a file named `SKILL.md` there gets published as a real, installable skill.

## Adding a skill

```bash
mkdir -p skills/my-new-skill
cp template/SKILL.md.template skills/my-new-skill/SKILL.md
python3 scripts/validate_skills.py
```

Then fill in `skills/my-new-skill/SKILL.md`. The `name` in the frontmatter must match the directory name, and the `description` must say both what the skill does and when it should trigger.

## Validate

```bash
python3 scripts/validate_skills.py            # all skills
python3 scripts/validate_skills.py skills/my-new-skill
```

No dependencies required. Exits non-zero on any problem.

## Publishing

skills.sh indexes public GitHub repositories automatically — there is no submission step or manifest to file. Push to a public repo and the skills become installable by `owner/repo`. The skills.sh leaderboard ranks by anonymous install telemetry from the `skills` CLI, so a skill's placement follows real installs.

## License

MIT
