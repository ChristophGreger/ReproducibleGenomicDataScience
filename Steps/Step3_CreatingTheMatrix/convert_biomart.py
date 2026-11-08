#!/usr/bin/env python3
"""Validate a BioMart export and normalize it to AlterNet's seven-column TSV."""

import argparse
import csv
import os
from pathlib import Path
import re
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COLUMNS = (
    "Gene stable ID",
    "Gene stable ID version",
    "Transcript stable ID",
    "Transcript stable ID version",
    "Gene name",
    "Transcript name",
    "Gene type",
)
GENE_ID = re.compile(r"ENSG[0-9]{11}")
TRANSCRIPT_ID = re.compile(r"ENST[0-9]{11}")
VERSION = re.compile(r"[1-9][0-9]*")


def validate_ids(row, line_number):
    for stable, versioned, pattern in ((row[0], row[1], GENE_ID),
                                       (row[2], row[3], TRANSCRIPT_ID)):
        if not pattern.fullmatch(stable):
            raise ValueError("Line {}: invalid human Ensembl stable ID {!r}."
                             .format(line_number, stable))
        base, separator, version = versioned.rpartition(".")
        if base != stable or separator != "." or not VERSION.fullmatch(version):
            raise ValueError("Line {}: versioned ID {!r} must be {}.<positive version>."
                             .format(line_number, versioned, stable))


def convert(source, destination, force=False):
    source = source.resolve()
    destination = destination.resolve()
    if source == destination or (destination.exists() and os.path.samefile(source, destination)):
        raise ValueError("Input and output must be different files.")
    if destination.exists() and not force:
        raise ValueError("Output already exists: {}. Use --force to replace it."
                         .format(destination))
    if not source.is_file():
        raise ValueError("Input file does not exist: {}".format(source))

    seen_transcripts = {}
    seen_genes = {}
    read_rows = written_rows = duplicates = 0
    temporary = None
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            header_line = handle.readline()
            if not header_line:
                raise ValueError("Input file is empty: {}".format(source))
            try:
                delimiter = csv.Sniffer().sniff(header_line, delimiters="\t,").delimiter
            except csv.Error as error:
                raise ValueError("Expected a tab- or comma-separated header.") from error
            handle.seek(0)
            reader = csv.reader(handle, delimiter=delimiter, strict=True)
            header = [value.strip() for value in next(reader)]
            if len(set(header)) != len(header):
                raise ValueError("Input header contains duplicate column names.")
            missing = [column for column in COLUMNS if column not in header]
            if missing:
                raise ValueError("Missing required columns: {}.".format(", ".join(missing)))
            positions = [header.index(column) for column in COLUMNS]

            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", delete=False,
                prefix="." + destination.name + "-", suffix=".tmp",
                dir=str(destination.parent),
            ) as output:
                temporary = Path(output.name)
                writer = csv.writer(output, delimiter="\t", lineterminator="\n")
                writer.writerow(COLUMNS)
                for values in reader:
                    if not values:
                        continue
                    if len(values) != len(header):
                        raise ValueError("Line {}: expected {} fields, found {}."
                                         .format(reader.line_num, len(header), len(values)))
                    row = tuple(values[position].strip() for position in positions)
                    read_rows += 1
                    validate_ids(row, reader.line_num)
                    gene_id, _, transcript_id = row[:3]
                    previous = seen_transcripts.get(transcript_id)
                    if previous is not None:
                        if previous != row:
                            raise ValueError("Line {}: conflicting annotation or gene mapping for {}."
                                             .format(reader.line_num, transcript_id))
                        duplicates += 1
                        continue
                    gene_annotation = (row[1], row[4], row[6])
                    if gene_id in seen_genes and seen_genes[gene_id] != gene_annotation:
                        raise ValueError("Line {}: conflicting gene annotation for {}."
                                         .format(reader.line_num, gene_id))
                    seen_genes[gene_id] = gene_annotation
                    seen_transcripts[transcript_id] = row
                    writer.writerow(row)
                    written_rows += 1
                if not written_rows:
                    raise ValueError("Input contains no annotation records.")
            if force:
                os.replace(str(temporary), str(destination))
            else:
                # Exclusive publication also protects against an output created
                # by another process after the initial existence check.
                os.link(str(temporary), str(destination))
        return read_rows, written_rows, duplicates
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", type=Path,
                        default=PROJECT_ROOT / "files/special_files/mart_export.txt",
                        help="Tab- or comma-separated BioMart export")
    parser.add_argument("--output", type=Path,
                        default=PROJECT_ROOT / "files/special_files/biomart_ensembl116.txt",
                        help="Destination for the normalized seven-column TSV")
    parser.add_argument("--force", action="store_true",
                        help="Replace an existing output file")
    args = parser.parse_args()
    try:
        read_rows, written_rows, duplicates = convert(args.input, args.output, args.force)
    except KeyboardInterrupt:
        print("Interrupted; no incomplete output was published.", file=sys.stderr)
        return 130
    except (OSError, ValueError, csv.Error) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 1
    print("Read {:,} rows; wrote {:,} unique transcripts; removed {:,} identical duplicates."
          .format(read_rows, written_rows, duplicates))
    print("BioMart TSV: {}".format(args.output.resolve()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
