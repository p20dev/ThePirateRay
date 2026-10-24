# LightBurn-to-Rayforge UX capability map

- Date: 2026-10-20
- Scope: desktop workflow and offline capability fit
- Rayforge evidence baseline: commit `c28918c87f8273dd1d244f5a057addc192807fa5`
- Hardware access: none

## Purpose

This note translates the useful parts of LightBurn's documented workflow into
testable requirements for The Pirate Ray and compares them with the evidence
already collected for Rayforge. It is a product-gap analysis, not permission
to copy LightBurn code, text, graphics, assets, or proprietary behavior.

The target is an approachable galvo job workbench. A normal maker should begin
by opening a design, working on the canvas, selecting a layer, adjusting the
applicable process settings, previewing the result, and optionally applying a
material recipe. Machine, controller, lens, correction, and driver selection
belong in an advanced or administrator path after initial configuration.

The previously referenced `docs/design/mopa-workbench-ux.md` was absent from
the active repository checkout and had no Git history, branch, or stash copy.
It has now been recreated as a traceable working product contract from the
repository handoff, charter, roadmap, and evidence cited in this note. The
missing HTML prototype was not treated as application evidence.

## Evidence labels

- **Proven offline**: exercised in the pinned code path with deterministic
  output and no transport.
- **Source-inspected**: found in the pinned upstream source, but not exercised
  in the packaged Windows application.
- **Product requirement**: agreed behavior that still needs an implementation
  or interaction test.
- **Gated**: must remain unavailable until named evidence or safety conditions
  are satisfied.
- **Deferred**: useful LightBurn behavior, but outside the first useful
  product.

## Reference workflow

LightBurn's documentation provides a useful interaction vocabulary:

1. the workspace represents the machine work area and contains arranged
   artwork;
2. colors/layers bind artwork to ordered operations;
3. the layer list controls visibility, output, order, mode, and abbreviated
   process settings;
4. the full settings editor reveals controls according to machine type and
   operation mode;
5. preview is used to inspect the planned output before job control;
6. material-library entries reapply grouped process settings;
7. framing is a separate physical alignment action, not merely another canvas
   view;
8. advanced galvo controls include frequency, Q-pulse width, sub-layers,
   timing, wobble, angle changes, and cleanup passes.

This vocabulary is useful, but The Pirate Ray should implement only the subset
required by real workshop jobs and supported by evidence.

## Capability map

