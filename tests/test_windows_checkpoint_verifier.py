import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.verify_rayforge_windows_checkpoint import ROOT, UPSTREAM, verify


ADDON_ROOT = "rayforge/builtin_addons/rayforge-addon-the-pirate-ray-jcz"


class WindowsCheckpointVerifierTests(unittest.TestCase):
    def _checkpoint(self, root: Path, unsafe_member: str | None = None) -> Path:
        bundle_name = f"rayforge-vpirateray-{UPSTREAM['commit'][:12]}.zip"
        executable = bundle_name.removesuffix(".zip") + ".exe"
        addon_files = {
            "rayforge-addon.yaml": b"name: the_pirate_ray_jcz\n",
            "pirate_ray_jcz/worker.py": b"TRANSPORT = None\n",
        }
        upstream = json.loads(
            (ROOT / "upstreams" / "rayforge.json").read_text(encoding="utf-8")
        )
        license_data = (ROOT / "third_party" / "licenses" / "Rayforge-LICENSE.txt").read_bytes()
        self.assertEqual(hashlib.sha256(license_data).hexdigest(), upstream["license_file"]["sha256_lf"])
        bundle = root / bundle_name
        with zipfile.ZipFile(bundle, "w") as archive:
            archive.writestr(f"{bundle_name[:-4]}/{executable}", b"synthetic")
            for relative, data in addon_files.items():
                archive.writestr(f"{bundle_name[:-4]}/_internal/{ADDON_ROOT}/{relative}", data)
            archive.writestr(
                f"{bundle_name[:-4]}/THIRD_PARTY_LICENSES/Rayforge-LICENSE.txt",
                license_data,
            )
            if unsafe_member:
                archive.writestr(unsafe_member, b"unsafe")
        installer = root / f"{bundle_name[:-4]}-installer.exe"
        installer.write_bytes(b"synthetic installer, never executed")
        license_sidecar = root / "Rayforge-LICENSE.txt"
        license_sidecar.write_bytes(license_data)
        manifest = {
            "schema_version": 2,
            "checkpoint": "Rayforge Windows no-device bundle",
            "rayforge_commit": UPSTREAM["commit"],
            "addon": "the_pirate_ray_jcz",
            "addon_packaged_root": ADDON_ROOT,
            "addon_source_files": [
                {"path": name, "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in addon_files.items()
            ],
            "hardware_access": False,
            "transport": None,
            "bundle": {
                "path": bundle.name,
                "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
                "bytes": bundle.stat().st_size,
            },
            "installer": {
                "path": installer.name,
                "sha256": hashlib.sha256(installer.read_bytes()).hexdigest(),
                "bytes": installer.stat().st_size,
            },
            "license_files": [{
                "upstream": "Rayforge",
                "path": license_sidecar.name,
                "bundle_path": "THIRD_PARTY_LICENSES/Rayforge-LICENSE.txt",
                "sha256": hashlib.sha256(license_data).hexdigest(),
                "bytes": len(license_data),
            }],
            "manual_interaction_required": True,
        }
        path = root / "rayforge-windows-checkpoint.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_valid_checkpoint_is_verified_without_execution(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            result = verify(self._checkpoint(Path(directory)))
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["executed_binaries"])
        self.assertEqual(result["verified_addon_files"], 2)

    def test_modified_installer_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            (manifest.parent / data["installer"]["path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "installer (size|SHA-256) mismatch"):
                verify(manifest)

    def test_bundle_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory), "../escape.txt")
            with self.assertRaisesRegex(ValueError, "unsafe path"):
                verify(manifest)

    def test_manifest_cannot_reference_external_artifacts(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["bundle"]["path"] = "../outside.zip"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "one filename"):
                verify(manifest)

    def test_missing_license_sidecar_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            (manifest.parent / data["license_files"][0]["path"]).unlink()
            with self.assertRaises(FileNotFoundError):
                verify(manifest)


if __name__ == "__main__":
    unittest.main()
