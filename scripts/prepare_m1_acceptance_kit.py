"""Create a checksummed M1 desktop acceptance kit from public fixtures only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAYFORGE_COMMIT = json.loads(
    (ROOT / "upstreams" / "rayforge.json").read_text(encoding="utf-8")
)["commit"]
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_ADDON_FILES = sum(
    path.is_file() and "__pycache__" not in path.parts
    for path in (ROOT / "spikes" / "rayforge-jcz-no-device-addon").rglob("*")
)
REPORT_TEMPLATE = "tests/fixtures/m1-manual-acceptance-template.json"
KIT_FILES = {
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


def create_kit(
    output: Path,
    repository_commit: str | None = None,
    artifact_verification: Path | None = None,
    checkpoint_manifest: Path | None = None,
) -> dict:
    verification_source = None
    checkpoint_source = None
    if (artifact_verification is None) != (checkpoint_manifest is None):
        raise ValueError(
            "artifact verification and checkpoint manifest must be supplied together"
        )
    if artifact_verification is not None and checkpoint_manifest is not None:
        verification_source = artifact_verification.resolve()
        checkpoint_source = checkpoint_manifest.resolve()
        verification = json.loads(
            verification_source.read_text(encoding="utf-8-sig")
        )
        checkpoint_bytes = checkpoint_source.read_bytes()
        checkpoint = json.loads(checkpoint_bytes.decode("utf-8-sig"))
        checkpoint_record = verification.get("checkpoint_manifest", {})
        if (
            verification.get("schema_version") != 1
            or verification.get("verification")
            != "Rayforge Windows no-device artifact verification"
            or verification.get("status") != "passed"
            or verification.get("hardware_access") is not False
            or verification.get("executed_binaries") is not False
            or verification.get("manual_interaction_required") is not True
            or verification.get("rayforge_commit") != RAYFORGE_COMMIT
            or SHA256.fullmatch(verification.get("bundle_sha256", "")) is None
            or SHA256.fullmatch(verification.get("installer_sha256", "")) is None
            or verification.get("verified_addon_files") != EXPECTED_ADDON_FILES
            or verification.get("addon") != "the_pirate_ray_jcz"
            or checkpoint_record.get("path") != checkpoint_source.name
            or checkpoint_record.get("sha256")
            != hashlib.sha256(checkpoint_bytes).hexdigest()
            or checkpoint.get("schema_version") != 2
            or checkpoint.get("checkpoint") != "Rayforge Windows no-device bundle"
            or checkpoint.get("addon") != verification.get("addon")
            or checkpoint.get("rayforge_commit")
            != verification.get("rayforge_commit")
            or checkpoint.get("bundle", {}).get("sha256")
            != verification.get("bundle_sha256")
            or checkpoint.get("installer", {}).get("sha256")
            != verification.get("installer_sha256")
        ):
            raise ValueError("artifact-verification report did not pass the no-device gate")

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

    commit = repository_commit or _repository_commit()
    template_path = ROOT / REPORT_TEMPLATE
    manifest = {
        "schema_version": 2,
        "kit": "M1 packaged no-device desktop acceptance",
        "repository_commit": commit,
        "hardware_access_authorized": False,
        "contains_private_evidence": False,
        "report_template": {
            "source": REPORT_TEMPLATE,
            "sha256": _sha256(template_path),
        },
        "files": records,
    }
    manifest_path = output / "kit-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report = json.loads(template_path.read_text(encoding="utf-8"))
    report["acceptance_kit"] = {
        "manifest_path": "kit-manifest.json",
        "manifest_sha256": _sha256(manifest_path),
        "repository_commit": commit,
    }
    if verification_source is not None:
        verification_target = output / "artifact-verification.json"
        shutil.copyfile(verification_source, verification_target)
        checkpoint_target = output / checkpoint_source.name
        shutil.copyfile(checkpoint_source, checkpoint_target)
        report["artifact_verification"] = {
            "status": "passed",
            "report_path": verification_target.name,
            "report_sha256": _sha256(verification_target),
        }
    (output / "manual-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
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
    parser.add_argument(
        "--checkpoint-manifest",
        type=Path,
        help="schema-2 manifest consumed by the artifact verifier",
    )
    parser.add_argument(
        "--artifact-verification",
        type=Path,
        help="passing JSON output from verify_rayforge_windows_checkpoint.py",
    )
    args = parser.parse_args()
    result = create_kit(
        args.output,
        artifact_verification=args.artifact_verification,
        checkpoint_manifest=args.checkpoint_manifest,
    )
    print(f"kit={args.output.resolve()}")
    print(f"files={len(result['files'])}")
    print(f"repository_commit={result['repository_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
