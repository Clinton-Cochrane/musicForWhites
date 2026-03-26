#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
ACTIVATE_FILE="$VENV_DIR/bin/activate"

if [[ ! -f "$ACTIVATE_FILE" ]]; then
    echo "ERROR: Missing activation script at $ACTIVATE_FILE"
    exit 1
fi

echo "Checking venv in: $VENV_DIR"

# shellcheck source=/dev/null
source "$ACTIVATE_FILE"

if [[ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]]; then
    echo "ERROR: VIRTUAL_ENV mismatch"
    echo "  expected: $VENV_DIR"
    echo "  actual:   ${VIRTUAL_ENV:-<unset>}"
    exit 1
fi

PYTHON_BIN="$(command -v python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
    echo "ERROR: python not found after activation"
    exit 1
fi

EXPECTED_PYTHON="$VENV_DIR/bin/python"
if [[ "$PYTHON_BIN" != "$EXPECTED_PYTHON" ]]; then
    echo "ERROR: wrong python selected"
    echo "  expected: $EXPECTED_PYTHON"
    echo "  actual:   $PYTHON_BIN"
    exit 1
fi

PREFIX_OUTPUT="$(python - <<'PY'
import sys
print(sys.prefix)
print(sys.base_prefix)
print(sys.executable)
PY
)"

SYS_PREFIX="$(printf '%s\n' "$PREFIX_OUTPUT" | sed -n '1p')"
BASE_PREFIX="$(printf '%s\n' "$PREFIX_OUTPUT" | sed -n '2p')"
SYS_EXECUTABLE="$(printf '%s\n' "$PREFIX_OUTPUT" | sed -n '3p')"

if [[ "$SYS_PREFIX" != "$VENV_DIR" ]]; then
    echo "ERROR: sys.prefix mismatch"
    echo "  expected: $VENV_DIR"
    echo "  actual:   $SYS_PREFIX"
    exit 1
fi

if [[ "$SYS_EXECUTABLE" != "$EXPECTED_PYTHON" ]]; then
    echo "ERROR: sys.executable mismatch"
    echo "  expected: $EXPECTED_PYTHON"
    echo "  actual:   $SYS_EXECUTABLE"
    exit 1
fi

if [[ "$BASE_PREFIX" == "$SYS_PREFIX" ]]; then
    echo "ERROR: base_prefix equals prefix (venv not isolated)"
    exit 1
fi

echo "OK: activation and python isolation look good."
