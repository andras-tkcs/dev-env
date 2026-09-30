#!/usr/bin/env bash
# Create a new MCP server repository from mcp-server-template/.
#
# Copies the template into <target-dir>, replaces every __PLACEHOLDER__ token, renames
# src/__PACKAGE__/, and makes the first commit on `main`. It does not create the GitHub repository
# or push anything: README.md's "Set up a new repository" walks through that part, because most of
# it (branch protection, secrets, PyPI) is a settings page only the owner can open.
#
# Usage:
#   scripts/new-mcp-server.sh <target-dir> \
#     --display-name "Acme MCP" --dist-name acme-mcp --owner acme --repo acme-mcp \
#     --maintainer your-github-handle --author "Your Name" --email you@example.com \
#     [--description "One line on what the server does"] [--no-git] [--force]
#
# --dist-name is the PyPI / command name (kebab-case). The Python package name is derived from it
# (acme-mcp -> acme_mcp) unless --package is given.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../mcp-server-template" && pwd)"

die() { echo "error: $*" >&2; exit 1; }

TARGET=""
DISPLAY_NAME="" DIST_NAME="" PACKAGE="" OWNER="" REPO="" MAINTAINER="" AUTHOR="" EMAIL=""
DESCRIPTION="An MCP server."
DO_GIT=1 FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --display-name) DISPLAY_NAME="$2"; shift 2 ;;
    --dist-name)    DIST_NAME="$2"; shift 2 ;;
    --package)      PACKAGE="$2"; shift 2 ;;
    --owner)        OWNER="$2"; shift 2 ;;
    --repo)         REPO="$2"; shift 2 ;;
    --maintainer)   MAINTAINER="$2"; shift 2 ;;
    --author)       AUTHOR="$2"; shift 2 ;;
    --email)        EMAIL="$2"; shift 2 ;;
    --description)  DESCRIPTION="$2"; shift 2 ;;
    --no-git)       DO_GIT=0; shift ;;
    --force)        FORCE=1; shift ;;
    -h|--help)      sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)             die "unknown option $1" ;;
    *)              [ -z "$TARGET" ] || die "only one target directory"; TARGET="$1"; shift ;;
  esac
done

[ -n "$TARGET" ] || die "no target directory given (see --help)"
for var in DISPLAY_NAME DIST_NAME OWNER REPO MAINTAINER AUTHOR EMAIL; do
  [ -n "${!var}" ] || die "--$(echo "$var" | tr 'A-Z_' 'a-z-') is required"
done
[ -n "$PACKAGE" ] || PACKAGE="$(echo "$DIST_NAME" | tr '-' '_' | tr 'A-Z' 'a-z')"

[[ "$DIST_NAME" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || die "--dist-name must be lowercase kebab-case"
[[ "$PACKAGE" =~ ^[a-z_][a-z0-9_]*$ ]] || die "--package must be a valid Python identifier"
[[ "$MAINTAINER" != @* ]] || MAINTAINER="${MAINTAINER#@}"
for value in "$DISPLAY_NAME" "$DESCRIPTION" "$AUTHOR"; do
  [[ "$value" != *"|"* ]] || die "values may not contain '|'"
done

if [ -e "$TARGET" ] && [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
  [ "$FORCE" = 1 ] || die "$TARGET exists and is not empty (pass --force to copy into it anyway)"
fi
mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"

echo "==> Copying template into $TARGET"
# `cp -a dir/.` copies dotfiles (.claude/, .github/) too.
cp -a "$TEMPLATE_DIR/." "$TARGET/"
find "$TARGET" -name '__pycache__' -type d -prune -exec rm -rf {} +

echo "==> Renaming src/__PACKAGE__ -> src/$PACKAGE"
mv "$TARGET/src/__PACKAGE__" "$TARGET/src/$PACKAGE"

echo "==> Replacing placeholders"
TODAY="$(date -u +%Y-%m-%d)"
YEAR="$(date -u +%Y)"
# Longest tokens first is not needed (none is a prefix of another), but every token is anchored on
# its double underscores so `__init__`/`__version__`/`__main__` are never touched.
grep -rlZ --exclude-dir=.git -e '__[A-Z][A-Z_]*__' "$TARGET" | while IFS= read -r -d '' file; do
  sed -i \
    -e "s|__DISPLAY_NAME__|$DISPLAY_NAME|g" \
    -e "s|__DIST_NAME__|$DIST_NAME|g" \
    -e "s|__PACKAGE__|$PACKAGE|g" \
    -e "s|__OWNER__|$OWNER|g" \
    -e "s|__REPO__|$REPO|g" \
    -e "s|__MAINTAINER__|$MAINTAINER|g" \
    -e "s|__AUTHOR_NAME__|$AUTHOR|g" \
    -e "s|__CONTACT_EMAIL__|$EMAIL|g" \
    -e "s|__DESCRIPTION__|$DESCRIPTION|g" \
    -e "s|__DATE__|$TODAY|g" \
    -e "s|__YEAR__|$YEAR|g" \
    "$file"
done

left="$(grep -rnoE --exclude-dir=.git '__(DISPLAY_NAME|DIST_NAME|PACKAGE|OWNER|REPO|MAINTAINER|AUTHOR_NAME|CONTACT_EMAIL|DESCRIPTION|DATE|YEAR)__' "$TARGET" || true)"
[ -z "$left" ] || die "placeholders left behind:\n$left"

chmod +x "$TARGET"/.claude/hooks/*.sh "$TARGET"/scripts/*.py 2>/dev/null || true

if [ "$DO_GIT" = 1 ]; then
  echo "==> Initialising git on main"
  cd "$TARGET"
  if [ ! -d .git ]; then
    git init -q -b main
  fi
  git add -A
  git -c user.name="$AUTHOR" -c user.email="$EMAIL" commit -q -m "Start $DISPLAY_NAME from the MCP server template" \
    -m "Process, testing policy, ADRs and Claude Code commands copied from dev-env's mcp-server-template."
  echo "    first commit: $(git log -1 --oneline)"
fi

cat <<EOF

Done. Next:
  cd $TARGET
  python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
  .venv/bin/python scripts/pre_release_check.py     # the definition-of-done gate, should be all PASS
Then follow "Set up a new repository" in dev-env's README.md (GitHub repo, protection, secrets).
EOF
