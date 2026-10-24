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
offline metadata seam; it is not yet wired to Rayforge's project importer or
workflow. Host integration must bind settings to layer indices, establish
serialized units from independent evidence, resolve absent pulse width and
validate exact machine, lens, correction and parameter limits. No existing
golden lifecycle or upstream importer run was repeated; the package inventory
was extended to include the new module.

Validation covers unit conversion, absent fields, case sensitivity, duplicate
values, invalid numbers, image modes, mixed layers and malformed XML. Existing
packaging, no-device and public evidence checks remain part of the test suite.
