# LightBurn control-machine observation

- Date: 2026-10-24
- Application: LightBurn Pro 2.1.03
- Hardware state: laser physically disconnected by the operator
- Scope: passive UI and local-preference inspection only

## Confirmed in the running application

The window title identified LightBurn Pro `2.1.03` with the operator-verified
`Gradients DepthMap` project open. The active device was `100 JPT E2 MOPA`, the
connection status read `Disconnected`, the port selector read `(Auto)`, and the
loaded material library was `Mopa-100W-110mm`.

The Cuts / Layers panel labels the MOPA controls as `Frequency (kHz)` and
`Q-Pulse (ns)`. This independently establishes the UI display units needed by
the offline importer contract; it does not establish the serialized-file unit
or authorize conversion without the documented normalization rule.

The visible selected-layer controls showed speed `1800 mm/s`, one pass, power
`17%`, frequency `1000 kHz`, and Q-pulse width `10 ns`. The project layer list
also showed an Image layer at `1800 / 59` and two additional layers at
`12 / 59`. These values are observations of the open project, not recommended
recipes.

## Preference cross-check and preserved files

The live preferences still contain four device records. The named JPT profile
is `JCZFiber` over `LibUSB`, has a 110 x 110 mm work area, enables Q-pulse-width
control, and requires framing before start. The profile stores a raw frequency
range of 1 to 4000 and has home-on-startup disabled.

The active preferences file and LightBurn's newest native `.lbprefs` backup
were copied into PrivateStash with before/source-after/copy SHA-256 equality
checks. Five operator-supplied PNG screenshots preserve every tab in the
general Settings dialog: Editor Settings, Units and Grids, Display,
Import / Export, and Camera. Their sanitized public records are in
[`public-lightburn-control-machine-observation.jsonl`](../../evidence/public-lightburn-control-machine-observation.jsonl).
Exact local paths, raw preferences and machine-specific fields remain private.

The screenshots corroborate version `2.1.03` and show millimeters as the design
unit. DXF import has unit auto-detection enabled with millimeters selected as
the fallback, while SVG import uses the 96 DPI Inkscape convention with
auto-detection enabled. The visible output curve tolerance is `0.050 mm`.
These are observed application settings, not machine-safe processing values.

## Collection limits

The five supplied screenshots close the ordinary Settings-dialog item. The
automation screenshot channel itself repeatedly returned `window capture timed
out`; geometry-dependent controls therefore could not be safely invoked to
capture every separate Device Settings tab. No substitute Support Data bundle
was generated.

No Start or Frame control was used, no USB endpoint or controller was opened,
and no machine setting was intentionally changed. The operator's 110 mm lens
statement remains operator-confirmed rather than photographically verified.
Exterior hardware labels and the complete Device Settings screenshot set remain
open evidence items.
