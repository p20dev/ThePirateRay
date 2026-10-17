#!/usr/bin/env python3
"""Build a deterministic JSON Lines manifest for an immutable artifact tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

CLASSIFICATIONS = ("public", "private-sensitive", "private-third-party")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_entry(
    path: Path,
    root: Path,
    classification: str,
    origin: str,
    observed_at: str,
    include_private_locators: bool,
) -> dict[str, object]:
    digest = sha256_file(path)
    entry: dict[str, object] = {
        "artifact_id": f"sha256-{digest[:20]}",
        "sha256": digest,
        "size_bytes": path.stat().st_size,
        "observed_at_utc": observed_at,
        "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "origin": origin,
        "classification": classification,
        "analysis_refs": [],
    }
    if include_private_locators:
        entry["relative_path"] = path.relative_to(root).as_posix()
    return entry


def build_manifest(
    root: Path,
    classification: str,
    origin: str,
    observed_at: str,
    include_private_locators: bool = True,
) -> list[dict[str, object]]:
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"unsupported classification: {classification}")
    if not root.is_dir():
        raise ValueError(f"artifact root is not a directory: {root}")
    files = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda p: p.relative_to(root).as_posix())
    return [
        manifest_entry(path, root, classification, origin, observed_at, include_private_locators)
        for path in files
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--classification", choices=CLASSIFICATIONS, required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument(
        "--observed-at",
        default=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        help="ISO-8601 acquisition timestamp; pass an explicit value for reproducible output",
    )
    parser.add_argument("--public", action="store_true", help="omit private relative paths")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = build_manifest(
        args.root.resolve(),
        args.classification,
        args.origin,
        args.observed_at,
        include_private_locators=not args.public,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        for entry in entries:
            stream.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {len(entries)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
