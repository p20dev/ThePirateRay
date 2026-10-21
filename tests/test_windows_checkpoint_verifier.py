import hashlib
import json
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from types import SimpleNamespace

from scripts.verify_rayforge_windows_checkpoint import (
    ADDON_SOURCE,
    ROOT,
    UPSTREAM,
    _safe_archive_files,
    verify,
)


ADDON_ROOT = "rayforge/builtin_addons/rayforge-addon-the-pirate-ray-jcz"


class WindowsCheckpointVerifierTests(unittest.TestCase):
    def _checkpoint(
        self,
        root: Path,
        unsafe_member: str | None = None,
        extra_addon_file: str | None = None,
        duplicate_member: bool = False,
        case_collision: bool = False,
        symlink_member: bool = False,
    ) -> Path:
        bundle_name = f"rayforge-vpirateray-{UPSTREAM['commit'][:12]}.zip"
        executable = bundle_name.removesuffix(".zip") + ".exe"
        addon_files = {
            path.relative_to(ADDON_SOURCE).as_posix(): path.read_bytes()
            for path in sorted(ADDON_SOURCE.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
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
            if extra_addon_file:
                archive.writestr(
                    f"{bundle_name[:-4]}/_internal/{ADDON_ROOT}/{extra_addon_file}",
                    b"unexpected",
                )
            archive.writestr(
                f"{bundle_name[:-4]}/THIRD_PARTY_LICENSES/Rayforge-LICENSE.txt",
                license_data,
            )
            if unsafe_member:
                unsafe = zipfile.ZipInfo("placeholder")
                unsafe.filename = unsafe_member
                unsafe.orig_filename = unsafe_member
                archive.writestr(unsafe, b"unsafe")
            if duplicate_member:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr(
                        f"{bundle_name[:-4]}/{executable}", b"duplicate"
                    )
            if case_collision:
                archive.writestr(
                    f"{bundle_name[:-4].upper()}/{executable.upper()}",
                    b"case collision",
                )
            if symlink_member:
                link = zipfile.ZipInfo(f"{bundle_name[:-4]}/link")
                link.create_system = 3
                link.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(link, "target")
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
        self.assertEqual(1, result["schema_version"])
        self.assertEqual("the_pirate_ray_jcz", result["addon"])
        self.assertRegex(result["checkpoint_manifest"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(result["executed_binaries"])
        expected_count = sum(
            path.is_file() and "__pycache__" not in path.parts
            for path in ADDON_SOURCE.rglob("*")
        )
        self.assertEqual(result["verified_addon_files"], expected_count)

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

    def test_windows_unsafe_and_colliding_archive_paths_are_rejected(self):
        unsafe = SimpleNamespace(
            filename="folder\\escape.txt",
            flag_bits=0,
            external_attr=0,
            is_dir=lambda: False,
        )
        archive = SimpleNamespace(infolist=lambda: [unsafe])
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            _safe_archive_files(archive)

        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory), duplicate_member=True)
            with self.assertRaisesRegex(ValueError, "duplicate or case-colliding"):
                verify(manifest)

            manifest = self._checkpoint(Path(directory), case_collision=True)
            with self.assertRaisesRegex(ValueError, "duplicate or case-colliding"):
                verify(manifest)

    def test_symbolic_link_archive_entry_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory), symlink_member=True)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
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

    def test_checkpoint_and_addon_identity_are_required(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["addon"] = "foreign_addon"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unexpected checkpoint addon"):
                verify(manifest)

    def test_manifest_cannot_omit_or_change_repository_addon_source(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(Path(directory))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["addon_source_files"].pop()
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "file list does not match"):
                verify(manifest)

            manifest = self._checkpoint(Path(directory))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["addon_source_files"][0]["sha256"] = "0" * 64
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from repository"):
                verify(manifest)

    def test_unlisted_packaged_addon_file_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            manifest = self._checkpoint(
                Path(directory), extra_addon_file="pirate_ray_jcz/transport.py"
            )
            with self.assertRaisesRegex(ValueError, "file set does not match"):
                verify(manifest)


if __name__ == "__main__":
    unittest.main()
