# Creating the transcript TPM matrix

We now need to combine the individual `abundance.tsv` files from kallisto into a single matrix with the same layout as the authors' [`minimal_NF_magnet_prefiltered_tpm.tsv`](../../AlterNetCode/data/minimal_NF_magnet_prefiltered_tpm.tsv): one row per transcript, the columns `transcript_id` and `gene_id`, and one TPM column per sequencing run. This step creates the complete matrix before the subsequent APPRIS and expression filters.

To add the gene IDs, we need a mapping from transcript IDs to gene IDs. We obtain this mapping from Ensembl BioMart. I used **Ensembl release 116** for the kallisto transcriptome index, so I also downloaded the BioMart annotation for that release. I selected the fields needed to reproduce the authors' BioMart file with the newer annotation:

- Gene stable ID
- Gene stable ID version
- Transcript stable ID
- Transcript stable ID version
- Gene name
- Transcript name
- Gene type

The downloaded file is stored in [`files/special_files/mart_export.txt`](../../files/special_files/mart_export.txt). I asked ChatGPT to write [`convert_biomart.py`](convert_biomart.py) to prepare it in the format expected by the authors' code. Inspection showed that this particular `.txt` export is already tab-separated and has the same seven columns as the authors' [`biomart.txt`](../../AlterNetCode/data/biomart.txt). The script therefore validates and normalizes the export rather than changing its delimiter. It saves a separate file named `biomart_ensembl116.txt` and preserves the original download.

I then asked ChatGPT to write [`create_matrix.py`](create_matrix.py), which combines the new BioMart mapping with all individual kallisto `abundance.tsv` files to create the large transcript TPM matrix.

A second README, [`ReadMeFilteringandNormalization.md`](ReadMeFilteringandNormalization.md), explains the subsequent APPRIS and expression filters. Gene aggregation and normalization are left to `run_alternet.py`.

## Written by ChatGPT

The two Python scripts and the usage instructions below were written by ChatGPT.

Both scripts require **Python 3.8 or newer** and use only the Python standard library. Run the following commands **from the project root**, in this order:

```bash
python3 Steps/Step3_CreatingTheMatrix/convert_biomart.py
python3 Steps/Step3_CreatingTheMatrix/create_matrix.py
```

### 1. Prepare the BioMart annotation

`convert_biomart.py` reads `files/special_files/mart_export.txt` and writes `files/special_files/biomart_ensembl116.txt`. The output is tab-separated, with the seven columns listed above in the same order as the authors' file. The script accepts tab-separated or comma-separated input, selects and orders the required columns, normalizes line endings and surrounding whitespace, and removes identical duplicate transcript records. Blank gene and transcript names are preserved. Missing or inconsistent IDs and conflicting transcript annotations cause an error.

| Option | Purpose |
| --- | --- |
| `--input PATH` | Use a different downloaded BioMart export. |
| `--output PATH` | Save the normalized BioMart file elsewhere. |
| `--force` | Replace an existing output after successful validation. |
| `-h`, `--help` | Show all options and their defaults. |

### 2. Assemble the TPM matrix

`create_matrix.py` reads the run IDs in `Steps/Step1_Downloading_Sequences/SRR_Acc_List.txt`, in their listed order. For every run, it reads `files/kallisto/quant/<RUN_ID>/abundance.tsv` and extracts the **`tpm`** values. The `target_id` column supplies the transcript IDs. Version suffixes such as `.1` are checked against BioMart and removed for the output stable IDs. BioMart supplies the corresponding unversioned gene IDs.

The result is saved as **`files/matrix/transcript_tpm_unfiltered.tsv`**:

```text
transcript_id    gene_id          SRR10676844    SRR10676845    ...
ENST...         ENSG...          0.0            1.25           ...
```

The actual file uses tabs between fields. Transcript rows follow the order in the first listed run; later abundance files may have a different row order and are aligned by transcript ID. The script requires every listed run and the same transcript set in every sample. It rejects unmapped transcripts, version mismatches, duplicate transcript IDs, and negative or nonfinite TPMs instead of silently dropping or replacing values.

All transcripts are retained, including those with zero TPM in every sample. TPM values remain as quantified by kallisto; this script performs no additional normalization, gene-level aggregation, sample selection by condition, or expression filtering. The authors' example is already a small, prefiltered NF matrix, so the new complete matrix has the same layout but a different set of rows and samples. Gene-level aggregation is performed later by AlterNet.

| Option | Purpose |
| --- | --- |
| `--biomart PATH` | Use a different normalized BioMart TSV. |
| `--quant-dir PATH` | Use a different directory containing `<RUN_ID>/abundance.tsv`. |
| `--accessions PATH` | Use a different run list; this controls sample inclusion and column order. |
| `--output PATH` | Save the matrix elsewhere. |
| `--force` | Replace an existing output after successful validation. |
| `-h`, `--help` | Show all options and their defaults. |

Both scripts preserve their inputs and refuse to overwrite an existing output unless `--force` is supplied. Custom relative paths are resolved from the current working directory; quote paths containing spaces. Output files are published only after successful processing. If interrupted with **Ctrl+C**, temporary output is cleaned up and the command can be run again from the beginning.

The matrix builder uses a temporary, disk-backed numeric array in the output directory. With 670,670 transcripts and 166 runs, this workspace alone needs approximately **850 MiB**, in addition to the final TSV. Progress is printed for each sample and every 100,000 output rows. Generated annotations and matrices remain under `files/`, which is excluded from Git by the project's existing `.gitignore`.

Both scripts were executed on the local data on **8 November 2026**. The resulting matrix contains **670,670 transcript rows and 166 sample columns**, plus the two ID columns, and occupies 623,645,457 bytes (approximately 595 MiB). Every transcript-to-gene mapping and the complete file structure were checked. All 2,012,010 TPM values from three samples (`SRR10676844`, `SRR10676936`, and `SRR10677186`) were also compared with their source abundance files and matched exactly.
