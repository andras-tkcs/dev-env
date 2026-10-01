#!/usr/bin/env python3
"""Create a new repository from one of the templates in templates/.

Copies templates/<kind>/ into <target-dir>, replaces every __PLACEHOLDER__ token in file contents
and path names, refuses to finish if one is left, and makes the first commit on `main`. It does not
create the GitHub repository or push anything: each template's guide in docs/ walks through that
part, because most of it (branch protection, secrets, publishing accounts) is a settings page only
the owner can open.

Every template takes the common options below; templates/<kind>/template.json declares the rest.

    python3 scripts/new_project.py --list
    python3 scripts/new_project.py mcp-server ~/Coding/acme-mcp --help
    python3 scripts/new_project.py ios-app ~/Coding/acme-notes \\
      --display-name "Acme Notes" --bundle-id com.acme.notes \\
      --owner acme --repo acme-notes --maintainer your-handle \\
      --author "Your Name" --email you@example.com

Stdlib only, so it runs from a fresh clone with nothing installed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import stat
import subprocess  # nosec B404  # fixed git argv only
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
MANIFEST = "template.json"

# Never copied: the manifest is for this script, the rest is local build output that may exist in a
# template someone has been testing in place.
_IGNORED = {MANIFEST, "__pycache__", ".venv", ".build", ".swiftpm", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
_IGNORED_SUFFIXES = (".xcodeproj", ".xcworkspace", ".egg-info")

# Shared by every template, in the order --help lists them.
COMMON_PARAMS = [
    {"token": "DISPLAY_NAME", "flag": "--display-name", "help": "human-readable name (Acme MCP)", "free_text": True},
    {"token": "OWNER", "flag": "--owner", "help": "GitHub user or organization", "pattern": r"^[A-Za-z0-9-]+$"},
    {"token": "REPO", "flag": "--repo", "help": "GitHub repository name", "pattern": r"^[A-Za-z0-9._-]+$"},
    {"token": "MAINTAINER", "flag": "--maintainer", "help": "GitHub handle for CODEOWNERS", "strip_prefix": "@"},
    {"token": "AUTHOR_NAME", "flag": "--author", "help": "author name for metadata and the first commit", "free_text": True},
    {"token": "CONTACT_EMAIL", "flag": "--email", "help": "contact e-mail (SECURITY.md, metadata)", "pattern": r"^[^@\s\"]+@[^@\s\"]+$"},
    {"token": "DESCRIPTION", "flag": "--description", "help": "one line on what the project does", "free_text": True, "optional": True},
]
# Filled in by this script, never by a flag.
AUTOMATIC_TOKENS = ("DATE", "YEAR", "TEMPLATE")

TOKEN_RE = re.compile(r"__([A-Z][A-Z0-9_]*)__")


class GenerateError(Exception):
    """A value or a template is wrong. Printed without a traceback."""


@dataclass
class Template:
    kind: str
    path: Path
    name: str
    summary: str
    guide: str
    params: list[dict] = field(default_factory=list)
    description_default: str = ""
    executable: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    @property
    def all_params(self) -> list[dict]:
        return COMMON_PARAMS + self.params

    @property
    def tokens(self) -> set[str]:
        return {param["token"] for param in self.all_params} | set(AUTOMATIC_TOKENS)


def load_templates() -> dict[str, Template]:
    templates: dict[str, Template] = {}
    for manifest in sorted(TEMPLATES_DIR.glob(f"*/{MANIFEST}")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        kind = manifest.parent.name
        templates[kind] = Template(
            kind=kind,
            path=manifest.parent,
            name=data["name"],
            summary=data["summary"],
            guide=data["guide"],
            params=data.get("params", []),
            description_default=data.get("description_default", ""),
            executable=data.get("executable", []),
            next_steps=data.get("next_steps", []),
        )
    return templates


def _dest(flag: str) -> str:
    return flag.lstrip("-").replace("-", "_")


def _transform(value: str, how: str) -> str:
    if how == "snake":
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if how == "pascal":
        words = re.split(r"[^A-Za-z0-9]+", value)
        joined = "".join(word[:1].upper() + word[1:] for word in words if word)
        return joined.lstrip("0123456789")
    raise GenerateError(f"unknown transform {how!r} in a template manifest")


def resolve_values(template: Template, given: dict[str, str | None]) -> dict[str, str]:
    """Every token's value: from its flag, else derived or defaulted, then validated."""
    values: dict[str, str] = {}
    for param in template.all_params:
        token, flag = param["token"], param["flag"]
        value = given.get(_dest(flag))
        if value is None and "default_from" in param:
            value = _transform(values[param["default_from"]], param.get("transform", "snake"))
        if value is None and "default" in param:
            value = param["default"]
        if value is None and token == "DESCRIPTION":
            value = template.description_default
        if value is None:
            raise GenerateError(f"{flag} is required")
        if "strip_prefix" in param and value.startswith(param["strip_prefix"]):
            value = value[len(param["strip_prefix"]) :]
        if param.get("free_text") and re.search(r'["\\\x00-\x1f]', value):
            # Values land inside TOML, YAML, JSON and Swift string literals unescaped.
            raise GenerateError(f"{flag} may not contain a double quote, a backslash or a control character")
        if "pattern" in param and not re.fullmatch(param["pattern"], value):
            raise GenerateError(f"{flag} {value!r} must be {param.get('pattern_help', 'of the form ' + param['pattern'])}")
        if not value and not param.get("optional") and not param.get("allow_empty"):
            raise GenerateError(f"{flag} may not be empty")
        values[token] = value
    today = dt.datetime.now(dt.timezone.utc).date()
    values.update({"DATE": today.isoformat(), "YEAR": str(today.year), "TEMPLATE": template.name})
    return values


