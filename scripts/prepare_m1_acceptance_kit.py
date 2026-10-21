"""Create a checksummed M1 desktop acceptance kit from public fixtures only."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KIT_FILES = {
    "manual-report.json": "tests/fixtures/m1-manual-acceptance-template.json",
    "inputs/synthetic-mopa-import.lbrn2": "tests/fixtures/synthetic-mopa-import.lbrn2",
    "inputs/synthetic-jcz-device.lbdev": "tests/fixtures/synthetic-jcz-device.lbdev",
    "inputs/synthetic-pirateray-recipe-metadata.json": (
        "tests/fixtures/synthetic-pirateray-recipe-metadata.json"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repository_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def create_kit(output: Path, repository_commit: str | None = None) -> dict:
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"acceptance-kit directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    records = []
    for destination, source_name in KIT_FILES.items():
        source = ROOT / source_name
        target = output / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({
            "path": destination,
            "source": source_name,
            "classification": "synthetic-public",
            "bytes": target.stat().st_size,
            "sha256": _sha256(target),
        })

    manifest = {
        "schema_version": 1,
        "kit": "M1 packaged no-device desktop acceptance",
        "repository_commit": repository_commit or _repository_commit(),
        "hardware_access_authorized": False,
        "contains_private_evidence": False,
        "files": records,
    }
    manifest_path = output / "kit-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".build" / "acceptance-kit",
    )
    args = parser.parse_args()
    result = create_kit(args.output)
    print(f"kit={args.output.resolve()}")
    print(f"files={len(result['files'])}")
    print(f"repository_commit={result['repository_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
