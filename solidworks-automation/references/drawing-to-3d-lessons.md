# SolidWorks Drawing-to-3D Lessons (field, 2026-07-12)

Lessons from converting open mechanical shop drawings (DXF/PDF) into SolidWorks parts,
then comparing simplified automated models against drawing-implied secondary features
and imported STEP ground truth.

Source set used in the loop:

- `whitequark/mechanical-parts` shop drawings (NW flanges / nipples / viewport base)
- STEP ground truth: `whatever-part/whatever.step`
- Local working tree (F drive only): `F:\codexpace\sw-drawing-to-3d`

## 1. Do not trust bbox-only pass/fail

Outer bounding box can match while the model is still wrong.

Measured / estimated gaps when secondary drawing features are ignored:

| Part | Simple model | Drawing-implied improved estimate | Volume delta |
|---|---:|---:|---:|
| NW40 blank | OD55 x 6 solid | minus OD41.2 x depth 2.5 recess | **~23%** |
| NW25 nipple | OD40 x 30 tube ID21.4 | flange OD40 land 2.5 + tube OD26.4 | **~72%** |
| Viewport base | OD180 / ID101 / thk12 + 2x M5 | + ring groove ~OD153 depth 2 | **~10%** |

Rule:

- **BBox check is necessary, not sufficient.**
- Always compare **volume / surface area** and a **feature inventory** from the drawing:
  recesses, ridges, PCD holes, chamfers, O-ring grooves, land thickness.

## 2. DXF geometry is often exploded

These shop DXFs store most circles as many short LINE segments, not CIRCLE entities.

Observed:

- `nw40-blank.dxf`: almost no CIRCLE entities; dimensions live in MTEXT (`55.0`, `6.0`, `41.2`, `15%%D`)
- `nw25-nipple-30mm.dxf`: dims in MTEXT (`40.0`, `30.0`, `21.4`, `26.4`, `25.4`, `2.5`)
- `nw160-viewport-base.dxf`: only tiny CIRCLE radii (M5), major dims in MTEXT (`180.0`, `12.0`, `101.3`, `130.0`, `153.0`, `M5x1`)

Rule:

1. Parse **DIMENSION / MTEXT / TEXT** first for authoritative sizes.
2. Use arc/line clustering only as fallback.
3. Never assume CIRCLE entities exist just because the drawing looks circular.

## 3. Robust modeling pattern for through holes

On this SolidWorks 2024 + Python COM install:

- `FeatureCut4` / multi-arg cut paths are fragile / often return None or type mismatch
- **One sketch with outer profile + inner closed loops + `FeatureExtrusion2`** is robust
- SolidWorks treats inner closed contours as holes during extrude

Use:

```python
select_plane(doc)  # "前视基准面" then "Front Plane"
SketchManager.InsertSketch(True)
CreateCircle(outer...)
for hole in holes:
    CreateCircle(hole...)
SketchManager.InsertSketch(True)
FeatureManager.FeatureExtrusion2(...)  # blind depth in meters
```

Still required separately:

- face recesses / grooves / non-through pockets
- stepped OD (nipple ridge / flange land)
- chamfers and fillets

Do **not** claim those are done if only the through-hole extrude path succeeded.

## 4. COM quirks that burned runtime

### Rebuild

- `EditRebuild3` may be a **bool property**, not a callable
- Prefer `doc.ForceRebuild3(False)`

### Mass properties

- `doc.GetMassProperties` works and returns a tuple:
  `(comx, comy, comz, volume_m3, area_m2, mass_kg, ...)`
- `Extension.CreateMassProperty2()` also works (`Volume`, `SurfaceArea`, `Mass`, `CenterOfMass`)
- `CreateMassProperty()` alone was unreliable earlier in this environment

### Bounding box

- `GetPartBox(True)` works on native parts built in-session
- Imported STEP docs may **not** expose `GetPartBox` / `GetBodies2` on the early-bound wrapper
- For imports, use mass props first; bbox may need extreme-point / visible-box fallbacks

### Open / import

- Prefer `GetActiveObject` then `Dispatch`
- `LoadFile4(step_path, "", None, None)` can return **`(doc, status)` tuple** — unwrap before use
- `OpenDoc(path, 1)` is a good first path for existing SLDPRT reopen
- `OpenDoc6` byref error/warning VARIANTs are easy to get wrong

### SaveAs

```python
export_data = VARIANT(pythoncom.VT_DISPATCH, None)
err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
warn = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
doc.Extension.SaveAs(path, 0, 1, export_data, err, warn)
```

Passing Python `None` where a COM dispatch/export object is required fails.

### SelectByID2

Use a real COM null variant for the selection object argument:

```python
vn = VARIANT(pythoncom.VT_DISPATCH, None)
doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, False, 0, vn, 0)
```

Bare `None` can raise type mismatch on this machine.

## 5. Calibration loop that actually teaches the modeler

Minimum W-A-R checks after each part:

1. **Feature count increased** after intended features
2. **Body count == expected**
3. **BBox sorted dims** within tolerance
4. **Volume** within tolerance of drawing-derived estimate (not just outer cylinder)
5. **Secondary feature checklist** from drawing text:
   - groove/recess diameters and depths
   - ridge / land / step lengths
   - hole counts and PCDs
   - chamfer angle notes (`15%%D` etc.)

If volume error is large but bbox is perfect, the model is almost certainly missing internal/secondary features — rebuild feature tree, do not "scale to fit".

## 6. Ground-truth workflow (self-model then compare)

Recommended loop for skill improvement:

1. Download shop drawing (DXF/PDF) **and** any official STEP/SLDPRT if present
2. Extract dims from drawing text first
3. Build automated model from drawing only
4. Import ground-truth STEP (`LoadFile4`, unwrap tuple)
5. Compare volume/area/COM and feature inventory
6. Write the delta back into this lesson / builders
7. Re-run revalidate (multi-pass open + measure)

Do **not** put project outputs on the Desktop. Keep real files under `F:\codexpace\...`.
Desktop launchers are optional and only when the user asks.

## 7. Practical interpretation notes for KF / vacuum parts

- Blank flanges often include sealing recess / counterbore text that simple OD×thickness disks miss
- Nipples are rarely constant outer cylinders; look for ridge OD + tube OD + land thickness
- Viewport bases often have central bore + bolt holes + face grooves; outer 180×12 bbox can stay identical after groove cuts

## 8. What to optimize in automation code next

Priority order:

1. Drawing-text dimension parser (MTEXT/DIMENSION), not only entity geometry
2. Feature checklist generator from parsed dims
3. Multi-step builders: flange land + tube + bore; disk + face groove
4. Volume estimator from the same checklist used by the builder
5. Ground-truth STEP import + compare harness
6. Keep multi-contour extrude as default through-hole strategy

## Evidence files from this loop

- Build: `F:\codexpace\sw-drawing-to-3d\reports\latest_report.json` (5/5 simple builds)
- Revalidate: `F:\codexpace\sw-drawing-to-3d\reports\latest_revalidate.json` (15/15)
- Gap analysis: `F:\codexpace\sw-drawing-to-3d\reports\drawing_feature_gap_analysis.json`
- STEP measure probe: `F:\codexpace\sw-drawing-to-3d\reports\ground_truth_step_measure.json`
