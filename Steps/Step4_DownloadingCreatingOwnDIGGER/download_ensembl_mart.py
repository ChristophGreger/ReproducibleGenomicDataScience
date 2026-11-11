"""Download and verify the Ensembl 116 BioMart tables used in Step 4."""

import argparse
from collections.abc import Callable
from pathlib import Path
import subprocess
import tempfile


BASE_URL = "https://ftp.ensembl.org/pub/release-116/mysql/ensembl_mart_116"
DEFAULT_ARCHIVE_DIR = (
    Path(__file__).resolve().parents[2] / "files" / "special_files" / "ensembl_mart_116"
)
MANIFEST_NAME = "CHECKSUMS"
SCHEMA_NAME = "ensembl_mart_116.sql.gz"
TABLE_PREFIX = "hsapiens_gene_ensembl__"
TABLE_SUFFIXES = (
    "exon_transcript__dm",
    "translation__main",
    "protein_feature_pfam__dm",
)
ARCHIVE_NAMES = (SCHEMA_NAME,) + tuple(
    f"{TABLE_PREFIX}{table}.txt.gz" for table in TABLE_SUFFIXES
)


def read_checksums(path: Path) -> dict[str, tuple[int, int]]:
    """Read BSD checksums and sizes in 1 KiB blocks for the required files."""
    checksums = {}
    with path.open(encoding="ascii") as manifest:
        for line in manifest:
            fields = line.split(maxsplit=2)
            if len(fields) == 3 and fields[2].strip() in ARCHIVE_NAMES:
                checksum, blocks, name = fields
                name = name.strip()
                if name in checksums:
                    raise ValueError(f"Duplicate checksum for {name} in {path}")
                checksums[name] = int(checksum), int(blocks)

    missing = set(ARCHIVE_NAMES) - checksums.keys()
    if missing:
        raise ValueError(f"{path} has no checksums for: {', '.join(sorted(missing))}")
    return checksums


def verify_archive(path: Path, expected: tuple[int, int]) -> None:
    """Check the compressed file with the same algorithm as BSD `sum`."""
    expected_checksum, expected_blocks = expected
    if (path.stat().st_size + 1023) // 1024 != expected_blocks:
        raise ValueError(f"{path.name}: file size does not match Ensembl CHECKSUMS")

    checksum = 0
    with path.open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            for byte in chunk:
                checksum = ((checksum >> 1) + ((checksum & 1) << 15) + byte) & 0xFFFF
    if checksum != expected_checksum:
        raise ValueError(f"{path.name}: checksum does not match Ensembl CHECKSUMS")


def download(destination: Path, verify: Callable[[Path], object]) -> None:
    """Validate a temporary download before publishing it in the cache."""
    url = f"{BASE_URL}/{destination.name}"
    print(f"Downloading {destination.name}", flush=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, suffix=".part", delete=False
    ) as output:
        temporary = Path(output.name)
    try:
        subprocess.run(
            [
                "curl", "--http1.1", "--fail", "--location", "--silent",
                "--show-error", "--proto", "=https", "--proto-redir", "=https",
                "--connect-timeout", "30", "--max-time", "600", "--retry", "2",
                "--output", str(temporary), url,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        verify(temporary)
        temporary.replace(destination)
    except FileNotFoundError as exc:
        if exc.filename == "curl":
            raise RuntimeError(
                "Install curl or provide a complete cache with --archive-dir"
            ) from exc
        raise
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Could not download {url}: {exc.stderr.strip()}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def prepare_archives(archive_dir: Path) -> None:
    """Ensure the schema and three data tables are present and verified."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    manifest = archive_dir / MANIFEST_NAME
    try:
        checksums = read_checksums(manifest)
    except (FileNotFoundError, ValueError):
        download(manifest, read_checksums)
        checksums = read_checksums(manifest)

    for name in ARCHIVE_NAMES:
        path = archive_dir / name
        expected = checksums[name]
        try:
            verify_archive(path, expected)
        except (FileNotFoundError, ValueError):
            download(path, lambda downloaded: verify_archive(downloaded, expected))
            print(f"Verified {name}", flush=True)
        else:
            print(f"Using verified archive {name}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive-dir", type=Path, default=DEFAULT_ARCHIVE_DIR,
        help="Folder for the Ensembl downloads (default: %(default)s)",
    )
    args = parser.parse_args()
    try:
        prepare_archives(args.archive_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"Ensembl archive error: {exc}\n")


if __name__ == "__main__":
    main()
