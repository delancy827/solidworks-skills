# SolidWorks Materials Forming / Mold Design Lessons (field, 2026-07-12)

Lessons from materials forming & control engineering oriented work:
stamping die edge sizing + die-casting cavity/core process sizing, then
SolidWorks automated modeling and calibration.

Working tree (F drive only): `F:\codexpace\sw-mold-forming`  
Course refs used: 液力耦合器壳体压铸模课程设计说明书 + 冲压复习资料/既有 skill 冲模算例

## 1. Domain split: process calculation first, CAD second

For 材料成型及控制工程, never jump straight to "looks like a mold" solids.

Always produce a process sheet first:

### Stamping (冲模)

1. Workpiece OD/ID/t and material  
2. Single/double-sided clearance `c` / `Z`  
3. Blanking vs piercing edge ownership  
4. Wear allowance + IT tolerance split (handbook)  
5. Then model punch/die buttons

### Die casting (压铸)

1. Alloy (e.g. ZL102) and shrink `K`  
2. Cavity count / parting / gate style  
3. Injection pressure, projected area, clamp force  
4. Cavity/core sizes with shrink direction  
5. Moldbase, support plate, ejector, cooling, vent constraints  
6. Then model inserts / cores (approximate geometry ok for automation regression)

## 2. Stamping edge formulas vs handbook truth

Course/skill worked example (washer):

- Work: OD53 / ID34 / t=2.5 / 08 steel  
- Double clearance used in example: `Z = 0.18 mm` => single `c = 0.09 mm`

Simple formula (no wear/tolerance):

| Feature | Simple | Handbook example | Delta |
|---|---:|---:|---:|
| Blank die OD | 53.00 | 52.63 | **+0.37 mm** |
| Blank punch OD | 52.82 | 52.45 | **+0.37 mm** |
| Pierce punch OD | 34.00 | 34.31 | **-0.31 mm** |
| Pierce die ID | 34.18 | 34.49 | **-0.31 mm** |

Rules:

- 落料：凹模跟外形，凸模 = 凹模 - 2c  
- 冲孔：凸模跟内孔，凹模 = 凸模 + 2c  
- Production models **must** include wear direction and tolerance split; bare clearance-only edges are only for teaching scaffolds  
- If your automated model matches simple formula volume/bbox but not handbook edges, it is still process-wrong for manufacturing

## 3. Die-casting shrink and cavity sizing

From the housing course design:

- Part: OD≈575 mm, H≈165 mm, ZL102  
- Shrink used: **K = 0.6%** (handbook range 0.4%~0.6%)  
- Course cavity values: **OD'≈577.6 mm, H'≈165.6 mm**  
- Pure `L*(1+K)` gives 578.45 / 165.99 — close but not identical; course likely applied rounding / selected table values

Rules:

- External cavity/features generally **grow** with shrink  
- Internal core/features need explicit convention; do not blindly apply the same `(1+K)` everywhere  
- Insert wall stiffness matters: course took cavity insert wall ≈ **45 mm**  
- Circular insert approximation is fine for automation regression, but real housing cavity is non-circular (ribs, bosses, local cores)

## 4. Process constraints that should be stored even if not solid-modeled

Record these as metadata next to the CAD model:

| Item | Course value / range | Why it matters |
|---|---|---|
| Machine | horizontal cold chamber | alloy + size class |
| Cavities | 1 | clamp force / mold size |
| Parting | flat | machining + flash control |
| Gate | center | fill balance for shell |
| Injection pressure | 100 MPa | quality / force calc |
| Expansion force | ≈3375.74 kN | machine selection |
| Safety factor | 1.25 | required clamp ≈4219 kN |
| Moldbase | ≈1000×1000 mm | install envelope |
| Fixed plate height | ≈275 mm | cavity stack |
| Support plate | 160 mm (calc ~146) | bending under shot pressure |
| Ejector pin | Ø25 mm | push-out stress |
| Cooling | Ø≈11.1, distance≈19 mm | thermal + strength |
| Vent depth | 0.10~0.15 mm near cavity | gas defects |

If CAD ignores these, the model can still "look assembled" while being process-infeasible.

