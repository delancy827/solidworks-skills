# SolidWorks Assembly Debugging Lessons

This note records lessons learned from a SolidWorks automation task involving a
round-base clevis support, two clevis-link components, and two pin components.
Use it to improve future CAD automation runs and to avoid repeating the same
assembly mistakes.

## Core Lessons

1. Do not trust a single numeric check when the task is driven by a drawing.
   A transform can report coincident points while the standard view still shows
   an obviously wrong assembly. Always compare rendered views against the
   supplied front/top/side/isometric references.

2. Read the target assembly as an assembly, not as isolated parts.
   The drawing required:
   - one base support part,
   - two instances of the clevis-link part,
   - two instances of the pin part,
   - one pin between the support and first link,
   - one pin between the two link parts.

3. Detect repeated parts from the drawing.
   If a drawing shows the same forked link shape at the head and at the support
   side, instantiate the same part twice. Do not replace a missing repeated link
   with only an extra pin.

4. Validate component transforms using each component's actual assembly
   transform. The support inserted at `(0,0,0)` did not leave its hole center at
   the assumed world coordinate. The robust pattern is:
   - transform the support's local hole center into assembly coordinates,
   - use that actual point as the target for the mating link and pin,
   - transform the first link's fork-end hole center into assembly coordinates,
   - use that actual point as the target for the second link and second pin.

5. Screenshots are part of the validation loop.
   Generate and inspect at least:
   - isometric view after inserting the base support,
   - isometric view after inserting the first link,
   - isometric view after inserting pins and repeated link(s),
   - top view,
   - front view.

6. For coursework or audit-style deliverables, replay modeling steps.
   Teachers often expect screenshots while modeling, not just final part images.
   Generate coarse but meaningful process screenshots:
   - each major boss/extrude,
   - each major cut,
   - hole creation,
   - assembly insertion and view checks.

## Assembly Validation Checklist

Before claiming the assembly is finished:

- [ ] Compare the generated isometric view with the drawing's isometric view.
- [ ] Compare front/top/side relationships with the drawing, not only one view.
- [ ] Count repeated components in the drawing and in the assembly tree.
- [ ] Confirm each pin passes through a visible hole pair.
- [ ] Confirm fork/single-ear relationships are nested correctly.
- [ ] Confirm no part is floating in space in any standard view.
- [ ] Confirm screenshots in the Word/process document are regenerated after
      assembly corrections.
- [ ] Close SolidWorks after automation to avoid many stale windows.

## Robust Transform Pattern

Use actual transformed points rather than assumed world coordinates:

```csharp
double[] supportHole = TransformPoint(support, 0.0, 0.115, 0.0);
SetLinkTransform(firstLink, 135.0, supportHole);
SetPinTransform(supportPin, supportHole);

double[] firstLinkForkHole = TransformPoint(firstLink, 0.075, 0.025, 0.025);
SetLinkTransform(secondLink, 180.0, firstLinkForkHole);
SetPinTransform(linkToLinkPin, firstLinkForkHole);
```

Then inspect rendered screenshots. If the drawing shows a different angle,
adjust the second link angle and regenerate screenshots.

## Privacy and Repository Hygiene

Do not commit generated coursework files unless explicitly requested:

- `.SLDPRT`, `.SLDASM`, `.SLDDRW`
- generated Word documents,
- screenshots containing private coursework paths,
- temporary SolidWorks lock files,
- compiled `.exe` files,
- credentials or GitHub tokens.

Keep reusable source code and lessons in the repository; keep user deliverables
in the user's course folder.
