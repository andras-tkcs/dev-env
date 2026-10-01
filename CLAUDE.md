# CLAUDE.md

Notes for Claude Code sessions on dev-env itself. dev-env holds templates, not a product: most
changes edit files under `templates/<kind>/` that will be copied into other repositories.

- [`README.md`](README.md) — the templates, generating a project, changing a template, adding one.
- [`docs/working-mode.md`](docs/working-mode.md) — what every template shares and must provide.
- [`docs/adr/`](docs/adr/README.md) — why dev-env is organized this way.

## Working on a template

- A file under `templates/` is written for the generated repository, not for dev-env: its
  relative links, its `CLAUDE.md` and its `.claude/` commands are that repository's. They do not
  apply to sessions working on dev-env.
- Shared files (`scripts/check_templates.py` lists them) change in every template in the same
  commit. Keep stack-specific commands out of them.
- A new placeholder goes into the template's `template.json` first.
- Before pushing, run `python3 scripts/check_templates.py`, then generate the template you changed
  (`--generate <kind> <dir>`) and run its `scripts/pre_release_check.py` there. A Linux session
  cannot run the iOS template's simulator rows: push and read `templates.yml`'s `ios-app-macos`
  job instead, and say so rather than reporting them as passed.
