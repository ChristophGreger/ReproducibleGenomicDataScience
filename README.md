# Reproducible Genomic Data Science

Seminar project reproducing **Figure 3E/F of AlterNet** using RNA-seq data from **166 MAGNet samples with dilated cardiomyopathy (DCM)**.

**Paper:** [AlterNet: Alternative splicing-aware gene regulatory network inference](https://doi.org/10.1101/2025.11.21.689745) · [Local PDF](Paper.pdf)

[`AlterNetCode/`](AlterNetCode/) contains a local copy of [the authors' code](https://github.com/bionetslab/alternet), based on commit [`ce1d35b`](https://github.com/bionetslab/alternet/commit/ce1d35b827f02917d0ceaf19eee037e5fb06d396).

## Set up and run DCM

Install the [external DCM tools](environment.md#dcm-setup-and-execution), including [Pixi](https://pixi.prefix.dev/latest/installation/). Supported platforms are Linux x86_64 

From the repository root:

```bash
./setup_dcm.sh
```

This downloads the prepared DCM inputs into `files/` and installs AlterNet with Pixi.

## Initial test

Check that the pipeline imports successfully:

```bash
(cd AlterNetCode && pixi run python -c "from alternet.runners.run_alternet import alternet_pipeline; print('Import OK')")
```

## Run

```bash
./run_dcm_tmux.sh
tmux attach -t alternet
```

Detach with **Ctrl+B**, release both keys, then press **D**. Results are saved in `AlterNetCode/results/DCM/`.

## Current status · 12 November 2026

Preprocessing is complete and the Linux setup works. The full DCM run has started on `bs201.ur.de` (Intel Xeon w3-2435); its first canonical repetition completed in 15 minutes 50 seconds. About 5-10 hours of computation left...

Details: [Data sources](data.md) · [Software environment](environment.md) · [Reproducibility log](reproducibility_log.md) · [Preprocessing steps](Steps/) 