## 5. SolidWorks automation patterns that transferred well

Reuse the proven drawing-to-3D COM patterns:

- One sketch outer + inner loops + `FeatureExtrusion2` for rings/punches/dies/inserts  
- `ForceRebuild3(False)`  
- Mass via `GetMassProperties`  
- SaveAs with COM null export VARIANT  
- Select plane with Chinese/English names and COM null selection object  
- Calibrate with **bbox + volume derived from process formulas**, not eyeballing

Built and passed (5/5) under `F:\codexpace\sw-mold-forming\models`:

- `stamp_blank_punch.SLDPRT`  
- `stamp_pierce_punch.SLDPRT`  
- `stamp_compound_die.SLDPRT`  
- `diecast_cavity_insert.SLDPRT`  
- `diecast_core.SLDPRT`

## 6. What was wrong / incomplete before optimization

1. Treating mold CAD as ordinary mechanical parts without process sheet  
2. Using part OD/ID directly as punch/die edges  
3. Accepting bbox pass while ignoring wear/tolerance corrections (~0.3 mm class)  
4. Applying one shrink multiplier to every dimension without internal/external direction  
5. Modeling only solids and forgetting clamp force / vent / cooling feasibility notes  
6. Putting deliverables on Desktop (avoid; keep under `F:\codexpace\...`)

## 7. Recommended self-train loop for mold direction

1. Take a course or handbook worked example (stamping washer / die-cast housing)  
2. Recompute edges/cavity sizes by formula  
3. Compare to handbook/course corrected numbers  
4. Build simplified SW solids from the chosen size set  
5. Assert bbox + volume  
6. Write deltas back into this lesson  
7. Only then attempt complex product-shaped cavity/core surfaces

## 8. Next optimizations for the skill / builders

Priority:

1. Stamping edge calculator with wear + IT split presets  
2. Die-cast shrink direction helper (external vs internal vs height)  
3. Clamp-force / projected-area calculator metadata  
4. Standard moldbase envelope checks (1000-class etc.)  
5. Later: true parting surface / tooling split experiments (SW mold tools), after size logic is solid

## Evidence

- Report: `F:\codexpace\sw-mold-forming\reports\latest_mold_report.json` (**5/5 pass**)  
- Spec text: `F:\codexpace\sw-mold-forming\refs\diecast_spec_15p.txt`  
- Stamping notes: `F:\codexpace\sw-mold-forming\refs\stamping_review.txt`

## 9. Process calculators validated (2026-07-12 continued)

### 9.1 Stamping wear allowance that matches the handbook example

For washer OD53 / ID34 / t2.5 / 08 steel:

- `c = 0.09` (Z=0.18)
- `IT14(53)≈0.74`, `IT14(34)≈0.62`
- wear `x ≈ 0.5 * IT14`

Gives **exact** handbook edges:

| Edge | Formula result | Handbook |
|---|---:|---:|
| Blank die | 53 - 0.37 = **52.63** | 52.63 |
| Blank punch | 52.63 - 2*0.09 = **52.45** | 52.45 |
| Pierce punch | 34 + 0.31 = **34.31** | 34.31 |
| Pierce die | 34.31 + 2*0.09 = **34.49** | 34.49 |

So the previously observed ~0.3 mm error was not random: it was **missing wear x=0.5·IT14**.

Implementation reference:

- `F:\codexpace\sw-mold-forming\scripts\run_process_corrected_v2.py`
- `F:\codexpace\sw-mold-forming\reports\process_calculators.json`

### 9.2 Die-cast shrink direction correction

Isotropic teaching model:

- cavity from external casting size: `L_m = L_c * (1+K)`
- core from internal casting size: also `L_m = L_c * (1+K)`

Using `(1-K)` for cores is wrong in this model.

Measured training delta on assumed ID559:

- wrong `(1-0.006)` => 555.646
- correct with course effective K≈0.452% => 561.528
- difference ≈ **5.88 mm (~1.06%)**

Also note: course text says K=0.6%, but cavity OD 577.6/575 implies **effective K≈0.452%**. Store both stated and back-calculated K.

