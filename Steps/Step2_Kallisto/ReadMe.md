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
