# Reproducibility log

This log follows my attempt to reproduce Figure 3E/F of AlterNet for the 166 MAGNet samples from donors with dilated cardiomyopathy (DCM). Dates are local to Berlin.

## 25–31 October 2026 · Planning the reproduction

- Read the paper, chose Figure 3E/F, and wrote the plan. We worked out which network edges go into the plots, how APPRIS identifies principal isoforms, and how DIGGER supplies exon and domain information. [Paper](Paper.pdf) · [Plan](Reproduction%20Plan/Greger_Christoph_Plan.pdf) · `ffd77fd`, `65e09bc`
- The caption says to sample from a filtered network. The methods say to use the unfiltered network. We planned to start with the filtered one. The manuscript code also narrows the background to edges from non-principal isoforms and calculates the p-value differently.
- Looked for the DCM inputs. GEO had processed gene expression, and the notebooks loaded a private transcript TPM matrix. BioMart was temporarily inaccessible. With no documented Kallisto reference or commands, I decided to quantify the original MAGNet reads.
- Checked how AlterNet uses multiple cores. Dask splits target genes across workers. The two networks and ten repeats per network run in sequence. The example runner uses private paths, so we prepared a separate configurable runner and benchmark.
- Restricted network access blocked the first GitHub clone. Retried with network access. On the Mac, PyArrow and NumPy versions clashed, and Dask needed permission to open a local port. Pinning PyArrow 22 and allowing local sockets got the test running. Both networks ran on the small NF example with two workers. Serial and parallel repeats agreed with the same seeds.
- Installed and tested Miniconda on the Mac separately from the later Pixi setup. The first installer download hit the same network restriction and worked on retry.
- Discussed local RAM, Google Cloud and AWS, storage and transfer costs. Full DCM scaling stayed unmeasured. Added `.gitignore` to keep large local files out of Git. `7c43cd5`

## 1 November 2026 · Getting the reads and building the index

- Selected DCM in the NCBI Run Selector for MAGNet (`PRJNA595151`) and saved the **166 run IDs**. Discussed download limits and cloud access. A ChatGPT-written script used the public SRA Toolkit and ran six downloads at a time. All 166 succeeded on their first recorded attempt. [Download instructions](Steps/Step1_Downloading_Sequences/ReadMe.md) · `8c0e622`
- Installed kallisto 0.52.0 through Homebrew. Checked which reference to use and chose the complete human cDNA file, which includes both coding and non-coding transcripts. 
- Built the index in the terminal with eight threads. Kallisto warned about trimming poly-A tails and replacing ambiguous bases. The finished index passed inspection and contained **670,670 transcripts**. [Index instructions](Steps/Step2_Kallisto/ReadMe.md) · `b0454dd`

## 1–3 November 2026 · Quantifying the samples

- Estimated the temporary disk space needed to unpack the largest SRA file. The processing script unpacks and quantifies one sample at a time, then deletes the temporary FASTQs. I used eight threads and chose `--rf-stranded` based on the library protocol.
- During monitoring, kallisto sometimes used only one CPU core. We traced that to its expression estimation step. The first TPM tables looked empty because they began with zeros. We checked three tables against kallisto's HDF5 output and confirmed they contained valid TPMs.
- Run `SRR10677035` was interrupted on 2 November. The next morning, processing resumed and skipped the completed samples. Verified all **166 abundance tables** and kept the original SRA files. [Quantification instructions](Steps/Step2_Kallisto/ReadMe.md) · `3f501bc`

## 3–4 November 2026 · Trying Linux and comparing alternatives

- My Linux `pixi install` failed. SignifiKANTE required `distributed` 2025.11.0, while Pixi selected 2025.10.0. Discussed clearing the old environment and aligning the versions. A successful Linux retry is still unverified.
- Compared running on a workstation, in the cloud, or on Colab. These discussions did not produce a full DCM benchmark.

## 8 November 2026 · Installing the project copy of AlterNet

- Copied the authors' code into `AlterNetCode/` so I could edit and track it here. Kept the bundled APPRIS and DIGGER files. The notebook needed a separate Jupyter frontend. Documented `pixi install` and changed the SignifiKANTE download from SSH to HTTPS so it works without a GitHub SSH key. `a5b7e5c`, `8495488`, `a25f6dd`


