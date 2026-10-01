# dev-env

A reusable way of working for software projects, taken from PrivacyFence and generalized: Claude
Code slash commands and skills, the plan → implement → review workflow, the ADR system, the
layered testing policy with a definition-of-done gate, and a tag-driven release pipeline — packaged
as one template per kind of project.

| Template | What it starts | Guide |
|---|---|---|
| [`templates/mcp-server/`](templates/mcp-server/) | A Python MCP server on the official SDK, published to PyPI | [`docs/mcp-server.md`](docs/mcp-server.md) |
| [`templates/ios-app/`](templates/ios-app/) | A SwiftUI iPhone and iPad app with its logic in a Swift package, shipped through TestFlight | [`docs/ios-app.md`](docs/ios-app.md) |

Each template is a complete repository with `__PLACEHOLDER__` tokens where project names go.
Generated as-is, its whole definition-of-done gate passes.

- [`docs/working-mode.md`](docs/working-mode.md) — the working mode every template shares, and what
  a template must provide. Start here.
- [`scripts/new_project.py`](scripts/new_project.py) — copies a template into a new directory,
  fills in the placeholders, and makes the first commit.
- [`scripts/check_templates.py`](scripts/check_templates.py) — keeps the templates on the shared
  working mode; [`.github/workflows/templates.yml`](.github/workflows/templates.yml) runs it and
  every template's own gate on each PR.
- [`docs/adr/`](docs/adr/README.md) — why dev-env itself is organized this way.

## Start a new project

```bash
git clone https://github.com/andras-tkcs/dev-env.git
python3 dev-env/scripts/new_project.py --list
python3 dev-env/scripts/new_project.py <kind> ~/Coding/<name> --help
```

Every template takes `--display-name`, `--owner`, `--repo`, `--maintainer`, `--author`, `--email`
and an optional `--description`; its `template.json` adds the rest (a PyPI name, a bundle ID). Then
follow the template's guide from "Set up a new repository": it walks through the GitHub settings,
the release secret, the publishing account and Claude Code on the web.

## Changing a template

A template is plain files: edit them, then prove the result still passes its own gate.

```bash
python3 scripts/check_templates.py
python3 scripts/check_templates.py --generate mcp-server /tmp/mcp-check
cd /tmp/mcp-check && python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]" \
  && .venv/bin/python scripts/pre_release_check.py
```

For the iOS template, generate it the same way and run `python3 scripts/pre_release_check.py` on a
Mac; on Linux it runs everything but the simulator rows. `templates.yml` runs both on every PR.

The sample values are long on purpose: a placeholder inside code can push a line past a
formatter's limit once it is filled in, and a short name hides that. Write any code line that
holds a name token so it stays within the limit whatever the name's length.

**A shared file changes in every template at once.** `make-plan.md`, `implement.md`, ADRs `0001`
and `0002`, and `docs/adr/README.md` above its index are identical across templates, and
`check_templates.py` fails until they are again. Keep stack-specific commands out of them: point
at the template's `docs/testing-policy.md` ("Fast checks") or its definition of done instead.

When PrivacyFence's process changes, port the change here in the same generalized form, to every
template it applies to, and note it in the generated repositories by adding an ADR there if it
changes a decision.

## Adding a kind of project

1. Create `templates/<kind>/` with a `template.json` (`name`, `summary`, `guide`, `params`,
   `executable`, `next_steps`; see the existing two).
2. Copy the shared files verbatim from an existing template, and write the rest of what
   [`docs/working-mode.md`](docs/working-mode.md#what-every-template-provides) lists for the new
   stack: its testing layers, its definition of done, its fast checks, its version-from-tag and
   release pipeline, and its own seed ADRs from `0003` on.
3. A working skeleton, not an empty one: the generated repository's gate must pass on day one.
4. Add a job for it to `.github/workflows/templates.yml`, a guide in `docs/<kind>.md`, and a row
   to the tables above and in `docs/working-mode.md`.
