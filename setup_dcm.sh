#!/usr/bin/env bash
# Download the DCM inputs, then install AlterNet with Pixi.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$REPO_DIR/download_dcm_inputs.sh"
bash "$REPO_DIR/install_alternet.sh"

printf '\nSetup complete. Start the DCM run in tmux with:\n  cd "%s"\n  ./run_dcm_tmux.sh\n' "$REPO_DIR"
