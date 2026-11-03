# Preparing the kallisto transcriptome index

I installed **kallisto** using **Homebrew**:

```bash
brew install kallisto
```

The installed version is **0.52.0**, which can be checked with `kallisto version`.

## Reference transcriptome

I consulted the [kallisto manual](https://pachterlab.github.io/kallisto/manual), which explains that index construction requires a **transcriptome FASTA**. Based on this requirement, I found the [human GRCh38.p14 assembly page on Ensembl](https://www.ensembl.org/genome/GCA_000001405.29).

From there, I selected the cDNA FASTA in the [Ensembl gene set directory for annotation date `2026_04`](https://ftp.ebi.ac.uk/pub/ensemblorganisms/GCA/000/001/405/29/ensembl/2026_04/geneset/):

- **Download:** [cdna.fa.bgz](https://ftp.ebi.ac.uk/pub/ensemblorganisms/GCA/000/001/405/29/ensembl/2026_04/geneset/cdna.fa.bgz)
- **Assembly:** GRCh38.p14 (`GCA_000001405.29`)
- **Local path of the decompressed FASTA:** `files/kallisto/cdna.fa`, relative to the project root

## Creating the index

Run this command **from the project root** to create the index using **8 threads** in the same `files/kallisto/` directory:

```bash
kallisto index \
  -t 8 \
  -i files/kallisto/transcripts.idx \
  files/kallisto/cdna.fa
```

The command reads the reference sequences from `files/kallisto/cdna.fa` and writes the kallisto transcriptome index to `files/kallisto/transcripts.idx`. This index can then be used with `kallisto quant` to quantify the sequencing reads.

## Processing the samples

> The script was written by ChatGPT.

Run from the project root with Python 3.8 or newer, `fasterq-dump`, and `kallisto` available on your `PATH`:

```bash
python3 Steps/Step2_Kallisto/process_samples.py
```

The script processes the runs in `Steps/Step1_Downloading_Sequences/SRR_Acc_List.txt` **one at a time**. It locates each local SRA download under `files/sequences/`, extracts paired FASTQ files with `fasterq-dump --split-3 -e 8`, and quantifies them with `kallisto quant -t 8 --rf-stranded`. Results are saved in `files/kallisto/quant/<RUN_ID>/`, and logs in `files/kallisto/quant/logs/`.

Temporary FASTQ and scratch files under `files/kallisto/work/` are deleted before starting the next run; the original SRA files are kept. On an error or Ctrl+C, processing stops and temporary files are cleaned up. Rerunning the command skips successfully completed runs with unchanged inputs. Use `--dry-run` to preview the commands without processing data, or `--limit 1` to process only the first listed run.

## Strand orientation

ChatGPT answered the question of whether to use `--rf-stranded` or `--fr-stranded`. For run `SRR10676844`, the [ENA experiment record](https://www.ebi.ac.uk/ena/browser/view/SRX7354339) reports **Illumina TruSeq stranded mRNA** preparation followed by Nugen Ovation amplification. [Illumina documents](https://knowledge.illumina.com/library-preparation/rna-library-prep/library-preparation-rna-library-prep-faq-list/000001233) that this protocol produces R1 antisense and R2 sense relative to the transcript, which corresponds to **`--rf-stranded`** in the [kallisto manual](https://pachterlab.github.io/kallisto/manual). This choice is based on the documented protocol; strandedness has not been measured directly from the reads.
