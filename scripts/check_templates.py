#!/usr/bin/env python3
"""Check that every template still carries the shared working mode, and still generates.

Each template under templates/ is a self-contained repository (docs/adr/0001). What keeps them one
working mode rather than drifting apart is this check (docs/working-mode.md, "What every template
provides"):

  1. **Required files.** Every template has the files the working mode is made of: the Claude Code
     commands, hook and steward skill, the ADR system, the testing policy and definition of done,
     the three workflows, and the release scripts.
  2. **Shared files are identical.** The plan/implement commands and the ADRs about the working
     mode itself are byte-identical across templates; `docs/adr/README.md` is identical up to its
     index. Change one, change all, in the same PR.
  3. **Anchors the shared files rely on.** The shared commands point at "Fast checks" in
     docs/testing-policy.md and "Definition of done" in the guidelines; every template has them.
  4. **No unknown placeholder.** Every `__UPPER_CASE__` token in a template is one its manifest
     declares, so a typo (`__DISPLAY_NAM__`) fails here instead of shipping into a new repository.
  5. **It generates.** scripts/new_project.py fills every placeholder with deliberately long sample
     values and leaves none behind.

    python3 scripts/check_templates.py
    python3 scripts/check_templates.py --generate ios-app /tmp/ios-check   # a sample repo for CI

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import new_project  # noqa: E402

REQUIRED = [
    "README.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".gitignore",
    ".claude/settings.json",
    ".claude/hooks/session-start.sh",
    ".claude/skills/steward/SKILL.md",
    ".claude/commands/make-plan.md",
    ".claude/commands/implement.md",
    ".claude/commands/dod.md",
    ".claude/commands/cut-release.md",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/workflows/tests.yml",
    ".github/workflows/build.yml",
    ".github/workflows/release.yml",
    "docs/README.md",
    "docs/adr/README.md",
    "docs/coding-and-testing-guidelines.md",
    "docs/testing-policy.md",
    "docs/releasing.md",
    "docs/release-testing.md",
    "scripts/pre_release_check.py",
    "scripts/check_coverage_floor.py",
    "scripts/changelog_section.py",
    "scripts/release_channel.py",
    "scripts/tag_release.py",
    "scripts/update_branch_protection.py",
]

SHARED_IDENTICAL = [
    ".claude/commands/make-plan.md",
    ".claude/commands/implement.md",
    "docs/adr/0001-record-decisions-as-adrs-and-keep-plans-temporary.md",
    "docs/adr/0002-process-docs-live-in-docs-not-in-claude-md.md",
]

# File -> the line up to which it is shared; what follows is per template.
SHARED_PREFIX = {"docs/adr/README.md": "## Index"}

ANCHORS = {
    "docs/testing-policy.md": "## Fast checks",
    "docs/coding-and-testing-guidelines.md": "### Definition of done",
}

# Long on purpose: a placeholder inside code can push a line past a formatter's limit once filled
# in, and a short name hides that.
SAMPLES = {
    "display_name": "A Deliberately Long Project Name To Check Line Wrapping",
    "dist_name": "a-deliberately-long-server-name-to-check-line-wrapping",
    "owner": "example-owner",
    "repo": "example-repo",
    "maintainer": "example-maintainer",
    "author": "Example Author",
    "email": "author@example.com",
    "bundle_id": "com.example.deliberately-long-bundle-identifier",
}

_SKIP_DIRS = {".git", "__pycache__", ".build", ".venv"}


def _files(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*")) if p.is_file() and not _SKIP_DIRS.intersection(p.relative_to(root).parts)]


def _prefix(text: str, marker: str) -> str:
    index = text.find("\n" + marker)
    return text if index < 0 else text[:index]


def check_structure(templates: dict[str, new_project.Template]) -> list[str]:
    problems: list[str] = []
    for kind, template in templates.items():
        for rel in REQUIRED:
            if not (template.path / rel).is_file():
                problems.append(f"{kind}: missing {rel}")
        for rel, anchor in ANCHORS.items():
            path = template.path / rel
            if path.is_file() and anchor not in path.read_text(encoding="utf-8").splitlines():
                problems.append(f"{kind}: {rel} has no {anchor!r} section (the shared commands point at it)")
        for path in _files(template.path):
            rel = path.relative_to(template.path)
            names = set(new_project.TOKEN_RE.findall(str(rel)))
            try:
                names |= set(new_project.TOKEN_RE.findall(path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                pass
            for unknown in sorted(names - template.tokens):
                problems.append(f"{kind}: {rel} uses __{unknown}__, which {new_project.MANIFEST} does not declare")

    kinds = list(templates)
    for first, other in zip(kinds, kinds[1:]):
        a, b = templates[first].path, templates[other].path
        for rel in SHARED_IDENTICAL:
            if (a / rel).is_file() and (b / rel).is_file() and (a / rel).read_bytes() != (b / rel).read_bytes():
                problems.append(f"{rel} differs between {first} and {other}; shared files change in every template at once")
        for rel, marker in SHARED_PREFIX.items():
            if (a / rel).is_file() and (b / rel).is_file():
                if _prefix((a / rel).read_text(encoding="utf-8"), marker) != _prefix((b / rel).read_text(encoding="utf-8"), marker):
                    problems.append(f"{rel} differs above {marker!r} between {first} and {other}")
    return problems


def sample_values(template: new_project.Template) -> dict[str, str]:
    return new_project.resolve_values(template, dict(SAMPLES))


def check_generation(templates: dict[str, new_project.Template]) -> list[str]:
    problems: list[str] = []
    for kind, template in templates.items():
        with tempfile.TemporaryDirectory() as tmp:
            try:
                new_project.generate(template, Path(tmp) / kind, sample_values(template))
            except new_project.GenerateError as exc:
                problems.append(f"{kind}: generation failed: {exc}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--generate", nargs=2, metavar=("KIND", "DIR"), help="write a sample repository and exit")
    args = parser.parse_args(argv)
    templates = new_project.load_templates()

    if args.generate:
        kind, target = args.generate
        if kind not in templates:
            print(f"error: no template {kind!r} (have: {', '.join(templates)})", file=sys.stderr)
            return 2
        template = templates[kind]
        new_project.generate(template, Path(target), sample_values(template))
        print(f"Generated a sample {template.name} repository in {target}")
        return 0

    problems = check_structure(templates) + check_generation(templates)
    for kind in templates:
        print(f"  checked {kind}")
    if problems:
        print("\nTemplate check FAILED:", file=sys.stderr)
        for line in problems:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("\nEvery template carries the shared working mode and generates cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
