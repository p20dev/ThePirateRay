import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
COMPAT_PATH = (
    ROOT
    / "spikes"
    / "rayforge-jcz-no-device-addon"
    / "pirate_ray_jcz"
    / "rayforge_compat.py"
)
SPEC = importlib.util.spec_from_file_location("rayforge_compat_test", COMPAT_PATH)
COMPAT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPAT)


class FakeRegistry:
    def __init__(self):
        self.drivers = []
        self.driver_by_classname = {}

    def register_driver(self, driver_cls):
        self.drivers.append(driver_cls)
        self.driver_by_classname[driver_cls.__name__] = driver_cls


class ExampleDriver:
    pass


class RayforgeCompatibilityTests(unittest.TestCase):
    def test_registration_and_cleanup_are_symmetric_and_idempotent(self):
        registry = FakeRegistry()

        self.assertTrue(
            COMPAT.register_driver(
                ExampleDriver, registry=registry, plugin_api_version=23
            )
        )
        self.assertFalse(
            COMPAT.register_driver(
                ExampleDriver, registry=registry, plugin_api_version=23
            )
        )
        self.assertEqual([ExampleDriver], registry.drivers)
        self.assertIs(
            ExampleDriver, registry.driver_by_classname["ExampleDriver"]
        )

        self.assertTrue(
            COMPAT.unregister_driver(
                ExampleDriver, registry=registry, plugin_api_version=23
            )
        )
        self.assertFalse(
            COMPAT.unregister_driver(
                ExampleDriver, registry=registry, plugin_api_version=23
            )
        )
        self.assertEqual([], registry.drivers)
        self.assertEqual({}, registry.driver_by_classname)

    def test_api_version_drift_fails_before_mutation(self):
        registry = FakeRegistry()

        with self.assertRaisesRegex(
            COMPAT.RayforgeCompatibilityError,
            "expected 23, got 24",
        ):
            COMPAT.register_driver(
                ExampleDriver, registry=registry, plugin_api_version=24
            )

        self.assertEqual([], registry.drivers)
        self.assertEqual({}, registry.driver_by_classname)

    def test_name_collision_is_never_replaced_or_removed(self):
        foreign_driver = type("ExampleDriver", (), {})
        registry = FakeRegistry()
        registry.register_driver(foreign_driver)

        with self.assertRaisesRegex(
            COMPAT.RayforgeCompatibilityError, "name collision"
        ):
            COMPAT.register_driver(
                ExampleDriver, registry=registry, plugin_api_version=23
            )
        with self.assertRaisesRegex(
            COMPAT.RayforgeCompatibilityError, "foreign"
        ):
            COMPAT.unregister_driver(
                ExampleDriver, registry=registry, plugin_api_version=23
            )

        self.assertEqual([foreign_driver], registry.drivers)
        self.assertIs(
            foreign_driver, registry.driver_by_classname["ExampleDriver"]
        )

    def test_incomplete_registry_contract_fails_closed(self):
        class MissingRegister:
            drivers = []
            driver_by_classname = {}

        with self.assertRaisesRegex(
            COMPAT.RayforgeCompatibilityError, "register_driver"
        ):
            COMPAT.register_driver(
                ExampleDriver,
                registry=MissingRegister(),
                plugin_api_version=23,
            )

    def test_adapter_has_no_transport_imports(self):
        source = COMPAT_PATH.read_text(encoding="utf-8").lower()
        for forbidden in ("import usb", "import serial", "import socket"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
