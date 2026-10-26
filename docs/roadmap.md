# Product and research roadmap

Last updated: 2026-10-24

## Destination

The long-term destination is an open-source desktop application that can
prepare and run laser jobs on Makerspace Næstved's equipment. It should offer
the useful core of a LightBurn-like workflow without copying proprietary code,
assets, or license-protected behavior:

1. import or create geometry;
2. arrange it on an accurate representation of the work area;
3. assign process parameters and reusable material presets;
4. preview the resulting tool path and estimated job behavior;
5. validate the job against a machine profile and safety policy;
6. connect, frame, and run through an independently implemented machine
   backend.

The first hardware target is the JPT 100 W E2/M7 MOPA fiber laser with its
JCZ/EZCAD2 controller and 110 x 110 mm lens. CO2 and additional laser backends
come later. The project is not considered successful merely because it can
emit a laser command: it must make unsafe or mismatched configurations hard to
use accidentally.

## First useful product

The first useful release is deliberately smaller than a LightBurn clone. It is
an offline **galvo job workbench** that can:

- load a sanitized JPT machine profile;
- import a small, documented vector subset;
- represent layers and MOPA parameters without losing their units;
- show the field boundary, geometry, hatch, order, and an approximate path;
- reject out-of-field geometry and invalid parameter combinations;
- save a portable, versioned project document;
- run the complete workflow against a deterministic simulated controller.

This produces useful application architecture and test fixtures before any
hardware command is possible. The real controller backend remains absent or
physically gated until its protocol and safety behavior are supported by
evidence.

The corresponding casual-maker workflow, layout, disclosure, preview and
offline acceptance requirements are recorded in the
[MOPA workbench UX requirements](design/mopa-workbench-ux.md).

## What the installer snapshot gives us

The collected installer snapshot establishes:

- the JCZ/EZCAD2 controller and `Lmcv2u` driver family;
- vendor-declared USB VID/PID values, subsequently confirmed by passive live
  Windows enumeration;
- known-good 110 mm and 300 mm configuration trees;
- exact hashes for the opaque, lens-specific `markcfg7` profiles;
- a shared correction file and observable workspace differences;
- software, manuals, and configuration artifacts that can be studied offline.

It does **not** yet establish:

- the command sequence used to discover or initialize the controller;
- how geometry, hatch settings, MOPA parameters, or timing are encoded on the
  wire;
- which values are controller settings versus laser-source settings;
- status, interlock, error, abort, and recovery behavior;
- whether an apparently harmless query can move a galvo or arm emission;
- the effective pulse-width default for settings that omit `QPulseWidth`.
- safe controller discovery, state and recovery behavior beyond the offline
  mock evidence.

The later LightBurn export collection now establishes version `2.1.03`, a
110 x 110 mm `JCZFiber`/`LibUSB` JPT profile, and the `QPulseWidth` device
library field. See the
[device-export analysis](research/lightburn-device-exports-2026-10-19.md).
The later verified-project and live-UI collection establishes LightBurn 2.1.03
project frequency as serialized Hz/displayed kHz and `QPulseWidth` as ns.

Consequently, treating a vendor DLL or opaque profile as a callable black box
would be premature and would make the safety boundary impossible to audit.

## Milestones

### M0 — Evidence baseline (complete)

Preserve and hash the installer snapshot, publish sanitized findings, and keep
public/private provenance verifiable. Complete M0 with one local collection
from the actual LightBurn control computer. The preferred transfer is a single
ZIP or a directly accessible local folder; Google Drive is not part of the
workflow.

Exit criteria:

- exact LightBurn version, bundle, preferences, screenshots, and working
  project examples are present in PrivateStash;
- mounted lens and USB device identity are confirmed;
- sanitized metadata and new analysis are committed publicly;
- both repositories pass their clean-clone validation.

### M1 — Reuse validation and offline JCZ vertical slice

Ecosystem research found that Rayforge already implements most of the desired
application and MeerK40t BalorMK already implements the relevant controller.
Validate those assets before defining competing application architecture. See
the [open-source landscape](research/open-source-landscape.md) and
[accepted ADR 0002](adr/0002-reuse-rayforge-and-balormk.md).

