# dev-env

A reusable way of working for MCP server projects, taken from PrivacyFence and generalized:
Claude Code slash commands and skills, the plan → implement → review workflow, the ADR system, the
layered testing policy with a definition-of-done gate, and a tag-driven release pipeline.

- [`mcp-server-template/`](mcp-server-template/) — the files a new repository starts from, with
  `__PLACEHOLDER__` tokens where project names go. It is a working Python MCP server skeleton:
  generated as-is, its whole definition-of-done gate passes.
- [`scripts/new-mcp-server.sh`](scripts/new-mcp-server.sh) — copies the template into a new
  directory, fills in the placeholders, and makes the first commit.

## Contents

- [The working mode, in one page](#the-working-mode-in-one-page)
- [What is in the template](#what-is-in-the-template)
- [Set up a new repository](#set-up-a-new-repository)
- [After setup: making it your server](#after-setup-making-it-your-server)
- [What was left out, and how to add it back](#what-was-left-out-and-how-to-add-it-back)
- [Changing the template](#changing-the-template)

## The working mode, in one page

**Plans, ADRs, reference docs.** Three kinds of document, three lifecycles
([`docs/adr/README.md`](mcp-server-template/docs/adr/README.md)):

| Kind | Answers | Lifecycle |
|---|---|---|
| Plan (`docs/<slug>-plan.md` or an issue) | What are we about to do? | Deleted when the work lands, after its decisions are extracted into ADRs |
| ADR (`docs/adr/NNNN-*.md`) | Why is it this way, what was rejected? | Permanent; frozen once accepted; superseded, never rewritten |
| Reference (`docs/*.md`, `CONTRIBUTING.md`) | How does it work today? | Edited in the same PR as the behavior |

**From idea to merged PR with Claude Code:**

1. `/make-plan <idea or issue>` (on Opus) researches the change. A **small** change gets a
   self-contained prompt to paste into a fresh Sonnet session. A **large** change gets a
   `docs/<slug>-plan.md` on a `plan/<slug>` branch, with an `## Implementation manifest` of
   phases sized so a Sonnet session can do each one mechanically. Anything only a human can do
   (console setup, secrets, real-device checks) goes only at the very start (`manual_before`) or
   the very end (`manual_after`), with a step-by-step HTML page.
2. `/implement <plan URL>` (on Sonnet) orchestrates: one child session per phase on
   `feature/<slug>--<phase>` branches, merged `--no-ff` into `feature/<slug>` with a
   `Plan-Phase:` trailer, verified after each merge, then one Opus review of the whole branch
   against the plan, then **one** PR to `main`. The plan's last phase deletes the plan document and
   writes its ADRs.
3. `/dod` runs the definition of done (tests at 100% pass, coverage ratchet, ruff, mypy ratchet,
   bandit) and reads the diff for the conditional and manual rows. It reports; it does not fix.
4. The **steward** skill tells a session how to drive its PR to green: what to dispatch to a runner
   instead of running locally, and that a red check is real until proven otherwise (never skip a
   test, never kick CI with an empty commit, never lower a coverage floor).
5. `/cut-release <version>` pre-flights `build.yml`, dry-runs `release.yml`, and cuts the tag only
   when you say so.

**Testing** is layered, and no dimension is tested as a Cartesian product
([`docs/testing-policy.md`](mcp-server-template/docs/testing-policy.md)): unit (in-process MCP
client) → integration (the real server over real stdio) → Python/OS matrix → pinned AI-client
contract → live upstream (self-hosted runner only) → packaged wheel → manual.

**Releases** are git tags, never commits. The version comes from the tag (`setuptools_scm`), the
release notes come from `CHANGELOG.md`'s section for that version, PyPI publishing uses OIDC
trusted publishing, and the tag is pushed by a workflow so that it is checked the same way every
time ([`docs/releasing.md`](mcp-server-template/docs/releasing.md)).

## What is in the template

| Path | What it is | PrivacyFence original |
|---|---|---|
| `CLAUDE.md` | Claude Code-only notes: the commands, skills, worktree convention; links out for all process | `CLAUDE.md` |
| `CONTRIBUTING.md` | Branch naming, PR rules, `releases/*` branches, plans vs ADRs | `CONTRIBUTING.md` |
| `.claude/commands/make-plan.md` | Planner: small scope → prompt; large → plan + manifest + manual-steps artifact | same, generalized |
| `.claude/commands/implement.md` | Orchestrator: child sessions per phase, merge, Opus review, one PR | same, generalized |
| `.claude/commands/dod.md` | The definition-of-done gate as a report | same, rewritten for this stack |
| `.claude/commands/cut-release.md` | Pre-flight → dry run → cut | same, without R2/packaging jobs |
| `.claude/commands/qa-record.md` | Record a live upstream fixture on the self-hosted runner | generalized from connector fixtures |
| `.claude/skills/steward/SKILL.md` | What to dispatch vs run locally; which PRs to follow; red checks | same, generalized |
| `.claude/hooks/session-start.sh` | Web sessions: unshallow + fetch tags, venv, install, PATH | same, without Node/Playwright |
| `.claude/settings.json` | The hook, and an allowlist of read-only and gate commands | same |
| `docs/coding-and-testing-guidelines.md` | Code and test conventions, MCP tool rules, **definition of done** | same, rewritten for MCP tools |
| `docs/testing-policy.md` | The seven test layers and where each runs | same, layers adapted |
| `docs/releasing.md`, `docs/release-testing.md` | Versioning, tagging, notes, PyPI; release gates | same, trimmed |
| `docs/live-qa.md` | QA account, self-hosted runner, recording fixtures | `docs/connector-qa.md`, generalized |
| `docs/adr/README.md` + `0001`–`0009` | ADR rules, template, index, and the decisions the template itself embodies | README same; ADRs condensed from PrivacyFence's |
| `.github/workflows/tests.yml` | Coverage + ratchet, Python matrix, Windows/macOS, static analysis | same, without shim/website/org jobs |
| `.github/workflows/build.yml` | sdist/wheel → packaged smoke on 3 OSes → TestPyPI → PyPI → GitHub Release | `build.yml` + `publish-pypi.yml`, merged |
| `.github/workflows/release.yml` | Cut the tag on a runner, dry run by default | same |
| `.github/workflows/live-check.yml`, `qa-record-fixture.yml` | Live upstream checks on the self-hosted runner | `connector-live-check.yml`, `qa-record-fixture.yml` |
| `.github/pull_request_template.md`, `CODEOWNERS`, `dependabot.yml` | PR checklist mirroring the DoD; owner review; grouped weekly bumps | same |
| `scripts/pre_release_check.py` | Every blocking CI check, PASS/FAIL each | same |
| `scripts/check_coverage_floor.py` | Coverage ratchet: overall and per-module floors | same |
| `scripts/mypy_strict_modules.py` | mypy ratchet over modules promoted in `pyproject.toml` | same |
| `scripts/changelog_section.py`, `tag_release.py`, `release_channel.py` | Release notes render; safe tagging; channel from version | same; `r2_release.py channel` became `release_channel.py` |
| `scripts/update_branch_protection.py` | The reviewed list of required checks; `show` / `apply` via `gh` | same idea, classic protection API |
| `scripts/live_check.py` | Live upstream check/record registry | `qa_fixture_recorder.py`, generalized |
| `src/__PACKAGE__/` | A minimal MCP server on the official SDK (`mcp.server.mcpserver`) | — |
| `tests/` | Unit (in-process client), integration (real stdio), packaged (installed wheel), script tests, no-history guard | patterns from PrivacyFence's suite |

## Set up a new repository

About 30 minutes, most of it in GitHub and PyPI settings pages. You need: a GitHub account that can
create the repository, Python 3.11+, git, and optionally the [GitHub CLI](https://cli.github.com/)
(`gh`) for the branch-protection step.

### 1. Choose the names

| Placeholder | Flag | Example | Used for |
|---|---|---|---|
| `__DISPLAY_NAME__` | `--display-name` | `Acme MCP` | Human-readable name in docs |
| `__DIST_NAME__` | `--dist-name` | `acme-mcp` | PyPI name, command name, MCP server name (kebab-case) |
| `__PACKAGE__` | `--package` (optional) | `acme_mcp` | Python import name; defaults to the dist name with `_` |
| `__OWNER__` | `--owner` | `acme` | GitHub user or organization |
| `__REPO__` | `--repo` | `acme-mcp` | GitHub repository name; also the self-hosted runner label `<repo>-qa` |
| `__MAINTAINER__` | `--maintainer` | `your-handle` | `CODEOWNERS` |
| `__AUTHOR_NAME__`, `__CONTACT_EMAIL__` | `--author`, `--email` | | `pyproject.toml`, `SECURITY.md`, first commit |
| `__DESCRIPTION__` | `--description` (optional) | | `pyproject.toml`, `README.md` |
| `__DATE__` | automatic | today | The seed ADRs' Accepted date |

Check the PyPI name is free: `https://pypi.org/project/<dist-name>/` should be a 404.

### 2. Generate the repository

```bash
git clone https://github.com/andras-tkcs/dev-env.git
dev-env/scripts/new-mcp-server.sh ~/Coding/acme-mcp \
  --display-name "Acme MCP" --dist-name acme-mcp \
  --owner acme --repo acme-mcp --maintainer your-handle \
  --author "Your Name" --email you@example.com \
  --description "Lets an AI assistant search Acme's catalogue."
```

The script copies the template (dotfiles included), renames `src/__PACKAGE__/`, replaces every
placeholder, refuses to finish if any is left, and commits on `main`. `--no-git` skips the commit.

### 3. Prove it locally

```bash
cd ~/Coding/acme-mcp
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python scripts/pre_release_check.py
```

Every row should say PASS. The suite starts the real server over stdio, so this also proves the
entry point works.

### 4. Add a license

The template ships none, on purpose. Add a `LICENSE` (for example Apache-2.0, like this repo and
PrivacyFence), add `license = "Apache-2.0"` under `[project]` in `pyproject.toml`, and commit.

### 5. Create the GitHub repository and push

Create an **empty** repository (no README, license or `.gitignore`) at
`https://github.com/new`, then:

```bash
git remote add origin git@github.com:acme/acme-mcp.git
git push -u origin main
```

The first push runs `tests.yml`; wait for it to go green before protecting `main`, because GitHub
only offers a check as "required" once it has run.

### 6. Repository settings

In **Settings → General**:

- **Pull Requests**: allow **merge commits**; untick squash merging and rebase merging (every
  commit on a branch lands in `main`, per `CONTRIBUTING.md`). Tick **Automatically delete head
  branches**.

In **Settings → Code security**: turn on **Private vulnerability reporting** (`SECURITY.md` points
at it), **Dependabot alerts** and **Dependabot security updates**.

**Protect `main`.** With `gh` authenticated as an admin:

```bash
python3 scripts/update_branch_protection.py apply
python3 scripts/update_branch_protection.py show     # should report no drift
```

Or by hand in **Settings → Branches → Add classic branch protection rule** for `main`: require a
pull request with 1 approval and code-owner review, require conversation resolution, require
status checks `test`, `Test (Python 3.11)`, `Test (Python 3.12)`, `Test (Python 3.14)`,
`static-analysis` (plus `Test (windows-latest)` and `Test (macos-latest)` if you add them to
`REQUIRED_STATUS_CHECKS`), and block force pushes and deletion.

### 7. Release secret and environments

1. Create a **fine-grained personal access token** at
   `https://github.com/settings/personal-access-tokens/new`: resource owner = the repo's owner,
   **Only select repositories** = this one, permission **Contents: Read and write**, nothing else.
   Set an expiry and a reminder to rotate it.
2. Add it as an Actions secret named `RELEASE_TAG_TOKEN` in **Settings → Secrets and variables →
   Actions → New repository secret**. It must not be the `GITHUB_TOKEN` (ADR 0006).
3. Create three environments in **Settings → Environments**: `release`, `testpypi`, `pypi`.
   Optionally add yourself as a **required reviewer** on `pypi` (and/or `release`) for a manual
   go/no-go before anything is published.

### 8. PyPI trusted publishing

On **both** `https://test.pypi.org/manage/account/publishing/` and
`https://pypi.org/manage/account/publishing/` (separate accounts), add a **pending publisher**:

| Field | Value |
|---|---|
| PyPI Project Name | your dist name (`acme-mcp`) |
| Owner | `acme` |
| Repository name | `acme-mcp` |
| Workflow name | `build.yml` |
| Environment name | `testpypi` on TestPyPI, `pypi` on PyPI |

No token is stored anywhere (ADR 0009). Only stable tags publish; pre-releases get a GitHub
pre-release with the files attached.

### 9. Claude Code

- **Claude Code on the web / the Claude app**: install the Claude GitHub App on the repository
  (`https://github.com/apps/claude/installations/select_target`), then pick the repository when
  starting a session. The environment's network access must reach PyPI for the session-start hook's
  `pip install`; the default trusted network setting does. The hook (`.claude/hooks/session-start.sh`)
  runs only in web sessions: it restores full history and tags, creates `.venv`, installs the
  package with its dev extra and puts `.venv/bin` first on `PATH`.
- **Locally**: nothing to install beyond the venv; `.claude/commands/` and `.claude/skills/` are
  picked up from the checkout. Follow `CLAUDE.md`'s worktree convention when running several
  sessions at once.
- Try it: `/dod` in a session should report every blocking row PASS.

### 10. First release (optional, recommended)

A pre-release proves the whole pipeline without touching PyPI:

1. Ask a session for `/cut-release 0.1.0a1`. It dispatches `build.yml` as a pre-flight, then
   `release.yml` with `dry_run: true`, and reports.
2. Tell it to cut for real. The tag starts `build.yml`, which builds, smoke-tests the wheel on
   Linux, Windows and macOS, and creates a GitHub pre-release.

For the first **stable** release, first open a PR that turns `## [Unreleased]` in `CHANGELOG.md`
into `## [0.1.0] — <date>` with a fresh empty `[Unreleased]` above it (`docs/releasing.md`).

### 11. Live upstream checks (only when the server calls an external API)

Follow [`docs/live-qa.md`](mcp-server-template/docs/live-qa.md): a dedicated QA account, a
self-hosted runner labelled `<repo>-qa` holding its credentials as files, a `LiveCheck` per
endpoint in `scripts/live_check.py`, then uncomment the `schedule:` in `live-check.yml`. Until then
both live workflows stay dispatch-only and idle.

## After setup: making it your server

- **Replace the placeholder tools.** `echo` and `server_info` in `src/<package>/server.py` exist
  to prove the transport. Follow "Adding a tool" in `docs/coding-and-testing-guidelines.md`, and
  update the tool-list assertions in `tests/unit/test_server.py` and the README's tool table.
- **Coverage floors.** `OVERALL_FLOOR` starts at 100. If you lower it, say why in the PR; add
  per-module floors in `scripts/check_coverage_floor.py` for the modules whose failure would matter
  most (auth, input validation, anything deciding what data leaves the server).
- **mypy ratchet.** Promote each new module with a `[[tool.mypy.overrides]]` block once it is
  clean.
- **Streamable HTTP.** If the server should also be reachable over HTTP, add the transport in
  `__main__.py`, an integration test that drives it with `mcp.Client("<url>")`, and an ADR for the
  trust boundary (who can reach the port, how requests are authenticated).
- **Record your own decisions** from `0010` on. The nine inherited ADRs stay until a new ADR
  supersedes one.

## What was left out, and how to add it back

PrivacyFence carries machinery that belongs to its product, not to the working mode. None of it is
in the template:

| Left out | Add it back when |
|---|---|
| Native installers (DMG/`.pkg`, Windows installer, `.deb`), code signing, graphical-session workflows | The server ships as a desktop app rather than a `pip`/`uvx` package |
| `.mcpb` Claude Desktop extension and its Node shim | You want one-click install in Claude Desktop |
| Cloudflare R2 archive and download Worker | You distribute builds outside PyPI and GitHub Releases |
| Pinned AI-client contract tests and the weekly `@latest` canary | Users depend on a specific client; see "Client contract tests" in `docs/testing-policy.md` |
| Lockfiles (`requirements/*.lock.txt`) and `dependency-audit.yml` | The server is deployed as an application with pinned dependencies |
| Website, design system, browser tests | The project has a UI |
| The MCP registry publishing workflow | You want the server listed in the official MCP registry |

## Changing the template

The template is plain files: edit them, then prove the result still passes its own gate.

```bash
rm -rf /tmp/tpl-check
scripts/new-mcp-server.sh /tmp/tpl-check --display-name "Check" --dist-name tpl-check \
  --owner o --repo r --maintainer m --author a --email a@example.com
cd /tmp/tpl-check && python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]" \
  && .venv/bin/python scripts/pre_release_check.py
```

Placeholders are `__UPPER_CASE__` tokens; the script only replaces the names in the table above, so
Python dunders (`__init__`, `__version__`) are never touched. When PrivacyFence's process changes,
port the change here in the same generalized form, and note it in the target repositories by
adding an ADR there if it changes a decision.
