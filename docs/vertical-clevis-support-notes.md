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

The side-view slot must be real geometry from the start:

- Build the round base.
- Build the lower bridge full depth up to the slot-bottom height.
- Build two separated upper ears with a 25 mm empty gap between them.
- Include the `Phi18` pin hole inside the ear boss profiles.
- Assert final volume so a missing slot or missing hole fails the build.

Do not build this part as one solid upright and then rely on a later Python COM
`FeatureCut4` cleanup. That path can silently leave a single solid plate, which
breaks the three-view relationship.

The builder refuses to run when many SolidWorks documents are already open
unless explicitly forced, and closes its generated document after saving unless
the user asks to keep it open.
