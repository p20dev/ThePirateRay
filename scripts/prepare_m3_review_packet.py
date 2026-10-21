"""Freeze a review-ready M3 plan into a non-authorizing review packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

if __package__:
    from scripts.validate_m3_hardware_protocol import validate
else:
    from validate_m3_hardware_protocol import validate


ROOT = Path(__file__).resolve().parents[1]


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


def create_packet(
    plan_path: Path,
    output: Path,
    repository_commit: str | None = None,
) -> dict:
    source = plan_path.resolve()
    validation = validate(source)
    if validation["status"] != "ready_for_review":
        raise ValueError("M3 plan is not ready for review")

    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"review-packet directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    frozen_plan = output / "plan.json"
    shutil.copyfile(source, frozen_plan)
    plan = json.loads(frozen_plan.read_text(encoding="utf-8-sig"))
    commit = repository_commit or _repository_commit()

    review = {
        "schema_version": 1,
        "review": "M3 hardware research session plan",
        "binding": {
            "plan_path": frozen_plan.name,
            "plan_sha256": _sha256(frozen_plan),
            "repository_commit": commit,
        },
        "session_window": {
            "starts_at": plan["session"]["planned_at"],
            "ends_at": plan["session"]["ends_at"],
        },
        "decision": "not_reviewed",
        "reviewer": None,
        "reviewed_at": None,
        "statements": {
            "exact_plan_bytes_reviewed": False,
            "operation_evidence_reviewed": False,
            "physical_controls_reviewed": False,
            "driver_and_rollback_reviewed": False,
            "abort_and_recovery_reviewed": False,
        },
        "notes": "",
        "hardware_access_authorized": False,
        "separate_human_approval_required": True,
    }
    review_path = output / "approval-record-template.json"
    review_path.write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    manifest = {
        "schema_version": 1,
        "packet": "M3 hardware research plan review",
        "repository_commit": commit,
        "contains_private_evidence": False,
        "hardware_access_authorized": False,
        "files": [
            {
                "path": frozen_plan.name,
                "bytes": frozen_plan.stat().st_size,
                "sha256": _sha256(frozen_plan),
            },
            {
                "path": review_path.name,
                "bytes": review_path.stat().st_size,
                "sha256": _sha256(review_path),
            },
        ],
    }
    manifest_path = output / "packet-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".build" / "m3-review-packet",
    )
    args = parser.parse_args()
    try:
        result = create_packet(args.plan, args.output)
    except ValueError as error:
        parser.error(str(error))
    print(f"packet={args.output.resolve()}")
    print(f"plan_sha256={result['files'][0]['sha256']}")
    print("hardware_access_authorized=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
