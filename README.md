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

The original documentation, including installation and usage instructions, is available in [`AlterNetCode/README.md`](AlterNetCode/README.md).

## Installation with Pixi

With [Pixi](https://pixi.prefix.dev/latest/installation/) installed, run the following from the root of this repository:

```bash
cd AlterNetCode
pixi install
```

This installs the dependencies and AlterNet itself as an editable package, so changes in `AlterNetCode/src/alternet/` do not require reinstalling it.

The current configuration supports **Linux x86_64 (`linux-64`)** and requires Git to fetch the public `SignifiKANTE` dependency over HTTPS. No GitHub account or SSH key is needed.
