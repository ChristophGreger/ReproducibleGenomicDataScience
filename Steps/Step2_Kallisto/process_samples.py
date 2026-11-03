#!/usr/bin/env python3
"""Convert and quantify one SRA run at a time, using eight threads per tool."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
THREADS = 8
COMPLETION_FILE = "pipeline_complete.json"


def read_accessions(path):
    accessions = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        accession = line.strip()
        if not accession:
            continue
        if not re.fullmatch(r"(?:SRR|ERR|DRR)[0-9]+", accession):
            raise ValueError(f"Invalid run ID in {path}, line {number}: {accession!r}")
        accessions.append(accession)
    if not accessions:
        raise ValueError(f"No run IDs found in {path}.")
    return list(dict.fromkeys(accessions))


def find_sra(root, accession):
    # prefetch may create either RUN/RUN.sra or RUN/RUN/RUN.sra.
    candidates = list((root / accession).rglob(f"{accession}.sra"))
    if (root / f"{accession}.sra").is_file():
        candidates.append(root / f"{accession}.sra")
    candidates = [path for path in candidates if path.is_file()]
    if len(candidates) != 1:
        raise ValueError(f"Expected one local SRA file for {accession}; found "
                         f"{len(candidates)} beneath {root}.")
    source = candidates[0].resolve()
    if source.stat().st_size == 0:
        raise ValueError(f"Empty SRA file: {source}")
    if any(path.name.endswith((".lock", ".tmp")) for path in source.parent.iterdir()):
        raise ValueError(f"Download appears unfinished: {source.parent}")
    return source


def fingerprint(path):
    stat = path.stat()
    return {"path": str(path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def signature(source, index):
    return {"schema": 1, "sra": fingerprint(source), "index": fingerprint(index),
            "threads": THREADS, "strandedness": "rf", "extraction": "split-3"}


def validate_quantification(directory):
    info = json.loads((directory / "run_info.json").read_text(encoding="utf-8"))
    if not isinstance(info, dict):
        raise ValueError(f"Invalid run_info.json in {directory}")
    for field in ("n_processed", "n_pseudoaligned"):
        value = info.get(field)
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"No reads reported for {field} in {directory}/run_info.json")
    with (directory / "abundance.tsv").open(encoding="utf-8") as abundance:
        columns = abundance.readline().strip().split("\t")
        if "target_id" not in columns or "tpm" not in columns or not abundance.readline().strip():
            raise ValueError(f"Missing or empty abundance table in {directory}")


def completed_result(directory, expected):
    if not directory.exists():
        return False
    try:
        manifest = json.loads((directory / COMPLETION_FILE).read_text(encoding="utf-8"))
        if manifest["inputs"] != expected:
            raise ValueError("input files or settings have changed")
        validate_quantification(directory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"Existing results will not be overwritten: {directory}. "
                         f"They are incomplete or use different inputs ({error}). "
                         "Choose another --output-dir to run again.") from error
    return True


def commands(source, index, workspace, quant_dir, fasterq, kallisto):
    # Use the accession directory when available, preserving SRA dependencies.
    accession = source.stem
    sra_input = source.parent if source.parent.name == accession else source
    fastq_dir = workspace / "fastq"
    extract = [fasterq, str(sra_input), "--split-3", "-e", str(THREADS),
               "-O", str(fastq_dir), "-t", str(workspace / "tmp")]
    quantify = [kallisto, "quant", "-t", str(THREADS), "--rf-stranded",
                "-i", str(index), "-o", str(quant_dir),
                str(fastq_dir / f"{accession}_1.fastq"),
                str(fastq_dir / f"{accession}_2.fastq")]
    return extract, quantify


def run_command(command, log):
    printable = shlex.join(command)
    print(printable, flush=True)
    log.write(f"\n[{datetime.now(timezone.utc).isoformat()}] {printable}\n")
    log.flush()
    with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                          start_new_session=True) as process:
        try:
            returncode = process.wait()
        except BaseException:
            # Stop the whole tool process group before deleting its workspace.
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
            raise
    if returncode:
        raise subprocess.CalledProcessError(returncode, command)


@contextmanager
def pipeline_lock(output_dir):
    # Prevent two invocations from extracting/quantifying samples simultaneously.
    with (output_dir / ".pipeline.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError(f"Another pipeline is using {output_dir}.") from error
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def process_sample(accession, source, args, fasterq, kallisto, expected):
    result_dir = args.output_dir / accession
    log_path = args.output_dir / "logs" / f"{accession}.log"
    print(f"Log: {log_path}", flush=True)
    # All deletion is limited to directories created by this invocation. Raw SRA
    # files and published results are never removed, including on interruption.
    with tempfile.TemporaryDirectory(prefix=f"{accession}-", dir=args.work_dir) as work:
        # Staging beneath output_dir permits an atomic rename even when the
        # FASTQ scratch directory is on a different filesystem.
        with tempfile.TemporaryDirectory(prefix=f".{accession}-", dir=args.output_dir) as stage:
            workspace = Path(work)
            quant_dir = Path(stage) / "quant"
            (workspace / "fastq").mkdir()
            (workspace / "tmp").mkdir()
            extract, quantify = commands(source, args.index, workspace, quant_dir,
                                         fasterq, kallisto)
            with log_path.open("a", encoding="utf-8") as log:
                try:
                    print(f"{accession}: extracting paired FASTQ files (8 threads)", flush=True)
                    run_command(extract, log)
                    mates = [workspace / "fastq" / f"{accession}_{mate}.fastq" for mate in (1, 2)]
                    if any(not path.is_file() or path.stat().st_size == 0 for path in mates):
                        raise ValueError("fasterq-dump did not produce two nonempty mate files")
                    extra = [path for path in (workspace / "fastq").glob("*.fastq")
                             if path not in mates and path.stat().st_size > 0]
                    if extra:
                        raise ValueError("Unpaired or unexpected reads found; stopping rather "
                                         "than silently discarding them: " + ", ".join(p.name for p in extra))
                    print(f"{accession}: quantifying with kallisto (8 threads, rf-stranded)", flush=True)
                    run_command(quantify, log)
                    validate_quantification(quant_dir)
                    if signature(source, args.index) != expected:
                        raise ValueError("The SRA file or index changed during processing")
                    manifest = {"inputs": expected,
                                "completed_at": datetime.now(timezone.utc).isoformat()}
                    (quant_dir / COMPLETION_FILE).write_text(
                        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                    if result_dir.exists():
                        raise ValueError(f"Results appeared during processing: {result_dir}")
                    quant_dir.rename(result_dir)
                    log.write("SUCCESS: results saved; temporary FASTQ and scratch files will be removed.\n")
                except BaseException as error:
                    log.write(f"FAILED: {type(error).__name__}: {error}\n"
                              "Temporary files will be removed; original SRA files are retained.\n")
                    raise
    print(f"{accession}: complete; temporary files removed; results: {result_dir}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Sequential SRA-to-kallisto processing with eight threads per tool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--accessions", type=Path,
                        default=PROJECT_ROOT / "Steps/Step1_Downloading_Sequences/SRR_Acc_List.txt",
                        help="Text file containing one run ID per line")
    parser.add_argument("--sra-dir", type=Path, default=PROJECT_ROOT / "files/sequences",
                        help="Directory containing the downloaded SRA runs")
    parser.add_argument("--index", type=Path, default=PROJECT_ROOT / "files/kallisto/transcripts.idx",
                        help="Existing kallisto transcriptome index")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "files/kallisto/quant",
                        help="Directory for per-run results and logs")
    parser.add_argument("--work-dir", type=Path, default=PROJECT_ROOT / "files/kallisto/work",
                        help="Directory for temporary FASTQ and fasterq-dump scratch files")
    parser.add_argument("--limit", type=int, help="Process only the first N listed runs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print planned commands without running tools or creating files")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    for field in ("accessions", "sra_dir", "index", "output_dir", "work_dir"):
        setattr(args, field, getattr(args, field).expanduser().resolve())
    try:
        accessions = read_accessions(args.accessions)
        if args.limit is not None:
            accessions = accessions[:args.limit]
        if not args.index.is_file() or args.index.stat().st_size == 0:
            raise ValueError(f"Missing or empty kallisto index: {args.index}")
        fasterq = shutil.which("fasterq-dump")
        kallisto = shutil.which("kallisto")
        if args.dry_run:
            for accession in accessions:
                source = find_sra(args.sra_dir, accession)
                if completed_result(args.output_dir / accession, signature(source, args.index)):
                    print(f"SKIP {accession}: already completed with these inputs")
                    continue
                print(f"\n{accession}")
                work = args.work_dir / f"{accession}-TEMP"
                quant = args.output_dir / f".{accession}-TEMP" / "quant"
                for command in commands(source, args.index, work, quant,
                                        fasterq or "fasterq-dump", kallisto or "kallisto"):
                    print(shlex.join(command))
                print(f"Save results to {args.output_dir / accession}; remove temporary files.")
            return 0
        if not fasterq or not kallisto:
            raise ValueError("fasterq-dump and kallisto must both be installed and available on PATH")
        (args.output_dir / "logs").mkdir(parents=True, exist_ok=True)
        args.work_dir.mkdir(parents=True, exist_ok=True)
        with pipeline_lock(args.output_dir):
            for number, accession in enumerate(accessions, 1):
                print(f"\n[{number}/{len(accessions)}] {accession}", flush=True)
                source = find_sra(args.sra_dir, accession)
                expected = signature(source, args.index)
                if completed_result(args.output_dir / accession, expected):
                    print("Already completed with these inputs; skipping.", flush=True)
                    continue
                process_sample(accession, source, args, fasterq, kallisto, expected)
        print("All selected runs completed. Original SRA files have been retained.")
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted. Original SRA files and completed results are retained. "
              "Rerun the same command to continue.", file=sys.stderr)
        return 130
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}\nProcessing stopped. Check the per-run logs in "
              f"{args.output_dir / 'logs'}.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    def terminate(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, terminate)
    sys.exit(main())
