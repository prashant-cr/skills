# Skills

A collection of [Agent Skills](https://skills.sh) — self-contained instruction packages that extend coding agents (Claude Code, Cursor, Copilot, Codex, Gemini CLI, and others) with new capabilities.

Each skill lives in its own directory under `skills/` and is defined by a single `SKILL.md`.

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
