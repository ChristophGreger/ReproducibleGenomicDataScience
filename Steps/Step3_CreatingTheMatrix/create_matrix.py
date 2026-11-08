#!/usr/bin/env python3
"""Join kallisto transcript TPMs into an unfiltered AlterNet-style TSV matrix."""

import argparse
from array import array
import csv
import math
import mmap
import os
from pathlib import Path
import re
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPT_ID = re.compile(r"ENST[0-9]{11}(?:\.[1-9][0-9]*)?")
STABLE_TRANSCRIPT_ID = re.compile(r"ENST[0-9]{11}")
GENE_ID = re.compile(r"ENSG[0-9]{11}")
VERSION_NUMBER = re.compile(r"[1-9][0-9]*")


def read_accessions(path):
    accessions = []
    seen = set()
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        accession = line.strip()
        if not accession:
            continue
        if not re.fullmatch(r"(?:SRR|ERR|DRR)[0-9]+", accession):
            raise ValueError(f"Invalid run ID in {path}, line {number}: {accession!r}")
        if accession in seen:
            raise ValueError(f"Duplicate run ID in {path}: {accession}")
        seen.add(accession)
        accessions.append(accession)
    if not accessions:
        raise ValueError(f"No run IDs found in {path}")
    return accessions


def read_biomart(path):
    mapping = {}
    required = {"Transcript stable ID", "Transcript stable ID version", "Gene stable ID"}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing required BioMart columns in {path}: {sorted(required)}")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"Duplicate BioMart column names in {path}")
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f"Malformed BioMart row in {path}, line {reader.line_num}")
            transcript = row["Transcript stable ID"].strip()
            version = row["Transcript stable ID version"].strip()
            gene = row["Gene stable ID"].strip()
            if not STABLE_TRANSCRIPT_ID.fullmatch(transcript) or not GENE_ID.fullmatch(gene):
                raise ValueError(f"Invalid BioMart stable IDs in {path}, line {reader.line_num}")
            stable_part, separator, number = version.rpartition(".")
            if stable_part != transcript or not separator or not VERSION_NUMBER.fullmatch(number):
                raise ValueError(f"Inconsistent transcript version in {path}, line {reader.line_num}")
            pair = (gene, version)
            if transcript in mapping and mapping[transcript] != pair:
                raise ValueError(f"Conflicting BioMart mappings for {transcript}")
            mapping[transcript] = pair
    if not mapping:
        raise ValueError(f"No transcript mappings found in {path}")
    return mapping


def read_abundance(path, mapping, positions=None):
    """Use numeric arrays and a byte mask instead of one Python object per cell."""
    first_sample = positions is None
    if first_sample:
        positions = {}
    values = array("d") if first_sample else array("d", [0.0]) * len(positions)
    seen = None if first_sample else bytearray(len(positions))
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, [])
        if len(header) != len(set(header)) or not {"target_id", "tpm"}.issubset(header):
            raise ValueError(f"Expected unique target_id and tpm columns in {path}")
        target_column, tpm_column = header.index("target_id"), header.index("tpm")
        for row in reader:
            if len(row) != len(header):
                raise ValueError(f"Malformed abundance row in {path}, line {reader.line_num}")
            target = row[target_column].strip()
            if not TRANSCRIPT_ID.fullmatch(target):
                raise ValueError(f"Invalid target ID in {path}, line {reader.line_num}: {target!r}")
            transcript = target.split(".", 1)[0]
            annotation = mapping.get(transcript)
            if annotation is None:
                raise ValueError(f"No BioMart mapping for {target} in {path}; check annotation releases")
            if "." in target and target != annotation[1]:
                raise ValueError(f"Transcript version mismatch for {target} in {path}: BioMart has {annotation[1]}")
            try:
                tpm = float(row[tpm_column])
            except ValueError as error:
                raise ValueError(f"Invalid TPM in {path}, line {reader.line_num}") from error
            if not math.isfinite(tpm) or tpm < 0:
                raise ValueError(f"TPM must be finite and nonnegative in {path}, line {reader.line_num}")
            if first_sample:
                if transcript in positions:
                    raise ValueError(f"Duplicate transcript {transcript} in {path}")
                positions[transcript] = len(values)
                values.append(tpm)
            else:
                index = positions.get(transcript)
                if index is None:
                    raise ValueError(f"Unexpected transcript {transcript} in {path}; samples use different target sets")
                if seen[index]:
                    raise ValueError(f"Duplicate transcript {transcript} in {path}")
                seen[index] = 1
                values[index] = tpm
    if not values:
        raise ValueError(f"No transcript TPMs found in {path}")
    if not first_sample and 0 in seen:
        raise ValueError(f"{path} is missing {seen.count(0)} transcripts present in the first sample")
    return positions, values


