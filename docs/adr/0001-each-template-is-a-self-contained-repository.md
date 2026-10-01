# ADR 0001: Each template is a self-contained repository; shared files are kept identical by a check, not by a common layer

## Status

Accepted — 2026-10-01.

## Context

dev-env began as one template, for MCP servers. Adding a second kind of project (an iOS app) means
deciding where the parts both share live: the plan and implement commands, the ADR rules, the
working-mode ADRs. Most of each template is stack-specific even where the idea is shared — the
definition of done names `pytest` in one and `swift test` in the other — so the genuinely
identical part is a handful of files.

## Decision

1. Each `templates/<kind>/` is a complete repository: everything a generated project contains is
   in that one directory, placeholders included, and nothing is assembled from elsewhere at
   generation time.
2. Files that must not drift are listed in `scripts/check_templates.py` (`SHARED_IDENTICAL`,
   `SHARED_PREFIX`) and must be byte-identical across templates; the check also requires every
   template to have the working mode's files and the sections the shared files point at.
3. Shared files never name a stack's commands. They point at a document each template provides
   (`docs/testing-policy.md`'s "Fast checks", the definition of done) instead.
4. `.github/workflows/templates.yml` runs the check, then generates each template and runs its own
   gate, on every PR.

## Alternatives considered

- **A `common/` layer overlaid with per-template files at generation time.** Less duplication, but
  no template is a repository you can read or test in place any more, an override silently shadows
  a common file, and a reader of the common file cannot see which templates replace it.
- **Placeholders for stack-specific commands inside shared files** (`__FAST_CHECK__`). Rejected:
  a multi-line command list does not fit a token, and the indirection to a doc the template owns
  is clearer for the session that reads it.
- **No shared files at all.** Rejected: the plan/implement pipeline would fork per template, and a
  fix to one would quietly miss the other.

## Consequences

- Changing a shared file means changing it in every template in the same PR; the check fails
  until that is done.
- A third template copies the shared files and writes the rest; `README.md`'s "Adding a kind of
  project" lists the steps.

## Verification

`scripts/check_templates.py`; `.github/workflows/templates.yml`; `docs/working-mode.md`, "What
every template provides".
