"""
Safe launcher for the vertical clevis support example.

The actual model is built by VerticalClevisSupport.cs because this part needs
reliable C# FeatureCut4 slot cutting and volume checks.  The Python COM path is
not used for the geometry: earlier direct-COM attempts could silently create one
solid web or an incorrectly narrow side-view slot.

Default behavior is intentionally conservative:
- reuse/start at most one SolidWorks instance through the C# program;
- refuse to run when many SolidWorks documents are already open;
- save under C:/Users/<user>/Desktop/vertical_clevis_support_output/;
- close the generated document after saving;
- do not capture screenshots unless --capture is passed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).with_name("VerticalClevisSupport.cs")
EXE = Path(__file__).with_name("VerticalClevisSupport.exe")
CSC = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")
SW_API = Path(r"E:\sw2024\SOLIDWORKS\api\redist")
SLDWORKS_DLL = SW_API / "SolidWorks.Interop.sldworks.dll"
SWCONST_DLL = SW_API / "SolidWorks.Interop.swconst.dll"


def compile_exe() -> None:
    missing = [str(path) for path in (CSC, SLDWORKS_DLL, SWCONST_DLL, SRC) if not path.exists()]
    if missing:
        raise SystemExit("Missing required build files:\n" + "\n".join(missing))

    command = [
        str(CSC),
        "/nologo",
        "/target:exe",
        f"/out:{EXE}",
        f"/reference:{SLDWORKS_DLL}",
        f"/reference:{SWCONST_DLL}",
        str(SRC),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    for dll in (SLDWORKS_DLL, SWCONST_DLL):
        target = EXE.with_name(dll.name)
        if not target.exists() or target.stat().st_mtime < dll.stat().st_mtime:
            shutil.copy2(dll, target)


def run_model(args: argparse.Namespace) -> int:
    compile_exe()

    command = [str(EXE)]
    if args.keep_open:
        command.append("--keep-open")
    if args.capture:
        command.append("--capture")
    if args.force_with_many_docs:
        command.append("--force-with-many-docs")

    env = os.environ.copy()
    return subprocess.run(command, cwd=ROOT, env=env).returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the vertical clevis support through the C# SolidWorks API path.")
    parser.add_argument("--keep-open", action="store_true", help="Keep the generated SolidWorks document open after saving.")
    parser.add_argument("--capture", action="store_true", help="Also export front/right/isometric JPG verification views.")
    parser.add_argument("--force-with-many-docs", action="store_true", help="Run even if SolidWorks already has many open documents.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    return run_model(args)


if __name__ == "__main__":
    raise SystemExit(main())
