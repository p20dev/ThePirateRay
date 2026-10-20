# MOPA workbench UX requirements

- Status: Working product contract
- Recreated: 2026-10-20
- Scope: desktop application workflow; hardware-free through M1

## Purpose

The Pirate Ray should give a casual makerspace user a clear path from opening
a design to a validated job. It should feel capable without presenting machine
selection, controller configuration, lens data, or every galvo parameter as
the first decision.

This document records product behavior, not an application architecture. The
current reuse direction remains Rayforge plus the narrowest practical JCZ
integration. A prototype or mockup can illustrate these requirements, but it
does not become a second implementation and does not prove machine behavior.

This file was recreated because the UX document named by the repository
handoff was absent from the active checkout and had no Git history, branch, or
stash copy. The requirements below come from that handoff, the project charter
and roadmap, and the evidence-backed
[LightBurn-to-Rayforge capability map](../research/lightburn-rayforge-ux-capability-map.md).

## Product principles

1. **Start with the design.** Opening or importing artwork is the normal first
   action. Choosing a controller, machine, or lens is an administrator task.
2. **Keep the canvas stable.** Panels may collapse and themes may change, but
   the work-area geometry, artwork position, and semantic layer colors do not.
3. **Show the next useful decision.** Common layer settings are immediately
   available; specialized settings appear only when the user's disclosure
   level, operation, and active profile make them relevant.
4. **Preview before job control.** The planned geometry, enabled operations,
   ordering, hatch, field boundary, and warnings are inspectable before any
   physical action.
5. **Make uncertainty visible.** Unknown units, profile identity, correction,
   lens compatibility, or parameter limits block encoding or execution rather
   than receiving guessed defaults.
6. **Reuse instead of cloning.** Extend existing Rayforge concepts and UI
   seams where possible. Do not recreate a canvas, geometry engine, material
   database, or general LightBurn parser.
7. **Separate preparation from hardware.** Offline editing, preview, saving,
   and simulation must remain useful when no controller backend is installed.

## Primary maker flow

The default flow is:

1. open or import a design;
2. inspect and arrange it on the machine-sized work area;
3. select an object or layer;
4. assign or edit the applicable operation settings;
5. optionally apply a compatible material recipe;
6. preview the planned path and operation order;
7. resolve preflight errors and review warnings;
8. save or export the portable project;
9. only when a separately supported hardware profile is active, enter the
   gated framing and job-control flow.

The application must not force machine, controller, lens, or connection
selection into steps 1–6 when a configured default profile already exists.

## Workspace layout

The central canvas is the stable visual anchor. It represents the configured
work area and shows artwork, selection, field boundaries, planned paths, and
non-destructive overlays.

The right side contains independently collapsible panels in this order:

1. **Layers** — operation list, color, order, selection, visibility and output
   state;
2. **Settings** — values applicable to the selected operation and current
   disclosure level;
3. **Material Library** — compatible recipes and their provenance;
4. **Framing** — offline framing preview initially, physical framing only when
   explicitly supported and gated.

**Job Control** remains fixed at the bottom rather than disappearing with the
other panels. In the offline product it shows simulation/no-device state and
must not imply that a controller is connected.

Collapsing panels may enlarge the available canvas viewport, but it must not
change document coordinates, work-area dimensions, geometry, layer colors, or
the meaning of the current selection.

## Layers

The layer list stays visible by default alongside the settings panel. Each
entry should expose, at minimum:

- semantic color and user-editable name;
- operation or mode;
- order;
- a visibility state for the canvas;
- a separate output-enabled state for preview and job planning;
- concise values for the most important applicable settings.

Visibility and output are independent. Hiding a layer must not silently
disable it, and disabling output must be visually distinct from hiding it.
Reordering operations must immediately affect preview order without moving
the source geometry.

The first supported operation types remain an open product decision. Until
that decision is reviewed, the UI must not imply support beyond operation
types already preserved end-to-end by tests.

## Settings and disclosure levels

The settings panel has three disclosure levels:

- **Beginner** — the smallest set needed for an ordinary, already-configured
  job;
- **Advanced** — additional operation controls for a trained maker;
- **Expert** — specialized galvo, timing, diagnostic, and compatibility
  details supported by the active profile.

Changing level reveals or hides rows; it must not replace the canvas, move the
panels into a different workflow, or reset values. Unsupported settings remain
absent rather than disabled with invented defaults.

Power, speed, passes, frequency, Q-pulse width, interval, hatch, scan angle,
and timing are candidate fields, not a promise that every operation exposes
all of them. Frequency and Q-pulse width require explicit units. Machine- and
source-specific ranges require verified profile evidence.

Exactly which fields belong in Beginner mode remains an open product decision.
The initial choice should be made from representative workshop jobs, not by
copying every field from LightBurn.

## Material library

Recipes are optional accelerators, not a mandatory wizard. A user can ignore
the library and edit job values directly.

A recipe can describe:

- material;
- thickness when relevant;
- operation or recipe variant, such as engraving or cutting;
- process settings with explicit units;
- source and validation status;
- compatible machine, source, lens, correction profile, and software schema;
- notes and revision information.

The library supports multiple collections:

- makerspace-shared;
- personal;
- optionally project-specific.

