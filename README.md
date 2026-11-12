# Reproducible Genomic Data Science

This repository contains the materials and code used to reproduce AlterNet as part of the seminar.

## AlterNet code

The [`AlterNetCode/`](AlterNetCode/) directory contains a local copy of all tracked files from [bionetslab/alternet](https://github.com/bionetslab/alternet/tree/main). The files were copied directly into this project without their Git history. The directory is neither a submodule nor a separate Git repository.

This keeps project management and version control simple: the AlterNet code is maintained alongside the other project files in this repository. Any changes needed for the reproduction can be made directly in `AlterNetCode/` and committed together with the other project changes. Updates to the original repository are not applied automatically.

Details of the imported copy:

- Source: [bionetslab/alternet](https://github.com/bionetslab/alternet)
- Branch: `main`
- Commit: [`ce1d35b827f02917d0ceaf19eee037e5fb06d396`](https://github.com/bionetslab/alternet/commit/ce1d35b827f02917d0ceaf19eee037e5fb06d396)
- Copied on: 8 November 2026

During the import, exceptions were added to `AlterNetCode/.gitignore` for the two bundled files `data/appris_data.appris.txt` and `data/digger_data.csv` so that they can also be tracked normally in this repository. All other files were copied without changes.

After the import, GPT-6 Astra switched the SignifiKANTE dependency from SSH to HTTPS at my request and updated the corresponding lockfile entries, the local package checksum, and this README. The pinned SignifiKANTE commit and package versions were preserved.

Codex (GPT-6.1 Sol) subsequently added Intel macOS support so I can test the code on my Apple Silicon Mac using Rosetta 2, while keeping Linux support. The macOS environment uses `lda` 3.0.0 and `gseapy` 1.1.2 because these versions provide prebuilt Intel Mac packages and avoid requiring local C/Rust compilation. These version constraints apply only to macOS.

The original documentation, including installation and usage instructions, is available in [`AlterNetCode/README.md`](AlterNetCode/README.md).

## Installation with Pixi

With [Pixi](https://pixi.prefix.dev/latest/installation/) installed, run the following from the root of this repository:

```bash
./install_alternet.sh
```

[`install_alternet.sh`](install_alternet.sh) runs `pixi install` in `AlterNetCode/`. This installs the dependencies and AlterNet itself as an editable package, so changes in `AlterNetCode/src/alternet/` do not require reinstalling it.

The configuration supports **Linux x86_64 (`linux-64`)** and **Intel macOS (`osx-64`)**. On Apple Silicon Macs, Rosetta 2 must be installed; Pixi automatically selects the Intel environment. Use a current Pixi release (tested with 0.84.1).

Git is required to fetch the public `SignifiKANTE` dependency over HTTPS. No GitHub account or SSH key is needed.

## Set up and run DCM

With Pixi installed, run from the repository root:

```bash
./setup_dcm.sh
cd AlterNetCode
pixi run python run_dcm.py
```

[`setup_dcm.sh`](setup_dcm.sh) first calls [`download_dcm_inputs.sh`](download_dcm_inputs.sh), then [`install_alternet.sh`](install_alternet.sh). It stops if either step fails. The DCM analysis is started separately with the command shown above. Both child scripts can also be run on their own with `./download_dcm_inputs.sh` or `./install_alternet.sh`.

[`download_dcm_inputs.sh`](download_dcm_inputs.sh) downloads the filtered DCM TPM matrix, the Ensembl 116 BioMart mapping and APPRIS 116 from Google Drive (about 161 MB in total) into the paths used by [`run_dcm.py`](AlterNetCode/run_dcm.py). The three files are readable by anyone with their links; no Google login is needed. The script requires Bash, `curl`, and either `sha256sum` or `shasum`, checks each download against its SHA256 checksum, and skips files that already match. The original DIGGER file and human transcription factor list are already included in `AlterNetCode/data/`.

### Run DCM in tmux

After setup, with `tmux` and Pixi available, start a new DCM run in the background from the repository root:

```bash
./run_dcm_tmux.sh
```

[`run_dcm_tmux.sh`](run_dcm_tmux.sh) starts `pixi run python -u run_dcm.py` in a detached session named `alternet`. It starts a new analysis; it does not take over a process already running in another terminal. If the session already exists, it shows the command to open it instead of starting another run.

To view the output, connect to the same server where you started the session and run:

```bash
tmux attach -t alternet
```

Press **Ctrl+B**, release both keys, then press **D** to detach. The analysis continues if you disconnect from SSH. The session stays open after the analysis finishes and displays its exit code (`0` means success); type `exit` in that session to close it when you are done. Results are written to `AlterNetCode/results/DCM/`.