def create_matrix(args):
    accessions = read_accessions(args.accessions)
    inputs = [args.quant_dir / accession / "abundance.tsv" for accession in accessions]
    for path in inputs:
        if not path.is_file():
            raise ValueError(f"Missing abundance file: {path}. Finish Step 2 or supply another --accessions file")
    output = args.output.resolve()
    if output in {path.resolve() for path in [args.biomart, args.accessions, *inputs]}:
        raise ValueError("The output path must differ from all input paths")
    if output.exists() and not args.force:
        raise ValueError(f"Output already exists: {output}. Use --force to replace it")
    mapping = read_biomart(args.biomart)
    print(f"Loaded {len(mapping):,} BioMart transcript mappings.", flush=True)
    positions, values = read_abundance(inputs[0], mapping)
    transcripts = list(positions)
    rows, columns = len(transcripts), len(accessions)
    print(f"Creating {rows:,} transcript rows and {columns} sample columns; no filtering or rescaling.", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    # The dense numeric workspace lives on disk; RAM use does not grow by a
    # Python float object for every transcript/sample combination.
    with tempfile.TemporaryDirectory(prefix=".create-matrix-", dir=output.parent) as temporary:
        workspace = Path(temporary)
        with (workspace / "values.bin").open("w+b") as binary:
            binary.truncate(rows * columns * values.itemsize)
            with mmap.mmap(binary.fileno(), 0) as memory:
                cells = memoryview(memory).cast("d")
                try:
                    cells[0::columns] = values
                    print(f"[1/{columns}] {accessions[0]}: validated and loaded", flush=True)
                    for column, (accession, path) in enumerate(zip(accessions[1:], inputs[1:]), 1):
                        _, values = read_abundance(path, mapping, positions)
                        cells[column::columns] = values
                        print(f"[{column + 1}/{columns}] {accession}: validated and loaded", flush=True)
                    staged = workspace / "matrix.tsv"
                    with staged.open("w", encoding="utf-8", newline="") as handle:
                        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
                        writer.writerow(["transcript_id", "gene_id", *accessions])
                        for index, transcript in enumerate(transcripts):
                            start = index * columns
                            # repr(float) round-trips every parsed TPM value.
                            row_values = [repr(cells[start + column]) for column in range(columns)]
                            writer.writerow([transcript, mapping[transcript][0], *row_values])
                            if (index + 1) % 100000 == 0:
                                print(f"Wrote {index + 1:,}/{rows:,} transcript rows", flush=True)
                finally:
                    cells.release()
        if args.force:
            os.replace(staged, output)
        else:
            # Publish exclusively, including if another process created the
            # destination while this invocation was building the matrix.
            os.link(staged, output)
    print(f"Saved {rows:,} transcripts x {columns} samples to {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--biomart", type=Path,
                        default=PROJECT_ROOT / "files/special_files/biomart_ensembl116.txt",
                        help="Normalized, tab-separated BioMart annotation")
    parser.add_argument("--quant-dir", type=Path, default=PROJECT_ROOT / "files/kallisto/quant",
                        help="Directory containing RUN_ID/abundance.tsv files")
    parser.add_argument("--accessions", type=Path,
                        default=PROJECT_ROOT / "Steps/Step1_Downloading_Sequences/SRR_Acc_List.txt",
                        help="Run IDs to include, one per line, in output column order")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "files/matrix/transcript_tpm_unfiltered.tsv",
                        help="Destination TSV matrix")
    parser.add_argument("--force", action="store_true", help="Replace an existing output after successful validation")
    args = parser.parse_args()
    try:
        create_matrix(args)
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted; temporary matrix files removed.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