The first work is entirely offline:

- evaluate stock MeerK40t against a synthetic MOPA job using only its mock
  controller;
- prove an external Rayforge addon can register and package a binary
  no-device driver on Windows;
- map a Rayforge operation stream into a deterministic JCZ command trace and
  compare it with BalorMK output;
- test existing LightBurn import with synthetic and private known-working
  galvo projects;
- identify only the missing profile, validation, diagnostic and safety
  concepts instead of designing replacements for existing ones.

The first controller-level part of the MeerK40t mock evaluation is recorded in
[the mock MOPA spike](research/meerk40t-mock-mopa-spike.md). It confirms
deterministic frequency, pulse-width and square-geometry command-list encoding
through BalorMK's forced mock transport. That first spike left cut-plan,
spooler and hatch coverage open and did not settle ADR 0002.

[The hatch cut-plan and mock-spooler follow-up](research/meerk40t-hatch-cutplan-spike.md)
now confirms that stock planning turns a synthetic hatch into Balor geometry,
preserves frequency and pulse width, and completes through `MockConnection`
with USB access trapped. Graphical workflow, import, correction, cancellation
and recovery coverage remain open.

The first Rayforge addon proof is recorded in
[the external binary-driver addon spike](research/rayforge-addon-spike.md).
An external addon can register a no-discovery, no-transport binary driver and
survive load, disable, enable and reload without patching Rayforge core. The
working registration path is an import-time call to the module-level driver
registry plus explicit unload cleanup, not the documented
`register_machines(machine_manager)` hook. Full application packaging and a
stable addon-aware unregister API remain open.

[The Rayforge-to-JCZ equivalence spike](research/rayforge-jcz-equivalence-spike.md)
confirms deterministic semantic agreement with the pinned BalorMK mock trace
for power, speed, frequency, MOPA pulse width, square coordinates and a one
millisecond dwell. It deliberately stops before production packet encoding,
lens correction or transport and records an upstream pulse-width unit
documentation conflict that must be resolved explicitly.

[Negative JCZ encoder cases](research/rayforge-jcz-negative-cases.md) now prove
fail-closed handling for a synthetic profile mismatch, out-of-field geometry,
power outside Rayforge's fraction range, non-positive frequency and pulse
width, and unsupported Ops. Hardware-specific upper limits remain unknown and
are deliberately not guessed.

[The transport-free JCZ record spike](research/rayforge-jcz-packet-spike.md)
now extends the deterministic 12-byte records with fixed-size list buffering
and explicit state-before-motion ordering. Upload, execution and physical
transport remain outside M1.

[The synthetic LightBurn MOPA import spike](research/rayforge-lightburn-mopa-import-spike.md)
confirms that Rayforge preserves geometry, power, speed and passes. Three
operator-verified LightBurn 2.1.03 projects plus the running UI establish the
serialized Hz/display-kHz relationship and direct ns `QPulseWidth` contract.
The external addon maps complete vector settings into disabled workflow steps
with exact evidence provenance. Missing pulse width, image equivalence and
every hardware gate still fail closed.

ADR 0002 accepts the Rayforge-addon architecture with BalorMK as the pinned
behavioral oracle. Packaged Windows interaction is a release gate, not an open
architecture question. An independent app now requires a later ADR with
concrete evidence that this accepted route cannot meet product needs.

Exit criteria: a representative JPT job survives import/planning, MOPA
parameters and units, validation and deterministic mock encoding; the chosen
host architecture is recorded in an accepted ADR; and automated tests prove
that no production controller backend is reachable.

### M2 — Configuration understanding

Build read-only parsers and structural comparison tools for the relevant
EZCAD2 and LightBurn artifacts. Unknown binary fields remain unknown; the code
must preserve that distinction rather than infer values by trial and error.

Priorities:

1. parse documented text configuration and material libraries;
2. inspect known-working LightBurn projects and exports;
3. map equivalent concepts into the application's neutral domain model;
4. characterize opaque configuration files using comparisons across known
   lens profiles and controlled, user-made setting changes;
