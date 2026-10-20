# Rayforge material-recipe model spike

- Date: 2026-10-20
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Scope: offline recipe schema, matching, persistence and extension seams
- Transport: none

## Result

Rayforge already provides the main recipe mechanism needed by the MOPA
workbench. A recipe is a YAML-backed preset that can target a machine, laser
head, material, thickness range and operation type. Applied settings are
filtered through the selected step type's allowlist, and individual values can
be marked “leave unchanged”. This is a substantially better reuse point than a
second PirateRay recipe engine.

The pinned laser-step contract includes power, speed, frequency in Hz and pulse
width in ns. A synthetic recipe carrying those fields matched only when its
machine, material, thickness and step context were complete. It rejected a
wrong material and missing stock context. An unknown setting survived recipe
storage but was excluded when applying values to the synthetic step.

## Existing fit

The current model covers:

- stable recipe identity, name and description;
- machine and laser-head compatibility;
- material and thickness compatibility;
- operation/step-type compatibility;
- setting-level apply/leave-unchanged behavior;
- post-processing settings;
- specificity-based recipe selection;
- one user-editable YAML file per recipe;
- forward-compatible unknown metadata through `Recipe.extra`.

Rayforge materials and recipes are separate concepts. Materials describe stock
identity and appearance; recipes carry process settings and can refer to a
material UID. That separation fits the PirateRay requirement that recipes are
optional accelerators rather than mandatory material wizards.

## PirateRay gaps

The source does not expose native, validated fields for:

- evidence provenance;
- approval or validation status;
- source/profile revision;
- lens compatibility;
- correction-profile compatibility;
- named personal, makerspace-shared or project collections.

Machine and head matching use identifiers, but those identifiers alone do not
prove that a recipe is safe for a JPT source, mounted lens or correction file.
The existing `extra` round-trip can preserve namespaced PirateRay metadata,
but preservation is not validation and the stock Rayforge UI does not explain
or enforce those fields.

## Narrow implementation direction

Reuse `Recipe`, `RecipeManager`, the existing selector/editor and step
allowlists. The smallest extension should define a versioned, namespaced
PirateRay metadata block with explicit provenance and compatibility fields,
then validate it before a recipe can receive a stronger label than
“unverified”. Keep unknown or incomplete compatibility fail-closed for
encoding and physical execution.

Do not fork the recipe schema merely to add collections. First test whether
separate manager directories or a small library wrapper can provide personal
and makerspace-shared views while retaining Rayforge's file-per-recipe format.
Project-local portability remains a separate, unproven requirement.

The exact evidence required for “makerspace-approved” remains a product and
safety decision for Kaz. This spike deliberately does not invent that policy.

## Implemented offline metadata gate

The external no-device addon now contains a version-1 `pirateray` metadata
validator. It requires non-empty provenance and exact matches for machine
profile, source type, lens profile and correction-profile hash. Missing or
mismatched values are rejected independently.

The only currently accepted status is `unverified`. The tempting
`makerspace-approved` label is rejected until its evidence and review policy
has been decided. Even successfully validated metadata returns
`encoding_allowed: false` and `hardware_use_allowed: false`; this contract
organizes evidence but grants no controller capability.

The synthetic public fixture and regression tests exercise the contract
without using physical machine identifiers or settings.

## Reproduce

Run against the pinned checkout with the isolated Rayforge Python environment:

```powershell
python scripts/spike_rayforge_recipe_model.py <rayforge-checkout> `
  --output tests/fixtures/rayforge-recipe-model.json
```

## Source anchors

- `rayforge/core/recipe.py`: schema, matching, allowlisting and `extra`
- `rayforge/core/recipe_manager.py`: YAML persistence and selection
- `rayforge/core/material.py`: material identity and appearance
- `rayforge/core/material_library.py`: material-library storage
- `rayforge/builtin_addons/rayforge-addon-laser/laser_essentials/steps/laser_step.py`:
  laser recipe fields and Hz/ns contracts
- `rayforge/ui_gtk/doceditor/recipes/`: existing editor and selector

No USB enumeration, controller command, motion, physical framing, arming or
laser output occurred.