| Maker need | LightBurn reference behavior | Current Rayforge evidence | Classification | Narrow next step |
| --- | --- | --- | --- | --- |
| Open a design directly into a work area | Artwork is imported or created on a machine-sized workspace | Rayforge has a desktop editor, projects, geometry and broad import support; the local spike proved a preview artifact from synthetic geometry | Source-inspected; preview proven offline | Exercise open/import in the packaged no-device Windows checkpoint |
| See and select operations as layers | The layer list uses color to identify operations and keeps order visible | Rayforge has layers and workflow steps, but the desired persistent layer/settings arrangement has not been interaction-tested | Source-inspected plus product requirement | Verify selection, ordering, naming and color semantics without creating a parallel layer model |
| Hide geometry without disabling output, and disable output without hiding geometry | LightBurn separates `Show` and `Output` | Rayforge separates `Layer.visible` canvas state from `Step.visible` job participation and serializes both; output is operation-level rather than a layer-level control | Proven offline at model/source level; aggregate UI untested | Add or propose a tri-state layer Output control over existing step states, then verify it in the packaged no-device GUI |
| Edit common settings quickly | The layer list exposes mode, speed, power, passes and applicable galvo fields | Rayforge's generated laser-step settings expose power, speed, frequency and pulse width; serialization is proven offline | Proven offline at the model/UI-contract level | Confirm editing and save/reload in the packaged no-device GUI |
| Reveal complexity progressively | LightBurn Beginner Mode hides some advanced settings; PirateRay calls for Beginner, Advanced and Expert levels without moving the canvas | Rayforge capability sections can hide machine-dependent fields, but three user-facing disclosure levels are not proven | Product requirement | Define the smallest beginner field set from real job needs before adding controls |
| Preserve MOPA units and values | Galvo frequency is presented in kHz and Q-pulse width in ns | Rayforge's workflow uses Hz and ns and preserves both; LightBurn project import does not yet map frequency or pulse width into workflow settings | Partly proven; import gated | Keep explicit conversion at the import boundary and wait for a known-working `.lbrn2` before mapping `QPulseWidth` |
| Apply a reusable material recipe | LightBurn libraries organize presets by material, thickness and description and apply/link them to layers | Rayforge recipes already match machine, head, material, thickness and step type and preserve Hz/ns settings; the external addon now validates versioned provenance plus exact source/lens/correction compatibility while withholding hardware authorization | Proven offline at model/source level; approval policy and portable collections remain | Integrate the validated metadata into recipe selection before changing the existing recipe UI |
| Inspect planned behavior before any run | LightBurn Preview reflects enabled layers and planned order | Rayforge produced a populated `JobArtifact` with Ops, path length and no machine code | Proven offline; human interaction untested | Verify layer filtering, order, hatch and warnings in the packaged no-device GUI |
| Reject a visibly invalid job | Preview/preflight should reveal unintended output; the target product must reject profile mismatch and out-of-field geometry | Existing JCZ negative tests reject profile mismatch, out-of-field geometry, invalid values and unsupported Ops | Proven offline at encoder boundary | Surface these failures as understandable preflight messages without weakening the fail-closed gate |
| Keep machine and lens selection out of the normal start flow | LightBurn device settings are separate from ordinary layer work | Rayforge has machine profiles and capability-gated settings; the desired administrator-oriented placement is not interaction-tested | Product requirement | Verify default-profile startup and move profile/lens changes behind an advanced path if upstream behavior requires it |
| Save and reopen without losing job intent | Project files retain artwork and layer settings | The synthetic step retained power, speed, frequency and pulse width through serialization/deserialization; full project interaction is untested | Partly proven offline | Add save/reload to the packaged no-device checklist |
| Frame safely | Galvo framing is a distinct physical action used to align a job | No physical framing is authorized; galvo framing semantics and Rayforge fit remain unproven | Gated | Keep only an explicitly labelled on-canvas simulation until a reviewed hardware protocol authorizes exact behavior |
| Start, hold, cancel and recover | Job control is distinct from editing and preview | The no-device driver proves hold/resume, cancellation, cleared buffers and explicit recovery | Proven offline at driver level; GUI untested | Exercise the controls only against the no-device driver in the packaged GUI |
| Run a material test | LightBurn generates a grid varying two applicable process parameters | No production Rayforge/PirateRay material-test flow has been proven; a UI mock is not machine functionality | Deferred | Retain as a future offline planner feature; do not expose a physical run action |
| Use sub-layers, cleanup passes, wobble and per-layer galvo timings | LightBurn exposes these as advanced, mode- and device-specific settings | Hatch planning and basic MOPA operations are proven, but these specialized semantics are not covered end-to-end | Deferred | Select only from demonstrated workshop needs after the basic JPT vertical slice closes |
| Use identical geometry and semantic colors in light and dark themes | PirateRay requires theme changes not to reshape the work area | No current packaged-app evidence | Product requirement | Treat theme as presentation only and add a later visual regression check |

## What should be reused

The evidence supports reusing Rayforge's existing:

- canvas, document, layer, project and geometry concepts;
- import pipeline rather than creating a general LightBurn parser;
- workflow steps and generated capability-aware settings UI;
- material-recipe foundation;
- preview-facing `JobArtifact`, simulation and preflight boundaries;
- machine-profile, addon, encoder and asynchronous driver seams;
- project serialization and packaged desktop direction.

The PirateRay-specific work should remain narrow:

- JCZ profile recognition and provenance;
- evidence-backed LightBurn MOPA import conversion;
- JPT/lens/correction compatibility validation;
- fail-closed preflight and clear diagnostics;
- a casual-maker presentation of existing capabilities;
- a physically gated Balor transport after a separate reviewed protocol.

## Gaps that must not be papered over

1. Three known-working private galvo projects establish project-level
   `QPulseWidth` serialization. Omission/default behavior still requires an
   explicit policy before promotion to executable output.
2. The current Windows environment has not launched the pinned Rayforge GTK
   application; the headless UI contract is not a human interaction test.
