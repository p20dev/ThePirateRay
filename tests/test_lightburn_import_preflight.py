import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parents[1]
ADDON = ROOT / "spikes" / "rayforge-jcz-no-device-addon"
sys.path.insert(0, str(ADDON))
from pirate_ray_jcz.import_preflight import (
    ImportPreflightError, assert_no_unresolved_imports, inspect_imported_workflow,
)
from pirate_ray_jcz.preflight_presentation import format_preflight_report
from pirate_ray_jcz.workflow_import import METADATA_KEY


def document(*steps):
    return SimpleNamespace(children=[SimpleNamespace(children=list(steps))])


def imported_step(*, visible=False, record=None):
    if record is None:
        record = {
            "status": "staged-review-required",
            "source_layer_id": "3",
            "blockers": ["machine identity unverified", "unit contract unresolved"],
            "encoding_allowed": False,
            "hardware_use_allowed": False,
        }
    return SimpleNamespace(name="Imported contour", visible=visible,
                           extra={METADATA_KEY: record}, children=[])


class ImportPreflightTests(unittest.TestCase):
    def test_plain_document_is_ready(self):
        report = inspect_imported_workflow(document(
            SimpleNamespace(name="ordinary", visible=True, extra={}, children=[])))
        self.assertEqual(report, {"ready": True, "issues": []})
        assert_no_unresolved_imports(document())

    def test_staged_import_is_presented_and_execution_is_rejected(self):
        doc = document(imported_step())
        report = inspect_imported_workflow(doc)
        self.assertFalse(report["ready"])
        self.assertEqual(["IMPORT_REVIEW_REQUIRED"],
                         [issue["code"] for issue in report["issues"]])
        self.assertIn("unit contract unresolved", report["issues"][0]["message"])
        with self.assertRaisesRegex(ImportPreflightError, "IMPORT_REVIEW_REQUIRED"):
            assert_no_unresolved_imports(doc)

    def test_manual_reenable_adds_a_distinct_error(self):
        report = inspect_imported_workflow(document(imported_step(visible=True)))
        self.assertEqual(
            ["IMPORT_OUTPUT_REENABLED", "IMPORT_REVIEW_REQUIRED"],
            [issue["code"] for issue in report["issues"]],
        )

    def test_malformed_metadata_and_document_fail_closed(self):
        for doc in (
            object(),
            document(imported_step(record="bad")),
            document(imported_step(record={"source_layer_id": "3", "blockers": []})),
        ):
            with self.subTest(doc=doc):
                report = inspect_imported_workflow(doc)
                self.assertFalse(report["ready"])
                self.assertTrue(any("INVALID" in issue["code"] for issue in report["issues"]))

    def test_offline_driver_runs_preflight_before_session_prepare(self):
        source = (ADDON / "pirate_ray_jcz" / "worker.py").read_text(encoding="utf-8")
        preflight = source.index("assert_no_unresolved_imports(doc)")
        prepare = source.index("self.offline_session.prepare(encoded)")
        self.assertLess(preflight, prepare)

    def test_packaged_presentation_lists_stable_blocker_codes(self):
        presentation = format_preflight_report(
            inspect_imported_workflow(document(imported_step()))
        )
        self.assertEqual("blocked", presentation["status"])
        self.assertEqual("Import preflight blocked", presentation["heading"])
        self.assertIn("IMPORT_REVIEW_REQUIRED", presentation["body"])
        self.assertIn("Output remains disabled", presentation["body"])

    def test_packaged_presentation_fails_closed_on_malformed_report(self):
        for report in (None, {}, {"ready": True, "issues": [{}]}):
            with self.subTest(report=report):
                presentation = format_preflight_report(report)
                self.assertEqual("blocked", presentation["status"])
                self.assertIn("malformed", presentation["body"])

    def test_frontend_registers_read_only_tools_action(self):
        source = (ADDON / "pirate_ray_jcz" / "frontend.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('ACTION_NAME = "pirateray-import-preflight"', source)
        self.assertIn('menu_id="tools"', source)
        self.assertIn("inspect_imported_workflow(action_manager.doc)", source)
        self.assertNotIn("machine_cmd", source)


if __name__ == "__main__":
    unittest.main()
