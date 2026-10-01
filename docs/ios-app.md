# The iOS app template

[`templates/ios-app/`](../templates/ios-app/) is a SwiftUI iPhone and iPad app with its logic in a
Swift package, tested on simulators in CI and shipped to TestFlight from a tag. The working mode it
carries is described once, for every template, in [`working-mode.md`](working-mode.md); this page
is what is specific to iOS apps.

- [What is in the template](#what-is-in-the-template)
- [How the working mode maps onto iOS](#how-the-working-mode-maps-onto-ios)
- [Set up a new repository](#set-up-a-new-repository)
- [After setup: making it your app](#after-setup-making-it-your-app)
- [What was left out, and how to add it back](#what-was-left-out-and-how-to-add-it-back)

## What is in the template

| Path | What it is | MCP template counterpart |
|---|---|---|
| `App/` | The SwiftUI app: one screen with a name field, a greeting and the version; assets | `src/<package>/server.py` |
| `AppCore/` | A Swift package holding the app's logic (`Greeting`, `AppInfo`), Foundation only, tested with Swift Testing; builds on Linux | — (the split exists because the app itself needs a Mac) |
| `AppTests/`, `AppUITests/` | Hosted tests that read the built bundle; XCUITests that launch the app and type into it | `tests/unit/`, `tests/integration/` |
| `project.yml` | The Xcode project as an XcodeGen spec; the `.xcodeproj` is generated and git-ignored | `pyproject.toml` |
| `.swift-format` | Formatter and linter configuration (100 columns, documented public API, no force unwraps) | ruff configuration |
| `CLAUDE.md`, `CONTRIBUTING.md` | As in the MCP template, plus "Working without a Mac" | same |
| `.claude/commands/make-plan.md`, `implement.md` | Identical to the MCP template's | same file |
| `.claude/commands/dod.md` | The gate for Swift, and where to read a row a Linux session cannot run | rewritten |
| `.claude/commands/cut-release.md` | Pre-flight `build.yml`, dry run, cut; then TestFlight | adapted |
| `.claude/skills/steward/SKILL.md` | What needs a Mac and which workflow does it; what only a person does in App Store Connect | adapted |
| `.claude/hooks/session-start.sh` | Web sessions: unshallow and fetch tags (build numbers), check for a Swift toolchain, resolve AppCore | adapted |
| `docs/coding-and-testing-guidelines.md` | Where code goes, Swift and SwiftUI conventions, **definition of done** | rewritten |
| `docs/testing-policy.md` | Seven layers: unit, UI, compatibility, backend contract, release archive, distribution, manual | adapted |
| `docs/releasing.md`, `docs/release-testing.md` | Version from tag and build number from commit count; signing; TestFlight; manual device checks | adapted |
| `docs/adr/README.md` + `0001`–`0010` | ADR rules (identical above the index) and the decisions this template embodies | `0001`, `0002` identical; the rest are iOS's own |
| `.github/workflows/tests.yml` | `core` and `lint` and `scripts` on Linux; `app (iphone, newest)`, `app (iphone, oldest)`, `app (ipad, newest)` on macOS | same role |
| `.github/workflows/build.yml` | `version` → unsigned Release `archive` with a version check → signed `testflight` upload → `github-release` | same role |
| `.github/workflows/release.yml` | Cut the tag on a runner, dry run by default | same file, different version format |
| `scripts/` | Release notes, safe tagging, channel and marketing version, coverage ratchet over `llvm-cov` JSON, simulator picker, the gate, branch protection; tested with stdlib `unittest` | same scripts, adapted |

## How the working mode maps onto iOS

| Concern | How the template does it | Why (ADR) |
|---|---|---|
| Merge conflicts in the Xcode project between parallel sessions | `project.yml` is the source; `.xcodeproj` is generated and never committed | 0003 |
| A cloud session has no Mac | Logic lives in AppCore, which `swift test` runs on Linux; the app's tests come from `tests.yml` | 0007 |
| Versions | Tag `v1.2.0` or `v1.2.0-rc.1` → `MARKETING_VERSION=1.2.0`; `CURRENT_PROJECT_VERSION=$(git rev-list --count HEAD)` | 0004 |
| Release notes | `CHANGELOG.md` section → GitHub Release body; the App Store's "What's New" is written from it | 0005 |
| Cutting a release | `release.yml` pushes the tag with `RELEASE_TAG_TOKEN` after a `build.yml` pre-flight | 0006 |
| Signing and upload | Automatic signing with an App Store Connect API key in the `app-store` environment; `xcodebuild` uploads | 0009 |
| Lint | `swift format` from the toolchain; Swift 6 language mode; warnings are errors | 0010 |
| No project history in code | `scripts/tests/test_no_project_history.py` | 0008 |

## Set up a new repository

About an hour, most of it in GitHub's and Apple's settings pages. You need: a Mac with Xcode and
its iOS simulators, [Homebrew](https://brew.sh), Python 3 (Xcode's command line tools include it),
git, a paid Apple Developer Program membership for TestFlight, and optionally the
[GitHub CLI](https://cli.github.com/) (`gh`) for the branch-protection step.

### 1. Choose the names

| Placeholder | Flag | Example | Used for |
|---|---|---|---|
| `__DISPLAY_NAME__` | `--display-name` | `Acme Notes` | The name under the icon, docs |
| `__MODULE__` | `--module` (optional) | `AcmeNotes` | Xcode target, scheme and app type name; defaults to the display name in UpperCamelCase |
| `__BUNDLE_ID__` | `--bundle-id` | `com.acme.notes` | The app's bundle identifier; tests get `.tests` and `.uitests` suffixes |
| `__TEAM_ID__` | `--team-id` (optional) | `ABCDE12345` | `DEVELOPMENT_TEAM`; leave it out until you have one |
| `__OWNER__` | `--owner` | `acme` | GitHub user or organization |
| `__REPO__` | `--repo` | `acme-notes` | GitHub repository name |
| `__MAINTAINER__` | `--maintainer` | `your-handle` | `CODEOWNERS` |
| `__AUTHOR_NAME__`, `__CONTACT_EMAIL__` | `--author`, `--email` | | `SECURITY.md`, first commit |
| `__DESCRIPTION__` | `--description` (optional) | | `README.md` |
| `__DATE__`, `__TEMPLATE__` | automatic | today, `iOS app` | The seed ADRs' Accepted date and origin |

The bundle ID is permanent once the app is in App Store Connect. Check it is free by registering it
(step 7) before you build anything on it.

### 2. Generate the repository

```bash
git clone https://github.com/andras-tkcs/dev-env.git
python3 dev-env/scripts/new_project.py ios-app ~/Coding/acme-notes \
  --display-name "Acme Notes" --bundle-id com.acme.notes \
  --owner acme --repo acme-notes --maintainer your-handle \
  --author "Your Name" --email you@example.com \
  --description "Notes that sync between your iPhone and iPad."
```

The script copies the template, renames `App/__MODULE__App.swift`, replaces every placeholder,
refuses to finish if any is left, and commits on `main`. `--no-git` skips the commit.

### 3. Prove it locally

```bash
cd ~/Coding/acme-notes
brew install xcodegen
python3 scripts/pre_release_check.py
```

Every row should say PASS, with no SKIP: on a Mac it generates the project, runs AppCore's tests
with the coverage ratchet, `swift format`, the scripts' tests, and the app and UI tests on a
simulator. Then `open AcmeNotes.xcodeproj` and run it.

### 4. Add a license

The template ships none, on purpose. Add a `LICENSE` and commit.

### 5. Create the GitHub repository and push

Create an **empty** repository (no README, license or `.gitignore`) at
`https://github.com/new`, then:

```bash
git remote add origin git@github.com:acme/acme-notes.git
git push -u origin main
```

The first push runs `tests.yml`; wait for it to go green before protecting `main`, because GitHub
only offers a check as "required" once it has run. The macOS jobs take ten to twenty minutes.

### 6. Repository settings

In **Settings → General → Pull Requests**: allow **merge commits**; untick squash and rebase
merging; tick **Automatically delete head branches**. In **Settings → Code security**: turn on
**Private vulnerability reporting**, **Dependabot alerts** and **Dependabot security updates**.

**Protect `main`.** With `gh` authenticated as an admin:

```bash
python3 scripts/update_branch_protection.py apply
python3 scripts/update_branch_protection.py show     # should report no drift
```

Or by hand: require a pull request with 1 approval and code-owner review, conversation
resolution, and the status checks `core`, `lint`, `scripts`, `app (iphone, newest)`,
`app (iphone, oldest)`, `app (ipad, newest)`; block force pushes and deletion.

### 7. Apple: app record, team, API key, icon

Follow the generated repository's `docs/releasing.md`, "Signing and App Store Connect": register
the bundle ID and create the app record in App Store Connect, put your Team ID in `project.yml`'s
`DEVELOPMENT_TEAM` (in a PR), generate an App Store Connect API key, store it as `ASC_KEY_P8`,
`ASC_KEY_ID` and `ASC_ISSUER_ID` secrets of a new `app-store` environment, and add a 1024×1024
app icon. No certificate or provisioning profile is created by hand (ADR 0009).

### 8. Release secret and environments

1. Create a **fine-grained personal access token** at
   `https://github.com/settings/personal-access-tokens/new`: resource owner = the repo's owner,
   **Only select repositories** = this one, permission **Contents: Read and write**, nothing else.
   Set an expiry and a reminder to rotate it.
2. Add it as an Actions secret named `RELEASE_TAG_TOKEN`. It must not be the `GITHUB_TOKEN`
   (ADR 0006).
3. Create the `release` environment next to `app-store`. Optionally add yourself as a **required
   reviewer** on `app-store`, so every upload waits for your go.

### 9. Claude Code

- **Claude Code on the web / the Claude app**: install the Claude GitHub App on the repository
  (`https://github.com/apps/claude/installations/select_target`) and pick the repository when
  starting a session. The session is Linux: it can never build the app, and it can only run
  AppCore's tests and `swift format` if the environment has a Swift toolchain. To give it one,
  open the cloud environment's settings (the environment menu in the session's title bar, then
  **Edit**): add `download.swift.org` to **Network access**'s allowed domains (or choose a broader
  access level), and install Swift in **Setup script**, following
  [swift.org's Linux instructions](https://www.swift.org/install/linux/) so that `swift` is on the
  PATH of new shells. Without it, the session-start hook prints a `WARNING` and sessions read those
  rows from `tests.yml` instead (the steward skill says how).
- **Locally**: nothing to install beyond XcodeGen; `.claude/` is picked up from the checkout.
- Try it: `/dod` in a session should report every row PASS, or say which `tests.yml` run each
  remote row came from.

### 10. First release (recommended)

A release candidate proves the whole pipeline, signing included, without reaching the App Store:

1. Ask a session for `/cut-release 0.1.0-rc.1`. It dispatches `build.yml` as a pre-flight, then
   `release.yml` with `dry_run: true`, and reports.
2. Tell it to cut for real. The tag starts `build.yml`, which archives, signs, uploads to App Store
   Connect and creates a GitHub pre-release. The build shows up in TestFlight after Apple's
   processing.

For the first **stable** release, open a PR that turns `## [Unreleased]` in `CHANGELOG.md` into
`## [0.1.0] — <date>` with a fresh empty `[Unreleased]` above it, merge it, cut `0.1.0`, and submit
the build for review in App Store Connect.

## After setup: making it your app

- **Replace the placeholder screen.** `Greeting` in AppCore and `ContentView` exist to prove the
  layers. Follow "Adding a screen" in `docs/coding-and-testing-guidelines.md`, and replace the UI
  test with one for your first real user path.
- **Coverage floors.** `OVERALL_FLOOR` in `scripts/check_coverage_floor.py` starts at 100. Add
  per-file floors for the AppCore files whose failure would matter most (decoding, anything that
  decides what leaves the device).
- **Deployment target.** `project.yml`'s `deploymentTarget` (and `AppCore/Package.swift`'s
  `platforms`) start at iOS 18. Changing it changes what `app (iphone, oldest)` tests; record why
  in an ADR.
- **iPhone only?** Set `TARGETED_DEVICE_FAMILY: "1"` in `project.yml`, drop the `ipad` leg from
  `tests.yml` and `REQUIRED_STATUS_CHECKS`, and say so in an ADR.
- **Record your own decisions** from `0011` on. The ten inherited ADRs stay until a new ADR
  supersedes one.

## What was left out, and how to add it back

| Left out | Add it back when |
|---|---|
| A backend contract check against a live server on a self-hosted runner | The app talks to a server; see "Layer 4" in the generated `docs/testing-policy.md`, and the MCP template's `live-check.yml` and ADR 0007 as the pattern |
| Snapshot tests of views | A screen's exact rendering matters enough to review image diffs; pick a library and record it in an ADR (it is a third-party dependency) |
| Localization (String Catalogs) | The app ships in more than one language |
| A privacy manifest (`PrivacyInfo.xcprivacy`) | The app or a dependency uses an API Apple lists as needing a required reason |
| Widgets, App Clips, watchOS, macOS (Catalyst) targets | The product needs them; each is a target in `project.yml` and a leg in `tests.yml` |
| fastlane, Xcode Cloud | Rejected in ADR 0009; supersede it if your situation differs |
| Crash reporting and analytics SDKs | A third-party SDK is an ADR and a privacy-label change |
