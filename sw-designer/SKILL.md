---
name: sw-designer
description: "用户需要 SolidWorks 参数化设计、建模策略、设计审查、装配/工程图规范或工艺可行性检查时调用本技能。"
metadata:
  category: engineering-cad
  version: 2.7.0
  author: Delancy
---

# SolidWorks Designer

Use this skill for design decisions, parameterization strategy, design review, manufacturability checks, and pre-automation planning. If the task requires writing or executing SolidWorks API code, switch to `solidworks-automation`.

## Design workflow

1. **Clarify intent.** Identify the deliverable: part, assembly, drawing, mold, sheet-metal part, weldment, or review only.
2. **Collect constraints.** Record dimensions, material, manufacturing process, tolerances, units, standards, and any downstream drawing or simulation requirements.
3. **Choose a modeling strategy.** Prefer native基准面 and robust sketch profiles. Avoid sketching on inclined faces unless no orthogonal strategy can represent the geometry.
4. **Parameterize.** Use an explicit parameter table or class. Do not bury dimensions in scattered literals.
5. **Validate design intent.** Check feature order, body count, symmetry, wall thickness, fillets, chamfers, hole counts, and mating references.
6. **Hand off cleanly.** Produce a dimension ledger and validation checklist before automation begins.

## Design rules

- Fully define sketches when the geometry allows it.
- Prefer orthogonal基准面 and stable references over face-dependent selections.
- Use design tables or explicit parameter dictionaries for families of parts.
- Keep feature order editable: base geometry, secondary features, holes, fillets/chamfers, then appearance or metadata.
- For assemblies, count repeated instances before modeling and prefer standard interfaces or named references over fragile face picks.
- For drawings, check projection, annotation order, hole callouts, and tolerance stack before export.
- For molds or forming tools, compute process dimensions before CAD; do not treat part geometry as tool geometry.

## Reference routes

Read only the reference that matches the task.

- `references/design-manual.md` — full 17-chapter design guide. Search with `rg -n "keyword" references/design-manual.md`, then read the relevant section rather than the entire manual.
- `../solidworks-automation/references/drawing-to-3d-lessons.md` — drawing interpretation and geometry validation.
- `../solidworks-automation/references/materials-forming-mold-lessons.md` — forming and mold process checks.
- `../solidworks-automation/references/assembly-debugging-lessons.md` — assembly intent and repeated-instance rules.

## Boundary

Use `cad-automation` for AutoCAD work. Use `solidworks-automation` when the user wants scripts, COM calls, live SolidWorks control, or model generation.
