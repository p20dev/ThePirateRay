# Offline LightBurn project MOPA import seam

The addon's `project_import.py` reads observed `CutSetting` and
`CutSetting_Img` elements without loading Rayforge, geometry or any transport.
It preserves raw `frequency`, `QPulseWidth`, layer order and image dither mode.
The synthetic unit tests contain no private geometry or complete recipes.

Normalization requires the caller to opt into the evidence-backed serialized
unit contract `frequency=Hz;QPulseWidth=ns`. The contract is restricted to
LightBurn `AppVersion="2.1.03"`; a missing or different version fails closed.
It comes from correlating an operator-verified project's raw
`frequency=1000000` and `QPulseWidth=10` with LightBurn's visible `1000 kHz`
and `10 ns` controls. This is not an inference from magnitude or an
authorization claim. Frequency is represented in Hz and kHz (division by
1000), while pulse width remains in ns. Without explicit contract selection,
only raw values are returned.

Absent fields remain absent, never zero or inherited defaults. Malformed,
non-finite, non-positive, duplicate and excessively large values are rejected.
The numeric ceiling is a parser bound, not a machine operating limit. Image
settings remain blocked pending image-processing equivalence, including
`3dslice`. XML declarations and unsupported project formats are rejected.

Every result has `encoding_allowed=False`, `hardware_use_allowed=False` and
`transport=None`, even with complete normalized values. This is a callable
offline metadata seam. The companion workflow bridge matches the normalized
LightBurn layer index to Rayforge's source-segment layer ID and stages complete
vector MOPA values through the host's setters. Every staged step is disabled
through `Step.set_visible(False)`, and its raw values, normalized values, exact
unit-contract provenance, review status and blockers are saved in the
serializable `Step.extra` data. Tampered or missing provenance is rejected
before any step is mutated.
Image settings and incomplete settings remain disabled without applying MOPA
values. Multi-step staging is preflighted and rolled back on setter failure.

The bridge deliberately has no function that enables output or removes a
blocker. Host UI and preflight integration must still resolve absent pulse
width and validate exact machine, lens, correction and parameter limits before
a separate reviewed promotion path can exist. Image-layer equivalence remains
unverified. Rayforge's relevant Step and LaserStep files are included in the
pinned upstream contract manifest.

The addon now also exposes a transport-free document preflight report with
stable issue codes and human-readable blocker messages. Its packaged frontend
adds a read-only `PirateRay Import Preflight` action to Rayforge's Tools menu;
the dialog renders those codes and keeps output disabled. The offline driver
runs this check before it prepares encoded buffers. A staged import is rejected;
manually re-enabling its step adds a distinct error, and malformed review data
fails closed. There is intentionally no accepted or promoted import state yet.

Validation covers unit conversion, absent fields, case sensitivity, duplicate
values, invalid numbers, image modes, mixed layers, exact layer binding,
transactional rollback and malformed XML. Existing packaging, no-device and
public evidence checks remain part of the test suite.
