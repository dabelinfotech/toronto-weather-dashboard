#!/usr/bin/env bash
#
# push_to_github.sh
# -------------------
# Initializes this project as a git repo and pushes it to a GitHub
# repository under the dabelinfotech organization (or any org/user you set).
#
# Two modes:
#   1. Automatic repo creation (recommended) -- uses the GitHub CLI (`gh`)
#      to create the remote repo for you, then pushes.
#   2. Manual -- if you already created the repo on github.com, this script
#      will just wire up the remote and push.
#
# Usage:
#   chmod +x push_to_github.sh
#   ./push_to_github.sh
#
# Configure the variables below (or export them as env vars before running).

set -euo pipefail

# ---------------------------------------------------------------------------
# CONFIGURATION -- edit these or export as environment variables
# ---------------------------------------------------------------------------
GITHUB_ORG="${GITHUB_ORG:-dabelinfotech}"
REPO_NAME="${REPO_NAME:-toronto-weather-dashboard}"
REPO_VISIBILITY="${REPO_VISIBILITY:-public}"     # public | private
REPO_DESCRIPTION="${REPO_DESCRIPTION:-Hourly weather data cleaning, KPI analysis, and interactive HTML dashboard for Toronto, 2012.}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-Initial commit: weather cleaning pipeline + KPI dashboard}"

# ---------------------------------------------------------------------------
# 1. Sanity checks
# ---------------------------------------------------------------------------
if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed. Install git and re-run." >&2
  exit 1
fi

HAS_GH=false
if command -v gh >/dev/null 2>&1; then
  HAS_GH=true
fi

# ---------------------------------------------------------------------------
# 2. Initialize local git repo (idempotent)
# ---------------------------------------------------------------------------
if [ ! -d ".git" ]; then
  echo "Initializing git repository..."
  git init -b "$DEFAULT_BRANCH"
else
  echo "Git repository already initialized."
fi

git add .
if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "$COMMIT_MESSAGE"
fi

# ---------------------------------------------------------------------------
# 3. Create the remote repo (if it doesn't already exist) and push
# ---------------------------------------------------------------------------
REMOTE_URL="https://github.com/${GITHUB_ORG}/${REPO_NAME}.git"

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote 'origin' already set to: $(git remote get-url origin)"
else
  if [ "$HAS_GH" = true ]; then
    echo "Creating GitHub repo ${GITHUB_ORG}/${REPO_NAME} via GitHub CLI..."
    gh repo create "${GITHUB_ORG}/${REPO_NAME}" \
      --"${REPO_VISIBILITY}" \
      --description "${REPO_DESCRIPTION}" \
      --source=. \
      --remote=origin \
      --push
    echo "Done -- repo created and pushed."
    exit 0
  else
    echo "GitHub CLI ('gh') not found."
    echo "Create the repo manually at: https://github.com/organizations/${GITHUB_ORG}/repositories/new"
    echo "Then re-run this script, or run:"
    echo "  git remote add origin ${REMOTE_URL}"
    echo "  git push -u origin ${DEFAULT_BRANCH}"
    git remote add origin "$REMOTE_URL"
  fi
fi

# ---------------------------------------------------------------------------
# 4. Push
# ---------------------------------------------------------------------------
echo "Pushing to ${REMOTE_URL} ..."
git push -u origin "$DEFAULT_BRANCH"
echo "Push complete: https://github.com/${GITHUB_ORG}/${REPO_NAME}"
