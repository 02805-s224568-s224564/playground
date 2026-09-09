#!/usr/bin/env bash
#
# Run this once after cloning. It:
#   1. creates a .venv virtualenv,
#   2. installs the Python packages from requirements.txt,
#   3. installs the nbstripout git filter into .git/config.
#
# Step 3 is the one that cannot be skipped: the filter lives in .git/config,
# which is not part of the clone, so without it git silently commits notebook
# outputs and merges start conflicting.
#
# Safe to re-run.

set -euo pipefail

cd "$(dirname "$0")/.."

# --- 1. Find a usable Python -------------------------------------------------
PYTHON=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "error: no Python 3.12+ found on PATH." >&2
  echo "       Install one from https://www.python.org/downloads/ and re-run." >&2
  exit 1
fi

echo "==> Using $("$PYTHON" --version) at $(command -v "$PYTHON")"

# --- 2. Virtualenv + packages ------------------------------------------------
if [ ! -d .venv ]; then
  echo "==> Creating .venv"
  "$PYTHON" -m venv .venv
else
  echo "==> Reusing existing .venv"
fi

# Windows (Git Bash) puts the executables in Scripts/ instead of bin/.
if [ -x .venv/bin/python ]; then
  VENV_BIN=".venv/bin"
elif [ -x .venv/Scripts/python.exe ]; then
  VENV_BIN=".venv/Scripts"
else
  echo "error: .venv looks broken — delete it and re-run this script." >&2
  exit 1
fi

echo "==> Installing packages from requirements.txt"
"$VENV_BIN/python" -m pip install --quiet --upgrade pip
"$VENV_BIN/python" -m pip install --quiet -r requirements.txt

# --- 3. nbstripout git filter ------------------------------------------------
echo "==> Installing the nbstripout git filter"
"$VENV_BIN/nbstripout" --install --attributes .gitattributes

if "$VENV_BIN/nbstripout" --is-installed; then
  echo "==> nbstripout is active for this clone"
else
  echo "warning: nbstripout did not register — notebook outputs will be committed." >&2
  exit 1
fi

cat <<'EOF'

Done. Activate the environment with:

    source .venv/bin/activate        # macOS / Linux
    .venv\Scripts\activate           # Windows (PowerShell)

then start working:

    jupyter lab

EOF
