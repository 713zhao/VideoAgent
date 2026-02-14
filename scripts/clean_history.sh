#!/usr/bin/env bash
set -euo pipefail

# Clean repository history to remove `.env` from all commits.
# Usage: run from anywhere. The script will clone a bare mirror, clean it,
# and optionally force-push the cleaned history back to the remote.

ORIGIN_URL=$(git -C "$(pwd)" remote get-url origin 2>/dev/null || true)
if [ -z "$ORIGIN_URL" ]; then
  echo "Cannot determine origin remote URL. Run this from a git repo or set ORIGIN_URL manually." >&2
  exit 1
fi

TMPDIR=$(mktemp -d /tmp/clean-repo.XXXX)
MIRROR="$TMPDIR/VideoAgent-mirror.git"
echo "Mirror clone path: $MIRROR"

echo "Cloning mirror from $ORIGIN_URL..."
git clone --mirror "$ORIGIN_URL" "$MIRROR"

cd "$MIRROR"

echo "Checking for git-filter-repo..."
if command -v git-filter-repo >/dev/null 2>&1; then
  echo "Using system git-filter-repo"
  GFR_CMD=(git-filter-repo --invert-paths --paths .env)
elif python -m git_filter_repo --version >/dev/null 2>&1 2>/dev/null; then
  echo "Using python -m git_filter_repo"
  GFR_CMD=(python -m git_filter_repo --invert-paths --paths .env)
else
  echo "git-filter-repo not installed. Will fall back to git filter-branch (slower)."
  GFR_CMD=()
fi

echo "This script will remove '.env' from all commits in the repository mirror at: $MIRROR"
echo "A backup of this mirror remains under: $TMPDIR"
echo
read -p "Proceed with cleaning the mirror repository? (yes/no) " ans
if [ "$ans" != "yes" ]; then
  echo "Aborted by user. Mirror preserved at: $MIRROR"
  exit 0
fi

if [ ${#GFR_CMD[@]} -gt 0 ]; then
  echo "Running: ${GFR_CMD[*]}"
  "${GFR_CMD[@]}"
else
  echo "Running git filter-branch fallback (this can be slow)..."
  git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
fi

echo "Cleaning reflogs and running git gc..."
git reflog expire --expire=now --all || true
git gc --prune=now --aggressive || true

echo
echo "Mirror cleaned. You can inspect it at: $MIRROR"
echo "If you are ready to overwrite the remote history, this script can force-push the cleaned history back to origin."
read -p "Force-push cleaned history to origin ($ORIGIN_URL)? This is destructive. Type 'push' to proceed: " push_ok
if [ "$push_ok" = "push" ]; then
  echo "Force-pushing cleaned tags and branches to origin..."
  git push --force --all origin
  git push --force --tags origin
  echo "Force-push complete. Notify collaborators to re-clone the repository." 
else
  echo "Skipped force-push. Mirror left at: $MIRROR"
fi

echo "DONE"