## 8–9 November 2026 · Building and filtering the matrix

- Checked what suffixes like `.1` and `.5` mean. The GTEx loader strips them, but our MAGNet samples use a separate workflow. I downloaded BioMart for Ensembl 116, the same release as our Kallisto index, to assign a gene ID to each transcript. We checked the versions before removing the suffixes for AlterNet.
- The BioMart download was already tab-separated. Used ChatGPT-written scripts to prepare it and combine the 166 sample tables. The combined matrix had **670,670 rows**. We checked all gene mappings and compared three columns with their source TPMs. [Matrix instructions](Steps/Step3_CreatingTheMatrix/ReadMe.md) · `f137f14`
- The GTEx code filters by gene type, but one gene can produce both coding and non-coding transcripts. I downloaded a second BioMart export and found that the gene and transcript types differed for **160,176 transcripts**. We tested filtering with the BioMart transcript type and scaling the TPMs separately.
- The authors' MAGNet notebook uses APPRIS for the coding filter. After the download page initially failed to load, I obtained the full Ensembl 116 APPRIS table. We kept only transcripts listed with `Transcript type` exactly equal to `protein_coding`. **277,916 transcripts** passed this step, and **71,320** passed the subsequent 50% expression cutoff. [MAGNet notebook](AlterNetCode/src/alternet/tutorials/preprocess_magnet_minimal.ipynb) · `b737822`
- Checked the data passed to training in the minimal example. The paper describes training on Z-scores. The runner sends raw TPMs to GRNBoost2 and uses Z-scores later for correlations. Kept raw TPMs in the saved matrix. [Runner](AlterNetCode/src/alternet/runners/run_alternet.py)
- Compared the paper's 50% cutoff with the manuscript notebook's 90%. I chose **90%** to cut the workload. We counted only sample columns and required positive TPM in at least 150 of 166 samples. The verified output has **24,397 transcripts from 11,347 genes**, including **2,409 TF isoforms** (down from 7,266 at 50%). [Filtering instructions](Steps/Step3_CreatingTheMatrix/ReadMeFilteringandNormalization.md) · `95beb19`

## 9 November 2026 · Checking annotation versions

