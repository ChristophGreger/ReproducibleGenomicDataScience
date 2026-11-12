# Exploring an Ensembl 116 exon and Pfam table

I explored obtaining exon and Pfam annotations from **Ensembl release 116**, the same release as our cDNA reference, transcript-to-gene mapping, and APPRIS table. AlterNet obtains these annotations from its bundled DIGGER file. It collects the exon IDs and Pfam IDs into separate lists for each transcript and compares the sets between isoforms. I asked ChatGPT to write the scripts in this step to obtain those inputs from Ensembl 116. [AlterNet annotation code](../../AlterNetCode/src/alternet/annotation.py)

The full BioMart export failed in the browser. A direct `curl` request also stopped after roughly 90 MB with an HTTP/2 error before BioMart returned its `[success]` marker. These scripts download the published BioMart database tables and assemble the export locally.

On 11 November, I decided to use AlterNet's original DIGGER file for the reproduction. I do not yet fully understand ChatGPT's explanation of the chromosome selection and the other annotation filters, so I will leave the generated Ensembl 116 file unused for now. This step records the completed exploratory workflow. Evaluating the Ensembl 116 table and its filtering could be a later seminar extension. The DCM launcher uses the bundled DIGGER file. [Current DCM inputs](../../AlterNetCode/run_dcm.py)

## Completed run and saved output

On **11 November 2026**, ChatGPT ran the full download and reconstruction for me with freshly downloaded Ensembl archives. All archive checksums passed, and the rebuilt TSV matched the existing complete file byte for byte.

The verified file is already available at [`files/special_files/biomart_exons_pfam_ensembl116.tsv`](../../files/special_files/biomart_exons_pfam_ensembl116.tsv). It contains **7,525,629 data rows** for **382,428 transcripts** and is **292,209,341 bytes** (about 292 MB). The downloaded source archives are stored in `files/special_files/ensembl_mart_116/`.

## Where Ensembl documents the downloads

