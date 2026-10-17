import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.build_manifest import build_manifest


class BuildManifestTests(unittest.TestCase):
    def test_manifest_is_sorted_hashed_and_private_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "nested").mkdir()
            (root / "z.txt").write_text("z", encoding="utf-8")
            (root / "nested" / "a.bin").write_bytes(b"a")

            entries = build_manifest(
                root,
                "private-third-party",
                "test-source",
                "2026-10-17T00:00:00Z",
            )

            self.assertEqual([entry["relative_path"] for entry in entries], ["nested/a.bin", "z.txt"])
            expected = hashlib.sha256(b"a").hexdigest()
            self.assertEqual(entries[0]["sha256"], expected)
            self.assertEqual(entries[0]["artifact_id"], f"sha256-{expected[:20]}")

    def test_public_manifest_omits_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "item.txt").write_text("safe", encoding="utf-8")
            entries = build_manifest(
                root,
                "public",
                "test-source",
                "2026-10-17T00:00:00Z",
                include_private_locators=False,
            )
            self.assertNotIn("relative_path", entries[0])
            self.assertNotIn("source_locator", entries[0])

    def test_invalid_classification_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                build_manifest(
                    Path(temporary), "secret", "test-source", "2026-10-17T00:00:00Z"
                )


if __name__ == "__main__":
    unittest.main()
