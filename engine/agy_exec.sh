#!/usr/bin/env bash
# agy_exec.sh: Runs a single turn in AGY CLI cleanly using isolated environment
set -euo pipefail

PROMPT="${1:-}"
BASE_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
WORKSPACE_DIR="${WORKSPACE_DIR:-$BASE_DIR/workspace}"
LOG_FILE="${LOG_FILE:-$BASE_DIR/logs/agy.log}"
GEMINI_DIR="${GEMINI_DIR:-$BASE_DIR/auth/gemini_profile}"
XDG_DATA_HOME="${XDG_DATA_HOME:-$BASE_DIR/auth/xdg-data}"

if [[ -z "$PROMPT" ]]; then
  echo "Error: Prompt cannot be empty" >&2
  exit 1
fi

AGY_BIN="${AGY_BIN:-$(which agy 2>/dev/null || echo "$BASE_DIR/bin/agy")}"
if [[ ! -x "$AGY_BIN" ]]; then
  echo "Error: AGY binary not found at $AGY_BIN" >&2
  exit 1
fi

export XDG_DATA_HOME
mkdir -p "$WORKSPACE_DIR" "$LOG_FILE" "$(dirname "$LOG_FILE")" "$GEMINI_DIR" "$XDG_DATA_HOME"
cd "$WORKSPACE_DIR"

exec "$AGY_BIN" --dangerously-skip-permissions \
  --gemini_dir="$GEMINI_DIR" \
  -p "$PROMPT"