Personal collections are portable through import/export and require no cloud
account. Applying an incompatible or unverified recipe must produce an
explanation and must not silently override the active machine profile.

The evidence required for the label “makerspace-approved” remains an open
product decision. Exported LightBurn values and observed recipes are not, by
themselves, certified hardware limits or approved settings.

## Preview and preflight

Preview must work without a controller. It should show, where supported:

- field boundary and geometry;
- enabled versus disabled output layers;
- operation order;
- hatch or fill representation;
- an approximate path;
- warnings and blocking validation failures;
- estimated behavior only when the estimate's basis is explicit.

Preflight blocks at least:

- geometry outside the supported field;
- machine, source, lens, or correction-profile mismatch;
- unknown or ambiguous units;
- unsupported operations;
- invalid parameter values;
- incomplete MOPA import data required by the selected backend.

A warning must not be presented as a passed safety check. An approximate path
or time estimate must be labelled as approximate.

## Framing

Framing has two distinct meanings:

1. **Canvas framing preview** — an offline overlay showing the proposed bounds
   or contour. This is safe to provide during M1 when clearly labelled as a
   simulation.
2. **Physical galvo framing** — controller behavior that may move galvos or
   activate a guide source. This remains unavailable until a separately
   reviewed protocol authorizes the exact operation and safety conditions.

The UI must never present simulated framing as proof that the physical machine
has framed the job. `RequireFrameBeforeStart` is a profile observation and a
future policy input, not authorization to issue a framing command.

## Job control and states

Job Control remains visually separate from design editing. The interface must
make its current execution boundary explicit, for example:

- **Offline** — edit, save, validate and preview only;
- **Simulated** — run against a deterministic fake/no-device driver;
- **Blocked** — a named profile, validation, recovery, or evidence condition
  prevents execution;
- **Hardware unavailable** — no reviewed production backend is reachable;
- future hardware states only after their protocols are reviewed.

The no-device workflow may expose Start Simulation, Hold, Resume, Cancel and
Recover when backed by deterministic tests. A physical Start action remains
absent or disabled while the production controller backend is gated.

Cancellation must clear pending work, and restart must require explicit
recovery when that is the driver contract. The UI must not translate a failed
or cancelled job into an apparently ready state without explanation.

## Machine and administrator settings

Machine, controller, source, lens, correction and connection settings belong
in an advanced administrator area. They must remain inspectable because they
are safety-relevant, but they are not routine choices at job start.

The normal workspace may show a concise active-profile summary and any
compatibility problem. Changing the lens or correction profile is an explicit
configuration action. The application must not offer a guessed replacement
when required profile evidence is missing.

## Themes and visual semantics

The default direction is clear and light. A dark theme may be provided, but it
must preserve:

- canvas geometry and scale;
- artwork position and appearance sufficiently for comparison;
- semantic layer colors;
- panel placement and collapse state;
- selection, warning, blocked, offline and simulated meanings.

Theme changes must not be used to hide safety or provenance information.

## Diagnostics and wording

Messages should state:

1. what is wrong or unknown;
2. why the action is blocked or limited;
3. which evidence or user action can resolve it;
4. whether the result is offline, simulated, inferred, or physically verified.

Avoid language that implies communication with a controller when only a model,
preview, mock transport, or UI prototype is active.

## Deferred capabilities

The following are not required for the first useful offline product unless a
representative workshop job proves otherwise:

- physical framing or marking;
- automatic Windows USB-driver switching;
- arbitrary raw controller commands;
- all LightBurn operation modes;
- sub-layers, cleanup passes, wobble, 3D sliced images, and specialized galvo
  timing controls;
- a production material-test run flow;
- cloud accounts or cloud-only recipe storage;
- simultaneous support for every makerspace laser.

## Offline acceptance scenarios

The UX direction is ready for implementation decisions when a packaged
no-device desktop checkpoint can demonstrate:

1. opening representative synthetic geometry directly into the workbench;
2. selecting, naming, coloring and ordering layers;
3. independent visibility and output state, or a documented upstream gap;
4. editing supported settings with visible units and capability gates;
5. applying or declining a compatible synthetic material recipe;
6. previewing enabled geometry, hatch/order and field violations;
7. saving and reopening without losing supported settings;
8. starting a simulation, holding, resuming, cancelling and explicitly
   recovering against the no-device driver;
9. keeping controller discovery and transport unreachable;
10. preserving canvas geometry and layer semantics across theme and disclosure
    changes.

Passing these scenarios does not authorize physical framing or marking.

## Open product decisions

Kaz should decide these when a concrete implementation needs them:

1. Which operation types are included in the first useful release?
2. Which exact fields are visible in Beginner mode for each operation?
3. What evidence and review process makes a shared recipe
   “makerspace-approved”?

All other choices should follow the casual-maker defaults above unless new
evidence reveals a conflict.

## Traceability

- [Project charter](../project-charter.md)
- [Product and research roadmap](../roadmap.md)
- [LightBurn-to-Rayforge UX capability map](../research/lightburn-rayforge-ux-capability-map.md)
- [Graphical workflow model spike](../research/rayforge-graphical-workflow-spike.md)
- [Windows GUI preflight](../research/rayforge-windows-gui-preflight.md)
- [Proposed reuse decision](../adr/0002-reuse-rayforge-and-balormk.md)

