#!/usr/bin/env python3
"""Validate every skill in this repository.

Checks the frontmatter rules the `skills` CLI and Claude Code enforce, plus the
repo-layout invariant that keeps this a multi-skill repository.

Usage:
    python3 scripts/validate_skills.py            # validate all skills
    python3 scripts/validate_skills.py skills/my-skill
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
REQUIRED_KEYS = {"name", "description"}
MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
MAX_COMPATIBILITY_LEN = 500
# SKILL.md bodies beyond this are a smell: move detail into references/.
BODY_LINE_BUDGET = 500


def parse_frontmatter(text):
    """Return (frontmatter_dict, body, error). Top-level keys only, no yaml dep."""
    if not text.startswith("---"):
        return None, None, "no YAML frontmatter (file must start with '---')"
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        return None, None, "malformed frontmatter (missing closing '---')"

    fields = {}
    for line in match.group(1).split("\n"):
        if not line.strip() or line.startswith("#"):
            continue
        # Nested keys belong to the preceding top-level key (e.g. metadata).
        if line.startswith((" ", "\t", "-")):
            continue
        if ":" not in line:
            return None, None, f"frontmatter line is not 'key: value': {line!r}"
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("\"'")
    return fields, match.group(2), None


def validate_skill(skill_dir):
    """Return a list of error strings for one skill directory."""
    errors = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir}: SKILL.md not found"]

    rel = skill_md.relative_to(REPO_ROOT)
    fields, body, error = parse_frontmatter(skill_md.read_text())
    if error:
        return [f"{rel}: {error}"]

    for key in sorted(REQUIRED_KEYS - set(fields)):
        errors.append(f"{rel}: missing required frontmatter key '{key}'")

    for key in sorted(set(fields) - ALLOWED_KEYS):
        errors.append(
            f"{rel}: unexpected frontmatter key '{key}' "
            f"(allowed: {', '.join(sorted(ALLOWED_KEYS))})"
        )

    name = fields.get("name", "")
    if name:
        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append(f"{rel}: name '{name}' must be kebab-case (a-z, 0-9, hyphens)")
        elif name.startswith("-") or name.endswith("-") or "--" in name:
            errors.append(f"{rel}: name '{name}' cannot start/end with '-' or contain '--'")
        if len(name) > MAX_NAME_LEN:
            errors.append(f"{rel}: name is {len(name)} chars, max {MAX_NAME_LEN}")
        if name != skill_dir.name:
            errors.append(f"{rel}: name '{name}' must match directory name '{skill_dir.name}'")

    description = fields.get("description", "")
    if description:
        if "<" in description or ">" in description:
            errors.append(f"{rel}: description cannot contain angle brackets")
        if len(description) > MAX_DESCRIPTION_LEN:
            errors.append(f"{rel}: description is {len(description)} chars, max {MAX_DESCRIPTION_LEN}")
    if description and " use " not in f" {description.lower()} ":
        errors.append(
            f"{rel}: description has no explicit trigger clause "
            "(add 'Use when ...' so the skill fires reliably)"
        )

    compatibility = fields.get("compatibility", "")
    if len(compatibility) > MAX_COMPATIBILITY_LEN:
        errors.append(f"{rel}: compatibility is {len(compatibility)} chars, max {MAX_COMPATIBILITY_LEN}")

    if body is not None:
        line_count = len(body.strip().split("\n"))
        if line_count > BODY_LINE_BUDGET:
            errors.append(
                f"{rel}: body is {line_count} lines (budget {BODY_LINE_BUDGET}); "
                "move detail into references/ and link to it"
            )

    return errors


def discover_skills():
    """Skill dirs the CLI would find: skills/<name>/ and skills/<category>/<name>/."""
    skills_root = REPO_ROOT / "skills"
    if not skills_root.is_dir():
        return []
    found = set()
    for pattern in ("*/SKILL.md", "*/*/SKILL.md"):
        for skill_md in skills_root.glob(pattern):
            found.add(skill_md.parent)
    return sorted(found)


def main():
    if len(sys.argv) > 1:
        skill_dirs = [Path(arg).resolve() for arg in sys.argv[1:]]
    else:
        skill_dirs = discover_skills()

    errors = []
    # A root SKILL.md makes the CLI treat the whole repo as one skill.
    if (REPO_ROOT / "SKILL.md").exists():
        errors.append(
            "SKILL.md at repo root: this shadows every skill in skills/. "
            "Move it to skills/<name>/SKILL.md."
        )

    if not skill_dirs and not errors:
        print("No skills found under skills/. Nothing to validate.")
        return 0

    names = {}
    for skill_dir in skill_dirs:
        errors.extend(validate_skill(skill_dir))
        names.setdefault(skill_dir.name, []).append(skill_dir)

    for name, dirs in sorted(names.items()):
        if len(dirs) > 1:
            paths = ", ".join(str(d.relative_to(REPO_ROOT)) for d in dirs)
            errors.append(f"duplicate skill name '{name}' in: {paths}")

    if errors:
        print(f"FAIL: {len(errors)} problem(s) across {len(skill_dirs)} skill(s)\n")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"OK: {len(skill_dirs)} skill(s) valid")
    for skill_dir in skill_dirs:
        print(f"  - {skill_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
