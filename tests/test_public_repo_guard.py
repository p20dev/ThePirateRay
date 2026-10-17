import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_public_repo import check, load_deny_patterns


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

    def test_private_deny_list_is_applied_without_echoing_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "notes.md"
            candidate.write_text("machine-sensitive-value", encoding="utf-8")
            with patch("scripts.check_public_repo.tracked_files", return_value=[candidate]):
                failures = check(root, ("sensitive-value",))
            self.assertEqual(failures, ["private deny-list token found in notes.md"])

    def test_deny_list_ignores_comments_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "deny.txt"
            path.write_text("# private values\n\n first-token \nsecond-token\n", encoding="utf-8")
            self.assertEqual(load_deny_patterns(path), ("first-token", "second-token"))


if __name__ == "__main__":
    unittest.main()
