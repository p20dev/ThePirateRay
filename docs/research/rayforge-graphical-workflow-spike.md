# Rayforge graphical workflow model spike

- Date: 2026-10-19
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Transport: none
- Controller backend reachable: no

## Result

Pinned Rayforge exposes power, cut speed, frequency and pulse width through
the existing laser-step `VarSet` contract. The graphical laser settings page
builds its rows from that contract and places frequency and pulse width in a
capability-gated **Machine** section. The declared units are Hz and ns.

A synthetic contour step retained power `0.42`, cut speed `750`, frequency
`40000` and pulse width `100` through Rayforge's normal step serialization and
deserialization. The same values were placed in a transport-free `Ops` stream
and wrapped in Rayforge's preview-facing `JobArtifact`. Its preview contained
nine operations, a 40 mm declared path and no encoded machine code.

The deterministic result is stored in
`tests/fixtures/rayforge-graphical-workflow.json`.

## Interpretation

This is evidence that a JCZ addon can reuse Rayforge's existing workflow
model, settings-page machinery and preview artifact instead of creating a
parallel editor. It also confirms that MOPA frequency and pulse width can be
represented in the workflow UI and project-step model once a compatible laser
head advertises those capabilities.

This is not a claim that the packaged application has been exercised by a
human. It is a headless model, UI-contract and preview-artifact test. The
Machine section intentionally remains hidden unless the active machine and
head provide PWM parameters.

## Remaining graphical evidence

A later no-device Windows test must:

1. launch a packaged Rayforge build with the external addon;
2. select a synthetic JCZ-capable profile and confirm the Machine section;
3. open or create geometry, edit MOPA values and inspect the preview;
4. save and reload the project without losing those values;
5. exercise start, hold, cancel and explicit recovery against the no-device
   driver.

That test must still expose no USB discovery or controller transport. Until it
passes, the graphical half of roadmap item 5 and ADR 0002 remain open.

## Reproduce

Run against the pinned Rayforge checkout:

```powershell
python scripts/spike_rayforge_graphical_workflow.py <rayforge-checkout>
```

On Windows the imported Rayforge task manager creates a local asyncio wake-up
socket. A sandbox that blocks local socket creation cannot run the spike even
though the spike performs no network or controller I/O.