- ChatGPT checked the candidate Ensembl releases for me to identify the source versions of the authors' bundled BioMart and APPRIS files. The files match Ensembl **112** and **113**, respectively. I could not determine which Ensembl release the authors used for their original Kallisto reference.
- The authors' [example workflow](AlterNetCode/README.md#minimal-working-example) combines those BioMart and APPRIS files with DIGGER from Ensembl **99**. Across the bundled files, **2,311 of 9,012** TF transcripts mapped by BioMart and marked `protein_coding` in APPRIS lack Pfam annotations in DIGGER. The authors therefore faced the same annotation coverage problem with these inputs. The extent of this gap in the original DCM run is unknown.
- Kept BioMart and APPRIS **116** for our data. The older APPRIS file misses 1,034 TF isoforms in our matrix. The TF list uses gene names and maps through BioMart. We found no DIGGER export for Ensembl 116. Since the authors' workflow used the same DIGGER file, we accepted its coverage for the reproduction and kept the bundled **Ensembl 99** file. It supplies domain annotations for **1,203 of 2,409 TF isoforms**.

  In the future, I could look more closely at which domain annotations [Ensembl 116 BioMart](https://jun2026.archive.ensembl.org/biomart/martview) can export and whether its isoform-level Pfam annotations would be a suitable alternative for Figure 3E/F. For now, I am using the bundled Ensembl **99** DIGGER file for the reproduction.

- The filtered DCM matrix is ready. The full DCM network run and reproduction of Figure 3E/F remain open.

## 10 November 2026 · Checking the bundled DIGGER version

- I asked ChatGPT to check whether the exon and Pfam annotations in AlterNet's bundled `digger_data.csv` came from Ensembl 99 BioMart, as stated in the DIGGER paper's “Mapping of protein domains to exons” section. [DIGGER paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7778957/) 
- I asked ChatGPT to compare the annotations per transcript against the archived Ensembl data. In BioMart **99**, **61** of the DIGGER transcript IDs were absent. Among the shared transcripts, **331** had different exon ID sets and **54** had different Pfam ID sets. Ensembl **98** matched the exon IDs, Pfam IDs, and Pfam start and end positions exactly for **all 67,552 transcripts** in the bundled file. The Ensembl 99 attribution is wrong for this file 🙂. 
- AlterNet drops all DIGGER columns except `Transcript stable ID`, `Exon stable ID`, `Exon rank in transcript`, and `Pfam ID`. The exon rank survives the import and goes unused afterwards 🙂. [AlterNet annotation code](AlterNetCode/src/alternet/annotation.py)
- The further I get, the funnier it gets. I used to wonder how people caught all these little details before LLMs. Turns out they just didn't, lol.
- I realised that I can get the required exon and Pfam annotations for our Ensembl **116** reference directly from BioMart. Using DIGGER for this part of AlterNet seems like a pointless detour, since AlterNet only uses the annotations that DIGGER originally obtained from BioMart.
- I have decided to use **Ensembl 116 BioMart** for the exon and Pfam annotations too. Keeping everything on the same annotation release seems much more sensible, and getting the data is straightforward now that I know my way around Ensembl. I will make a small change to AlterNet's import code to handle the BioMart file format.
- I tried downloading the exon and Pfam annotations from Ensembl 116 BioMart, but the export cut off in the middle of a row. Ensembl seems to be having an issue, so I will try again tomorrow.

## 11 November 2026 · Trying a direct BioMart download

- I tried downloading the full Ensembl 116 exon/Pfam export directly with `curl`, using BioMart's completion stamp. It aborted at around **90 MB** with an HTTP/2 error before `[success]`. Both the browser and direct downloads have now failed. The full export appears too large to download reliably this way. [BioMart download documentation](https://jun2026.archive.ensembl.org/info/data/biomart/biomart_restful.html)
- I switched to downloading the official Ensembl 116 BioMart database tables and asked ChatGPT to document the reconstruction in Step 4. The scripts verify Ensembl's published checksums, read the column definitions from the SQL schema, and join the exon, translation, and Pfam tables. ChatGPT ran the full download and reconstruction successfully. The rebuilt TSV matched the existing complete file byte for byte. The verified output is already saved at [`files/special_files/biomart_exons_pfam_ensembl116.tsv`](files/special_files/biomart_exons_pfam_ensembl116.tsv), with **7,525,629 data rows** for **382,428 transcripts**, occupying **292,209,341 bytes** (about 292 MB). The source archives are in `files/special_files/ensembl_mart_116/`. [Step 4 instructions and Ensembl documentation](Steps/Step4_DownloadingCreatingOwnDIGGER/README.md)
- I would have preferred to use BioMart's email-notified download directly, without ChatGPT. Ensembl seems to have persistent technical problems that remain unresolved. Registration and login also did not work for me.
- I asked ChatGPT to run the same reconstruction with **Ensembl 98** and compare the relevant data with AlterNet's bundled DIGGER file. The exon and Pfam ID sets matched exactly for all **67,552 DIGGER transcripts**. ChatGPT found that selecting transcripts on chromosomes **1–22, X and Y** with at least one Pfam ID reproduced exactly the DIGGER transcript selection. It attributed the additional transcripts in the full BioMart export to these filters and explained that keeping transcripts without Pfam hits can change AlterNet's comparisons.
- I have decided to use the original [`digger_data.csv`](AlterNetCode/data/digger_data.csv) supplied with AlterNet for the reproduction after all. I do not yet fully understand ChatGPT's reconstruction and the consequences of the different annotation filters well enough. Evaluating a correctly version-matched **Ensembl 116** annotation file and its handling of missing Pfam hits could be an extension later in the seminar.

## 11 November 2026 · Using standardized values for network inference

- I asked ChatGPT to change both AlterNet runners so the gene-level network uses the existing standardized gene matrix and the AS-aware network combines standardized TF transcript and gene matrices. The code changes are very small and trivial, changing just two lines in each runner to use the already computed scaled matrices. Transcript TPMs are summed per gene before scaling. `StandardScaler` calculates Z-scores for each gene or transcript across samples. Isoform abundance categories continue to use TPM-based expression percentages. [Pipeline runner](AlterNetCode/src/alternet/runners/run_alternet.py) · [Alternative runner](AlterNetCode/src/alternet/runners/infer_nets.py)
