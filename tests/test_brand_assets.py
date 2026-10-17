import hashlib
import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANDING = ROOT / "assets" / "branding"
GENERATED = BRANDING / "generated"
EXPECTED_SOURCE_SHA256 = "afcd7e457b5bf9cf92a7222b3ab8a2850d75c05bc2c37d242c959cd7569e6fa4"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dimensions(path):
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


class BrandAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GENERATED / "manifest.json").read_text(encoding="utf-8"))

    def test_canonical_logo_is_unchanged(self):
        self.assertEqual(sha256(BRANDING / "the-pirate-ray-logo.png"), EXPECTED_SOURCE_SHA256)
        self.assertEqual(self.manifest["sourceSha256"], EXPECTED_SOURCE_SHA256)

    def test_manifest_matches_every_generated_file(self):
        records = {record["path"]: record for record in self.manifest["files"]}
        actual = {
            path.relative_to(GENERATED).as_posix(): path
            for path in GENERATED.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        }
        self.assertEqual(set(records), set(actual))
        for relative, path in actual.items():
            with self.subTest(path=relative):
                self.assertEqual(records[relative]["sha256"], sha256(path))
                self.assertEqual(records[relative]["bytes"], path.stat().st_size)
                if path.suffix == ".png":
                    self.assertEqual(
                        png_dimensions(path),
                        (records[relative]["width"], records[relative]["height"]),
                    )

    def test_copy_ready_platform_assets_exist(self):
        required = (
            "web/favicon.ico",
            "web/site.webmanifest",
            "web/maskable-icon-512.png",
            "windows/app.ico",
            "macos/AppIcon.icns",
            "ios/AppIcon.appiconset/Contents.json",
            "android/mipmap-anydpi-v26/ic_launcher.xml",
            "linux/hicolor/512x512/apps/the-pirate-ray.png",
            "social/open-graph-1200x630.png",
        )
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((GENERATED / relative).is_file())

    def test_manifest_json_files_are_valid(self):
        json.loads((GENERATED / "web" / "site.webmanifest").read_text(encoding="utf-8"))
        json.loads(
            (GENERATED / "ios" / "AppIcon.appiconset" / "Contents.json").read_text(encoding="utf-8")
        )

    def test_branding_readme_catalogs_every_image(self):
        readme = (BRANDING / "README.md").read_text(encoding="utf-8")
        image_suffixes = {".png", ".ico", ".icns"}
        for record in self.manifest["files"]:
            relative = record["path"]
            if Path(relative).suffix.lower() in image_suffixes:
                with self.subTest(path=relative):
                    self.assertIn(f"generated/{relative}", readme)


if __name__ == "__main__":
    unittest.main()