def _ignore(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in _IGNORED or name.endswith(_IGNORED_SUFFIXES)}


def _substitute(text: str, values: dict[str, str]) -> str:
    return TOKEN_RE.sub(lambda match: values.get(match.group(1), match.group(0)), text)


def leftover_tokens(target: Path, tokens: set[str]) -> list[str]:
    """Every declared token still present in a path or a text file under ``target``."""
    found: list[str] = []
    for path in sorted(target.rglob("*")):
        if ".git" in path.relative_to(target).parts:
            continue
        rel = path.relative_to(target)
        for match in TOKEN_RE.finditer(str(rel)):
            if match.group(1) in tokens:
                found.append(f"{rel}: path holds {match.group(0)}")
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                for match in TOKEN_RE.finditer(line):
                    if match.group(1) in tokens:
                        found.append(f"{rel}:{lineno}: {match.group(0)}")
    return found


def generate(template: Template, target: Path, values: dict[str, str], *, force: bool = False) -> Path:
    if target.exists() and any(target.iterdir()) and not force:
        raise GenerateError(f"{target} exists and is not empty (pass --force to copy into it anyway)")
    target.mkdir(parents=True, exist_ok=True)
    target = target.resolve()

    shutil.copytree(template.path, target, ignore=_ignore, dirs_exist_ok=True, symlinks=True)

    # Deepest first, so renaming a directory never invalidates a path still to be visited.
    for path in sorted(target.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if ".git" in path.relative_to(target).parts:
            continue
        renamed = _substitute(path.name, values)
        if renamed != path.name:
            path.rename(path.with_name(renamed))

    for path in target.rglob("*"):
        if not path.is_file() or path.is_symlink() or ".git" in path.relative_to(target).parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        replaced = _substitute(text, values)
        if replaced != text:
            path.write_text(replaced, encoding="utf-8")

    left = leftover_tokens(target, template.tokens)
    if left:
        raise GenerateError("placeholders left behind:\n  " + "\n  ".join(left))

    for pattern in template.executable:
        for path in target.glob(pattern):
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def first_commit(template: Template, target: Path, values: dict[str, str]) -> str:
    def git(*args: str) -> str:
        return subprocess.run(  # nosec B603 B607
            ["git", *args], cwd=target, check=True, capture_output=True, text=True
        ).stdout.strip()

    if not (target / ".git").exists():
        git("init", "-q", "-b", "main")
    git("add", "-A")
    git(
        "-c", f"user.name={values['AUTHOR_NAME']}",
        "-c", f"user.email={values['CONTACT_EMAIL']}",
        "commit", "-q",
        "-m", f"Start {values['DISPLAY_NAME']} from the {template.name} template",
        "-m", f"Process, testing policy, ADRs and Claude Code commands copied from dev-env's templates/{template.kind}/.",
    )
    return git("log", "-1", "--oneline")


def build_parser(templates: dict[str, Template]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--list", action="store_true", help="list the available templates and exit")
    kinds = parser.add_subparsers(dest="kind", metavar="<kind>")
    for kind, template in templates.items():
        sub = kinds.add_parser(kind, help=template.summary, description=f"{template.name}: {template.summary}")
        sub.add_argument("target", type=Path, help="directory to create the repository in")
        for param in template.all_params:
            required = not ("default_from" in param or "default" in param or param.get("optional"))
            sub.add_argument(param["flag"], dest=_dest(param["flag"]), help=param["help"], required=required)
        sub.add_argument("--no-git", action="store_true", help="skip git init and the first commit")
        sub.add_argument("--force", action="store_true", help="copy into a non-empty target directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    templates = load_templates()
    parser = build_parser(templates)
    args = parser.parse_args(argv)

    if args.list or not args.kind:
        for kind, template in templates.items():
            print(f"{kind:12} {template.summary}  (guide: {template.guide})")
        return 0 if args.list else 2

    template = templates[args.kind]
    try:
        values = resolve_values(template, vars(args))
        print(f"==> Generating {template.name} into {args.target}")
        target = generate(template, args.target, values, force=args.force)
        if not args.no_git:
            print(f"    first commit: {first_commit(template, target, values)}")
    except (GenerateError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else exc
        print(f"error: {detail}", file=sys.stderr)
        return 1

    print("\nDone. Next:")
    print(f"  cd {target}")
    for step in template.next_steps:
        print(f"  {_substitute(step, values)}")
    print(f"Then follow dev-env's {template.guide} (GitHub repository, protection, secrets).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
