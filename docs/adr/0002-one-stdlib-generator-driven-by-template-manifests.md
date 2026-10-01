# ADR 0002: One stdlib-only generator, driven by each template's `template.json`

## Status

Accepted — 2026-10-01.

## Context

Generating a repository means copying a template, filling `__PLACEHOLDER__` tokens in contents and
paths, validating the values, refusing to finish with a token left, and making the first commit.
With one template that was a shell script with `sed`. With several, each needs its own values (a
PyPI name, a bundle ID, an optional team ID) and its own derived defaults, and a shell script per
template would duplicate the rest.

## Decision

1. `scripts/new_project.py` is the only generator. It takes the template kind as a subcommand,
   the common options every template shares, and the template-specific options its
   `templates/<kind>/template.json` declares (flag, pattern, default or derivation).
2. It uses the Python standard library only, so it runs from a fresh clone with nothing installed.
3. `template.json` is never copied into a generated repository.

## Alternatives considered

- **cookiecutter or copier.** A dependency to install before the first command, and a Jinja
  syntax (`{{ }}`) that collides with GitHub Actions expressions (`${{ }}`) in every workflow file,
  so each template would need escaping throughout.
- **One shell script per template.** Rejected: the copy, validation, leftover check and commit
  logic would be duplicated, and `sed` replacement breaks on values containing its delimiter.

## Consequences

- Python 3 is needed to generate a project of any kind; macOS with Xcode's command line tools and
  every Linux CI image have it.
- A new template declares its tokens in `template.json`; `scripts/check_templates.py` fails on a
  token a template uses but does not declare.

## Verification

`scripts/new_project.py`; `templates/*/template.json`; `scripts/check_templates.py`.
