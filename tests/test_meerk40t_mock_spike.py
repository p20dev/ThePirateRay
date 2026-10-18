import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "spike_meerk40t_mock_mopa.py"
FIXTURE = Path(__file__).parent / "fixtures" / "meerk40t-mock-mopa-trace.json"
SPEC = importlib.util.spec_from_file_location("spike_meerk40t_mock_mopa", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MockSpikeSafetyTests(unittest.TestCase):
    def test_golden_trace_records_pin_mock_and_mopa_values(self):
        result = json.loads(FIXTURE.read_text(encoding="utf-8"))
        trace = "\n".join(result["trace"])
        self.assertEqual(MODULE.PINNED_COMMIT, result["commit"])
        self.assertEqual("MockConnection", result["transport"])
        self.assertEqual("trapped; none attempted", result["usb_access"])
        self.assertIn("801b:01f4", trace)
        self.assertIn("8026:00c8", trace)
        self.assertEqual(4, trace.count("listMarkTo"))

    def test_usb_trap_rejects_enumeration(self):
        with patch.dict(sys.modules, clear=False):
            MODULE._install_usb_trap()
            import usb.core

            with self.assertRaisesRegex(AssertionError, "real USB access"):
                usb.core.find(idVendor=0x9588, idProduct=0x9899)

    def test_rejects_unpinned_checkout(self):
        with patch.object(MODULE, "_commit_of", return_value="wrong"):
            with self.assertRaisesRegex(RuntimeError, "expected MeerK40t"):
                MODULE.run(Path("unused"))


if __name__ == "__main__":
    unittest.main()
