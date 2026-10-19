import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
ADDON = ROOT / "spikes" / "rayforge-jcz-no-device-addon"
FIXTURE = ROOT / "tests" / "fixtures" / "rayforge-addon-spike.json"
EQUIVALENCE_FIXTURE = (
    ROOT / "tests" / "fixtures" / "rayforge-jcz-equivalence.json"
)
NEGATIVE_FIXTURE = (
    ROOT / "tests" / "fixtures" / "rayforge-jcz-negative-cases.json"
)


class RayforgeAddonSpikeTests(unittest.TestCase):
    def test_golden_result_is_hardware_free_binary_driver(self):
        result = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertFalse(result["uses_gcode"])
        self.assertIsNone(result["discovery"])
        self.assertIsNone(result["transport"])
        self.assertEqual(
            ["load", "disable", "enable", "reload", "disable"],
            result["lifecycle"],
        )
        self.assertEqual(23, result["rayforge_api_version"])

    def test_addon_contains_no_hardware_transport_import(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ADDON / "pirate_ray_jcz").glob("*.py"))
        )
        compact = source.lower()
        for forbidden in ("import usb", "import serial", "import socket"):
            self.assertNotIn(forbidden, compact)
        self.assertIn("discovery = none", compact)
        self.assertIn("uses_gcode = false", compact)

    def test_manifest_and_golden_package_agree(self):
        result = json.loads(FIXTURE.read_text(encoding="utf-8"))
        actual = sorted(
            path.relative_to(ADDON).as_posix()
            for path in ADDON.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
        self.assertEqual(result["packaged_files"], actual)

    def test_semantic_equivalence_fixture_has_no_failed_mapping(self):
        result = json.loads(EQUIVALENCE_FIXTURE.read_text(encoding="utf-8"))
        self.assertIsNone(result["transport"])
        self.assertEqual(13, result["rayforge_ops_count"])
        self.assertTrue(all(result["balormk_equivalence"].values()))
        commands = [item["command"] for item in result["semantic_trace"]]
        self.assertEqual(4, commands.count("mark"))
        self.assertIn("pulse_width", commands)
        self.assertIn("laser_on_point", commands)

    def test_packet_records_match_pinned_balor_values(self):
        result = json.loads(EQUIVALENCE_FIXTURE.read_text(encoding="utf-8"))
        records = result["command_records_hex"]
        self.assertTrue(all(len(record) == 24 for record in records))
        self.assertEqual(
            [
                "128000080000000000000000",
                "0c8094000000000000000000",
                "0680a7040000000000000000",
                "1b80f4010000000000000000",
                "2680c8000000000000000000",
                "0180007000700000a0160000",
                "058000710070000000010000",
                "058000710071000000010000",
                "058000700071000000010000",
                "058000700070000000010000",
                "038064000000000000000000",
                "028000000000000000000000",
            ],
            records,
        )

    def test_negative_cases_all_fail_closed_without_transport(self):
        result = json.loads(NEGATIVE_FIXTURE.read_text(encoding="utf-8"))
        self.assertTrue(result["all_failed_closed"])
        self.assertIsNone(result["transport"])
        self.assertEqual(6, len(result["cases"]))
        self.assertEqual(
            {"rejected"}, {case["result"] for case in result["cases"]}
        )


if __name__ == "__main__":
    unittest.main()