### 9.3 Clamp force back-check

`F_kN = K_safe * p_MPa * A_mm2 / 1000`

Course expansion force 3375.74 kN at 100 MPa => projected area ≈ **33757.4 mm²**.  
Required clamp with K=1.25 ≈ **4219.7 kN**.

### 9.4 SW build results for corrected sizes

Passed solids (bbox+volume):

- wear-corrected blank punch / pierce punch / compound die
- course cavity insert
- core with correct `(1+K)` shrink

Still brittle:

- stepped punch-die (body Ø65 + land Ø52.45 + through hole) — second face extrude can leave land-only solid
- MUST assert final height/volume; feature_count alone is insufficient

### 9.5 Modeling rule for stepped tooling

Preferred robust order when face extrude is flaky:

1. Build largest body + through hole first, or
2. Build land first then reverse-extrude body from bottom face, then
3. Hard-assert total height and volume against process formula

If assert fails, do not mark pass.

## 10. Continued learning loop results (no stop, 2026-07-12)

### 10.1 Stepped punch-die finally stabilized

Failed approaches on this machine:

- face-select second extrude from top (land-only residual risk)
- `FeatureRevolve` / `FeatureRevolve2` COM signatures (`无效的参数数目` / `非选择性的参数`)

**Working pattern:**

1. Front plane sketch: body OD + through hole → extrude body height  
2. `FeatureManager.InsertRefPlane(distance)` from `前视基准面` by body height  
3. Select `基准面1`  
4. Sketch land OD + same through hole → extrude land height  
5. Hard assert bbox height and volume

Validated geometry (wear-corrected edges):

- body Ø65 × 45  
- land Ø52.45 × 15  
- hole Ø34.31 through  
- volume **126260.1937 mm³**, bbox **65×65×60**, error ~0

Script: `F:\codexpace\sw-mold-forming\scripts\build_stepped_robust.py`  
Result: process models **6/6 pass**

### 10.2 Support plate formula from thesis

Thesis variables:

- `t` support thickness (cm)
- `S` pad distance (cm)
- `L` support length (cm)
- `P` injection pressure (MPa)
- `A` projected area of casting+overflow on parting (text unit messy: cm / cm²)
- `σ` allowable bending (MPa), 45# steel often 160

Course numerical result:

- calculated **t = 146.35 mm**
- design take **t = 160 mm** (~9.6% margin)

Also structural rules recorded in thesis:

- pads on long-side ends => thicker support plate  
- blind sleeve bottom thickness ≈ 0.8 × support plate  
- if pad span large / plate thin, reinforce with push-plate guide pillars or posts

### 10.3 Accessory tokens built from process sheet (5 then 8)

All SW-calibrated under `F:\codexpace\sw-mold-forming\models\v3_accessories`:

| Part | Size basis | Status |
|---|---|---|
| support plate | 540×540×160 | pass |
| fixed sleeve | OD775×H275, bore 577.6 | pass |
| ejector pin | Ø25×195 | pass |
| cooling channel token | OD15 / ID11.1 ×100 | pass |
| guide pillar | Ø71×120 | pass |
| ejector retainer plate | 540×20 + Ø40 holes | pass |
| push plate | 540×40 + Ø40 holes | pass |
| guide bush | OD80/ID71×80 | pass |

Latest accessories report: **8/8 pass**

### 10.4 Process constants to memorize for ZL102 housing course design

- cold-chamber, 1 cavity, flat parting, center gate  
- p = 100 MPa, K_safe = 1.25  
- expansion force ≈ 3375.74 kN → required clamp ≈ 4219.7 kN  
- projected area back-calc ≈ 33757 mm²  
- shrink stated 0.6%, effective from 577.6/575 ≈ 0.452%  
- vent near cavity 0.10~0.15 mm  
- cooling d≈11.1, stand-off≈19 mm  
- fixed sleeve outer = 575 + 2×100 = 775  
- ejector system plates: 540×20 / 540×40, guide Ø40, screws 8×M16  

### 10.5 What the skill should do automatically next time

