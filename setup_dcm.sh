#!/usr/bin/env bash
# Download the DCM inputs, then install AlterNet with Pixi.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$REPO_DIR/download_dcm_inputs.sh"
bash "$REPO_DIR/install_alternet.sh"

printf '\nSetup complete. Start the DCM run with:\n  cd "%s/AlterNetCode"\n  pixi run python run_dcm.py\n' "$REPO_DIR"
