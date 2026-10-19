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
CANCEL_FIXTURE = (
    ROOT / "tests" / "fixtures" / "rayforge-jcz-cancel-recovery.json"
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
                "518000000000000000000000",
                "2680c8000000000000000000",
                "0680a7040000000000000000",
                "1b80f4010000000000000000",
                "128000080000000000000000",
                "0c8094000000000000000000",
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

    def test_controller_list_is_fixed_size_and_safely_ordered(self):
        result = json.loads(EQUIVALENCE_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(3072, result["list_buffer_size"])
        self.assertEqual(256, result["list_record_capacity"])
        self.assertEqual(1, result["list_buffer_count"])
        self.assertEqual(1, len(result["list_buffer_sha256"]))
        self.assertEqual(13, result["list_meaningful_record_count"])
        self.assertEqual(243, result["list_padding_record_count"])
        self.assertEqual(
            [
                "ready",
                "pulse_width",
                "jump_speed",
                "frequency",
                "power",
                "mark_speed",
                "jump",
                "mark",
                "mark",
                "mark",
                "mark",
                "laser_on_point",
                "job_end",
            ],
            result["controller_list_commands"],
        )

    def test_negative_cases_all_fail_closed_without_transport(self):
        result = json.loads(NEGATIVE_FIXTURE.read_text(encoding="utf-8"))
        self.assertTrue(result["all_failed_closed"])
        self.assertIsNone(result["transport"])
        self.assertEqual(8, len(result["cases"]))
        self.assertEqual(
            {"rejected"}, {case["result"] for case in result["cases"]}
        )

    def test_cancel_requires_recovery_and_clears_all_buffers(self):
        result = json.loads(CANCEL_FIXTURE.read_text(encoding="utf-8"))
        self.assertIsNone(result["transport"])
        self.assertEqual([], result["hardware_commands"])
        self.assertEqual(2, result["long_job_buffer_count"])
        self.assertEqual(6144, result["buffered_bytes_before_cancel"])
        self.assertEqual(0, result["buffered_bytes_after_cancel"])
        self.assertEqual("hold", result["held_state"])
        self.assertEqual("running", result["resumed_state"])
        self.assertEqual("cancelled", result["cancelled_state"])
        self.assertTrue(result["restart_without_recovery_rejected"])
        self.assertEqual("idle", result["recovered_state"])
        self.assertEqual("complete", result["second_job_state"])


if __name__ == "__main__":
    unittest.main()
