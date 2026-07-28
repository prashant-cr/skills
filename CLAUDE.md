# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A multi-skill Agent Skills repository, published to skills.sh by pushing to a public GitHub repo. The deliverable is Markdown that other agents read at runtime — there is no build step, no package to compile, and no application to run. "Correct" here means a skill triggers when it should and gives an agent instructions it can follow without the author present.

Skills installed from here are consumed by many agents (Claude Code, Cursor, Copilot, Codex, Gemini CLI, Windsurf, and more), so avoid instructions that only make sense inside one agent's harness.

## Commands

```bash
python3 scripts/validate_skills.py                  # validate every skill
python3 scripts/validate_skills.py skills/my-skill  # validate one
```

The validator is the test suite. It is dependency-free (no PyYAML — the local Python lacks it, so keep it that way) and exits non-zero on failure. Run it after any edit to a `SKILL.md`.

```bash
npx skills add . --skill <name> --copy   # install locally to test a skill for real
npx skills add prashant-cr/skills --list   # what consumers see
```

Note: local `node` is v20 but the `skills` CLI wants >=22.20.0. It currently runs anyway and prints an EBADENGINE warning; treat a hard failure there as a Node version problem, not a repo problem.

## Layout invariant

The `skills` CLI discovers skills at exactly two depths: `skills/<name>/SKILL.md` (flat) and `skills/<category>/<name>/SKILL.md` (catalog). Anything deeper is invisible without `--full-depth`.

**Never create a `SKILL.md` at the repository root.** A shallower `SKILL.md` takes precedence over nested ones, so a root one makes the CLI treat the whole repository as a single skill and hides every real skill. The validator fails on this.

`template/` is a scaffold, not a skill. Being outside `skills/` is **not** enough to hide it — the CLI scans sibling directories too, and a `template/SKILL.md` gets discovered and published as an installable placeholder skill (verified). It is therefore named `template/SKILL.md.template`. Keep that extension; copy it to `skills/<name>/SKILL.md` to start a new skill.

The same trap applies to any scratch or example copy: a file named exactly `SKILL.md` within one or two levels of the repo root is publishable. Name work-in-progress copies anything else, or keep them out of the repo.

## Frontmatter contract

Only these keys are allowed: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`. Any other key breaks installation.

- `name` — kebab-case, max 64 chars, and **must match the containing directory name**.
- `description` — max 1024 chars, no angle brackets (`<` or `>`) anywhere. This is the entire triggering mechanism.

## Writing skills

`description` is the only part of a skill always resident in an agent's context; the body loads only once the skill triggers. So all "when to use this" information belongs in the description, never in the body — a trigger condition written in the body is never read by the agent deciding whether to trigger.

Agents systematically *under*-trigger skills. Write descriptions that are pushy and name concrete surface phrases: not "Formats API docs", but "Formats API docs. Use whenever the user mentions API references, endpoint documentation, or OpenAPI specs, even if they don't ask for formatting explicitly." The validator warns when a description contains no "use" clause.

Progressive disclosure governs the body: keep `SKILL.md` under ~500 lines (the validator enforces this) and push detail into `references/`, linked from the body with an explicit condition for when to read it — "read `references/aws.md` when targeting AWS". Deterministic or repetitive work belongs in `scripts/`, which an agent can execute without loading the source into context. When a skill spans several frameworks or providers, split by variant into one reference file each rather than growing the body.

Write instructions in the imperative.

## Tooling

The `skill-creator` skill (installed globally at `~/.agents/skills/skill-creator`) handles authoring, eval runs, and description-trigger optimization. Invoke it for substantive skill work rather than reimplementing its scripts here; `scripts/improve_description.py` there optimizes triggering, and its `evals/evals.json` format is the convention to follow if a skill in this repo grows tests.

## Publishing

**Installability and discoverability are different things, and only the first is automatic.**

A pushed skill is immediately installable by anyone via `npx skills add prashant-cr/skills` — the
CLI reads GitHub directly, with no registry in between. There is no submission form and no
approval queue.

Appearing in `npx skills find` or on the skills.sh leaderboard is separate and is driven purely
by anonymous install telemetry from the CLI. Verified: `npx skills find scraping --owner
prashant-cr` returned nothing while this repo had zero installs, even though searches for the
same terms returned other repos' skills with as few as 9 installs. Nothing in the repository
changes this — only real installs do. Don't manufacture installs to seed the count; install
counts are the trust signal other users rank on, and `find-skills` explicitly tells agents to
distrust unknown authors below 100 installs.

What does help before installs exist is GitHub-side discovery: the repo description, topics
(`agent-skills`, `claude-code`, `web-scraping`, …), and the README. Someone finds the repo on
GitHub, installs via the CLI, and that install is what registers.

Validate before pushing; a broken `SKILL.md` fails at install time on someone else's machine.

Keep the "Available skills" table in `README.md` in sync when adding or removing a skill.
