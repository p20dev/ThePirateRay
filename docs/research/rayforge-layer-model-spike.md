# Rayforge layer visibility and output spike

- Date: 2026-10-20
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Scope: layer model, workflow output, ordering and serialization
- Transport: none

## Result

Rayforge already separates the two behaviors required by the PirateRay UX,
but at different levels of its model:

- `Layer.visible` controls whether a layer is rendered on the canvas and in
  visual previews;
- `Step.visible` controls whether a workflow operation participates in the
  generated job pipeline.

The states are independent. A hidden layer can retain an enabled operation,
which matches LightBurn's rule that hiding artwork does not silently disable
output. Conversely, disabling a workflow step removes that operation from job
generation without changing the layer's canvas visibility.

The pinned model round-trip preserved:

- layer name `Engraving`;
- layer color `#123456`;
- hidden layer state;
- operation name `Mark outline`;
- enabled operation state;
- an explicitly reordered layer list (`Second`, then `First`).

The deterministic result is stored in
`tests/fixtures/rayforge-layer-model.json`.

## UX fit

Rayforge's existing layer header exposes one eye control for
`Layer.visible`. Its operation editor exposes a visibility switch for each
`Step.visible`. The pipeline checks step visibility and does not check layer
visibility when constructing job nodes.

This means the required Show/Output semantics do **not** require a new pipeline
field or a duplicate layer model. The smallest PirateRay-facing extension is
an aggregate **Output** control in the layer presentation:

- on: all supported workflow steps in the layer are enabled;
- off: all workflow steps in the layer are disabled;
- mixed: some workflow steps are enabled and some are disabled.

An aggregate toggle must preserve or deliberately define what happens to a
previous mixed selection. The safest interaction is to expose the mixed state,
let the layer toggle affect all steps, and leave per-operation switches
available in Advanced view. This is a UI policy decision over existing model
state, not a serialization migration.

## Ordering

`Doc.layers` is the single ordered layer list. Drag-and-drop calls the
undoable `reorder_layers` command, canvas stacking follows the same list, and
the intent builder iterates it in order when constructing job nodes. The
serialized document retains that order.

The source documentation states that layers execute left to right. A packaged
no-device GUI checkpoint should still confirm that the visible ordering affordance
is understandable to a casual maker and that preview communicates the same
order.

## Remaining interaction evidence

The source and model evidence close the data-model question, but not the human
interaction checkpoint. A packaged no-device test should verify:

1. the layer eye changes only canvas/preview visibility;
2. a disabled operation remains visibly distinct from a hidden layer;
3. the proposed aggregate Output control reports on/off/mixed correctly;
4. save/reload retains names, colors, order and both states;
5. preview and no-device job output omit disabled steps but retain hidden,
   enabled layers.

No USB enumeration, controller command, motion, physical framing, or emission
occurred.

## Reproduce

Run against the pinned checkout with the already isolated Rayforge Python
environment:

```powershell
python scripts/spike_rayforge_layer_model.py <rayforge-checkout> `
  --output tests/fixtures/rayforge-layer-model.json
```

## Source anchors

- `rayforge/core/layer.py`: layer visibility, color and serialization
- `rayforge/core/step.py`: operation visibility and serialization
- `rayforge/pipeline/intent_builder.py`: step filtering and ordered job nodes
- `rayforge/ui_gtk/doceditor/layer_column.py`: layer eye control
- `rayforge/ui_gtk/doceditor/step_box.py`: operation visibility control
- `rayforge/ui_gtk/doceditor/layers_tab.py`: undoable drag ordering
- `rayforge/ui_gtk/canvas2d/surface.py`: canvas stacking order
- `website/docs/features/multi-layer.md`: documented execution semantics

