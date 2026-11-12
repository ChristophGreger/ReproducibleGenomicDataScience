#!/usr/bin/env python3
"""Run AlterNet on the filtered 166-sample DCM data.

From the AlterNetCode directory, run:
    pixi run python run_dcm.py

Results are written to AlterNetCode/results/DCM/ with the prefix DCM.
The pipeline standardizes the TPM matrices before network inference.
"""

from pathlib import Path

import pandas as pd


ALTERNET_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ALTERNET_DIR.parent

MATRIX_PATH = PROJECT_DIR / "files/matrix/filtered/transcript_tpm_filtered.tsv"
BIOMART_PATH = PROJECT_DIR / "files/special_files/biomart_ensembl116.txt"
APPRIS_PATH = PROJECT_DIR / "files/special_files/appris_data.appris.txt"
DIGGER_PATH = ALTERNET_DIR / "data/digger_data.csv"
TF_LIST_PATH = ALTERNET_DIR / "data/allTFs_hg38.txt"

RESULTS_PATH = ALTERNET_DIR / "results/DCM"
PREFIX = "DCM"
RUNS = 10


def main():
    from alternet.runners.run_alternet import alternet_pipeline

    transcript_data = pd.read_csv(MATRIX_PATH, sep="\t")
    biomart = pd.read_csv(BIOMART_PATH, sep="\t")
    appris = pd.read_csv(APPRIS_PATH, sep="\t", low_memory=False)
    digger = pd.read_csv(DIGGER_PATH, low_memory=False)
    tf_list = pd.read_csv(TF_LIST_PATH, sep="\t", header=None)

    RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    alternet_pipeline(
        transcript_data_cp=transcript_data,
        appris_df=appris,
        digger_df=digger,
        tf_list=tf_list,
        biomart=biomart,
        results_path=RESULTS_PATH,
        prefix=PREFIX,
        runs=RUNS,
    )
    print(f"AlterNet finished. Results are in {RESULTS_PATH}", flush=True)


if __name__ == "__main__":
    main()
