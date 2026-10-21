"""Fail-closed compatibility boundary for Rayforge's driver registry.

Rayforge API 23 does not expose addon-aware driver registration and cleanup.
Keep the unavoidable internal registry access here so it can be removed when
the host provides a supported symmetric API.
"""

from typing import Any


SUPPORTED_PLUGIN_API_VERSION = 23


class RayforgeCompatibilityError(RuntimeError):
    """The pinned Rayforge registry contract is unavailable or has drifted."""


def _resolve_host() -> tuple[Any, int]:
    from rayforge.core.hooks import PLUGIN_API_VERSION
    from rayforge.machine import driver as registry

    return registry, PLUGIN_API_VERSION


def _validate_host(registry: Any, plugin_api_version: int) -> None:
    if plugin_api_version != SUPPORTED_PLUGIN_API_VERSION:
        raise RayforgeCompatibilityError(
            "unsupported Rayforge addon API: "
            f"expected {SUPPORTED_PLUGIN_API_VERSION}, got {plugin_api_version}"
        )
    if not isinstance(getattr(registry, "driver_by_classname", None), dict):
        raise RayforgeCompatibilityError(
            "Rayforge driver_by_classname registry is unavailable"
        )
    if not isinstance(getattr(registry, "drivers", None), list):
        raise RayforgeCompatibilityError("Rayforge drivers registry is unavailable")
    if not callable(getattr(registry, "register_driver", None)):
        raise RayforgeCompatibilityError("Rayforge register_driver is unavailable")


def _host(
    registry: Any | None, plugin_api_version: int | None
) -> tuple[Any, int]:
    if registry is None or plugin_api_version is None:
        resolved_registry, resolved_version = _resolve_host()
        registry = resolved_registry if registry is None else registry
        plugin_api_version = (
            resolved_version
            if plugin_api_version is None
            else plugin_api_version
        )
    _validate_host(registry, plugin_api_version)
    return registry, plugin_api_version


def register_driver(
    driver_cls: type,
    *,
    registry: Any | None = None,
    plugin_api_version: int | None = None,
) -> bool:
    """Register exactly one driver class, or fail before replacing anything."""

    registry, _version = _host(registry, plugin_api_version)
    name = driver_cls.__name__
    registered = registry.driver_by_classname.get(name)
    named_entries = [item for item in registry.drivers if item.__name__ == name]

    if registered is driver_cls:
        if named_entries == [driver_cls]:
            return False
        raise RayforgeCompatibilityError(
            f"inconsistent Rayforge driver registry for {name}"
        )
    if registered is not None or named_entries:
        raise RayforgeCompatibilityError(
            f"Rayforge driver name collision for {name}"
        )

    registry.register_driver(driver_cls)
    if registry.driver_by_classname.get(name) is not driver_cls:
        raise RayforgeCompatibilityError(
            f"Rayforge did not index registered driver {name}"
        )
    if sum(item is driver_cls for item in registry.drivers) != 1:
        raise RayforgeCompatibilityError(
            f"Rayforge did not register exactly one {name} driver"
        )
    return True


def unregister_driver(
    driver_cls: type,
    *,
    registry: Any | None = None,
    plugin_api_version: int | None = None,
) -> bool:
    """Remove only the exact class previously registered by this addon."""

    registry, _version = _host(registry, plugin_api_version)
    name = driver_cls.__name__
    registered = registry.driver_by_classname.get(name)
    identity_entries = [item for item in registry.drivers if item is driver_cls]
    named_foreign = [
        item
        for item in registry.drivers
        if item.__name__ == name and item is not driver_cls
    ]

    if registered is None and not identity_entries and not named_foreign:
        return False
    if registered is not driver_cls or named_foreign:
        raise RayforgeCompatibilityError(
            f"refusing to unregister foreign Rayforge driver {name}"
        )

    del registry.driver_by_classname[name]
    registry.drivers[:] = [
        item for item in registry.drivers if item is not driver_cls
    ]
    if name in registry.driver_by_classname or any(
        item is driver_cls for item in registry.drivers
    ):
        raise RayforgeCompatibilityError(
            f"Rayforge did not fully unregister driver {name}"
        )
    return True
