# GitHub Push Handoff

This repository has local improvements from the SolidWorks coursework debugging
session. The user wants another agent to push the skill update to GitHub.

## What To Push

Recommended files to include:

- `solidworks-automation/SKILL.md`
- `docs/solidworks-assembly-debugging-lessons.md`
- `docs/github-push-handoff.md`
- `src/clevis-joint/CourseProjectAssembly.cs`
- `src/clevis-joint/CourseProjectStepReplay.cs`
- `src/clevis-joint/InspectCylinders.cs`
- `src/clevis-joint/make_course_doc.py`

## Do Not Push

Do not push private/generated coursework artifacts:

- files under `C:/Users/<user>/Desktop/.../冲压作业/`,
- `.SLDPRT`, `.SLDASM`, `.SLDDRW`,
- `.docx` coursework output,
- generated screenshots,
- SolidWorks lock files such as `~$*.SLDPRT`,
- compiled `.exe` or `.pdb` files,
- credentials, GitHub tokens, or local machine secrets.

## Suggested Git Commands

```powershell
git status --short
git add solidworks-automation/SKILL.md `
        docs/solidworks-assembly-debugging-lessons.md `
        docs/github-push-handoff.md `
        src/clevis-joint/CourseProjectAssembly.cs `
        src/clevis-joint/CourseProjectStepReplay.cs `
        src/clevis-joint/InspectCylinders.cs `
        src/clevis-joint/make_course_doc.py
git commit -m "Improve SolidWorks assembly debugging workflow"
git push
```

If the remote branch is not set:

```powershell
git push -u origin HEAD
```

## Why These Changes Matter

The prior automation incorrectly treated the task as a single-link assembly.
The drawing required two instances of the clevis link and two pin instances.
The updated workflow records how to:

- detect repeated parts from multi-view drawings,
- use actual transformed component hole centers,
- validate visually against front/top/isometric views,
- replay modeling screenshots for coursework process documents.
