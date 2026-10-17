# ADR 0002: Prove reuse of Rayforge and BalorMK before building an app

- Status: Proposed
- Date: 2026-10-17

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

## Proposed decision

Do not begin independent desktop product implementation. First run three
offline, version-pinned proofs:

1. evaluate stock MeerK40t with BalorMK's mock controller as the shortest
   route to a usable product;
2. prove that an external Rayforge addon can register a binary no-device
   driver and survive packaging on Windows;
3. translate one synthetic Rayforge operation stream to JCZ/Balor commands and
   compare it with a BalorMK mock trace.

If the proofs pass, prefer one of these outcomes in order:

1. use and contribute to MeerK40t if its full application is adequate;
2. implement and upstream a Rayforge JCZ/Balor addon, adapting the narrowest
   practical layer from BalorMK;
3. extract a small maintained controller library shared by either application.

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

