# Vertical Clevis Support Notes

Use this note for the `Phi150 x 30` round base support with two vertical ears,
a `60 mm` total ear pack depth, a `25 mm` middle slot, a `20 mm` slot-bottom
height above the base, and a `Phi18` pin hole.

The safe entry point is:

```bash
python src/clevis-joint/vertical_clevis_support.py
```

That launcher compiles and runs the C# strong-typed modeler
`src/clevis-joint/VerticalClevisSupport.cs`.

Generated files are written under
`C:/Users/<user>/Desktop/vertical_clevis_support_output/`, with verification
views in the `views/` subfolder. Do not scatter generated CAD files directly on
the desktop root.

The side-view slot must be real geometry and centered on the middle plane:

- Build the round base.
- Build one full-depth upright boss with the `Phi18` through hole.
- Cut the middle slot from the front-plane sketch using C# `FeatureCut4`
  mid-plane depth `25 mm`, so the side view is split `12.5 mm` on each side of
  the center plane.
- Keep the slot bottom `20 mm` above the base top; material below that remains
  as the bridge between the two ears.
- Assert final volume so a missing slot, too-narrow slot, or missing hole fails
  the build.

Do not build this part by separately adding two offset ear bosses. That path is
sensitive to offset-plane and flip-direction interpretation and can leave the
side-view slot too narrow or the root geometry stepped. Use the C# strong-typed
cut path in `VerticalClevisSupport.cs`.

The builder refuses to run when many SolidWorks documents are already open
unless explicitly forced, and closes its generated document after saving unless
the user asks to keep it open.