5. publish only independently derived format notes and sanitized fixtures.

Exit criteria: the app can report a configuration, explain which claims are
observed versus inferred, and detect a wrong-lens or unknown-profile condition
without writing to the machine.

### M3 — Controller validation and read-only access

This is a new, explicitly approved hardware-research phase. Begin with focused
validation of the existing independent BalorMK implementation. Use passive
observation of known software only for specific unresolved behavior. Captures
and raw third-party material stay private; derived protocol notes and
synthetic tests are public.

The first real backend capabilities are limited to device enumeration,
identity, firmware/capability discovery, and status. Every operation receives
an evidence level and a safety classification. Unknown messages are recorded,
not replayed.

Before touching the connected machine, write a test protocol that specifies:

- how emission is physically prevented;
- which motion is possible and how the work area is cleared;
- an observer and accessible emergency stop;
- the precise allowed USB operations;
- abort conditions and rollback/recovery steps;
- what is captured and how it is sanitized.

The initial, non-executable protocol, machine-readable template and validator
are now recorded in the
[M3 hardware-research protocol](research/m3-hardware-research-protocol.md).
The committed template is intentionally incomplete. Validator success means
only `ready_for_review`; it never grants permission to access hardware.

Exit criteria: the app recognizes the correct controller and reports status
without moving a galvo, arming the source, modifying persistent state, or
requiring proprietary executable code in the public build.

### M4 — Controlled motion and marking experiments

Add capabilities one at a time behind explicit feature gates:

1. upload a synthetic no-output job, if supported;
2. exercise abort and recovery without emission;
3. perform controlled framing only after its galvo behavior is understood;
4. mark a minimal calibration primitive at a conservative, reviewed setting;
5. verify coordinate scale, orientation, timing, and MOPA parameters;
6. compare planned versus observed behavior and retain a test record.

Machine limits and source parameters come from known-good evidence and physical
verification. They are never discovered through broad value sweeps.

Exit criteria: a reviewed integration test can mark a known calibration job
repeatedly, stop safely, and reject incorrect machine/lens profiles.

### M5 — Workshop-usable JPT release

Turn the proven vertical slice into a workshop tool:

- practical SVG/DXF import and editing;
- layers, hatch/fill, ordering, transforms, text strategy, and presets;
- framing, start/pause/abort, progress, and understandable diagnostics;
- configuration backup and recovery;
- onboarding, compatibility matrix, signed releases, and operator guidance;
- usability and safety tests with makerspace users.

Advanced LightBurn features are selected from real workshop needs rather than
copied feature-for-feature.

Exit criteria: trained users can prepare and run ordinary JPT jobs without
LightBurn, within a documented support envelope.

### M6 — Additional laser backends

Use the neutral job model and safety architecture to add the Eduard x1550 and
Bodor BCL503MU. Each controller family gets its own evidence, protocol,
capability, and hardware-validation track. A successful JPT backend does not
imply compatible safety or control behavior on either CO2 machine.

## Current completion track

The exploratory work package is complete: verified projects, device evidence,
profile import, list buffering, cancellation/recovery, workflow modeling and
the M3 protocol draft are all present. Work now converges on two deliverables:

1. produce the pinned Windows Rayforge checkpoint on a reviewed external build
   runner, verify the transferred artifact set and complete the no-device
   desktop interaction checklist;
2. promote complete vector MOPA imports only after an absent-pulse-width
   policy, image equivalence and exact machine-context validation.

Exterior photographs, additional screenshots and speculative protocol research
are not M1 blockers. Hardware work remains separately gated by M3.

### Completed implementation record

The M3 draft, template, validator and regression tests are present.
Hardware work still cannot proceed until the exact read-only operation evidence,
driver/rollback plan, physical controls, distinct assigned roles and separate
human approval are all in place.

