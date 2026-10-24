# LightBurn device-export analysis

- Date: 2026-10-19
- Scope: four user-provided LightBurn exports, analyzed offline
- LightBurn version recorded by all three bundle manifests: `2.1.03`
- Safety boundary: no executable, driver, USB endpoint or machine command was
  used

## Evidence

Raw exports remain in PrivateStash. This public record contains hashes,
structure and independently derived findings only.

| Artifact ID | Size | Role |
| --- | ---: | --- |
| `sha256-e16fdb0aa7c374c4c94d` | 20,309 bytes | Complete bundle containing three device profiles, preferences and libraries |
| `sha256-fc6cf52f4ef815dd5037` | 5,720 bytes | Eduard device bundle |
| `sha256-88c762adcb8e9693c913` | 97,356 bytes | Exported LightBurn preferences |
| `sha256-d422e9886e29ed666c07` | 8,798 bytes | JPT MOPA device bundle |

Every digest and size is recorded in
[`evidence/public-lightburn-exports.jsonl`](../../evidence/public-lightburn-exports.jsonl).
Private paths, device GUIDs and local account data are intentionally omitted.

## Bundle structure

The complete bundle has eight entries: preferences, material-test presets,
three LightBurn device profiles, two material libraries and a bundle manifest.
Each device-specific bundle contains preferences, one device profile and a
manifest. All manifests declare bundle format `1.0` and LightBurn `2.1.03`.

## Device findings

| Display name | LightBurn backend | Connection | Work area | Attribution |
| --- | --- | --- | ---: | --- |
| `100 JPT E2 MOPA` | `JCZFiber` | `LibUSB` | 110 × 110 mm | Focus machine |
| `Eduard X1550` | `Ruida` | `Serial` | 1500 × 1000 mm | Makerspace CO2 machine |
| `Ruida 644XS` | `Ruida` | `CDM` | 500 × 300 mm | Unassigned; physical machine unknown |

The preferences contain four device records because the unassigned Ruida
profile occurs twice. This is not evidence for a fourth physical machine, and
the 500 × 300 mm profile must not be attributed to the Bodor or any other
machine without independent confirmation.

The JPT profile additionally records:

- a numeric laser type of `1` and fiber type of `3`;
- enabled Q-pulse-width control;
- profile frequency bounds stored as `1` and `4000`;
- `RequireFrameBeforeStart` enabled;
- 60 cut-list entries.

Numeric enums are preserved as observations. Their semantic labels are not
guessed from the numbers alone.

## MOPA process-setting evidence

Across the 60 exported cut-list entries:

- 35 contain `frequency`;
- 25 contain `QPulseWidth`;
- all 25 pulse-width entries also contain frequency;
- observed raw frequency values range from 30,000 to 1,000,000;
- observed `QPulseWidth` values range from 2 to 180.

LightBurn's official galvo cut-setting documentation presents frequency in
kHz and Q-Pulse Width in nanoseconds. The larger integers stored by the export
show that the serialized representation cannot simply be copied into a UI
field without an explicit conversion contract. Subsequent operator-verified
LightBurn 2.1.03 project/UI correlation establishes raw Hz to display kHz and
direct-ns `QPulseWidth`; see the
[control-machine observation](lightburn-control-machine-observation-2026-10-24.md).

These observed recipe values and profile fields are **not certified hardware
limits or safe operating parameters**. They must not be used to probe the
machine. LightBurn likewise warns that incorrect galvo source settings can
damage a laser.

Sources:

- [LightBurn galvo-specific cut settings](https://docs.lightburnsoftware.com/2.2/Reference/CutSettingsEditor/GalvoSpecificCutSettings/)
- [LightBurn galvo source settings](https://docs.lightburnsoftware.com/latest/Reference/DeviceSettings/GalvoPorts/)

## Reuse impact

Rayforge's current LightBurn **project** importer retains raw frequency
metadata but maps neither frequency nor pulse width into workflow settings.
Its separate LightBurn **device** importer recognizes common profile fields,
but its driver map does not cover this observed `LibUSB`/`JCZFiber` pairing
and it does not map the JPT-specific settings or cut list.

The narrowest useful implementation is therefore an extension rather than a
new general parser:

1. add evidence-backed JCZ device-profile recognition;
2. preserve source units and raw values at the import boundary;
3. bind the now-confirmed LightBurn 2.1.03 Hz/ns contract to exact provenance;
4. validate imported values against a separately verified machine profile;
5. fail closed when units, profile identity or ranges are unknown.

## Remaining collection gaps

The exports settle the exact LightBurn release and the two named device
profiles. The known-working projects, Device Settings screenshots and closed
preferences snapshot were subsequently collected. Phase 0 still needs:

- exterior machine, source, controller and installed-lens photographs;
- mounted-lens, connection, startup and interlock notes;
- the stock driver's identity and version on the control computer.

An About screenshot is still useful as visual corroboration, but the bundle
manifests already establish version `2.1.03`.
