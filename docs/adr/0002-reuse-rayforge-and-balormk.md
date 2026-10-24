# ADR 0002: Prove reuse of Rayforge and BalorMK before building an app

- Status: Accepted
- Date: 2026-10-17
- Accepted: 2026-10-24

## Context

The initial roadmap assumed that The Pirate Ray would define its own offline
application core and would later research the JCZ protocol. Ecosystem research
found two MIT-licensed projects that substantially change that assumption:

- Rayforge already implements most of the desired cross-platform desktop
  product and has an addon/driver architecture, LightBurn import, simulation,
  material recipes, pre-flight validation, and MOPA-relevant operation fields.
- MeerK40t's BalorMK already implements the EZCAD2-compatible JCZ controller
  protocol, MOPA pulse width, a mock connection, and the exact USB VID/PID
  independently observed in our installer evidence.

Creating another editor, geometry stack and controller implementation would
duplicate large, safety-relevant bodies of work and permanently increase the
maintenance burden.

## Decision

Do not begin independent desktop product implementation. First run three
offline, version-pinned proofs:

1. evaluate stock MeerK40t with BalorMK's mock controller as the shortest
   route to a usable product;
2. prove that an external Rayforge addon can register a binary no-device
   driver and survive packaging on Windows;
3. translate one synthetic Rayforge operation stream to JCZ/Balor commands and
   compare it with a BalorMK mock trace.

The proofs pass at the offline architecture boundary. Build the product as a
Rayforge JCZ addon and retain pinned BalorMK behavior as the controller-level
oracle. Adapt only the narrowest necessary implementation after licensing and
attribution allow it. Packaged Windows interaction remains an M1 release gate,
not a reason to defer the host-architecture decision.

An independent desktop application requires a later ADR showing concrete,
tested gaps in both existing applications.

No copied upstream source enters this repository until the project license is
chosen and exact commit-level copyright/license attribution is recorded.

## Proof obligations

- All experiments are mock/no-I/O and cannot enumerate or open USB devices.
- Frequency and pulse-width units and defaults survive end-to-end.
- Galvo coordinates, correction, timing, list buffering, framing, cancel and
  status semantics fit the host abstraction or their required extensions are
  explicit.
- The adapter emits deterministic traces suitable for golden tests.
- Hardware transport is optional, disabled by default, and separated from
  encoding.
- Machine/source/lens/profile mismatch fails closed.
- Windows driver switching is excluded from automatic setup.
- Upstream contribution feasibility and API stability are assessed before a
  permanent fork is accepted.

## Consequences if accepted

- The project becomes an integration, validation and safety effort rather
  than a general CAD application effort.
- M1 is shortened to ecosystem validation and a JCZ vertical slice.
- Protocol capture is a fallback used only for unresolved behavior, not the
  first discovery method.
- The eventual public repository may primarily contain an addon, machine
  profiles, tests, fixtures and documentation.
- Project license selection becomes a prerequisite for adapted code. MIT is
  the simplest compatibility candidate, but this ADR does not select it.

## Rejection criteria

Reject the proposed Rayforge route if the addon seam cannot support a binary
galvo driver without maintaining invasive core changes, or if the operation
model loses required galvo/MOPA semantics. Reject the stock MeerK40t route if
the tested application cannot provide a safe and maintainable workshop
workflow. Record evidence before choosing a standalone app.

## Research basis

See [Open-source landscape](../research/open-source-landscape.md) for the
candidate matrix, inspected commits, risks and detailed spike plan.

Subsequent offline evidence:

- [MeerK40t mock MOPA spike](../research/meerk40t-mock-mopa-spike.md):
  deterministic controller-level frequency, pulse-width and square encoding;
- [MeerK40t hatch cut-plan and mock-spooler spike](../research/meerk40t-hatch-cutplan-spike.md):
  stock planning and spooling preserve a synthetic hatch and MOPA settings on
  forced mock transport;
- [Rayforge addon spike](../research/rayforge-addon-spike.md): external binary
  driver load and lifecycle are viable, with a documented registry API gap.
- [Rayforge-to-JCZ equivalence spike](../research/rayforge-jcz-equivalence-spike.md):
  the required MOPA and geometry semantics survive a real Rayforge `Ops`
  stream and match the pinned BalorMK mock trace.
- [JCZ negative cases](../research/rayforge-jcz-negative-cases.md): the encoder
  boundary rejects profile mismatch, invalid values, out-of-field geometry and
  unsupported commands without a transport.
- [JCZ 12-byte record spike](../research/rayforge-jcz-packet-spike.md): the
  external encoder deterministically packs controller-shaped command records
  matching the pinned BalorMK mock values, while retaining no transport.
- [Synthetic LightBurn MOPA import spike](../research/rayforge-lightburn-mopa-import-spike.md):
  geometry and common settings survive, but frequency is not mapped to the
  workflow and pulse-width representation still lacks fixture evidence.
- [Graphical workflow model spike](../research/rayforge-graphical-workflow-spike.md):
  Rayforge's generated settings contract exposes frequency and pulse width,
  preserves them through step serialization and supplies preview Ops without
  transport; packaged GTK interaction remains untested.
- [LightBurn-to-Rayforge UX capability map](../research/lightburn-rayforge-ux-capability-map.md):
  the casual-maker workflow maps mostly to existing Rayforge product seams;
  the remaining UX gaps are narrow, testable extensions rather than evidence
  for a separate desktop application.
- [Rayforge layer visibility and output spike](../research/rayforge-layer-model-spike.md):
  canvas visibility and job participation are already independent serialized
  states; LightBurn-style layer Output is a narrow aggregate UI concern, not a
  new pipeline or document-model requirement.
- [M1 no-device acceptance checkpoint](../research/m1-no-device-acceptance.md):
  the public regression suite and leak guard now form one transport-free gate
  over addon lifecycle, workflow, layers, recipes, encoding, negative cases,
  cancellation/recovery and synthetic imports. Packaged Windows interaction
  remains a release gate.
- [Upstream contract and license audit](../research/upstream-contract-and-license-audit.md):
  both pins and license notices are now machine-verifiable; the documented
  addon lifecycle is usable, but driver registration and cleanup still rely
  on an internal registry seam that should be replaced upstream.

Three operator-verified private projects subsequently established the
project-level `frequency` and `QPulseWidth` serialization needed to implement
the disabled-output import seam. Together, the evidence satisfies the host
architecture decision. It does not authorize hardware access or claim that the
packaged Windows interaction and import-promotion release gates have passed.

