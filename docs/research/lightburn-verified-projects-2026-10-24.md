# Operator-verified LightBurn projects

- Date: 2026-10-24
- Provenance: two files explicitly selected by the operator as successfully tested
- Scope: byte-preserving acquisition and offline XML analysis; no hardware access

The two explicitly supplied files supersede the earlier exclusion only for
these selected originals. Other unverified local projects remain excluded.
Raw geometry, names, paths and complete settings remain in PrivateStash.
Both copied files were verified against their originals with SHA-256.
See [public manifest](../../evidence/public-lightburn-verified-projects.jsonl).

Both roots are `LightBurnProject`, with `AppVersion="2.1.03"` and
`FormatVersion="1"`. Process settings occur as direct children of
`CutSetting`, with numeric strings in a `Value` attribute.

| Artifact ID | Layer type | Raw `frequency` | Raw `QPulseWidth` |
| --- | --- | ---: | ---: |
| `sha256-1e1ec8441cc23ee997a6` | Scan | 200000 | absent |
| `sha256-1e1ec8441cc23ee997a6` | Cut | 80000 | 180 |
| `sha256-1e1ec8441cc23ee997a6` | Scan | 1000000 | 10 |
| `sha256-0807d2a2d1613e1aff90` | Scan | 1000000 | 10 |
| `sha256-0807d2a2d1613e1aff90` | Cut | 80000 | 180 |
| `sha256-0807d2a2d1613e1aff90` | Scan | 1000000 | 10 |

All four Scan settings also have `crossHatch Value="1"`. These are stored
layer settings, not independent proof of which settings emitted on a machine.
Successful operation is the operator's statement; it was not replayed here.

## Import implications

This closes the missing operator-verified project serialization evidence gate:
`frequency` and case-sensitive `QPulseWidth` are now observed in actual
projects, consistent with the earlier device export findings.

The absent pulse-width field must remain distinguishable from zero or an
explicit value. Its effective LightBurn default or inheritance is not established
by this inspection. An importer must preserve absence and require an explicit,
validated resolution before a MOPA job can become executable.

These raw values do not independently establish units, safe ranges, calibration
or device identity. The next implementation should use synthetic geometry and
test explicit unit conversions, field absence and invalid values. It must not
copy private project geometry into public fixtures or enable hardware access.

The reviewed Windows artifact and manual no-device desktop acceptance remain
open. ADR 0002 remains Proposed until those gates have also passed.
