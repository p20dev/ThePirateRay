"""Verify a packaged no-device checkpoint without executing its binaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = json.loads(
    (ROOT / "upstreams" / "rayforge.json").read_text(encoding="utf-8")
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _text_digest_lf(data: bytes) -> str:
    normalized = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _artifact_path(root: Path, value: str) -> Path:
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 1:
        raise ValueError(f"artifact path must be one filename: {value!r}")
    return root / relative.name


def _check_file(root: Path, record: dict, label: str) -> Path:
    path = _artifact_path(root, record["path"])
    data = path.read_bytes()
    if record.get("bytes") != len(data):
        raise ValueError(f"{label} size mismatch")
    digest = record.get("sha256", "")
    if not SHA256.fullmatch(digest) or digest != _digest(data):
        raise ValueError(f"{label} SHA-256 mismatch")
    return path


def verify(manifest_path: Path) -> dict:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("schema_version") != 2:
        raise ValueError("unsupported checkpoint schema")
    if manifest.get("rayforge_commit") != UPSTREAM["commit"]:
        raise ValueError("Rayforge commit does not match the repository pin")
    if manifest.get("hardware_access") is not False or manifest.get("transport") is not None:
        raise ValueError("checkpoint does not declare a no-device boundary")
    if manifest.get("manual_interaction_required") is not True:
        raise ValueError("checkpoint must retain the manual interaction gate")

    artifact_root = manifest_path.parent
    bundle = _check_file(artifact_root, manifest["bundle"], "bundle")
    installer = _check_file(artifact_root, manifest["installer"], "installer")
    license_records = manifest.get("license_files", [])
    if len(license_records) != 1 or license_records[0].get("upstream") != "Rayforge":
        raise ValueError("checkpoint must include the Rayforge license sidecar")
    license_path = _check_file(artifact_root, license_records[0], "Rayforge license")
    expected_license_hash = UPSTREAM["license_file"]["sha256_lf"]
    if _text_digest_lf(license_path.read_bytes()) != expected_license_hash:
        raise ValueError("Rayforge license does not match the pinned upstream")
    packaged_root = PurePosixPath(manifest["addon_packaged_root"])
    if packaged_root.is_absolute() or ".." in packaged_root.parts:
        raise ValueError("unsafe packaged addon root")

    with zipfile.ZipFile(bundle) as archive:
        files = {
            PurePosixPath(info.filename): info
            for info in archive.infolist()
            if not info.is_dir()
        }
        for path in files:
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("bundle contains an unsafe path")
        executable = manifest["bundle"]["path"].removesuffix(".zip") + ".exe"
        if not any(path.name == executable for path in files):
            raise ValueError("bundle application executable is missing")
        bundle_license = PurePosixPath(license_records[0]["bundle_path"])
        license_matches = [
            path for path in files
            if tuple(path.parts[-len(bundle_license.parts):]) == bundle_license.parts
        ]
        if len(license_matches) != 1:
            raise ValueError("Rayforge license is missing from the portable bundle")
        if _text_digest_lf(archive.read(files[license_matches[0]])) != expected_license_hash:
            raise ValueError("bundled Rayforge license does not match the pinned upstream")

        verified_addon_files = 0
        for record in manifest["addon_source_files"]:
            relative = PurePosixPath(record["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe addon source path")
            matches = [
                path for path in files
                if tuple(path.parts[-len((packaged_root / relative).parts):])
                == (packaged_root / relative).parts
            ]
            if len(matches) != 1:
                raise ValueError(f"packaged addon file missing or ambiguous: {relative}")
            digest = record.get("sha256", "")
            if not SHA256.fullmatch(digest):
                raise ValueError(f"invalid addon SHA-256: {relative}")
            if _digest(archive.read(files[matches[0]])) != digest:
                raise ValueError(f"packaged addon SHA-256 mismatch: {relative}")
            verified_addon_files += 1

    return {
        "status": "passed",
        "rayforge_commit": manifest["rayforge_commit"],
        "hardware_access": False,
        "executed_binaries": False,
        "bundle_sha256": manifest["bundle"]["sha256"],
        "installer_sha256": manifest["installer"]["sha256"],
        "verified_addon_files": verified_addon_files,
        "manual_interaction_required": True,
        "installer_name": installer.name,
        "license_sidecar": license_path.name,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.manifest)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
