# Filtering the transcript TPM matrix

Section **4.1, "The AlterNet pipeline"**, of the [paper](../../Paper.pdf) describes the preprocessing of the expression matrix. The authors' [`preprocess_magnet_minimal.ipynb`](../../AlterNetCode/src/alternet/tutorials/preprocess_magnet_minimal.ipynb) implements the transcript selection using **APPRIS**: it retains transcript IDs whose `Transcript type` is exactly **`protein_coding`**. 

We follow this approach. I downloaded the APPRIS score table for our **Ensembl release 116** reference from [APPRIS](https://appris.bioinfo.cnio.es/) and saved it as [`files/special_files/appris_data.appris.txt`](../../files/special_files/appris_data.appris.txt). It is already a tab-separated table with a header, including `Transcript ID`, `Ensembl Gene ID`, and `Transcript type`, so no conversion is needed. 

The original BioMart mapping, [`biomart_ensembl116.txt`](../../files/special_files/biomart_ensembl116.txt), continues to provide transcript-to-gene IDs when assembling the unfiltered matrix. **APPRIS provides the transcript-type selection for this filtering step.**

We first retain only transcripts listed in APPRIS with `Transcript type == protein_coding`. This is an exact match, following the authors' notebook: a value such as `protein_coding,RT` does not match. Transcripts absent from APPRIS are also excluded. Selection uses the transcript-type field rather than the principal/alternative isoform labels or APPRIS scores.

Next, we retain isoforms with **TPM > 0 in at least 90% of samples**. With our 166 samples, this requires **at least 150 positive sample values**. The fraction is calculated using only the sample columns. Each condition is processed separately, as described in Section 4.2 of the paper.

Section 4.2 of the paper specifies a 50% cutoff. I chose the **90% cutoff** used in the manuscript repository's preprocessing notebook because network inference is already expected to take a long time. On our data, the stricter cutoff reduces the number of target genes from 15,278 to 11,347 and the number of TF transcript predictors from 7,266 to 2,409. [Manuscript preprocessing notebook](https://github.com/bionetslab/alternet-manuscript/blob/main/python/preprocess_magnet.ipynb)

Gene aggregation and normalization are left to [`run_alternet.py`](../../AlterNetCode/src/alternet/runners/run_alternet.py). Our preprocessing script only filters transcript rows and preserves their TPM values. The current runner computes Z-score matrices but still passes unscaled TPMs to inference; that existing behavior is unchanged here and needs checking when configuring the AlterNet run.

This is likely an oversight in the authors' implementation. When I run AlterNet, it will be particularly interesting to see whether using the Z-score matrices instead of the unscaled TPMs changes the inference results.


## Written by ChatGPT

The script [`filter_transcripts.py`](filter_transcripts.py) and the usage instructions below were written by ChatGPT.

The script requires **Python 3.8 or newer** and uses only the Python standard library. Run it **from the project root**:

```bash
python3 Steps/Step3_CreatingTheMatrix/filter_transcripts.py
```

By default, it reads:

- **Matrix:** `files/matrix/transcript_tpm_unfiltered.tsv`
- **APPRIS annotation:** `files/special_files/appris_data.appris.txt`
- **Coding criterion:** APPRIS `Transcript type == protein_coding`
- **Expression criterion:** TPM > 0 in at least 90% of the samples

It creates a new directory, **`files/matrix/filtered/`**, containing:

| File | Contents |
| --- | --- |
| `transcript_tpm_filtered.tsv` | Filtered transcript TPMs, retaining `transcript_id`, `gene_id`, and all sample columns in their original order. |
| `filtering_summary.json` | Input paths and SHA-256 checksums, annotation counts, filter settings, sample IDs, and retained/removed counts. |

The script preserves the TPM field values and retained row order. It validates APPRIS mappings and every matrix row, including rows that will be excluded. Duplicate matrix IDs, conflicting APPRIS annotations, inconsistent gene mappings for matched transcripts, malformed rows, and invalid, negative, or nonfinite TPMs cause an error. Matrix transcripts absent from APPRIS are removed and counted separately, matching the notebook's membership filter.

| Option | Purpose | Default |
| --- | --- | --- |
| `--input PATH` | Unfiltered transcript TPM matrix. | `files/matrix/transcript_tpm_unfiltered.tsv` |
| `--appris PATH` | APPRIS score table containing transcript IDs, gene IDs, and transcript types. | `files/special_files/appris_data.appris.txt` |
| `--min-positive-fraction Q` | Minimum sample fraction with TPM > 0. Accepts a decimal or fraction. | `0.9` |
| `--output-dir PATH` | A new destination directory. | `files/matrix/filtered` |
| `-h`, `--help` | Show all options and defaults. | - |

The required positive sample count is rounded up to 150 of 166 samples at the default threshold. For another condition, supply a matrix containing only that condition's samples and choose a separate output directory.

The output directory must not already exist. To repeat the analysis, choose a new `--output-dir`. Both output files are published together only after successful processing. Errors or **Ctrl+C** clean up temporary output, and input files remain unchanged. Custom relative paths are resolved from the current working directory; quote paths containing spaces. Generated data remain under `files/`, which is excluded from Git.

## Using the new APPRIS file in AlterNet

Use the same downloaded APPRIS table for the later annotation stage. When preparing the inputs for `alternet_pipeline`, load:

```python
import pandas as pd

appris_df = pd.read_csv("files/special_files/appris_data.appris.txt", sep="\t")
biomart = pd.read_csv("files/special_files/biomart_ensembl116.txt", sep="\t")
transcript_data_cp = pd.read_csv(
    "files/matrix/filtered/transcript_tpm_filtered.tsv", sep="\t"
)
```

Pass these objects as the corresponding arguments to `alternet_pipeline`. This selects the newly downloaded APPRIS table instead of the older annotation bundled in `AlterNetCode/data/`. The transcript input is the filtered **TPM** matrix.

## Execution and verification

The APPRIS-based filtering was executed on **9 November 2026**.

| Processing stage | Transcripts remaining |
| --- | ---: |
| Unfiltered matrix | 670,670 |
| Present in APPRIS with `Transcript type == protein_coding` | 277,916 |
| Positive TPM in at least 150 of 166 samples | 24,397 |

The resulting matrix contains **24,397 transcripts from 11,347 genes across 166 samples**. The APPRIS membership filter removes 239,785 transcripts absent from the downloaded annotation and 152,969 records with other transcript types. The prevalence filter then removes 253,519 further transcripts. Exactly 742 retained transcripts have positive TPM in exactly 150 samples.

An independent check selected the rows with at least 150 positive TPM values from the previously verified 50% output. The SHA-256 checksum of those rows and the original header matched the new TSV exactly, verifying retained IDs, TPM field values, and row and column order.
