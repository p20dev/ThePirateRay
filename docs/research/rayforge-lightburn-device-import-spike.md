# Rayforge synthetic LightBurn JCZ device-import spike

- Date: 2026-10-19
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Fixture: synthetic public `.lbdev`; no machine identifiers
- Scope: device-profile importer only, with no discovery or transport

## Result

Pinned Rayforge parses the synthetic `JCZFiber` profile and preserves its
display name, 110 x 110 mm work area and generic home-on-start value. It does
not select a driver because its LightBurn driver map has no `JCZFiber` entry.

The imported `DeviceProfile` also has no representation of the observed
`RequireFrameBeforeStart` setting or the synthetic cut-list `frequency` and
`QPulseWidth` fields. The import is therefore explicitly classified as unsafe
for JCZ use rather than receiving guessed defaults.

The checked result is
`tests/fixtures/rayforge-lightburn-device-import.json`. Two runs produced the
same SHA-256 digest,
`3c26f43be6b06e9b17a5decbe4ba7bb633eb1b8ac7bb0361449d7498a3b9279c`.

## Evidence boundary

The fixture uses field names already recorded by the sanitized LightBurn
device-export analysis. Its values are synthetic examples inside observed
ranges, not a copy of a private export and not certified machine limits or
material settings. It deliberately omits private GUIDs, source paths and
unpublished connection serialization.

This spike characterizes the current importer; it does not implement a driver
mapping. A future `JCZFiber` mapping must target the separately tested
no-transport addon driver and require an exact compatible profile. It must not
silently map `JCZFiber` to a G-code or Ruida driver.

## Reproduce

Run against the pinned Rayforge checkout:

```powershell
python scripts/spike_rayforge_lightburn_device_import.py C:\path\to\rayforge
```

## Next seam

The smallest evidence-backed extension is to recognize `JCZFiber` as a
distinct, fail-closed profile kind, preserve its raw settings with explicit
units/provenance, and associate it only with the external no-device JCZ driver.
Cut-list recipes and project-layer `QPulseWidth` mapping remain gated until a
known-working `.lbrn2` fixture establishes project serialization.

No USB enumeration, controller command, motion, framing or emission occurred.
