import json
import unittest
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).parents[1]
ADDON = ROOT / "spikes" / "rayforge-jcz-no-device-addon"
FIXTURE = (
    ROOT / "tests" / "fixtures" / "synthetic-pirateray-recipe-metadata.json"
)
sys.path.insert(0, str(ADDON))

from pirate_ray_jcz.recipe_metadata import (  # noqa: E402
    COMPATIBILITY_KEYS,
    RecipeMetadataError,
    validate_rayforge_recipe,
    validate_recipe_metadata,
)


class RayforgeRecipeMetadataTests(unittest.TestCase):
    def setUp(self):
        self.metadata = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.context = dict(self.metadata["compatibility"])

    def test_complete_synthetic_metadata_is_preserved_but_not_authorized(self):
        result = validate_recipe_metadata(self.metadata, self.context)
        self.assertEqual(1, result["schema_version"])
        self.assertEqual("unverified", result["status"])
        self.assertFalse(result["encoding_allowed"])
        self.assertFalse(result["hardware_use_allowed"])
        self.assertEqual(self.context, result["compatibility"])

    def test_every_compatibility_axis_fails_closed_on_mismatch(self):
        for key in COMPATIBILITY_KEYS:
            with self.subTest(key=key):
                context = dict(self.context)
                context[key] = f"wrong-{key}"
                with self.assertRaisesRegex(
                    RecipeMetadataError, f"recipe {key} does not match"
                ):
                    validate_recipe_metadata(self.metadata, context)

    def test_missing_evidence_and_context_fail_closed(self):
        cases = []
        missing_provenance = deepcopy(self.metadata)
        del missing_provenance["provenance"]
        cases.append((missing_provenance, self.context))
        missing_compatibility = deepcopy(self.metadata)
        del missing_compatibility["compatibility"]["lens_profile_id"]
        cases.append((missing_compatibility, self.context))
        missing_context = dict(self.context)
        del missing_context["correction_profile_sha256"]
        cases.append((self.metadata, missing_context))

        for metadata, context in cases:
            with self.subTest(metadata=metadata, context=context):
                with self.assertRaises(RecipeMetadataError):
                    validate_recipe_metadata(metadata, context)

    def test_unreviewed_approval_label_is_rejected(self):
        metadata = deepcopy(self.metadata)
        metadata["status"] = "makerspace-approved"
        with self.assertRaisesRegex(RecipeMetadataError, "approval policy"):
            validate_recipe_metadata(metadata, self.context)

    def test_rayforge_extra_is_the_only_accepted_seam(self):
        recipe = SimpleNamespace(extra={"pirateray": self.metadata})
        result = validate_rayforge_recipe(recipe, self.context)
        self.assertEqual("synthetic-public", result["provenance"]["kind"])

        with self.assertRaises(RecipeMetadataError):
            validate_rayforge_recipe(SimpleNamespace(extra={}), self.context)

    def test_module_has_no_hardware_transport(self):
        source = (
            ADDON / "pirate_ray_jcz" / "recipe_metadata.py"
        ).read_text(encoding="utf-8").lower()
        for forbidden in (
            "import usb",
            "import serial",
            "import socket",
            "pyusb",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