Start at the Ensembl 116 **Downloads** page, open **Download data via FTP**, then find **Database dumps → Multi-species data → BioMart → MySQL**. In the resulting directory, open `ensembl_mart_116`. The database includes multiple species. The human tables used here begin with `hsapiens_gene_ensembl__`. [Downloads page](https://jun2026.archive.ensembl.org/downloads.html) · [FTP download page](https://jun2026.archive.ensembl.org/info/data/ftp/index.html) · [BioMart 116 database directory](https://ftp.ensembl.org/pub/release-116/mysql/ensembl_mart_116/)

Ensembl's **Installing the Ensembl Data** guide explains the archive format. There is one gzipped, tab-separated text file per table, an SQL file defining the table structures, and a `CHECKSUMS` file for checking the downloaded archives with the UNIX `sum` algorithm. Our scripts read the relevant tables directly in Python. [Ensembl guide to the database dumps](https://jun2026.archive.ensembl.org/info/docs/webcode/mirror/install/ensembl-data.html)

The exact column names, data types, and column order are published in `ensembl_mart_116.sql.gz`. Ensembl also explains the gene, transcript, and translation main tables and their dimension tables in its BioMart FAQ. The scripts use those shared internal keys to recreate our three-column export. The particular reconstruction in this step was written for this project and checked against direct BioMart results. [SQL schema](https://ftp.ensembl.org/pub/release-116/mysql/ensembl_mart_116/ensembl_mart_116.sql.gz) · [BioMart table structure FAQ](https://static.ensembl.org/Help/Faq?id=476)

## Script usage

> The scripts and this usage documentation were written by ChatGPT.

You need **Python 3.9 or newer** and `curl` on your `PATH`. The Python code uses the standard library. Run the builder from the project root.

```bash
python3 Steps/Step4_DownloadingCreatingOwnDIGGER/create_biomart_exons_pfam.py
```

This downloads and verifies the required archives, then creates the tab-separated file `files/special_files/biomart_exons_pfam_ensembl116.tsv`. Its three columns are `Transcript stable ID`, `Exon stable ID`, and `Pfam ID`.

The compressed inputs are cached in `files/special_files/ensembl_mart_116/`. Valid cached files are reused, so the builder can be run offline after the initial download. If an output already exists, the builder compares it with the newly generated file. An identical output is accepted. For a differing output, choose another path with `--output`.

To download and check the archives separately, use the downloader.

```bash
python3 Steps/Step4_DownloadingCreatingOwnDIGGER/download_ensembl_mart.py
```

| Option | Script | Purpose |
| --- | --- | --- |
| `--archive-dir PATH` | Both | Use another directory for the compressed tables, schema, and checksum manifest. |
| `--output PATH` | Builder | Write the generated TSV to another location. |
| `-h`, `--help` | Both | Show the available options and defaults. |

Custom relative paths are resolved from the current working directory. Quote paths containing spaces. Allow roughly 146 MB for the compressed tables and schema, 292 MB for the output, and room for a temporary copy when checking an existing output. Generated files are under `files/`, which is excluded from Git.

## Downloaded files and the columns used

The downloader obtains `CHECKSUMS`, `ensembl_mart_116.sql.gz`, and the following three table archives. The positions in this table are counted from 1. The builder locates the fields by their names in the SQL schema.

| Table archive | Relevant fields |
| --- | --- |
| `hsapiens_gene_ensembl__exon_transcript__dm.txt.gz` | Column 5, `stable_id_1016`, supplies the `ENSE…` exon ID. Column 8, `transcript_id_1064_key`, links it to a transcript. |
| `hsapiens_gene_ensembl__translation__main.txt.gz` | Column 39, `translation_id_1068_key`, supplies the internal protein key. Column 51, `stable_id_1066`, supplies the public `ENST…` transcript ID. Column 78, `transcript_id_1064_key`, links it to the exon table. |
| `hsapiens_gene_ensembl__protein_feature_pfam__dm.txt.gz` | Column 2, `translation_id_1068_key`, links to the protein. Column 4, `hit_name_1048`, supplies the `PF…` Pfam ID. |

All files come from the same release-116 database directory. The downloader checks each compressed archive against its entry in Ensembl's checksum manifest before the builder uses it. [Archive directory](https://ftp.ensembl.org/pub/release-116/mysql/ensembl_mart_116/) · [Published checksums](https://ftp.ensembl.org/pub/release-116/mysql/ensembl_mart_116/CHECKSUMS)

## How the table is assembled

The translation table is the connection between the other two tables. For each internal transcript key, it supplies the public transcript ID and the internal protein key. The transcript key identifies the exons, and the protein key identifies the Pfam annotations.

The builder reproduces the BioMart attributes `ensembl_transcript_id`, `ensembl_exon_id`, and `pfam`, with unique rows and no filters. Each exon is paired with every distinct Pfam ID for that transcript. A transcript with 11 exons and 4 Pfam IDs therefore produces 44 rows. If the protein has no Pfam hit, there is one row per exon with a blank Pfam field. Transcripts without a translation are excluded, matching this BioMart query. [BioMart query documentation](https://jun2026.archive.ensembl.org/info/data/biomart/biomart_restful.html)

A row associates an exon and a Pfam ID with the same transcript. DIGGER additionally maps domain coordinates to the exons that encode them. For the isoform comparisons in AlterNet, the annotation code collects the two ID columns separately and compares their sets. This explains why the exon/Pfam pairings and repeated rows can be reduced to independent ID sets for the comparison. Transcript selection and missing-annotation handling also affect the result. [DIGGER paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7778957/) · [AlterNet grouping code](../../AlterNetCode/src/alternet/annotation.py#L99-L104)

## Comparison with the bundled DIGGER file

Running the same reconstruction with Ensembl 98 reproduced the exon and Pfam ID sets for all **67,552 transcripts** in AlterNet's bundled DIGGER file. Restricting the Ensembl 98 export to transcripts on **1–22, X and Y** with at least one Pfam ID also reproduced exactly the DIGGER transcript IDs. The full export contained **35,536 additional transcripts without Pfam hits** and **7,700 additional Pfam-annotated transcripts on other reference sequences**. The latter comprise 7,658 on alternative/Patch sequences, 29 on other scaffolds, and 13 on MT.

AlterNet handles an entirely missing DIGGER entry differently from a present transcript with an empty Pfam list. The former produces empty difference lists, while the latter can produce Pfam IDs marked as missing relative to a comparison isoform. Gene-level intersections also differ. A future use of this Ensembl 116 table needs to account for that behavior when deciding which transcripts to include. [Comparison helpers](../../AlterNetCode/src/alternet/annotation.py#L113-L177) · [Gene-level intersections](../../AlterNetCode/src/alternet/annotation.py#L522-L558)

## Verification and use in AlterNet

The original reconstruction was compared with direct requests to the Ensembl 116 BioMart service. All **84,401 rows** for chromosome 21 matched exactly as a set, including blank Pfam fields. All **64,004 complete rows** received from the beginning of an unfiltered query were also present. The expected output is pinned to the following values.

| Check | Expected value |
| --- | ---: |
| Data rows, excluding the header | 7,525,629 |
| Distinct transcript IDs | 382,428 |
| Rows with a blank Pfam ID | 1,259,409 |
| File size | 292,209,341 bytes |
| SHA-256 | `8559a4af690dcc9c41688c79737575cb6ea8f7468d694a49ddd1c40bcba4b06a` |

You can check the output independently on macOS with `shasum`.

```bash
shasum -a 256 files/special_files/biomart_exons_pfam_ensembl116.tsv
```

On Linux, use `sha256sum` on the same file. The digest covers the exact contents and row order produced by this builder.

A future integration would read the TSV as tab-separated data, select the three shared columns before grouping, and explicitly define the transcript filters and missing-annotation behavior described above. Our reproduction uses the original DIGGER import. The Step 3 BioMart file provides transcript-to-gene mappings, and APPRIS provides the transcript type and principal isoform labels. [Annotation import](../../AlterNetCode/src/alternet/annotation.py#L66-L104) · [Step 3](../Step3_CreatingTheMatrix/ReadMe.md)
