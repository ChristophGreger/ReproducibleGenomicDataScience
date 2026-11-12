#!/usr/bin/env bash
# Start the DCM analysis in a detached tmux session.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION="alternet"

for program in tmux pixi; do
    if ! command -v "$program" >/dev/null 2>&1; then
        printf 'Please install %s and make it available in your terminal first.\n' "$program" >&2
        exit 1
    fi
done

if tmux has-session -t "=$SESSION" 2>/dev/null; then
    printf 'Session %s already exists. Open it with: tmux attach -t %s\n' "$SESSION" "$SESSION"
    exit 0
fi

PIXI_BIN="$(command -v pixi)"
tmux new-session -d -s "$SESSION" -c "$REPO_DIR/AlterNetCode" \
    bash -c '
        "$1" run python -u run_dcm.py
        run_status=$?
        printf "\nDCM command finished (exit code %s).\n" "$run_status"
        exec bash
    ' bash "$PIXI_BIN"

printf 'DCM started in tmux session %s.\n' "$SESSION"
printf 'Show output: tmux attach -t %s\n' "$SESSION"
printf 'Detach again: press Ctrl+B, release both keys, then press D.\n'
