import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_upstream_contracts import ROOT, inspect_tree


class UpstreamContractTests(unittest.TestCase):
    def _tree(self, root: Path) -> tuple[dict, str]:
        license_path = root / "LICENSE"
        api_path = root / "package" / "api.py"
        api_path.parent.mkdir(parents=True)
        license_path.write_text("synthetic MIT text\n", encoding="utf-8")
        api_path.write_text(
            "VERSION = 3\nclass Registry:\n    def unregister(self):\n        pass\n",
            encoding="utf-8",
        )
        commit = "a" * 40
        manifest = {
            "name": "Synthetic upstream",
            "repository": "https://example.invalid/upstream.git",
            "commit": commit,
            "license": "MIT",
            "license_file": {
                "path": "LICENSE",
                "sha256_lf": hashlib.sha256(b"synthetic MIT text\n").hexdigest(),
            },
            "contract_files": [{
                "path": "package/api.py",
                "sha256": hashlib.sha256(api_path.read_bytes()).hexdigest(),
                "stability": "documented-api",
                "required_symbols": ["VERSION", "Registry", "Registry.unregister"],
            }],
        }
        return manifest, commit

    def test_matching_tree_passes(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            manifest, commit = self._tree(root)
            result = inspect_tree(manifest, root, commit)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["failures"], [])

    def test_commit_hash_and_symbol_drift_fail(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            manifest, _ = self._tree(root)
            changed = copy.deepcopy(manifest)
            changed["contract_files"][0]["required_symbols"].append("Registry.missing")
            result = inspect_tree(changed, root, "b" * 40)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("commit mismatch" in item for item in result["failures"]))
        self.assertTrue(any("Registry.missing" in item for item in result["failures"]))

    def test_license_drift_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            manifest, commit = self._tree(root)
            (root / "LICENSE").write_text("changed\n", encoding="utf-8")
            result = inspect_tree(manifest, root, commit)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("license hash mismatch" in item for item in result["failures"]))

    def test_real_manifests_pin_mit_license_and_stability(self):
        for name in ("rayforge", "meerk40t"):
            manifest = json.loads(
                (ROOT / "upstreams" / f"{name}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["license"], "MIT")
            self.assertEqual(len(manifest["commit"]), 40)
            self.assertEqual(len(manifest["license_file"]["sha256_lf"]), 64)
            self.assertTrue(manifest["contract_files"])
            self.assertTrue(all(item["stability"] for item in manifest["contract_files"]))
            notice = ROOT / "third_party" / "licenses" / f"{manifest['name']}-LICENSE.txt"
            normalized = notice.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
            self.assertEqual(
                hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                manifest["license_file"]["sha256_lf"],
            )


if __name__ == "__main__":
    unittest.main()
