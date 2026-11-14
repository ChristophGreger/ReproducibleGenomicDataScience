# Software environment

Tools used by the repository scripts and documented workflow are listed below. 

## DCM setup and execution

The DCM analysis runs on the university workstation `bs201.ur.de` with **Debian 12 (Bookworm)**.

| Tool | Version | Purpose |
| --- | --- | --- |
| Bash | 5.2.15(1)-release (x86_64-pc-linux-gnu) | Runs the root `.sh` scripts. |
| Pixi | 0.84.0 | Installs the AlterNet environment and runs Python. |
| Git | 2.39.5 | Clones the repository and fetches the SignifiKANTE dependency over HTTPS. |
| curl | 7.88.1 (Debian package 7.88.1-10+deb12u15) | Downloads the prepared DCM inputs and original AlterNet example files from Google Drive; also used in Step 4. |
| tmux | 3.3a | Runs DCM in a session that survives SSH disconnection. |
| `sha256sum` (GNU coreutils) | 9.1 | Verifies downloaded inputs. |
| GNU Awk | 5.2.1 | Extracts the checksum from command output. |
| Python | See Pixi lockfile | Executes AlterNet; installed by Pixi. |


## Rebuilding the inputs

These tools are needed when rerunning the preprocessing in `Steps/`, rather than downloading the prepared inputs.

I downloaded the SRA reads and ran kallisto on my **Mac**, installing SRA Toolkit and kallisto with **Homebrew**. The CIP-pool computers and university workstations available to me did not provide sufficient storage space and network bandwidth for the raw-data downloads and temporary FASTQ files. I therefore consider the requirement to perform all work on those machines inapplicable to preprocessing in my case. I had also not been told in advance to expect such extensive and complex preprocessing.

The DCM network inference itself runs on a university Linux workstation. A short test in a Docker container on my Mac confirmed that the SRA Toolkit and kallisto preprocessing steps also work on Linux; the exact versions and test scope are recorded in the [reproducibility log](reproducibility_log.md#14-november-2026--testing-preprocessing-on-linux).

| Tool | Version | Purpose |
| --- | --- | --- |
| Homebrew | 7.0.11 | Installs SRA Toolkit and kallisto on macOS. |
| Python 3 (`python3`) | 3.14.9 | Reported standalone Python version; separate from Pixi's Python. Runs the Step 1–4 scripts, which otherwise use the Python standard library. (but any python3 version should do it)  |
| NCBI SRA Toolkit: `prefetch`, `fasterq-dump` | 3.4.1 (both tools) | Downloads SRA reads in Step 1 and extracts FASTQs in Step 2. |
| kallisto | 0.52.0 | Builds the transcriptome index and quantifies reads in Step 2. |

Installation on macOS:

```bash
brew install sratoolkit kallisto
```

For a Linux rerun on Debian, these tools can alternatively be installed with administrator rights using:

```bash
sudo apt-get update
sudo apt-get install sra-toolkit kallisto
```

The installed versions depend on the configured package repositories and may differ from the versions recorded above.

