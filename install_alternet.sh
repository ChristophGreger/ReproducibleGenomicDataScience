#!/usr/bin/env bash
# Install the AlterNet environment using the repository's Pixi configuration.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v pixi >/dev/null 2>&1; then
    printf 'Please install Pixi first: https://pixi.prefix.dev/latest/installation/\n' >&2
    exit 1
fi

cd "$REPO_DIR/AlterNetCode"
pixi install
