import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "spikes/rayforge-jcz-no-device-addon"))
from pirate_ray_jcz.project_import import (
    ProjectImportError, UNIT_CONTRACT, UNIT_CONTRACT_EVIDENCE,
    import_project_mopa,
)


def project(fields, tag="CutSetting", kind="Scan", layer_id="0"):
    return (f'<LightBurnProject AppVersion="2.1.03" FormatVersion="1">'
            f'<{tag} type="{kind}">'
            f'<index Value="{layer_id}"/>{fields}</{tag}></LightBurnProject>').encode()


FIELDS = '<frequency Value="125000"/><QPulseWidth Value="25"/>'


class ProjectMopaTests(unittest.TestCase):
    def test_explicit_contract_converts_without_authorizing_execution(self):
        result = import_project_mopa(project(FIELDS), unit_contract=UNIT_CONTRACT)
        self.assertEqual(result["layers"][0]["normalized"], {
            "frequency_hz": 125000, "frequency_khz": 125, "pulse_width_ns": 25,
        })
        self.assertEqual(result["unit_contract_evidence"], UNIT_CONTRACT_EVIDENCE)
        self.assertEqual(result["lightburn_app_version"], "2.1.03")
        self.assertFalse(result["encoding_allowed"])
        self.assertFalse(result["hardware_use_allowed"])
        self.assertIsNone(result["transport"])
        self.assertEqual(result["layers"][0]["source_layer_id"], "0")

    def test_units_are_never_inferred_from_magnitude(self):
        result = import_project_mopa(project(FIELDS))
        layer = result["layers"][0]
        self.assertIsNone(layer["normalized"])
        self.assertEqual(layer["raw"]["frequency"], "125000")
        self.assertIn("serialized units unresolved", layer["blockers"])
        with self.assertRaises(ProjectImportError):
            import_project_mopa(project(FIELDS), unit_contract="kHz/us")

    def test_contract_is_version_bound_and_matches_verified_ui_correlation(self):
        verified = '<frequency Value="1000000"/><QPulseWidth Value="10"/>'
        layer = import_project_mopa(
            project(verified), unit_contract=UNIT_CONTRACT
        )["layers"][0]
        self.assertEqual(layer["normalized"], {
            "frequency_hz": 1000000,
            "frequency_khz": 1000,
            "pulse_width_ns": 10,
        })
        for app_version in ("2.0.00", ""):
            data = project(verified).replace(b'AppVersion="2.1.03"',
                                             f'AppVersion="{app_version}"'.encode())
            with self.subTest(app_version=app_version):
                with self.assertRaisesRegex(ProjectImportError, "AppVersion 2.1.03"):
                    import_project_mopa(data, unit_contract=UNIT_CONTRACT)

    def test_missing_fields_remain_absent(self):
        for fields in ('<frequency Value="125000"/>', '<QPulseWidth Value="25"/>', ''):
            with self.subTest(fields=fields):
                layer = import_project_mopa(project(fields), unit_contract=UNIT_CONTRACT)["layers"][0]
                self.assertIsNone(layer["normalized"])
                self.assertTrue(layer["blockers"])

    def test_image_settings_remain_blocked_even_with_complete_parameters(self):
        fields = FIELDS + '<ditherMode Value="3dslice"/>'
        layer = import_project_mopa(project(fields, "CutSetting_Img", "Image"), unit_contract=UNIT_CONTRACT)["layers"][0]
        self.assertIn("image processing equivalence unverified", layer["blockers"])
        self.assertEqual(layer["image_mode"], "3dslice")

    def test_invalid_and_ambiguous_values_fail_closed(self):
        for field in ("frequency", "QPulseWidth"):
            for value in ("0", "-1", "NaN", "Infinity", "1e999", "", "abc"):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ProjectImportError):
                        import_project_mopa(project(f'<{field} Value="{value}"/>'))
            with self.assertRaises(ProjectImportError):
                import_project_mopa(project(FIELDS + f'<{field} Value="2"/>'))

    def test_wrong_case_is_absent_not_guessed(self):
        layer = import_project_mopa(project(FIELDS.replace("QPulseWidth", "qpulsewidth")))["layers"][0]
        self.assertIsNone(layer["raw"]["QPulseWidth"])

    def test_bad_xml_formats_and_declarations_rejected(self):
        for data in (b'<broken', b'<Other/>', b'<LightBurnProject FormatVersion="2"/>',
                     b'<!DOCTYPE x><LightBurnProject FormatVersion="1"/>',
                     project(FIELDS, kind="Unknown")):
            with self.subTest(data=data):
                with self.assertRaises(ProjectImportError):
                    import_project_mopa(data)

    def test_layer_indices_are_normalized_and_must_be_unique(self):
        layer = import_project_mopa(project(FIELDS, layer_id="007"))["layers"][0]
        self.assertEqual(layer["source_layer_id"], "7")
        duplicate = ('<LightBurnProject AppVersion="2.1.03" FormatVersion="1">'
                     '<CutSetting type="Cut"><index Value="1"/>'+FIELDS+'</CutSetting>'
                     '<CutSetting type="Scan"><index Value="1"/>'+FIELDS+'</CutSetting>'
                     '</LightBurnProject>').encode()
        with self.assertRaisesRegex(ProjectImportError, "duplicate layer index"):
            import_project_mopa(duplicate)

    def test_multiple_layers_preserve_order_and_missing_pulse(self):
        data = ('<LightBurnProject AppVersion="2.1.03" FormatVersion="1">'
                '<CutSetting type="Cut"><index Value="0"/>'+FIELDS+'</CutSetting>'
                '<CutSetting_Img type="Image"><index Value="1"/><frequency Value="125000"/>'
                '</CutSetting_Img></LightBurnProject>').encode()
        layers = import_project_mopa(data, unit_contract=UNIT_CONTRACT)["layers"]
        self.assertEqual([x["type"] for x in layers], ["Cut", "Image"])
        self.assertIsNone(layers[1]["normalized"])


if __name__ == "__main__":
    unittest.main()
