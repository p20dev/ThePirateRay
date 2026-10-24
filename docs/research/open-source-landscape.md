# Open-source landscape for The Pirate Ray

- Research date: 2026-10-17
- Scope: reusable software for a JPT E2/M7 MOPA fiber laser on a
  JCZ/EZCAD2-compatible controller, followed by possible CO2 backends
- Method: public project documentation, source inspection, tests, release
  history, and small shallow/sparse source checkouts; no vendor executable was
  run and no laser or USB device was contacted

## Executive conclusion

The project should **not** begin by writing a LightBurn clone or reverse
engineering the complete JCZ protocol from scratch. Two MIT-licensed projects
already cover most of the problem from opposite directions:

1. [MeerK40t](https://github.com/meerk40t/meerk40t), specifically its
   `balormk` module, already controls EZCAD2-compatible JCZ galvo controllers,
   includes MOPA pulse-width support, and has a mock USB connection. Its USB
   implementation uses VID `9588`, PID `9899`, write endpoint `0x02`, and read
   endpoint `0x88`. The VID/PID exactly match the values independently found
   in our private installer evidence.
2. [Rayforge](https://github.com/barebaric/rayforge) already supplies the
   actively developed desktop editor, project model, geometry/toolpath
   pipeline, LightBurn project and device import, material recipes,
   simulation, pre-flight checks, packaging, and addon architecture. Its
   neutral operation model and UI already represent laser frequency and pulse
   width. It does not currently provide a JCZ driver.

The leading architecture is therefore a **Rayforge JCZ/Balor backend or
addon**, with command semantics adapted from the current BalorMK
implementation. Before committing to that architecture, stock MeerK40t should
also be evaluated as the shortest route to a usable open-source application.
An independent desktop application is the fallback, not the starting point.

This is a research recommendation, not yet an architecture decision. The
proposed decision and its proof obligations are recorded in
[ADR 0002](../adr/0002-reuse-rayforge-and-balormk.md).

## What the project actually needs

The useful unit of reuse is larger than a USB library. A workshop application
needs all of the following:

| Capability | Importance for the JPT | Existing best candidate |
| --- | --- | --- |
| JCZ discovery, USB transport and command encoding | Critical | MeerK40t BalorMK |
| Galvo job sequencing, timing, status and abort | Critical | MeerK40t BalorMK |
| MOPA frequency and pulse-width representation | Critical | Both projects |
| Lens correction and coordinate mapping | Critical | BalorMK as reference; must validate against our profiles |
| Mock controller and deterministic traces | Critical before hardware | BalorMK mock plus a new adapter-level fake |
| Desktop canvas, document and undo/redo | Large effort | Rayforge |
| SVG/DXF/PDF/raster and LightBurn import | Large effort | Rayforge |
| Geometry, hatch, offsets and path planning | Large effort | Rayforge plus raygeo |
| Machine profiles, materials and recipes | Large effort | Rayforge |
| Preview, simulation and pre-flight checks | Safety-relevant | Rayforge, extended for galvo semantics |
| Packaging for Windows | Required | Both ship desktop builds; Rayforge is the preferred modern base |
| Future Ruida support | Relevant to the CO2 machines if confirmed | Rayforge/ruida-pa or MeerK40t; controller identity still unknown |

## Candidate assessment

The classifications mean:

- **adopt**: evaluate as a product or direct maintained dependency;
- **adapt**: use code or concepts behind a narrow interface, with attribution;
- **reference**: learn from it, but do not make it a primary dependency;
- **defer/reject**: does not solve the current controller problem well enough.

| Candidate | License | JCZ/MOPA | Desktop/product coverage | Maintenance signal at snapshot | Disposition |
| --- | --- | --- | --- | --- | --- |
| MeerK40t | MIT | Direct EZCAD2/JCZ; MOPA support | Full app, older wxPython architecture | Project declares maintenance mode, but still receives changes | **Adopt/evaluate now** and **adapt BalorMK** |
| BalorMK in MeerK40t | MIT at repository root; upstream documents its rewrite history | Direct, exact controller family | Controller, driver and limited galvo UI | Current code in main | **Primary protocol baseline** |
| galvoplotter | MIT | Direct low-level LMC; fiber and CO2 | Library only | Latest PyPI release found is old/beta | Prototype/reference; current BalorMK is ahead |
| Rayforge | MIT | No JCZ driver yet; neutral model already has MOPA fields | Broad modern app | Very active, current source and releases | **Preferred host platform, pending spike** |
| raygeo | MIT | Hardware-neutral | High-performance geometry kernel | Active and used by Rayforge | Adopt through Rayforge; direct use only if needed |
| ruida-pa | MIT | No JCZ | Binary Ruida backend | Active and used by Rayforge | Future CO2 candidate after controller identification |
| VisiCut / LibLaserCut | LGPL family | No credible JCZ path found | Mature Java architecture and drivers | Long-running project | Reference for abstractions |
| LaserWeb4 | AGPL-3.0 | No JCZ support found | Electron/web laser UI | Older ecosystem | Defer; weaker fit and license implications |
| lbrnts | MIT | File format only | TypeScript LightBurn parse/write | Small focused project | Reference if round-trip writing becomes necessary |
| lbrn2-to-svg | Open repository; verify exact license before reuse | File format only | Narrow conversion | Small project | Reference; Rayforge already imports `.lbrn2` |
| USBLM-V1 MeerK40t replacement | Open repository | Related JCZ hardware, but VID/PID `9588:9999` rather than ours | Firmware/stack-specific | Niche | Reference only; not our identified device |
| MarkEzd/EZCAD SDK wrappers | Often open wrapper code around proprietary DLLs | Direct through vendor DLL | Windows-only API wrappers | Depends on opaque vendor binary | Do not use as the public product foundation |

Repository activity is a maintenance indicator, not a security or quality
guarantee. License labels are project-declared and must be rechecked at the
exact commit before code is copied or distributed.

## Finding 1: MeerK40t can probably talk to this controller today

[MeerK40t describes itself](https://github.com/meerk40t/meerk40t) as an
MIT-licensed, cross-platform laser application and explicitly lists
EZCAD2-compatible JCZ galvo lasers among supported devices. Its current
`balormk` module is not a placeholder:

- `usb_connection.py` uses PyUSB/libusb and the exact `9588:9899` identity
  present in our sanitized machine profile;
- `controller.py` implements the LMC command layer, command lists, status,
  delays, power, frequency, MOPA pulse width, wait and abort behavior;
- `driver.py` translates MeerK40t cut operations into galvo jobs;
- `device.py` exposes laser-source, correction, timing and pulse-width
  settings;
- `mock_connection.py` records traffic without contacting hardware;
- the plugin registers a MOPA-capable fiber device.

The upstream [BalorMK documentation](https://github.com/meerk40t/meerk40t/blob/main/meerk40t/balormk/README.md)
states support for JCZ EZCAD2, fiber MOPA, power/frequency/pulse timing,
calibration and a simulation interface. The
[USB source](https://github.com/meerk40t/meerk40t/blob/main/meerk40t/balormk/usb_connection.py)
is especially strong corroborating evidence because its identifiers were
found independently rather than inferred from the project.

This changes M3 in the original roadmap. Protocol work should begin by
validating and testing an existing independent implementation, not by passive
capture or blank-sheet reverse engineering.

### Limits and risks

- MeerK40t explicitly says it is in maintenance mode and warns that weekly
  builds can regress. A known stable release and a pinned source commit must
  be evaluated separately.
- The low-level controller is embedded in MeerK40t service and cut-code
  abstractions. Copying only `driver.py` would not produce a clean standalone
  library.
- The current module has a mock transport, but its hardware-safety behavior
  and test depth do not meet this project's intended fail-closed standard.
- Source comments and compatibility branches show uncertainty around some
  controller/source variants. “EZCAD2 compatible” is not proof that every
  setting is correct for our JPT source, scan head and lens.
- The driver includes commands capable of moving the galvos and enabling
  emission. It is evidence and reusable code, not a safety certification.

### `galvoplotter`: cleaner boundary, older implementation

[galvoplotter](https://github.com/meerk40t/galvoplotter) is an MIT-licensed,
PyUSB-based low-level library for EZCAD2 LMC controllers. It has controller,
connection, spooler and job abstractions and was explicitly designed for
embedding. That makes its package boundary attractive.

The drawback is age: the latest package found on
[PyPI](https://pypi.org/project/galvoplotter/) is the beta `0.2.0` release
from 2023, while BalorMK has continued evolving and explicitly contains MOPA
support. It should be used to understand the smallest viable API, not pinned
blindly as the production backend. A good upstream outcome could be helping
extract today's BalorMK controller into a maintained standalone package.

## Finding 2: Rayforge already is most of the desired application

[Rayforge](https://github.com/barebaric/rayforge) is an MIT-licensed,
cross-platform Python/GTK4 desktop application. Current functionality includes
a 2D editor, layers, material recipes, projects, SVG/DXF/PDF/raster import,
3D toolpath simulation, rotary support, cameras, pre-flight bounds/no-go-zone
checks, and packaged Windows builds. It already imports LightBurn projects and
device profiles.

Source inspection found particularly relevant implementation details:

- `.lbrn`/`.lbrn2` parsing covers shapes, paths, transforms, images and text
  backup paths;
- imported LightBurn cut settings are mapped into Rayforge workflows,
  including speed, power, passes, offsets, raster interval/angle and dither;
- `.lbdev` device profiles have a separate importer;
- laser steps and recipes serialize `frequency` in Hz; the laser-step UI
  describes `pulse_width` as nanoseconds. Later LightBurn 2.1.03 evidence binds
  the JPT import seam to raw Hz/display kHz and direct ns without changing the
  separate Ruida encoder question;
- the neutral `Ops` command set contains frequency and pulse-width commands;
- binary rather than G-code drivers are supported through an `OpsEncoder`;
- driver state, cancel/hold, discovery, machine profiles, simulator and
  maturity warnings already exist.

Rayforge's [driver guide](https://rayforge.org/docs/developer/driver/) defines
separate encoder, pipeline, transport and asynchronous driver roles. Its
[addon guide](https://rayforge.org/docs/developer/addon-overview/) explicitly
describes third-party machine drivers loaded without modifying the core. This
is almost the exact integration seam the project needs.

### Why this is preferable to a new app

A new desktop app would immediately recreate document serialization,
selection and transforms, units, importers, undo/redo, toolpath generation,
preview, material management, settings UI, packaging and update work. None of
those areas differentiates The Pirate Ray. The differentiating work is:

- a trustworthy JCZ adapter;
- JPT/lens-specific profile validation;
- galvo/MOPA safety policy;
- reproducible offline and hardware tests;
- workshop-focused defaults and documentation.

Keeping that work in an addon or upstream contribution makes the result useful
outside Makerspace Næstved and reduces the permanent maintenance burden.

### Rayforge integration risks

- The public addon guide demonstrates `machine_manager.register(...)`, while
  the inspected current source exposes a module-level `register_driver(...)`
  registry and did not reveal the documented machine registration call in the
  loaded paths. This may be documentation drift or an incomplete checkout.
  A tiny addon-loading test must prove the supported seam before architecture
  is accepted.
- Rayforge currently models much of its world around moving-head/G-code
  machines. Galvo framing, list buffering, correction files, timing delays,
  infinite “red light” preview and coordinate transforms need an explicit fit
  analysis.
- GTK4/Libadwaita is a substantial Windows packaging dependency stack, even
  though the project publishes Windows builds.
- The addon API is evolving. The manifest API and Rayforge/raygeo versions
  must be pinned and compatibility tested.
- Existing frequency and pulse-width fields are necessary but not sufficient:
  their units, zero/default semantics and allowed ranges must be checked
  end-to-end against the JPT source.

## Finding 3: do not build a geometry engine

[raygeo](https://github.com/barebaric/raygeo) is Rayforge's MIT-licensed Rust
and PyO3 geometry library with Windows/macOS/Linux wheels. It already supplies
path construction, arcs and Beziers, boolean and offset operations, fitting,
nesting, raster modulation, smoothing, linearization, geometric queries and
cylindrical transforms.

If Rayforge is adopted, use raygeo through Rayforge's model rather than
inventing a competing neutral geometry model. If Rayforge is rejected after
the spike, raygeo remains a strong direct dependency candidate, subject to API
stability and binary-wheel review.

## Finding 4: LightBurn migration is mostly an extension problem

Rayforge's existing LightBurn import removes the need to create a general
`.lbrn2` parser. The private known-working fixture matrix now identifies the
vector MOPA fields and units; the focused remaining work is packaged GUI
verification plus unsupported image and omitted-value behavior.

Likely gaps to test include:

- MOPA pulse width and frequency on every operation type;
- hatch modes, cross-hatch order and galvo-specific timing;
- device origin, field size and lens correction references;
- text fidelity when only a `BackupPath` is portable;
- layer ordering and mark-count semantics;
- LightBurn units and default/omitted value behavior.

The small TypeScript project [lbrnts](https://github.com/tscircuit/lbrnts)
supports parsing and writing LightBurn files and may be useful as an
independent behavioral comparison if round-trip export becomes important. It
does not justify adding a JavaScript runtime to the initial Python stack.

## Finding 5: Windows USB driver handling is a product requirement

BalorMK uses PyUSB/libusb. The installed EZCAD/LightBurn stack normally uses a
Windows vendor driver. Only one driver can own the relevant interface, so a
Zadig/libusb change may make the current production software stop seeing the
laser until it is reverted.

[meerk40t-pnputil](https://github.com/meerk40t/meerk40t-pnputil) is an
MIT-licensed proof of concept for switching Windows drivers. It is evidence
that reversible handling is possible, not production code we should silently
run. Before live testing, record the current driver package and create a
documented rollback procedure. Driver changes require explicit operator
approval and are outside the current offline phase.

## Future CO2 machines

Do not infer the Eduard or Bodor controller from the machine brand. Physically
identify controller model, connection type and firmware first.

If either machine uses Ruida, Rayforge already integrates the MIT-licensed
[ruida-pa](https://github.com/StevenIsaacs/ruida-pa) project and MeerK40t also
has Ruida support. That could make a shared Rayforge platform even more
valuable. If the machines use another controller family, repeat this landscape
and evidence process for that controller.

## Proprietary vendor SDKs are not the main path

EZCAD/MarkEzd SDK wrappers found in public repositories usually expose an open
wrapper around a proprietary `MarkEzd.dll`. That may provide useful names and
semantic clues, but it does not give us an auditable, cross-platform, freely
redistributable controller stack. It also retains the vendor driver and
hardware-lock assumptions.

The public product should therefore not load or redistribute a copied vendor
DLL. Any future use of official SDK documentation must be separately reviewed
for license, provenance and clean-room implications.

## Recommended architecture to prove

```text
Rayforge UI / documents / imports / recipes / simulation
                         |
                     raygeo Ops
                         |
             ThePirateRay JCZ adapter boundary
                /                         \
     deterministic fake              Balor transport
       and trace sink          (adapted from current BalorMK)
                                        |
                              explicit hardware gate
                                        |
                              JCZ 9588:9899 controller
```

The adapter must keep protocol output separate from transport. The same
synthetic job must be encodable into a deterministic trace without importing
PyUSB or discovering hardware. Hardware transport is an optional component and
is disabled by default in development and CI.

The first public build should not expose arbitrary raw controller commands.
Machine identity, correction/profile hash, lens, field size and source type
must agree before a hardware job can be armed.

## Reuse boundaries

### Reuse directly or contribute upstream

- Rayforge application, document, import, recipe, simulation and packaging;
- raygeo through Rayforge;
- Rayforge's `Ops`, binary encoder and asynchronous driver contracts;
- BalorMK command constants, packet semantics and mock-derived test vectors,
  after exact-license and attribution review;
- PyUSB only behind the real hardware transport.

### Rewrite narrowly for fit and safety

- the Rayforge-to-Balor operation encoder;
- a small controller facade that does not depend on MeerK40t kernel services;
- validation of JPT frequency/pulse-width ranges and units;
- correction/profile loading with provenance and fail-closed matching;
- structured, redacted diagnostics;
- a hardware capability gate and test protocol.

### Do not build now

- a new canvas or general CAD system;
- a new SVG/DXF/PDF importer suite;
- a new geometry/boolean/hatch kernel;
- a new material database UI;
- a general LightBurn parser;
- a blank-sheet JCZ protocol implementation;
- an auto-installer that changes Windows USB drivers;
- support for all three lasers before their controllers are identified.

## Offline proof plan

No USB access, framing or emission is needed for these experiments.

### Spike A — stock MeerK40t

1. Pin stable MeerK40t and the inspected source commit.
2. Run only its mock controller in an isolated configuration directory.
3. Create a synthetic square plus hatch job with explicit power, speed,
   frequency and pulse width.
4. Save the mock command stream as a test artifact with upstream version.
5. Assess whether the existing app already meets enough workshop needs to
   prefer a small fork/contribution over a second frontend.

Go if mock execution is deterministic, the MOPA parameters survive the full
pipeline, and the UI/product gap is acceptable. Stop and document any path
that tries to enumerate real USB devices in mock mode.

### Spike B — Rayforge addon seam

1. Pin Rayforge at the inspected commit.
2. Create the smallest external addon that registers a no-device binary
   driver.
3. Prove install, discovery, enable/disable, project reload and packaging on
   Windows.
4. Resolve the documented `machine_manager.register` versus source-level
   `register_driver` discrepancy with a test or upstream clarification.

Go if an external addon can own a binary driver without patching core. If a
small upstream patch is needed and maintainers accept the design, that is also
a go. A permanent private fork is less attractive but still cheaper than a new
application.

### Spike C — golden command equivalence

1. Construct a tiny Rayforge `Ops` job: move, line, power, speed, frequency,
   pulse width, delay and end.
2. Encode it through a new no-I/O JCZ encoder.
3. Generate the equivalent BalorMK mock trace.
4. Compare semantic commands and packet bytes, documenting intentional
   differences.
5. Add negative cases for wrong profile, out-of-field geometry, unsupported
   commands, invalid MOPA ranges and cancellation.

Go if the adapter can stay small and deterministic. Do not connect the USB
transport as part of this spike.

### Spike D — LightBurn fixture coverage

1. Use sanitized synthetic projects plus private known-working projects.
2. Inventory every source field and its imported representation.
3. Add public synthetic regression fixtures for missing galvo/MOPA concepts.
4. Propose upstream Rayforge importer changes where generally useful.

## Decision gates

Choose **stock/forked MeerK40t** when its existing workflow is acceptable and
the fastest usable deployment outweighs UI modernization.

Choose **Rayforge plus a JCZ addon** when Spike B proves the extension seam and
Spike C shows that galvo semantics fit without invasive core changes. This is
the current preferred long-term result.

Choose a **small standalone controller library** only if the controller code
cannot responsibly live in either upstream. It should still be usable by both
projects and should not grow a GUI.

Choose an **independent desktop app** only after written evidence that both
full applications fail concrete requirements that cannot reasonably be fixed
upstream. “We can build it ourselves” is not sufficient evidence.

## Version-pinned research snapshot

Source inspected locally in shallow sparse checkouts:

- MeerK40t: `d511944e08788e88077727f682957759884ff5ca`
  (2026-09-25)
- Rayforge: `c28918c87f8273dd1d244f5a057addc192807fa5`
  (2026-10-17)

The checkouts are an ignored research cache and are not vendored into this
repository. Any reused code must later be added deliberately with license,
copyright, source commit and modification notices.

## Source index

- [MeerK40t repository and project status](https://github.com/meerk40t/meerk40t)
- [BalorMK overview](https://github.com/meerk40t/meerk40t/blob/main/meerk40t/balormk/README.md)
- [BalorMK USB implementation](https://github.com/meerk40t/meerk40t/blob/main/meerk40t/balormk/usb_connection.py)
- [galvoplotter repository](https://github.com/meerk40t/galvoplotter)
- [galvoplotter package](https://pypi.org/project/galvoplotter/)
- [Rayforge repository](https://github.com/barebaric/rayforge)
- [Rayforge driver guide](https://rayforge.org/docs/developer/driver/)
- [Rayforge addon guide](https://rayforge.org/docs/developer/addon-overview/)
- [raygeo repository](https://github.com/barebaric/raygeo)
- [ruida-pa repository](https://github.com/StevenIsaacs/ruida-pa)
- [meerk40t-pnputil](https://github.com/meerk40t/meerk40t-pnputil)
- [VisiCut](https://visicut.org/)
- [LaserWeb4](https://github.com/LaserWeb/LaserWeb4)
- [lbrnts](https://github.com/tscircuit/lbrnts)
- [USB-LMC-V1 replacement project](https://github.com/Meliadolin/usblm-v1-meerk40t)
- [Official LightBurn galvo documentation](https://docs.lightburnsoftware.com/latest/Collections/LightBurnForGalvos/)
- [Official EZCAD SDK product page](https://www.ezcad.com/products/ezcad-sdk/page/24/)

