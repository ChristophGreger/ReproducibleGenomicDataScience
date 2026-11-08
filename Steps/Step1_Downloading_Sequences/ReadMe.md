# Downloading the sequencing data

I downloaded the text file containing the identifiers for all individual sequencing runs from [this NCBI page](<https://www.ncbi.nlm.nih.gov/Traces/study/?page=3&acc=PRJNA595151&f=etiology_sam_s%3An%3Adilated%2520cardiomyopathy%2520(dcm)&o=acc_s%3Aa&s=SRR10676844,SRR10676845,SRR10676846,SRR10676847,SRR10676848,SRR10676849,SRR10676851,SRR10676852,SRR10676853,SRR10676854,SRR10676855,SRR10676856,SRR10676857,SRR10676858,SRR10676859,SRR10676860,SRR10676861,SRR10676863,SRR10676864,SRR10676865,SRR10676866,SRR10676867,SRR10676868,SRR10676869,SRR10676870,SRR10676871,SRR10676872,SRR10676873,SRR10676874,SRR10676875,SRR10676876,SRR10676877,SRR10676878,SRR10676879,SRR10676880,SRR10676881,SRR10676882,SRR10676883,SRR10676884,SRR10676885,SRR10676886,SRR10676887,SRR10676888,SRR10676889,SRR10676890,SRR10676891,SRR10676892,SRR10676893,SRR10676894,SRR10676896,SRR10676897,SRR10676898,SRR10676899,SRR10676900,SRR10676901,SRR10676902,SRR10676903,SRR10676905,SRR10676906,SRR10676907,SRR10676908,SRR10676909,SRR10676910,SRR10676911,SRR10676912,SRR10676915,SRR10676916,SRR10676918,SRR10676919,SRR10676920,SRR10676922,SRR10676924,SRR10676925,SRR10676926,SRR10676927,SRR10676928,SRR10676929,SRR10676930,SRR10676931,SRR10676932,SRR10676933,SRR10676934,SRR10676935,SRR10676936,SRR10676937,SRR10676938,SRR10676940,SRR10676941,SRR10676942,SRR10676943,SRR10676944,SRR10676945,SRR10676946,SRR10676947,SRR10676950,SRR10676951,SRR10676953,SRR10676956,SRR10676958,SRR10676959,SRR10676960,SRR10676963,SRR10676965,SRR10676966,SRR10676969,SRR10676974,SRR10676976,SRR10676982,SRR10676983,SRR10676989,SRR10676996,SRR10677004,SRR10677015,SRR10677018,SRR10677020,SRR10677021,SRR10677022,SRR10677023,SRR10677025,SRR10677028,SRR10677029,SRR10677030,SRR10677034,SRR10677035,SRR10677036,SRR10677037,SRR10677039,SRR10677043,SRR10677054,SRR10677055,SRR10677059,SRR10677066,SRR10677080,SRR10677090,SRR10677091,SRR10677093,SRR10677103,SRR10677106,SRR10677118,SRR10677121,SRR10677128,SRR10677129,SRR10677130,SRR10677131,SRR10677143,SRR10677144,SRR10677145,SRR10677146,SRR10677152,SRR10677154,SRR10677156,SRR10677159,SRR10677160,SRR10677164,SRR10677165,SRR10677166,SRR10677167,SRR10677169,SRR10677170,SRR10677172,SRR10677173,SRR10677178,SRR10677180,SRR10677183,SRR10677185,SRR10677186>).

I then asked **ChatGPT** to write a Python script that runs **six downloads simultaneously** because of the website's limited download bandwidth. The dataset consists of **166 files**, each approximately **4 GB** in size.

The downloads themselves are handled by the **SRA Toolkit**, which is provided by the **National Center for Biotechnology Information (NCBI)** specifically for this purpose.

## Installing the SRA Toolkit

With Homebrew installed, install the [SRA Toolkit](https://formulae.brew.sh/formula/sratoolkit) using:

```bash
brew install sratoolkit
```

This provides the `prefetch` and `fasterq-dump` commands used in Steps 1 and 2.

## Script usage

> The script and this usage documentation were written entirely by ChatGPT.

Python 3.8 or newer and the SRA Toolkit are required, with `prefetch` available on your `PATH`.

To use the default of **up to six simultaneous downloads**, execute this command from the project root:

```bash
python3 Steps/Step1_Downloading_Sequences/download_sequences.py
```

It reads `SRR_Acc_List.txt` from the script's directory and saves downloads in SRA format under `files/sequences/`. Logs are saved in `files/sequences/logs/`. Without `--workers`, the default is six simultaneous downloads. As soon as one finishes, the next queued run starts.

### Available options

| Option | Purpose | Default |
| --- | --- | --- |
| `--workers N` | Maximum number of simultaneous downloads; `N` must be at least 1. | `6` |
| `--retries N` | Additional attempts after a failed download; `0` disables retries. | `2` (up to three attempts in total) |
| `--accessions PATH` | Input text file containing one run ID per line. | `SRR_Acc_List.txt` next to the script |
| `--output-dir PATH` | Destination for run folders and logs. | `files/sequences/` in the project root |
| `--dry-run` | Print planned commands without downloading or creating files. | Off |
| `-h`, `--help` | Show all options and exit. | — |

Options can be combined. To preview the default configuration:

```bash
python3 Steps/Step1_Downloading_Sequences/download_sequences.py --dry-run
```

Custom relative paths are resolved from the current working directory. Put paths containing spaces in quotes.

Press **Ctrl+C** to stop. Run the same command again to resume incomplete downloads; failed downloads are retried twice automatically.
