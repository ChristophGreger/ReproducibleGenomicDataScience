# Reproducible Genomic Data Science

Seminar project reproducing **Figure 3E/F of AlterNet** using RNA-seq data from **166 MAGNet samples with dilated cardiomyopathy (DCM)**.

**Paper:** [AlterNet: Alternative splicing-aware gene regulatory network inference](https://doi.org/10.1101/2025.11.21.689745) · [Local PDF](Paper.pdf)

[`AlterNetCode/`](AlterNetCode/) contains a local copy of [the authors' code](https://github.com/bionetslab/alternet), based on commit [`ce1d35b`](https://github.com/bionetslab/alternet/commit/ce1d35b827f02917d0ceaf19eee037e5fb06d396).

## Set up and run DCM

Clone the repository and enter the project directory:

```bash
git clone https://github.com/ChristophGreger/ReproducibleGenomicDataScience.git
cd ReproducibleGenomicDataScience
```

Install the [external DCM tools](environment.md#dcm-setup-and-execution), including [Pixi](https://pixi.prefix.dev/latest/installation/). The supported platform is Linux x86_64.

From the repository root:

```bash
./setup_dcm.sh
```

This downloads the prepared DCM inputs into `files/` and all five original AlterNet example files into `AlterNetCode/data/` from Google Drive, then installs AlterNet with Pixi. The data files are not tracked in Git. Downloads are checked against SHA-256 checksums, and existing files with matching checksums are skipped.

To download the inputs without installing the environment, run `bash download_dcm_inputs.sh` from the repository root.

See [Rebuilding the inputs](environment.md#rebuilding-the-inputs) for the preprocessing setup and the storage and network constraints of the available university machines.

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

Preprocessing is complete and the Linux setup works. The full DCM run has started on `bs201.ur.de` (Debian 12 Bookworm, Intel Xeon w3-2435); its first canonical repetition completed in 15 minutes 50 seconds. About 5-10 hours of computation left.
  
Update November 13: The reset of the workstations deleted the finished run. Started new Run. Results probably on November 14

Details: [Data sources](data.md) · [Software environment](environment.md) · [Reproducibility log](reproducibility_log.md) · [Preprocessing steps](Steps/) 

## AI Declaration

Of course, almost none of the documentation or scripts here were written by hand; they were created with AI assistance. I always gave precise instructions for everything, though, except for the script documentation, which is clearly marked as ChatGPT stuff. But I do understand all of it myself (except for that one marked bit, which I don't use but am leaving in for the future). It was still a shitload of work, and I've already gone way beyond the scope of this seminar.
