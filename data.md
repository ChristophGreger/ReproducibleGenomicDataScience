# Data

The following inputs are used for the AlterNet reproduction on the MAGNet dilated cardiomyopathy (DCM) cohort. Local paths are relative to the repository root.

## Download the prepared inputs

Run `bash download_dcm_inputs.sh` from the repository root, or use `./setup_dcm.sh` to download the inputs and install the environment. The script downloads the three prepared DCM inputs into `files/` and all five files originally supplied in the authors' `data/` directory into `AlterNetCode/data/`. All eight files are hosted on Google Drive and kept outside Git. Each download is verified against its SHA-256 checksum; matching local files are skipped.

The original example files are `allTFs_hg38.txt`, `appris_data.appris.txt`, `biomart.txt`, `digger_data.csv`, and `minimal_NF_magnet_prefiltered_tpm.tsv`, hosted in this [Google Drive folder](https://drive.google.com/drive/folders/1p0U4Lhh7bhk_Rjd-Cs-RZUGlXKb0laK3). Their contents and local paths are preserved. The DCM run uses the original DIGGER file and TF list together with our prepared Ensembl 116 inputs; the other three original files remain available for the authors' minimal example and annotation comparisons.

## MAGNet RNA-seq reads

We use the raw SRA reads from **166 DCM runs** in BioProject **PRJNA595151** (GEO **GSE141910**, SRA study **SRP237337**). The checked-in accession list defines the exact cohort. The download script uses the NCBI SRA Toolkit and saves the reads under `files/sequences/`. [NCBI SRA Run Selector](https://www.ncbi.nlm.nih.gov/Traces/study/?acc=PRJNA595151) · [Run accession list](Steps/Step1_Downloading_Sequences/SRR_Acc_List.txt) · [Download script instructions](Steps/Step1_Downloading_Sequences/ReadMe.md)

## Ensembl cDNA reference

1. Open the human **GRCh38.p14** assembly page (`GCA_000001405.29`). It shows **GENCODE 50**, the human annotation used in Ensembl 116. [Ensembl assembly page](https://www.ensembl.org/genome/GCA_000001405.29)
2. Click **Get files** in the assembly details on the right.
3. Under **Annotation**, click **FASTA/GTF/GFF3** to open the FTP folder.
4. Download `cdna.fa.bgz`.

## BioMart mapping

1. Open BioMart in the June 2026 Ensembl archive. Under **Choose database**, select **Ensembl Genes 116**. Under **Choose dataset**, select **Human genes (GRCh38.p14)**. [Ensembl 116 BioMart](https://jun2026.archive.ensembl.org/biomart/martview)
2. Leave **Filters** unset so the export covers the complete human transcript set.
3. Click **Attributes** in the left panel. On the **Features** page, click the **+** next to **GENE**. Keep the four preselected ID fields and tick **Gene name**, **Transcript name**, and **Gene type**. The left panel should list these seven fields in order.

   - `Gene stable ID`
   - `Gene stable ID version`
   - `Transcript stable ID`
   - `Transcript stable ID version`
   - `Gene name`
   - `Transcript name`
   - `Gene type`

4. Click **Results** at the top. The results table is a 10-row preview. Under **Export all results to**, choose **File** and **TSV**, then click **Go** to download the full table.
5. Create `files/special_files/` if needed and save the TSV there as `biomart_ensembl116.txt`. If your browser saves it as `mart_export.txt`, rename it to `biomart_ensembl116.txt`. The export used here contains **670,670 transcript rows** plus the header.

## APPRIS annotations

1. Open the **Downloads** page linked in the AlterNet paper. [APPRIS Downloads](https://appris.bioinfo.cnio.es/#/downloads)
2. Set **Filter by Species** to **Human**, **Assembly Version** to **GRCh38**, and **Gene Dataset** to **Gencode50/Ensembl116**.
3. In the matching row, choose **TXT** in the **APPRIS scores** column. This is the full `appris_data.appris.txt` table with the `Transcript type` and `APPRIS Annotation` columns used for filtering and isoform annotation.
4. Save the tab-separated file as `files/special_files/appris_data.appris.txt`.

## DIGGER annotations

We use the DIGGER file originally supplied with AlterNet for the Pfam domain comparisons. The download script restores it from Google Drive to `AlterNetCode/data/digger_data.csv`.

## Human transcription factor list

We use the human transcription factor list originally supplied with the authors' AlterNet code. The download script restores it from Google Drive to `AlterNetCode/data/allTFs_hg38.txt`.

## Download checksums

These SHA-256 values identify the local copies used for the reproduction. A regenerated BioMart export may differ in row order.

```text
daafc3331285e95ea4efdeb359eb176840e77c16d905630f2788d1141e224bdc  files/kallisto/cdna.fa.bgz
7f765ba264becd0d799bd9aa2757e4b3419e56f334ca3520ebdc24e8de6a5aa2  files/matrix/filtered/transcript_tpm_filtered.tsv
bf5a206246dcd64b48de9c103788f9773de3144f7f83463381bbc18d863d020e  files/special_files/biomart_ensembl116.txt
a69a3e7ffc194d934c8bdeed8eaef1a9127aa3db71b697f26313170497b3bad0  files/special_files/appris_data.appris.txt
31589edf4d87ac6d4cbc0175c362d8a8171204260a59670b3000df449715cf4a  AlterNetCode/data/allTFs_hg38.txt
f0ee8ad511f9e018f6163de21356e785888a86f7a26bc288911071603f3f535d  AlterNetCode/data/appris_data.appris.txt
2dae9284e3fc60d09444983f20dd0d0bccc1226508a46ee2c238f92f3556b8ae  AlterNetCode/data/biomart.txt
6c58c2b015c800b8a82447635e3787b292388d691236c46de01d3a8e4312113b  AlterNetCode/data/digger_data.csv
756be4d5a2279a1c425c4a1ab59d7d2d006157f203ac6b710124905dd6c27772  AlterNetCode/data/minimal_NF_magnet_prefiltered_tpm.tsv
```

## Ensembl version provenance

ChatGPT checked the annotation files bundled with the authors' public AlterNet example against candidate Ensembl releases. The BioMart transcript-to-gene mappings matched **Ensembl 112**, and the APPRIS file matched the **Ensembl 113** archive byte for byte. According to the DIGGER paper, its exon and domain annotations were obtained from **Ensembl 99**, but a direct comparison showed that the relevant annotations in AlterNet's bundled DIGGER file match a filtered subset of **Ensembl 98**. [DIGGER paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7778957/) · [Reproducibility log](reproducibility_log.md#10-november-2026--checking-the-bundled-digger-version)

These versions describe the bundled example files. The exact FASTA used for the authors' original kallisto run and the full set of annotation versions used for their DCM analysis remain unknown. Their public preprocessing notebook starts from precomputed transcript TPMs.

For this reproduction, the cDNA reference, BioMart mapping, and APPRIS table all use the human **Ensembl 116** annotation (GENCODE 50). We kept the authors' DIGGER file for the Pfam domain comparisons. It provides Pfam annotations for **1,203 of 2,409** TF isoforms in our filtered DCM matrix. We accepted this coverage limitation because the authors' bundled inputs have the same kind of gap.

We have also reconstructed an Ensembl 116 exon/Pfam export from the official BioMart tables. Evaluating its use with appropriate transcript filters and missing-annotation handling could be a future seminar extension. The workflow and verification are documented in Step 4. [Exploratory BioMart workflow](Steps/Step4_DownloadingCreatingOwnDIGGER/README.md)
