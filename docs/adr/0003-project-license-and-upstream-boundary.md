# ADR 0003: Project license and upstream attribution boundary

- Status: Proposed
- Date: 2026-10-21

## Context

The Pirate Ray is intended to become open source, but the repository currently
has no project license. Rayforge and MeerK40t are both pinned under MIT terms,
and the leading architecture is a Rayforge addon informed by BalorMK behavior.
ADR 0002 forbids copied upstream source until license compatibility and exact
attribution are recorded.

## Proposed decision

1. License original The Pirate Ray code under MIT.
2. Keep exact upstream repositories, revisions, license notices and contract
   hashes in the public repository.
3. Include applicable notices in every source or binary distribution set.
4. Treat Rayforge's documented addon API as the preferred host boundary.
5. Isolate any unavoidable internal Rayforge registry access behind one
   compatibility adapter and remove it when a supported upstream API exists.
6. Use BalorMK as a pinned behavioral oracle until a separately reviewed
   decision authorizes adaptation of specific MIT-licensed implementation
   files.

## Why MIT is proposed

MIT matches both principal upstreams, is compatible with contributing the
addon upstream, and imposes a small, auditable notice obligation. It does not
solve safety, warranty, trademark or third-party-data questions; those remain
separate project responsibilities.

## Consequences

- A root project `LICENSE` can be added only after Kaz accepts this ADR.
- Source provenance becomes part of code review and release acceptance.
- A Windows installer may not be published alone; its verified license
  sidecar and checkpoint manifest are part of the distribution set.
- BalorMK code adaptation must identify source files and preserve the
  MeerK40t notice.
- A Rayforge upgrade fails closed when a pinned license, source hash or
  required symbol changes.

## Alternatives considered

- **Remain unlicensed:** acceptable for research snapshots but blocks the
  intended open-source product and upstream code adaptation.
- **Apache-2.0:** provides an explicit patent grant but adds notice and license
  complexity without a current upstream requirement.
- **GPL-family license:** may be appropriate for stronger reciprocity, but it
  is a larger product-policy decision and is not required by the current MIT
  dependencies.

## Acceptance

Kaz must explicitly choose the project license. Until then this ADR remains
Proposed, the README's no-license statement remains authoritative, and no root
`LICENSE` file is created.

The compatibility-adapter part of item 5 is implemented for the offline addon
and fails closed outside Rayforge addon API 23. This implementation evidence
does not accept this ADR or select the project license.

See the
[upstream contract and license audit](../research/upstream-contract-and-license-audit.md)
for the evidence and API-stability assessment.
