---
name: solidworks-automation
description: "用户需要用 Python/C#/VBA 连接 SolidWorks API 自动建模、装配、工程图、仿真等时调用本技能。"
metadata:
  category: engineering-cad
  version: 5.4.0
  author: Delancy
---

# SolidWorks Automation

Use this skill when the task requires executable SolidWorks automation code or a live COM session for parts, assemblies, drawings, Simulation, Flow Simulation, sheet metal, weldments, molds, or tooling. For design-only decisions or parameterization methodology without implementation, use `sw-designer` instead.

## Operating rules

- Reuse an active SolidWorks instance with `GetActiveObject("SldWorks.Application")`; only fall back to `Dispatch` when no usable instance exists.
- Reuse `sw.ActiveDoc` when it matches the task. Create a new document only when explicitly required or no suitable document exists.
- Wrap temporary documents in `try...finally` and close them by title; do not leave orphan windows or COM references.
- Treat units as meters inside the API. Keep user-facing dimensions in millimeters and convert explicitly.
- Before any mutation, capture a geometry fingerprint: feature count, body count, bbox, volume, and relevant dimensions.
- After each mutation, force a rebuild, re-read the fingerprint, and assert the expected change. Do not report success from a return value alone.
- If an assertion fails, stop the current strategy, print the traceback and current feature-tree state, and propose a concrete fallback. Do not silently catch the failure.
- Do not guess API names, argument counts, or COM null handling. Probe the live object with `dir()`, `get_com_member`, or a tiny subprocess before using an uncertain API.
- Keep real project files and generated models under `F:\codexspace\...`; do not copy full projects to the Desktop or C drive.

## Recommended workflow

1. **Preflight capability.** State whether the current runtime can inspect images/PDFs and whether SolidWorks is available. For drawing-driven work, identify the drawing source and who or what performed visual verification.
2. **Build a dimension ledger.** Separate exact, inferred, designer-choice, and unsupported dimensions. Bounding-box matching is not sufficient; account for recesses, lands, grooves, PCD holes, chamfers, and secondary features.
3. **Choose an execution channel.**
   - Prefer Python COM for connection, sketching, additive extrudes, measurements, and file I/O.
   - Prefer one sketch with outer and inner closed loops plus `FeatureExtrusion2` for through holes and rings.
   - Use C# or a generated VBA macro for methods that Python COM cannot call reliably, especially complex cut features with more than 12 parameters.
4. **Implement in the project workspace.** Keep builder code modular, parameter-driven, and testable without loading the full manual.
5. **Execute and validate.** Compile the script first. If SolidWorks is available, run it, force a rebuild, then assert feature/body counts, bbox, volume, and output-file existence. Use screenshots or rendered views when geometry intent matters.
6. **Report truthfully.** Distinguish completed geometry, markers-only holes, approximations, and unsupported features. Never describe an uncut marker as a through hole.

## Known SW 2024 COM shortcuts

- `SelectByID2` has 9 arguments; the Callout argument must be a real COM null variant, typically `VARIANT(VT_DISPATCH, None)`.
- `FeatureExtrusion2` uses 23 arguments on this install.
- `EditRebuild3` may be a property instead of a method. `ForceRebuild3(False)` is the safer rebuild call.
- `FeatureCut`, `FeatureCut3`, and `FeatureCut4` are fragile from Python COM. Use additive geometry, multi-contour sketches, C#, or VBA rather than pretending a `None` return means success.
- `LoadFile4` may return `(doc, status)`; unwrap it before using the document.
- `Extension.SaveAs` needs COM variants for export data and by-ref error/warning values.
- For assemblies, preload components, insert at process coordinates, then mate using stable named entities or `SelectByRay`; verify BOM count and envelope before attempting perfect mates.

## References

Read these only when the current task needs them.

- `references/automation-manual.md` — the full 46-section manual. Search it first with `rg -n "keyword" references/automation-manual.md`, then read the narrow line range. Avoid loading the whole file by default.
- `references/drawing-to-3d-lessons.md` — DXF/PDF-to-part rules, secondary-feature checks, volume calibration, and ground-truth STEP comparison.
- `references/materials-forming-mold-lessons.md` — stamping edge sizing, die-cast shrink direction, process metadata, moldbase checks, and mold assembly QA.
- `references/assembly-debugging-lessons.md` — repeated-instance counting, transformed hole centers, and render-based assembly validation.
- `examples/01_basic_part.py`
- `examples/02_assembly.py`
- `examples/03_drawing.py`
- `examples/04_simulation.py`
