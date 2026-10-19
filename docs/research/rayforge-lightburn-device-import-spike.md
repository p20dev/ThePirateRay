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

The external addon now supplies the narrow profile seam missing from Rayforge
core. It recognizes only the explicit public synthetic profile identity,
requires `JCZFiber`, positive work-area dimensions and
`RequireFrameBeforeStart: true`, and associates the result only with
`PirateRayJCZNoDeviceDriver`. Frequency and `QPulseWidth` remain raw
observations with unverified serialized-unit conversion. Encoding remains
blocked because the physical profile, lens/correction match, project
serialization and machine-specific limits are not yet verified.

The checked result is
`tests/fixtures/rayforge-lightburn-device-import.json`. Two runs produced the
same SHA-256 digest,
`94f0d17837471399334a82c84558985d35da0f1a8eee6a176eb02d57ae3aeb18`.

## Evidence boundary

The fixture uses field names already recorded by the sanitized LightBurn
device-export analysis. Its values are synthetic examples inside observed
ranges, not a copy of a private export and not certified machine limits or
material settings. It deliberately omits private GUIDs, source paths and
unpublished connection serialization.

This spike characterizes the current importer and proves the smallest mapping
at the external-addon boundary. It does not change Rayforge core or silently
map `JCZFiber` to a G-code or Ruida driver.

## Reproduce

Run against the pinned Rayforge checkout:

```powershell
python scripts/spike_rayforge_lightburn_device_import.py C:\path\to\rayforge
```

## Next seam

The next extension is offline controller-list buffering and explicit safe
state ordering. Cut-list recipes and project-layer `QPulseWidth` mapping remain
gated until a known-working `.lbrn2` fixture establishes project serialization.

No USB enumeration, controller command, motion, framing or emission occurred.
