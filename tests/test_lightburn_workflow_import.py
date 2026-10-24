import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "spikes/rayforge-jcz-no-device-addon"))
from pirate_ray_jcz.project_import import UNIT_CONTRACT, import_project_mopa
from pirate_ray_jcz.workflow_import import (
    METADATA_KEY, WorkflowImportError, stage_mopa_workflow_steps,
)


class Step:
    def __init__(self, fail=False):
        self.visible = True
        self.frequency = 1
        self.pulse_width = 2
        self.extra = {"preserved": True}
        self.fail = fail

    def set_frequency(self, value):
        self.frequency = value

    def set_visible(self, value):
        self.visible = value

    def set_pulse_width(self, value):
        if self.fail:
            raise ValueError("synthetic setter failure")
        self.pulse_width = value


def imported(fields, layer_id="3", kind="Cut", tag="CutSetting"):
    data = (f'<LightBurnProject FormatVersion="1"><{tag} type="{kind}">'
            f'<index Value="{layer_id}"/>{fields}</{tag}></LightBurnProject>').encode()
    return import_project_mopa(data, unit_contract=UNIT_CONTRACT)


FIELDS = '<frequency Value="125000"/><QPulseWidth Value="25"/>'


class WorkflowImportTests(unittest.TestCase):
    def test_complete_vector_settings_are_staged_but_output_is_disabled(self):
        step = Step()
        result = stage_mopa_workflow_steps(imported(FIELDS), {"3": step})
        self.assertEqual((step.frequency, step.pulse_width), (125000, 25))
        self.assertFalse(step.visible)
        self.assertFalse(result["encoding_allowed"])
        self.assertIsNone(result["transport"])
        gate = step.extra[METADATA_KEY]
        self.assertEqual(gate["status"], "staged-review-required")
        self.assertFalse(gate["encoding_allowed"])
        self.assertTrue(gate["blockers"])

    def test_missing_pulse_and_image_mode_do_not_apply_parameters(self):
        for result in (
            imported('<frequency Value="125000"/>'),
            imported(FIELDS + '<ditherMode Value="3dslice"/>', kind="Image", tag="CutSetting_Img"),
        ):
            with self.subTest(result=result):
                step = Step()
                staged = stage_mopa_workflow_steps(result, {"3": step})
                self.assertEqual((step.frequency, step.pulse_width), (1, 2))
                self.assertFalse(step.visible)
                self.assertFalse(staged["steps"][0]["parameters_applied"])

    def test_layer_identity_must_match(self):
        with self.assertRaisesRegex(WorkflowImportError, "no imported settings"):
            stage_mopa_workflow_steps(imported(FIELDS), {"4": Step()})

    def test_existing_metadata_and_reused_step_are_rejected(self):
        step = Step()
        step.extra[METADATA_KEY] = {"status": "existing"}
        with self.assertRaisesRegex(WorkflowImportError, "already has"):
            stage_mopa_workflow_steps(imported(FIELDS), {"3": step})

        two_layers = import_project_mopa(
            ('<LightBurnProject FormatVersion="1">'
             '<CutSetting type="Cut"><index Value="1"/>'+FIELDS+'</CutSetting>'
             '<CutSetting type="Cut"><index Value="2"/>'+FIELDS+'</CutSetting>'
             '</LightBurnProject>').encode(), unit_contract=UNIT_CONTRACT)
        reused = Step()
        with self.assertRaisesRegex(WorkflowImportError, "multiple layers"):
            stage_mopa_workflow_steps(two_layers, {"1": reused, "2": reused})

    def test_preflight_failure_does_not_mutate_any_step(self):
        result = import_project_mopa(
            ('<LightBurnProject FormatVersion="1">'
             '<CutSetting type="Cut"><index Value="1"/>'+FIELDS+'</CutSetting>'
             '<CutSetting type="Cut"><index Value="2"/>'+FIELDS+'</CutSetting>'
             '</LightBurnProject>').encode(), unit_contract=UNIT_CONTRACT)
        first = Step()
        with self.assertRaisesRegex(WorkflowImportError, "no serializable extra"):
            stage_mopa_workflow_steps(result, {"1": first, "2": object()})
        self.assertTrue(first.visible)
        self.assertEqual((first.frequency, first.pulse_width), (1, 2))

    def test_setter_failure_rolls_back_every_step(self):
        result = import_project_mopa(
            ('<LightBurnProject FormatVersion="1">'
             '<CutSetting type="Cut"><index Value="1"/>'+FIELDS+'</CutSetting>'
             '<CutSetting type="Cut"><index Value="2"/>'+FIELDS+'</CutSetting>'
             '</LightBurnProject>').encode(), unit_contract=UNIT_CONTRACT)
        first, second = Step(), Step(fail=True)
        with self.assertRaisesRegex(ValueError, "synthetic setter failure"):
            stage_mopa_workflow_steps(result, {"1": first, "2": second})
        for step in (first, second):
            self.assertTrue(step.visible)
            self.assertEqual((step.frequency, step.pulse_width), (1, 2))
            self.assertEqual(step.extra, {"preserved": True})


if __name__ == "__main__":
    unittest.main()
