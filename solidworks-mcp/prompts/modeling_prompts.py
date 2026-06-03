"""
MCP Prompts: 建模流程引导模板

model_part      — 零件建模分步执行计划
verify_and_fix  — 验证结果不符时的修正策略
design_review   — 设计审查检查清单
"""


def register_prompts(mcp):
    """注册 MCP Prompts"""

    @mcp.prompt()
    def model_part(description: str, dimensions: str = "") -> str:
        """Generate a step-by-step plan for modeling a part in SolidWorks.
        Use this when starting a new part modeling task.
        """
        return f"""# SolidWorks Part Modeling Plan

## Target
{description}

## Dimensions
{dimensions if dimensions else "(to be determined)"}

## Execution Steps

### Step 1: Connect & Create
1. Call `sw_connect` to connect to SolidWorks (singleton)
2. Call `sw_new_part` to create a new part document

### Step 2: Sketch the Profile
1. Call `sw_create_sketch("front")` to start sketching on Front Plane
2. Use `sw_draw_rectangle`, `sw_draw_circle`, `sw_draw_line`, `sw_draw_arc` as needed
3. Call `sw_close_sketch` when the profile is complete

### Step 3: Create Features
1. Call `sw_extrude(depth)` with depth in METERS (e.g., 50mm = 0.050)
2. For cuts: create a new sketch on the appropriate plane, draw cut profile, call `sw_extrude_cut`
3. For fillets/chamfers: select edges first, then call `sw_fillet` or `sw_chamfer`

### Step 4: Verify (CRITICAL!)
1. Call `sw_capture_and_verify("{description}")` to get screenshots and metrics
2. Examine the screenshots visually - does the model match the description?
3. Call `sw_verify_model` to check rebuild status and model health
4. If anything is wrong, go back to Step 2/3 to fix

### Step 5: Save
1. Call `sw_save_document(path)` to save the completed model

## Important Rules
- All coordinates and dimensions in METERS (SW internal unit)
- Always verify after each major operation using W-A-R verification
- Never assume success without checking screenshots and metrics
- FeatureExtrusion2 uses 23 parameters (SW 2024)
- SelectByID2 8th parameter must be VARIANT(VT_DISPATCH, None)
"""

    @mcp.prompt()
    def verify_and_fix(expected: str, actual: str) -> str:
        """Generate a correction strategy when model verification fails.
        Use this when sw_capture_and_verify shows the model doesn't match expectations.
        """
        return f"""# Model Verification Correction Strategy

## Expected
{expected}

## Actual Result
{actual}

## Correction Steps

### 1. Diagnose
- Call `sw_get_feature_tree` to inspect the feature tree
- Call `sw_get_bounding_box` to check actual dimensions
- Call `sw_get_body_count` to verify entity count
- Compare expected vs actual dimensions

### 2. Common Issues
- **Wrong dimensions**: Check if depth/coordinates are in meters (not mm!)
  - 50mm should be 0.050 in API calls
- **Missing features**: Feature count didn't increase → sketch may be invalid
  - Re-create the sketch and extrude again
- **Wrong direction**: Extrusion went wrong way → use `flip=True`
- **Extra bodies**: Expected 1 body but got more → use `merge=True`

### 3. Fix Strategy
- Delete the last failed feature by rebuilding with corrected parameters
- Re-create the sketch if needed
- Re-extrude with correct parameters
- Call `sw_capture_and_verify` again to confirm fix

### 4. Re-verify
- Call `sw_capture_and_verify("{expected}")` to confirm the fix
- Repeat if still not matching
"""

    @mcp.prompt()
    def design_review(model_info: str = "") -> str:
        """Generate a design review checklist for the current model.
        Based on the sw-designer skill's best practices.
        """
        return f"""# SolidWorks Design Review Checklist

## Model Info
{model_info if model_info else "(call sw_verify_model to populate)"}

## Checklist

### 1. Wall Thickness
- [ ] Are walls uniform thickness? (Avoid warping)
- [ ] Minimum wall thickness ≥ 2mm for plastic parts

### 2. Fillets & Chamfers
- [ ] Internal corners have fillets (R=2-5mm recommended)
- [ ] External sharp edges have chamfers (C0.5-1mm)
- [ ] Fillet radii are reasonable for manufacturing

### 3. Extrusion Depth
- [ ] Extrusion depths are reasonable (not excessively deep)
- [ ] Deep features won't cause manufacturing issues

### 4. Model Health
- [ ] Model rebuilds without errors (sw_verify_model → rebuild_ok)
- [ ] Feature tree is clean (no suppressed/failed features)
- [ ] Body count matches expected (sw_get_body_count)
- [ ] Bounding box matches design intent (sw_get_bounding_box)

### 5. Naming & Organization
- [ ] Features are in logical order
- [ ] No unnecessary features

## Actions
1. Call `sw_verify_model` for health check
2. Call `sw_capture_screenshots` to visually inspect
3. Review each checklist item above
4. Fix any issues found
"""