Item 2 is now covered by the
[synthetic LightBurn JCZ device-import spike](research/rayforge-lightburn-device-import-spike.md):
Rayforge preserves the common name and work-area fields, but maps no
`JCZFiber` driver and drops the JCZ-specific safety and MOPA fields from its
profile model. The fixture and regression test remain transport-free.

Item 3 now has a minimal external-addon seam: it recognizes only the synthetic
LightBurn 2.1.03 `JCZFiber` fixture with explicit provenance, the observed
110 x 110 mm/Q-pulse/frequency/frame contract, and binds it to the no-device
JCZ driver. Vector project values use the evidence-backed Hz/ns mapping, while
encoding remains disabled pending physical compatibility and review.

Item 4 now covers transport-free fixed-size list buffering and an explicit
state-before-motion order derived from pinned BalorMK. Port commands, upload,
execute, status and cancellation remain outside the encoder and cannot be
reached by this spike.

The cancellation half of item 5 now has an asynchronous no-device proof:
hold/resume work through the Rayforge driver contract, cancel clears every
pending list buffer, restart fails until explicit recovery, and a separately
encoded follow-up job can then complete. Physical stop/reset commands remain
absent.

The first graphical-workflow assessment now confirms that Rayforge's existing
generated settings UI exposes frequency and pulse width with Hz/ns contracts,
the values survive step serialization, and the preview artifact is populated
without machine code or transport. This is a headless UI-contract and pipeline
proof, not a completed human GTK test. Packaged Windows interaction with the
external addon remains the final desktop release gate; ADR 0002 has accepted
the architecture independently of it.

The first Windows launch preflight is recorded separately. It fails closed
because the available spike venv has no PyGObject `gi` module and this machine
has no MSYS2/UCRT64 Rayforge runtime. No dependencies were installed and no
GUI success is claimed. The packaged interaction test therefore remains
blocked on a reviewed Windows GTK runtime, not on controller behavior.

The transport-free portions are now consolidated by the
[M1 no-device acceptance checkpoint](research/m1-no-device-acceptance.md).
It reruns the public suite and leak guard and hashes the validated regression
reports. The on-demand build entry point fetches pinned source and stages the
addon but deliberately refuses to install a missing Windows toolchain. It
rejects modified upstream source and replaces the exact addon staging tree so
stale files cannot survive between builds.
An artifact produced elsewhere can be checked locally without execution: the
verifier rejects unsafe paths or changed bytes and confirms the pin plus every
packaged addon source before the manual GUI checklist may begin. It also
rejects omitted manifest entries and extra files hidden in the packaged addon
directory, plus ambiguous or unsafe Windows ZIP entries.
The manual checklist now also has a versioned, fail-closed report template and
validator. Missing steps remain incomplete, a complete operator run remains
ready for review until a named, timezone-stamped human review is recorded,
stop conditions fail the run, and hashed screenshots stay outside the public
repository pending sanitization.
A reproducible kit generator copies only allowlisted synthetic inputs into the
ignored build area, records their hashes and refuses to overwrite an existing
test run. Its schema-2 provenance chain binds the editable manual report to the
exact kit manifest, repository commit and non-executing artifact-verification
report; substituted or changed inputs, a different Rayforge pin, malformed
artifact hashes, a changed checkpoint manifest or an unverified addon fail
validation.
The pinned upstream contracts and license notices are now machine-verifiable.
Rayforge's documented addon lifecycle is viable, but production driver
registration still needs a supported symmetric registry API. The current
internal access is contained by a fail-closed API-23 compatibility adapter;
the project license is MIT under accepted ADR 0003; upstream attribution and
distribution notice requirements remain mandatory.

## Decision rules

- A simulator test precedes every equivalent hardware behavior.
- Read-only precedes state change; state change precedes motion; motion precedes
  emission.
- Safety-relevant values require provenance and units.
- A profile mismatch fails closed.
- Unknown protocol fields are never filled by guesswork.
- Raw proprietary artifacts remain private; public tests use synthetic or
  explicitly redistributable fixtures.
- Any bulk external-data operation is scoped and costed before it starts. More
  than roughly ten remote file operations require an explicit warning and a
  cheaper bulk-transfer alternative.

