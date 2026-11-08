#!/usr/bin/env python3
"""Filter raw transcript TPMs by APPRIS transcript type and expression prevalence."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPT_ID = re.compile(r"(ENST[0-9]{11})(?:\.[1-9][0-9]*)?")
GENE_ID = re.compile(r"(ENSG[0-9]{11})(?:\.[1-9][0-9]*)?")
OUTPUT_NAMES = ("transcript_tpm_filtered.tsv", "filtering_summary.json")


def positive_fraction(value):
    try:
        fraction = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise argparse.ArgumentTypeError("Use a fraction between 0 and 1, e.g. 0.5 or 1/2") from error
    if not 0 <= fraction <= 1:
        raise argparse.ArgumentTypeError("The positive fraction must be between 0 and 1")
    return fraction


def stable_id(value, pattern, context):
    match = pattern.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Invalid Ensembl ID {value!r}: {context}")
    return match.group(1)


def fingerprint(path):
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"Input changed while its SHA256 was being computed: {path}")
    return {"path": str(path.resolve()), "size_bytes": after.st_size,
            "mtime_ns": after.st_mtime_ns, "sha256": digest.hexdigest()}


def read_appris(path):
    """Use every APPRIS class; only the exact Transcript type controls coding."""
    mapping = {}
    seen_rows = set()
    counts = Counter()
    transcript_types = Counter()
    required = {"Ensembl Gene ID", "Transcript ID", "Transcript type"}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t", strict=True)
        header = next(reader, [])
        if len(header) != len(set(header)) or not required.issubset(header):
            raise ValueError(f"APPRIS must have unique columns including {sorted(required)}: {path}")
        gene_column = header.index("Ensembl Gene ID")
        transcript_column = header.index("Transcript ID")
        type_column = header.index("Transcript type")
        for row in reader:
            if len(row) != len(header):
                raise ValueError(f"Malformed APPRIS row in {path}, line {reader.line_num}")
            context = f"{path}, line {reader.line_num}"
            transcript = stable_id(row[transcript_column], TRANSCRIPT_ID, context)
            gene = stable_id(row[gene_column], GENE_ID, context)
            transcript_type = row[type_column]
            if not transcript_type.strip():
                raise ValueError(f"Missing APPRIS Transcript type: {context}")
            annotation = (gene, transcript_type)
            counts["input_records"] += 1
            if transcript in mapping and mapping[transcript] != annotation:
                raise ValueError(f"Conflicting APPRIS gene/type mappings for {transcript}: "
                                 f"{mapping[transcript]!r} versus {annotation!r}")
            # Hash the complete parsed row to recognize identical duplicates
            # without keeping every annotation field in memory.
            signature = hashlib.sha256(json.dumps(row, ensure_ascii=False,
                                      separators=(",", ":")).encode("utf-8")).digest()
            if signature in seen_rows:
                counts["identical_duplicate_records"] += 1
                continue
            seen_rows.add(signature)
            if transcript in mapping:
                counts["additional_records_with_consistent_mapping"] += 1
                continue
            mapping[transcript] = annotation
            transcript_types[transcript_type] += 1
    if not mapping:
        raise ValueError(f"No transcript annotations found in {path}")
    return mapping, {
        "input_records": counts["input_records"],
        "identical_duplicate_records": counts["identical_duplicate_records"],
        "additional_records_with_consistent_mapping": counts["additional_records_with_consistent_mapping"],
        "unique_transcripts": len(mapping),
        "protein_coding_transcripts": transcript_types["protein_coding"],
        "unique_transcript_type_counts": dict(transcript_types),
    }


def filter_matrix(args, mapping, destination):
    counts = Counter()
    seen = set()
    retained_genes = set()
    with args.input.open(encoding="utf-8-sig", newline="") as source, \
            (destination / OUTPUT_NAMES[0]).open("w", encoding="utf-8", newline="") as output:
        reader = csv.reader(source, delimiter="\t", strict=True)
        header = next(reader, [])
        if len(header) < 3 or header[:2] != ["transcript_id", "gene_id"]:
            raise ValueError("Matrix must start with transcript_id, gene_id and at least one sample column")
        if len(header) != len(set(header)) or any(not sample.strip() for sample in header[2:]):
            raise ValueError("Matrix column names must be unique and sample names must be nonempty")
        samples = header[2:]
        fraction = args.min_positive_fraction
        minimum_positive = (fraction.numerator * len(samples) + fraction.denominator - 1) // fraction.denominator
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        for row in reader:
            if len(row) != len(header):
                raise ValueError(f"Malformed matrix row at line {reader.line_num}: expected {len(header)} fields")
            context = f"{args.input}, line {reader.line_num}"
            transcript = stable_id(row[0], TRANSCRIPT_ID, context)
            gene = stable_id(row[1], GENE_ID, context)
            if transcript in seen:
                raise ValueError(f"Duplicate matrix transcript ID: {transcript}")
            seen.add(transcript)
            annotation = mapping.get(transcript)
            if annotation is not None and gene != annotation[0]:
                raise ValueError(f"Matrix/APPRIS gene mismatch for {transcript}: {gene} versus {annotation[0]}")
            try:
                values = [float(value) for value in row[2:]]
            except ValueError as error:
                raise ValueError(f"Invalid numeric TPM for {transcript}: {context}") from error
            if any(not math.isfinite(value) or value < 0 for value in values):
                raise ValueError(f"TPMs must be finite and nonnegative, including excluded rows: {transcript}")
            counts["input_transcripts"] += 1
            if annotation is None:
                counts["removed_missing_appris"] += 1
            else:
                counts["matched_appris_transcripts"] += 1
                if annotation[1] != "protein_coding":
                    counts["removed_appris_non_protein_coding"] += 1
                else:
                    counts["protein_coding_before_prevalence"] += 1
                    if sum(value > 0 for value in values) < minimum_positive:
                        counts["removed_low_prevalence"] += 1
                    else:
                        # Preserve the original field strings, including TPM
                        # precision, ID suffixes and sample/row ordering.
                        writer.writerow(row)
                        retained_genes.add(gene)
                        counts["retained_transcripts"] += 1
            if counts["input_transcripts"] % 100000 == 0:
                print(f"Validated {counts['input_transcripts']:,} rows; retained {counts['retained_transcripts']:,}", flush=True)
    counts["retained_genes"] = len(retained_genes)
    names = ("input_transcripts", "matched_appris_transcripts", "removed_missing_appris",
             "removed_appris_non_protein_coding", "protein_coding_before_prevalence",
             "removed_low_prevalence", "retained_transcripts", "retained_genes")
    return {"sample_count": len(samples), "sample_ids": samples,
            "minimum_positive_samples": minimum_positive,
            "counts": {name: counts[name] for name in names}}


def process(args):
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise ValueError(f"Output directory already exists: {args.output_dir}. Choose a new --output-dir")
    output = args.output_dir.resolve()
    inputs = {"matrix": args.input, "appris": args.appris}
    for source in inputs.values():
        try:
            source.resolve().relative_to(output)
        except ValueError:
            pass
        else:
            raise ValueError(f"An input path cannot be inside the output directory: {source}")
        if not source.is_file():
            raise ValueError(f"Input file does not exist: {source}")
    metadata = {name: fingerprint(path) for name, path in inputs.items()}
    mapping, annotation_summary = read_appris(args.appris)
    print(f"Loaded {len(mapping):,} APPRIS transcripts; "
          f"{annotation_summary['protein_coding_transcripts']:,} have Transcript type == protein_coding", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{output.name}-", dir=output.parent) as temporary:
        destination = Path(temporary) / "completed"
        destination.mkdir()
        summary = filter_matrix(args, mapping, destination)
        for name, source in inputs.items():
            stat = source.stat()
            if (stat.st_size, stat.st_mtime_ns) != (metadata[name]["size_bytes"], metadata[name]["mtime_ns"]):
                raise ValueError(f"Input changed during filtering: {source}")
        summary.update({
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "inputs": metadata,
            "annotation_summary": annotation_summary,
            "settings": {
                "appris_filter_column": "Transcript type",
                "appris_filter_operator": "==",
                "appris_filter_value": "protein_coding",
                "additional_appris_filters": [],
                "min_positive_fraction": str(args.min_positive_fraction),
                "positive_tpm_threshold": 0,
                "id_matching": "Ensembl stable IDs; optional numeric version suffixes are ignored",
                "normalization": "none; retained TPM field strings are copied unchanged",
                "gene_aggregation": "none",
                "missing_appris_transcripts": "excluded and counted separately",
            },
            "output_orientation": "transcript rows, sample columns",
            "output_files": list(OUTPUT_NAMES),
        })
        (destination / OUTPUT_NAMES[1]).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        if args.output_dir.exists() or args.output_dir.is_symlink() or output.exists():
            raise ValueError(f"Output directory appeared during processing: {args.output_dir}")
        os.rename(destination, output)
    counts = summary["counts"]
    print(f"Retained {counts['retained_transcripts']:,}/{counts['input_transcripts']:,} transcripts "
          f"from {counts['retained_genes']:,} genes across {summary['sample_count']} samples", flush=True)
    print(f"Excluded {counts['removed_missing_appris']:,} transcripts missing from APPRIS, "
          f"{counts['removed_appris_non_protein_coding']:,} other transcript types, and "
          f"{counts['removed_low_prevalence']:,} low-prevalence transcripts", flush=True)
    print(f"Saved two output files to {output}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "files/matrix/transcript_tpm_unfiltered.tsv",
                        help="Unfiltered raw transcript TPM matrix")
    parser.add_argument("--appris", type=Path, default=PROJECT_ROOT / "files/special_files/appris_data.appris.txt",
                        help="Headered APPRIS TSV with Ensembl Gene ID, Transcript ID and Transcript type")
    parser.add_argument("--min-positive-fraction", type=positive_fraction, default="0.5",
                        help="Minimum sample fraction with TPM > 0; decimal or exact fraction between 0 and 1")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "files/matrix/filtered",
                        help="New directory for the two outputs; must not already exist")
    args = parser.parse_args()
    try:
        process(args)
    except (OSError, ValueError, csv.Error, OverflowError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted; no incomplete output was published.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
