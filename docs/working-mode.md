# The working mode

What every project generated from dev-env shares, whatever it builds. It was taken from
PrivacyFence, an MCP server, and generalized; each template under [`templates/`](../templates/)
implements it for one kind of project. The per-template guides say what is specific:
[`mcp-server.md`](mcp-server.md), [`ios-app.md`](ios-app.md).

- [Plans, ADRs, reference docs](#plans-adrs-reference-docs)
- [From idea to merged PR with Claude Code](#from-idea-to-merged-pr-with-claude-code)
- [Testing in layers](#testing-in-layers)
- [Releases are tags](#releases-are-tags)
- [What every template provides](#what-every-template-provides)

## Plans, ADRs, reference docs

Three kinds of document, three lifecycles (each template's `docs/adr/README.md` has the full
rules, identical in every template above its index):

| Kind | Answers | Lifecycle |
|---|---|---|
| Plan (`docs/<slug>-plan.md` or an issue) | What are we about to do? | Deleted when the work lands, after its decisions are extracted into ADRs |
| ADR (`docs/adr/NNNN-*.md`) | Why is it this way, what was rejected? | Permanent; frozen once accepted; superseded, never rewritten |
| Reference (`docs/*.md`, `CONTRIBUTING.md`) | How does it work today? | Edited in the same PR as the behavior |

Every template seeds its ADRs with the decisions the template itself embodies. `0001` (plans are
temporary, ADRs permanent) and `0002` (process lives in `docs/`, not `CLAUDE.md`) are the same in
every template; the rest are the stack's own, numbered so the same concern sits at the same number
where one exists (`0004` is always where the version comes from, `0005` release notes, `0006` how a
tag is cut, `0008` no project history in code).

## From idea to merged PR with Claude Code

1. `/make-plan <idea or issue>` (on Opus) researches the change. A **small** change gets a
   self-contained prompt to paste into a fresh Sonnet session. A **large** change gets a
   `docs/<slug>-plan.md` on a `plan/<slug>` branch, with an `## Implementation manifest` of
   phases sized so a Sonnet session can do each one mechanically. Anything only a human can do
   (console setup, secrets, real-device checks) goes only at the very start (`manual_before`) or
   the very end (`manual_after`), with a step-by-step HTML page.
2. `/implement <plan URL>` (on Sonnet) orchestrates: one child session per phase on
   `feature/<slug>--<phase>` branches, merged `--no-ff` into `feature/<slug>` with a
   `Plan-Phase:` trailer, verified after each merge with the template's **fast checks**, then one
   Opus review of the whole branch against the plan, then **one** PR to `main`. The plan's last
   phase deletes the plan document and writes its ADRs.
3. `/dod` runs the template's definition of done (tests at 100% pass, coverage ratchet, linters,
   the stack's static checks) and reads the diff for the conditional and manual rows. It reports;
   it does not fix. A row that cannot run where the session is (a simulator on Linux) is read from
   CI, never assumed.
4. The **steward** skill tells a session how to drive its PR to green: what to dispatch to a runner
   instead of running locally, and that a red check is real until proven otherwise (never skip a
   test, never kick CI with an empty commit, never lower a coverage floor).
5. `/cut-release <version>` pre-flights `build.yml`, dry-runs `release.yml`, and cuts the tag only
   when you say so.

`make-plan.md` and `implement.md` are identical in every template: they never name a stack's
commands, only the documents that do (`docs/testing-policy.md`'s "Fast checks", the definition of
done in `docs/coding-and-testing-guidelines.md`, the steward skill's dispatch table).

## Testing in layers

**Do not test the full Cartesian product.** Each dimension is proven on its own, in one layer, and
only a few high-value end-to-end tests cross a boundary. Every template's `docs/testing-policy.md`
has a layers table and a "failure type → owning layer" table.

| Concern | MCP server | iOS app |
|---|---|---|
| Logic, offline | pytest, tools through the in-process MCP client | `swift test` on AppCore (Linux and macOS) |
| The real thing, end to end | The server process over real stdio | The app on a simulator, driven by XCUITest |
| Compatibility | Python versions × OS, one leg each | Newest and oldest iOS on iPhone, newest on iPad |
| A contract with something outside | Pinned AI-client CLIs (once added) | The app's backend (once it has one) |
| The live upstream | Self-hosted runner only, credentials never in GitHub | (same pattern, once added) |
| The shipped artifact | The built wheel, installed clean, on three OSes | The Release archive carries the tag's version; TestFlight accepts the signed build |
| Manual | Real AI clients pick the right tool | Real devices, VoiceOver, App Review |

A coverage ratchet guards the logic layer in every template: a floor only moves up, and lowering
one is a regression stated in the PR, never a config edit.

## Releases are tags

A release is a git tag, never a commit. The version comes from the tag, so there is no version
string to bump and no bump to collide; the release notes come from `CHANGELOG.md`'s section for
that version, written and reviewed in a PR; the tag is pushed by `release.yml` with a dedicated
token (a tag pushed with the `GITHUB_TOKEN` starts nothing), after `build.yml` was dispatched
against the same commit as a pre-flight that publishes nothing. Publishing credentials are scoped
to a GitHub Environment and used only on a tag ref.

## What every template provides

[`scripts/check_templates.py`](../scripts/check_templates.py) enforces this, and
`.github/workflows/templates.yml` runs it, plus each template's own gate in a freshly generated
sample repository, on every PR.

- **The files the working mode is made of**: `CLAUDE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`,
  `SECURITY.md`; `.claude/` with `settings.json`, the session-start hook, the steward skill and the
  `make-plan`, `implement`, `dod` and `cut-release` commands; `.github/` with the PR template,
  `CODEOWNERS`, Dependabot and the `tests.yml`, `build.yml` and `release.yml` workflows; `docs/`
  with the ADR system, the coding and testing guidelines, the testing policy, releasing and release
  testing; and `scripts/` with the gate, the coverage ratchet, the changelog renderer, the tagger,
  the channel resolver and the branch-protection list.
- **Shared files, byte-identical**: `.claude/commands/make-plan.md`, `.claude/commands/implement.md`,
  ADRs `0001` and `0002`, and `docs/adr/README.md` above its `## Index`.
- **The anchors those shared files point at**: a `## Fast checks` section in
  `docs/testing-policy.md`, and a `### Definition of done` section in
  `docs/coding-and-testing-guidelines.md`.
- **A `template.json`** declaring its placeholders, with no `__UPPER_CASE__` token in the template
  that the manifest does not declare.