3. `RequireFrameBeforeStart` is observed in a LightBurn device export and
   preserved by the narrow addon seam, but it is not proof of safe physical
   framing behavior.
4. Machine-specific frequency, pulse-width, timing and correction limits are
   not established by LightBurn documentation or exported recipe values.
5. PirateRay recipe metadata now supplies fail-closed provenance, approval and
   machine/lens/correction compatibility checks; packaged UI interaction is
   still part of the M1 desktop checklist.
6. The HTML prototype named by the handoff is absent from the active checkout;
   its historical controls must not be treated as implemented capability.

## Recommended implementation order

### P0 — recover the product contract (completed 2026-10-20)

- `docs/design/mopa-workbench-ux.md` has been recreated from traceable project
  requirements and this capability analysis.
- Resolve the open product decisions only when they block a concrete task:
  first supported operation types, beginner-visible fields, and the evidence
  required for a makerspace-approved recipe.

### P1 — complete the no-device desktop checkpoint

- Use a reviewed Windows GTK runtime for the pinned Rayforge checkout.
- Load the synthetic JCZ-capable profile with no discovery or transport.
- Open geometry, select a layer, edit power/speed/frequency/pulse width,
  preview, save, reload, hold, cancel and recover.
- Record the actual placement and behavior of layers, settings, recipes,
  preflight and job controls.

### P2 — close only evidenced gaps

- Propose small upstream or addon changes for independent Show/Output state,
  casual-maker disclosure and safety diagnostics only when P1 proves they are
  absent.
- Extend material recipes with provenance and compatibility metadata using the
  existing model where possible.
- Add LightBurn MOPA field conversion only after private project evidence
  establishes serialization and units.

### P3 — defer specialized and physical behavior

- Keep material-test execution, physical framing, controller status and laser
  start outside the offline product.
- Add sub-layers, cleanup passes, wobble and timing controls only in response
  to supported workshop jobs and end-to-end tests.

## Decision impact

This analysis finds no UX requirement that currently justifies a separate
desktop application. Rayforge covers the expensive general-product foundation,
while the identified gaps are narrow enough to test as addon or upstream
extensions. ADR 0002 should remain **Proposed** until the packaged no-device
interaction checkpoint and the LightBurn MOPA fixture gate are complete.

No USB enumeration, controller command, galvo movement, physical framing,
arming, or laser output was performed for this analysis.

## Sources

Project evidence:

- [Open-source landscape](open-source-landscape.md)
- [Graphical workflow model spike](rayforge-graphical-workflow-spike.md)
- [Layer visibility and output spike](rayforge-layer-model-spike.md)
- [Material-recipe model spike](rayforge-recipe-model-spike.md)
- [Windows GUI preflight](rayforge-windows-gui-preflight.md)
- [Synthetic LightBurn MOPA import spike](rayforge-lightburn-mopa-import-spike.md)
- [Synthetic LightBurn JCZ device-import spike](rayforge-lightburn-device-import-spike.md)
- [Rayforge JCZ negative cases](rayforge-jcz-negative-cases.md)
- [Rayforge cancellation and recovery spike](rayforge-jcz-cancel-recovery-spike.md)
- [ADR 0002](../adr/0002-reuse-rayforge-and-balormk.md)

Official LightBurn behavior references:

- [Workspace / Edit Window](https://docs.lightburnsoftware.com/latest/Reference/UI/Workspace/)
- [Cuts / Layers Window](https://docs.lightburnsoftware.com/latest/Reference/CutsLayersWindow/)
- [Galvo-Specific Cut Settings](https://docs.lightburnsoftware.com/latest/Reference/CutSettingsEditor/GalvoSpecificCutSettings/)
- [Sub-Layers](https://docs.lightburnsoftware.com/latest/Reference/CutSettingsEditor/SubLayers/)
- [Previewing](https://docs.lightburnsoftware.com/latest/GetStarted/PreviewBeginner/)
- [Material Test](https://docs.lightburnsoftware.com/latest/GetStarted/FirstMaterialTest/)
- [Galvo Ports and Laser Settings](https://docs.lightburnsoftware.com/latest/Reference/DeviceSettings/GalvoPorts/)

