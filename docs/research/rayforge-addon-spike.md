# Rayforge external binary-driver addon spike

- Date: 2026-10-18
- Upstream: `barebaric/rayforge`
- Commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Rayforge addon API: 23
- Scope: Windows, external addon lifecycle, no device or transport

## Result

An external addon loaded through Rayforge's real `AddonManager` and registered
`PirateRayJCZNoDeviceDriver`. The driver declares `uses_gcode = False`, has no
discovery specification or transport, and returns a recognizable binary test
payload from an `OpsEncoder`.

The following lifecycle completed twice with identical JSON results:

1. load the external addon;
2. resolve the driver by class name;
3. create its binary encoder and verify its payload;
4. disable the addon and verify driver removal;
5. re-enable it and verify re-registration;
6. reload it and verify there is exactly one registry entry;
7. package its three source/manifest files into a ZIP; and
8. disable it cleanly.

The two result files had SHA-256
`610f8f191526afe4685f8659c1ef2b34fac3c68a8f8088d77ca5e1fdd6080bfc`.
The checked result is `tests/fixtures/rayforge-addon-spike.json`.

## Registration seam finding

Rayforge's addon hook specification still exposes
`register_machines(machine_manager)`, but the inspected startup registration
table does not invoke that hook, and `MachineManager` has no method for adding
a driver class. The source-level driver registry instead exposes
`rayforge.machine.driver.register_driver(driver)`.

The working spike therefore registers during import of the addon's worker
entry point and removes its class in `on_unload`. This survives load, disable,
enable and reload, but it relies on mutable module-level registry internals for
cleanup. Before a production addon, Rayforge should ideally expose a dedicated
addon-aware driver registry hook with supported unregister behavior.

## Reproduce

Create an isolated environment containing Rayforge's non-GUI runtime driver
dependencies, then run:

```powershell
python scripts/spike_rayforge_addon.py C:\path\to\rayforge
```

The script refuses any Rayforge revision other than the pinned commit.

## What this proves

- An external addon can load a binary, non-G-code driver without patching the
  Rayforge source tree.
- Its worker entry point is sufficient in headless mode.
- The driver can remain completely free of discovery and transport.
- Addon load, disable, enable and reload work when registration and cleanup are
  handled explicitly.
- The addon itself can be packaged as a deterministic set of files on Windows.

## What remains open

- The ZIP check is addon packaging, not a proof that a complete PyInstaller or
  MSIX Rayforge build discovers an externally installed addon.
- The current registration seam is functional but not a stable, addon-aware
  API. Upstream feasibility should be assessed before relying on it.
- No JCZ command encoding, machine profile, UI, project reload, discovery,
  transport, controller status or cancellation is implemented here.
- Nothing in this spike authorizes USB access, galvo movement or emission.

## Decision impact

Spike B is a qualified go: the external binary-driver boundary is viable
without a Rayforge core fork, but registration lifecycle support should be
made explicit upstream. The next technical proof is Spike C: translate a tiny
Rayforge `Ops` stream into a deterministic no-I/O JCZ trace and compare its
semantics with the pinned BalorMK mock trace.
