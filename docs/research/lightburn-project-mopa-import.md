# Offline LightBurn project MOPA import seam

The addon's `project_import.py` reads observed `CutSetting` and
`CutSetting_Img` elements without loading Rayforge, geometry or any transport.
It preserves raw `frequency`, `QPulseWidth`, layer order and image dither mode.
The synthetic unit tests contain no private geometry or complete recipes.

Normalization requires the caller to declare the serialized-unit contract
`frequency=Hz;QPulseWidth=ns`. This is an explicit input, not an inference from
numeric magnitude or an authorization claim. With that contract, frequency is
represented in Hz and kHz (division by 1000), and pulse width in ns. Without
it, only raw values are returned. The seam does not establish the contract on
behalf of the caller or read machine limits from these values.

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
through `Step.set_visible(False)`, and its raw values, normalized values,
review status and blockers are saved in the serializable `Step.extra` data.
Image settings and incomplete settings remain disabled without applying MOPA
values. Multi-step staging is preflighted and rolled back on setter failure.

The bridge deliberately has no function that enables output or removes a
blocker. Host UI and preflight integration must still establish serialized
units from independent evidence, resolve absent pulse width and validate exact
machine, lens, correction and parameter limits before a separate reviewed
promotion path can exist. Rayforge's relevant Step and LaserStep files are now
included in the pinned upstream contract manifest.

The addon now also exposes a transport-free document preflight report with
stable issue codes and human-readable blocker messages. The offline driver
runs this check before it prepares encoded buffers. A staged import is rejected;
manually re-enabling its step adds a distinct error, and malformed review data
fails closed. There is intentionally no accepted or promoted import state yet.

Validation covers unit conversion, absent fields, case sensitivity, duplicate
values, invalid numbers, image modes, mixed layers, exact layer binding,
transactional rollback and malformed XML. Existing packaging, no-device and
public evidence checks remain part of the test suite.
