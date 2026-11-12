#!/usr/bin/env bash
# Download the three external inputs used by AlterNetCode/run_dcm.py.
# Usage from the repository root: bash download_dcm_inputs.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
download_tmp=""

cleanup() {
    if [[ -n "$download_tmp" ]]; then
        rm -f -- "$download_tmp"
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

checksum() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

download() {
    local file_id="$1" relative_path="$2" expected_sha256="$3"
    local target="$REPO_DIR/$relative_path"

    if [[ -f "$target" ]] && [[ "$(checksum "$target")" == "$expected_sha256" ]]; then
        printf 'Already present: %s\n' "$relative_path"
        return
    fi

    mkdir -p "$(dirname "$target")"
    download_tmp="$(mktemp "${target}.part.XXXXXX")"
    printf 'Downloading: %s\n' "$relative_path"
    curl --fail --location --retry 2 --connect-timeout 30 \
        "https://drive.usercontent.google.com/download?id=${file_id}&export=download&confirm=t" \
        --output "$download_tmp"

    if [[ "$(checksum "$download_tmp")" != "$expected_sha256" ]]; then
        printf 'Checksum mismatch for %s. Check the Drive link or try again.\n' "$relative_path" >&2
        exit 1
    fi
    mv -- "$download_tmp" "$target"
    download_tmp=""
}

download "1MCmsYYRK2_YOY00P4Ge3eTsVKy69Q_rj" \
    "files/matrix/filtered/transcript_tpm_filtered.tsv" \
    "7f765ba264becd0d799bd9aa2757e4b3419e56f334ca3520ebdc24e8de6a5aa2"

download "13WdN43Z2VJUrbOtCkar6BiEa2Tw28d9e" \
    "files/special_files/biomart_ensembl116.txt" \
    "bf5a206246dcd64b48de9c103788f9773de3144f7f83463381bbc18d863d020e"

download "1qsYYQbGV6dSeisZ5_d_iztgG2jqeCHaG" \
    "files/special_files/appris_data.appris.txt" \
    "a69a3e7ffc194d934c8bdeed8eaef1a9127aa3db71b697f26313170497b3bad0"

printf 'All DCM inputs are ready.\n'
