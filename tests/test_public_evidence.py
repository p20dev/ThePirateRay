import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicEvidenceTests(unittest.TestCase):
    def _manifest_paths(self) -> list[Path]:
        return sorted((ROOT / "evidence").glob("public-*.jsonl"))

    def _entries(self) -> list[dict]:
        return [
            json.loads(line)
            for path in self._manifest_paths()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def test_public_evidence_matches_manifest_contract(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "artifact-manifest.schema.json").read_text(encoding="utf-8")
        )
        required = set(schema["required"])
        allowed = set(schema["properties"])
        artifact_pattern = re.compile(schema["properties"]["artifact_id"]["pattern"])
        digest_pattern = re.compile(schema["properties"]["sha256"]["pattern"])
        classifications = set(schema["properties"]["classification"]["enum"])

        paths = self._manifest_paths()
        self.assertGreaterEqual(len(paths), 2)

        for entry in self._entries():
            self.assertFalse(required - set(entry))
            self.assertFalse(set(entry) - allowed)
            self.assertRegex(entry["artifact_id"], artifact_pattern)
            self.assertRegex(entry["sha256"], digest_pattern)
            self.assertEqual(entry["artifact_id"], f"sha256-{entry['sha256'][:20]}")
            self.assertIn(entry["classification"], classifications)
            self.assertNotIn("relative_path", entry)
            self.assertNotIn("source_locator", entry)

    def test_public_evidence_has_unique_content_ids(self) -> None:
        entries = self._entries()
        ids = [entry["artifact_id"] for entry in entries]
        self.assertEqual(len(ids), len(set(ids)))

    def test_expected_manifest_entry_counts(self) -> None:
        expected = {
            "public-installer-configs.jsonl": 9,
            "public-lightburn-control-machine-observation.jsonl": 7,
            "public-lightburn-exports.jsonl": 4,
            "public-lightburn-local-settings.jsonl": 1,
            "public-lightburn-verified-projects.jsonl": 3,
        }
        actual = {
            path.name: len(path.read_text(encoding="utf-8").splitlines())
            for path in self._manifest_paths()
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
