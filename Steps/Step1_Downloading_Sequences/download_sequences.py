#!/usr/bin/env python3
"""Download SRA runs with NCBI prefetch (six concurrent downloads by default)."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR.parent.parent / "files" / "sequences"


def read_accessions(path):
    """Read one run ID per line, ignoring blank lines and removing duplicates."""
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


def prefetch_command(executable, accession, output_dir):
    # NCBI requires the output directory for a single run to match its run ID.
    return [
        executable, accession, "--output-directory", str(output_dir / accession),
        "--max-size", "u", "--transport", "http", "--resume", "yes",
        "--verify", "yes",
    ]


def download(accession, executable, output_dir, retries, stop):
    """Return True on success, False on failure, or None if interrupted."""
    if stop.is_set():
        return None
    command = prefetch_command(executable, accession, output_dir)
    log_path = output_dir / "logs" / f"{accession}.log"
    try:
        with log_path.open("a", encoding="utf-8") as log:
            for attempt in range(retries + 1):
                if stop.is_set():
                    return None
                print(f"Starting {accession} (attempt {attempt + 1}/{retries + 1})", flush=True)
                log.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] "
                          f"Attempt {attempt + 1}: {shlex.join(command)}\n")
                log.flush()
                # HTTP avoids additional ascp processes. A separate session lets
                # Python stop each download cleanly when interrupted.
                with subprocess.Popen(
                    command, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True,
                ) as process:
                    while process.poll() is None:
                        if stop.wait(0.2):
                            process.terminate()
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
                            log.write("Interrupted; rerun the script to resume the download.\n")
                            return None
                    returncode = process.returncode
                if returncode == 0:
                    return True
                log.write(f"prefetch exited with code {returncode}.\n")
                log.flush()
                if attempt < retries:
                    delay = min(5 * 2 ** attempt, 30)
                    print(f"Retrying {accession} in {delay} seconds; "
                          f"Details: {log_path}", flush=True)
                    if stop.wait(delay):
                        return None
        return False
    except OSError as error:
        print(f"Error downloading {accession}: {error}", file=sys.stderr, flush=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download SRA runs listed in a text file using NCBI prefetch.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--accessions", type=Path, default=SCRIPT_DIR / "SRR_Acc_List.txt",
                        help="Text file containing one run ID per line")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="Output directory for sequence data")
    parser.add_argument("--workers", type=int, default=6,
                        help="Maximum number of concurrent downloads")
    parser.add_argument("--retries", type=int, default=2,
                        help="Additional attempts after a failed download")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands only, without downloading or creating files")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1.")
    if args.retries < 0:
        parser.error("--retries must not be negative.")
    try:
        accessions = read_accessions(args.accessions.expanduser().resolve())
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    output_dir = args.output_dir.expanduser().resolve()
    executable = shutil.which("prefetch")
    if args.dry_run:
        print(f"{len(accessions)} runs; at most {args.workers} concurrent downloads; output: {output_dir}")
        for accession in accessions:
            print(shlex.join(prefetch_command(executable or "prefetch", accession, output_dir)))
        return 0
    if executable is None:
        parser.error("prefetch was not found. Install the SRA Toolkit and add its "
                     "bin directory to PATH.")
    try:
        (output_dir / "logs").mkdir(parents=True, exist_ok=True)
    except OSError as error:
        parser.error(f"Cannot create the output directory: {error}")

    stop = threading.Event()
    interrupted = 0

    def request_stop(signum, _frame):
        nonlocal interrupted
        interrupted = signum
        stop.set()

    previous_handlers = {
        sig: signal.signal(sig, request_stop) for sig in (signal.SIGINT, signal.SIGTERM)
    }
    failures = []
    completed = 0
    print(f"{len(accessions)} runs; at most {args.workers} concurrent downloads; output: {output_dir}", flush=True)
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(download, accession, executable, output_dir,
                                args.retries, stop): accession
                for accession in accessions
            }
            for future in as_completed(futures):
                accession = futures[future]
                result = future.result()
                if result is None:
                    continue
                completed += 1
                if result:
                    print(f"[{completed}/{len(accessions)}] OK: {accession}", flush=True)
                else:
                    failures.append(accession)
                    print(f"[{completed}/{len(accessions)}] FAILED: {accession}", flush=True)
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)

    print(f"Successful: {completed - len(failures)}; failed: {len(failures)}; "
          f"pending/interrupted: {len(accessions) - completed}.")
    if failures:
        print("Failed runs: " + ", ".join(sorted(failures)))
        print(f"Details in: {output_dir / 'logs'}")
    if interrupted:
        print("Interrupted. Rerun the same command to resume downloads with prefetch.")
        return 128 + interrupted
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
