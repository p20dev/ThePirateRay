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

However, the importer does not map frequency into the workflow layer settings.
It maps only power, speed and passes from this fixture. The inspected Rayforge
LightBurn fixtures and importer contain no evidence-backed mapping for a MOPA
pulse-width field. Consequently, the imported job is explicitly classified as
unsafe for JCZ encoding rather than being completed with a guessed value.

Two runs produced identical output with SHA-256
`9ebce7b5b3388abfeed024e25f8f46001260bf814da19808bfc83fb6554fc26e`.
The golden result is `tests/fixtures/rayforge-lightburn-mopa-import.json`.

## Evidence classification

- **Observed:** Rayforge's own LightBurn test fixtures contain `frequency` and
  `overrideFrequency` elements.
- **Observed:** generic parsing retains these elements in source metadata.
- **Observed:** `_build_step_config` does not map frequency or pulse width.
- **Unknown:** the exact LightBurn field and unit for JPT MOPA pulse width in a
  known-working galvo project.
- **Not inferred:** no pulse-width tag, unit, default or machine limit was
  invented for the public fixture.

## Decision impact

Rayforge's existing LightBurn importer is useful for ordinary vector geometry
and common process settings, but it does not yet satisfy M1's MOPA parameter
survival requirement. The narrowest likely extension is an importer mapping
for frequency plus a separately evidenced pulse-width field, followed by an
explicit validation gate. A private known-working LightBurn project is still
needed to establish the pulse-width representation before implementing that
mapping.

No USB enumeration, controller command, motion or emission was attempted.
