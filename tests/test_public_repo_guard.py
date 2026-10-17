import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_public_repo import check


class PublicRepoGuardTests(unittest.TestCase):
    def test_disallowed_binary_suffix_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "vendor.dll"
            candidate.write_bytes(b"MZ")
            with patch("scripts.check_public_repo.tracked_files", return_value=[candidate]):
                self.assertIn("disallowed public artifact: vendor.dll", check(root))

    def test_private_drive_url_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "notes.md"
            candidate.write_text(
                "https://drive" + ".google.com/file/d/private_identifier", encoding="utf-8"
            )
            with patch("scripts.check_public_repo.tracked_files", return_value=[candidate]):
                failures = check(root)
            self.assertEqual(len(failures), 1)
            self.assertIn("Google Drive URL", failures[0])

    def test_safe_text_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "notes.md"
            candidate.write_text("artifact sha256-01234567890123456789", encoding="utf-8")
            with patch("scripts.check_public_repo.tracked_files", return_value=[candidate]):
                self.assertEqual(check(root), [])


if __name__ == "__main__":
    unittest.main()
