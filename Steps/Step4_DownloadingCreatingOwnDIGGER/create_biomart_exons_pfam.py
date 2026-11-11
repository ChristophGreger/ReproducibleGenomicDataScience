#!/usr/bin/env python3
"""Build the human Ensembl 116 exon/Pfam TSV from the official BioMart tables."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
import gzip
import hashlib
import os
from pathlib import Path
import re
import tempfile

from download_ensembl_mart import (
    DEFAULT_ARCHIVE_DIR,
    SCHEMA_NAME,
    TABLE_PREFIX,
    prepare_archives,
)


DEFAULT_OUTPUT = DEFAULT_ARCHIVE_DIR.parent / "biomart_exons_pfam_ensembl116.tsv"
EXPECTED_SHA256 = "8559a4af690dcc9c41688c79737575cb6ea8f7468d694a49ddd1c40bcba4b06a"
HEADER = b"Transcript stable ID\tExon stable ID\tPfam ID\n"
NULL = b"\\N"


@dataclass(frozen=True)
class ExportCounts:
    transcripts: int
    rows: int
    blank_pfam_rows: int


EXPECTED_COUNTS = ExportCounts(382_428, 7_525_629, 1_259_409)


def table_rows(archive_dir, schema, table_suffix, *columns):
    """Locate columns in the SQL schema and stream their values from the gzip file."""
    table = TABLE_PREFIX + table_suffix
    definition = re.search(
        rb"CREATE TABLE `" + re.escape(table.encode()) + rb"` \((.*?)\) ENGINE",
        schema,
        flags=re.DOTALL,
    )
    if definition is None:
        raise ValueError(f"Table {table} not found in {SCHEMA_NAME}")

    column_names = re.findall(rb"^\s+`([^`]+)` ", definition[1], flags=re.MULTILINE)
    positions = [column_names.index(column.encode()) for column in columns]
    last_position = max(positions)
    with gzip.open(archive_dir / f"{table}.txt.gz", "rb") as source:
        for line in source:
            fields = line.rstrip(b"\n").split(b"\t", last_position + 1)
            yield tuple(fields[position] for position in positions)


def load_pfam(archive_dir, schema):
    domains = defaultdict(set)
    for protein_id, pfam_id in table_rows(
        archive_dir, schema, "protein_feature_pfam__dm", "translation_id_1068_key", "hit_name_1048"
    ):
        # SQL NULL keys cannot join to a translation. A NULL domain becomes a blank field.
        if protein_id == NULL:
            continue
        domains[protein_id].add(b"" if pfam_id == NULL else pfam_id)
    return {protein_id: tuple(sorted(ids)) for protein_id, ids in domains.items()}


def load_translations(archive_dir, schema, domains):
    translations = {}
    for protein_id, stable_id, transcript_id in table_rows(
        archive_dir,
        schema,
        "translation__main",
        "translation_id_1068_key",
        "stable_id_1066",
        "transcript_id_1064_key",
    ):
        if protein_id == NULL:
            continue
        if protein_id not in domains:
            raise ValueError(f"No Pfam table entry for translation {protein_id.decode()}")

        translation = (stable_id, protein_id)
        if translations.setdefault(transcript_id, translation) != translation:
            raise ValueError(f"Conflicting translations for transcript {stable_id.decode()}")
    return translations


def write_export(archive_dir, target):
    with gzip.open(archive_dir / SCHEMA_NAME, "rb") as source:
        schema = source.read()

    print("Reading the Pfam and translation tables", flush=True)
    domains = load_pfam(archive_dir, schema)
    translations = load_translations(archive_dir, schema, domains)

    print("Joining exons and Pfam IDs and writing the TSV", flush=True)
    seen_exons = defaultdict(set)
    rows = 0
    blank_pfam_rows = 0
    target.write(HEADER)
    for transcript_id, exon_id in table_rows(
        archive_dir, schema, "exon_transcript__dm", "transcript_id_1064_key", "stable_id_1016"
    ):
        if transcript_id not in translations or exon_id == NULL:
            continue
        if exon_id in seen_exons[transcript_id]:
            continue
        seen_exons[transcript_id].add(exon_id)

        stable_id, protein_id = translations[transcript_id]
        pfam_ids = domains[protein_id]
        # BioMart returns every exon/Pfam combination within a transcript for these attributes.
        prefix = stable_id + b"\t" + exon_id + b"\t"
        target.write(b"".join(prefix + pfam_id + b"\n" for pfam_id in pfam_ids))
        rows += len(pfam_ids)
        blank_pfam_rows += b"" in pfam_ids

    return ExportCounts(len(seen_exons), rows, blank_pfam_rows)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, default=DEFAULT_ARCHIVE_DIR,
                        help="directory for the downloaded Ensembl archives (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="path for the generated TSV (default: %(default)s)")
    args = parser.parse_args()

    temporary_path = None
    try:
        prepare_archives(args.archive_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=args.output.parent, prefix=".biomart-", delete=False) as target:
            temporary_path = Path(target.name)
            counts = write_export(args.archive_dir, target)

        if counts != EXPECTED_COUNTS:
            raise ValueError(f"Unexpected export counts: {counts}. Expected {EXPECTED_COUNTS}.")
        digest = sha256(temporary_path)
        if digest != EXPECTED_SHA256:
            raise ValueError(f"Unexpected export SHA-256: {digest}. Expected {EXPECTED_SHA256}.")

        # Link the verified temporary file into place without replacing an existing output.
        try:
            os.link(temporary_path, args.output)
        except FileExistsError:
            if sha256(args.output) != digest:
                raise ValueError(f"Existing output differs: {args.output}. Choose a different --output path.")
            print(f"Existing output verified: {args.output}")
        else:
            print(f"Created: {args.output}")

        print(f"{counts.rows:,} rows for {counts.transcripts:,} transcripts "
              f"({counts.blank_pfam_rows:,} rows with a blank Pfam ID)")
        print(f"SHA-256: {digest}")
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