1. Build process sheet JSON first (stamping edges / die-cast shrink / clamp / support / vent / cooling)  
2. Size solids from that JSON only  
3. Prefer multi-contour extrude; for steps use offset-plane stack  
4. Assert bbox+volume; never trust feature_count alone  
5. Keep everything under `F:\codexpace\...`

## 11. Die-cast mold skeleton assembly (continued)

### 11.1 What worked

Created a real assembly from process-calibrated parts:

- File: `F:\codexpace\sw-mold-forming\assemblies\diecast_mold_skeleton.SLDASM`
- Template: `gb_assembly.asmdot`
- Components inserted: **18/18**
- Assembly bbox about **775 × 775 × 487.5 mm** (matches fixed sleeve OD 775 envelope)

Insertion pattern that worked on this machine:

1. `NewDocument(gb_assembly.asmdot)`
2. Pre-open each part (`OpenDoc6` type=1)
3. Activate assembly
4. `AddComponent5(path, 0, "", False, "", x, y, z)` with meters
5. `ForceRebuild3(False)` + `Extension.SaveAs`

### 11.2 Stack intent (process skeleton, not full manufacturing mate set)

Approximate Z stack used for course-size tokens:

- ejector retainer / push plate / support plate under
- fixed sleeve + cavity insert + core above
- 4 guide pillars + 4 bushes at (±200, ±200)
- 4 ejector pins at (±80, ±80)

This is a **teaching skeleton** to validate envelope and BOM presence, not a fully constrained production mold assembly yet.

### 11.3 Mating status / lesson

Automatic face-picked mates are still brittle:

- cylindrical face picks for concentric pillar/bush often fail silently
- planar stack coincident picks need reliable face selection / named entities

So for mold assemblies, prefer this order:

1. insert all components at process coordinates (**done, robust**)
2. fix base component
3. mate using **explicit named entities or stable selection marks**, not only coordinate face hits
4. assert component count + assembly bbox envelope against process sheet

### 11.4 Assembly QA checklist

- component count == expected BOM count  
- every critical part present (sleeve, cavity, core, support, push/retainer, guides, ejectors)  
- envelope XY ~= fixed sleeve / moldbase class (here 775)  
- envelope Z spans support/ejector stack + sleeve height  
- save `.SLDASM` under `F:\codexpace\...` only

## 12. Assembly mating breakthrough and remaining limits

### 12.1 Working mate signature on this install

Face selection:

- `Extension.SelectByRay(x,y,z, dx,dy,dz, radius, 2, append, mark, 0)` works
- Selected object type `2` = face
- Can get selection count = 2 reliably

Mate creation:

- `AddMate3(...)` fails: `非选择性的参数`
- Working call:

```python
err = VARIANT(VT_BYREF|VT_I4, 0)
mate = asm.AddMate5(
    mateType, align, flip,
    dist, 0.0, 0.0,
    0.0, 0.0,
    0.0, 0.0, 0.0,
    False, False,
    0, err,   # ErrorStatus byref LAST
)
```

Observed:

- returns mate COM object for several stack/guide pairs
- `err` often comes back as `1` (not 0) — treat as soft warning, verify by rebuild/bbox/BOM rather than trusting err alone

### 12.2 Current constrained skeleton status

File:

- `F:\codexpace\sw-mold-forming\assemblies\diecast_mold_skeleton_constrained.SLDASM`

QA:

- components **18/18** BOM exact
- envelope **775 × 775 × 487.5 mm**
- mates applied about **6/8** attempted (support-sleeve, push-support, 4 guide concentric)
- still hard: retainer face pick sometimes only 1 hit; cavity/core concentric needs better entity targeting

### 12.3 Practical mold-assembly automation order (updated)

1. Process-size all parts and calibrate solids  
2. Create assembly from `gb_assembly.asmdot`  
3. Preload parts + `AddComponent5` at process coordinates  
4. Fix base (fixed sleeve)  
5. Mate with SelectByRay + AddMate5(byref err)  
6. QA: BOM count, envelope bbox, optional transform dump  
7. Only then attempt drawing/BOM export

Do not block the whole mold workflow on perfect mates; envelope+BOM already prove the skeleton is process-consistent.
