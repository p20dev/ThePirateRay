import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicEvidenceTests(unittest.TestCase):
    def test_public_evidence_matches_manifest_contract(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "artifact-manifest.schema.json").read_text(encoding="utf-8")
        )
        required = set(schema["required"])
        allowed = set(schema["properties"])
        artifact_pattern = re.compile(schema["properties"]["artifact_id"]["pattern"])
        digest_pattern = re.compile(schema["properties"]["sha256"]["pattern"])
        classifications = set(schema["properties"]["classification"]["enum"])

        lines = (ROOT / "evidence" / "public-installer-configs.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(len(lines), 9)

        for line in lines:
            entry = json.loads(line)
            self.assertFalse(required - set(entry))
            self.assertFalse(set(entry) - allowed)
            self.assertRegex(entry["artifact_id"], artifact_pattern)
            self.assertRegex(entry["sha256"], digest_pattern)
            self.assertEqual(entry["artifact_id"], f"sha256-{entry['sha256'][:20]}")
            self.assertIn(entry["classification"], classifications)
            self.assertNotIn("relative_path", entry)
            self.assertNotIn("source_locator", entry)

    def test_public_evidence_has_unique_content_ids(self) -> None:
        entries = [
            json.loads(line)
            for line in (ROOT / "evidence" / "public-installer-configs.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        ids = [entry["artifact_id"] for entry in entries]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
