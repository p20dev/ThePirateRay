# Rayforge synthetic LightBurn MOPA import spike

- Date: 2026-10-18
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Fixture: synthetic public `.lbrn2`; no machine identifiers
- Scope: importer boundary only, with no discovery or transport

## Result

The pinned Rayforge importer successfully parsed a synthetic two-millimetre
square and preserved its layer name, geometry, 50 percent power, 250 mm/s
speed and one pass. LightBurn's observed `frequency` and
`overrideFrequency` elements also survive in the source asset's raw metadata.

The pinned upstream importer does not map frequency into workflow settings; it
maps only power, speed and passes from this fixture. The external addon now
supplies that narrow mapping for LightBurn 2.1.03. Subsequent operator-verified
evidence correlates raw `frequency=1000000` and `QPulseWidth=10` with visible
`1000 kHz` and `10 ns`, establishing the version-bound Hz/ns serialization
contract. The staged job nevertheless remains unsafe for JCZ encoding because
machine, lens, correction and promotion review are still unresolved.

Two runs produced identical output with SHA-256
`9ebce7b5b3388abfeed024e25f8f46001260bf814da19808bfc83fb6554fc26e`.
The golden result is `tests/fixtures/rayforge-lightburn-mopa-import.json`.

## Evidence classification

- **Observed:** Rayforge's own LightBurn test fixtures contain `frequency` and
  `overrideFrequency` elements.
- **Observed:** generic parsing retains these elements in source metadata.
- **Observed:** `_build_step_config` does not map frequency or pulse width.
- **Observed after this spike:** a LightBurn `2.1.03` device-library export
  uses `QPulseWidth`; official LightBurn documentation defines Q-pulse width
  in nanoseconds. See the
  [device-export analysis](lightburn-device-exports-2026-10-19.md).
- **Observed after this spike:** three known-working galvo projects use the
  case-sensitive `QPulseWidth` field. Missing fields remain absent; their
  effective default is still unknown and is never invented.
- **Not inferred:** no pulse-width tag, unit, default or machine limit was
  invented for the public fixture.

## Decision impact

Rayforge's existing LightBurn importer remains useful for ordinary vector
geometry and common process settings. The external addon now implements the
narrow frequency/`QPulseWidth` mapping with a version- and evidence-bound unit
contract, stages values on disabled workflow steps, and retains all blockers.
Image equivalence, absent pulse width and physical compatibility remain gated.

No USB enumeration, controller command, motion or emission was attempted.
