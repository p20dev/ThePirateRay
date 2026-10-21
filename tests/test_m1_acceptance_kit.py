import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_m1_acceptance_kit import (
    KIT_FILES,
    REPORT_TEMPLATE,
    ROOT,
    create_kit,
)


class M1AcceptanceKitTests(unittest.TestCase):
    def test_kit_contains_only_allowlisted_public_inputs(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            output = Path(directory) / "kit"
            manifest = create_kit(output, repository_commit="a" * 40)
            self.assertFalse(manifest["hardware_access_authorized"])
            self.assertFalse(manifest["contains_private_evidence"])
            self.assertEqual(2, manifest["schema_version"])
            self.assertEqual(
                hashlib.sha256((ROOT / REPORT_TEMPLATE).read_bytes()).hexdigest(),
                manifest["report_template"]["sha256"],
            )
            self.assertEqual(
                {record["path"] for record in manifest["files"]},
                set(KIT_FILES),
            )
            for record in manifest["files"]:
                path = output / record["path"]
                self.assertEqual(record["bytes"], path.stat().st_size)
                self.assertEqual(record["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(record["classification"], "synthetic-public")
            report = json.loads((output / "manual-report.json").read_text(encoding="utf-8"))
            self.assertEqual("a" * 40, report["acceptance_kit"]["repository_commit"])
            self.assertEqual(
                hashlib.sha256((output / "kit-manifest.json").read_bytes()).hexdigest(),
                report["acceptance_kit"]["manifest_sha256"],
            )

    def test_manifest_is_reproducible_for_same_commit(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            create_kit(root / "one", repository_commit="b" * 40)
            create_kit(root / "two", repository_commit="b" * 40)
            one = (root / "one" / "kit-manifest.json").read_bytes()
            two = (root / "two" / "kit-manifest.json").read_bytes()
        self.assertEqual(one, two)

    def test_nonempty_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            output = Path(directory) / "kit"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not empty"):
                create_kit(output, repository_commit="c" * 40)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_manifest_on_disk_matches_returned_data(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            output = Path(directory) / "kit"
            expected = create_kit(output, repository_commit="d" * 40)
            actual = json.loads((output / "kit-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)

    def test_passing_artifact_verification_is_bound_into_report(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            verification = root / "verification.json"
            verification.write_text(json.dumps({
                "status": "passed",
                "hardware_access": False,
                "executed_binaries": False,
                "manual_interaction_required": True,
            }), encoding="utf-8")
            output = root / "kit"
            create_kit(
                output,
                repository_commit="e" * 40,
                artifact_verification=verification,
            )
            copied = output / "artifact-verification.json"
            report = json.loads((output / "manual-report.json").read_text(encoding="utf-8"))
            copied_digest = hashlib.sha256(copied.read_bytes()).hexdigest()
        self.assertEqual("passed", report["artifact_verification"]["status"])
        self.assertEqual(
            copied_digest,
            report["artifact_verification"]["report_sha256"],
        )

    def test_failed_artifact_verification_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            verification = root / "verification.json"
            verification.write_text(json.dumps({
                "status": "failed",
                "hardware_access": False,
                "executed_binaries": False,
                "manual_interaction_required": True,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "did not pass"):
                create_kit(
                    root / "kit",
                    repository_commit="f" * 40,
                    artifact_verification=verification,
                )


if __name__ == "__main__":
    unittest.main()
