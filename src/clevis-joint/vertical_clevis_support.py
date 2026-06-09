"""
Vertical clevis support from the reference drawing.

This script intentionally avoids Python COM cut features for the main shape:
base + two ears are built additively with FeatureExtrusion2.  Hole geometry is
attempted with FeatureCut4 only when the API succeeds; otherwise the script
adds visible hole-center markers so the failed operation is obvious in SW.

Assumed dimensions from the drawing, in mm:
- Base: diameter 150, height 30
- Upright: 70 wide, 120 high above base, R35 rounded top
- Pin hole: diameter 18, centered on upright centerline
- Ear pack depth: 60 total, 25 slot between ears
- Central slot: open from 20 mm above the base top to the rounded head
"""

from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass

import pythoncom
import win32com.client


class SWBuildError(RuntimeError):
    """Raised when a SolidWorks operation cannot be verified."""


@dataclass(frozen=True)
class ClevisSupportDims:
    base_diameter: float = 150.0
    base_height: float = 30.0
    upright_width: float = 70.0
    upright_height_above_base: float = 120.0
    hole_diameter: float = 18.0
    ear_pack_depth: float = 60.0
    slot_width: float = 25.0
    slot_bottom_above_base: float = 20.0

    @property
    def ear_thickness(self) -> float:
        return (self.ear_pack_depth - self.slot_width) / 2.0

    @property
    def upright_radius(self) -> float:
        return self.upright_width / 2.0

    @property
    def hole_center_y(self) -> float:
        # The drawing points to the hole at the center of the semicircular head.
        return self.base_height + self.upright_height_above_base - self.upright_radius


def mm(value: float) -> float:
    return value / 1000.0


def safe_member(obj, name: str, default=None):
    try:
        value = getattr(obj, name)
        return value() if callable(value) else value
    except Exception:
        return default


class VerticalClevisBuilder:
    def __init__(self, dims: ClevisSupportDims):
        self.dims = dims
        self.sw = None
        self.doc = None
        self.created_doc_title = None

    def connect(self):
        pythoncom.CoInitialize()
        try:
            self.sw = win32com.client.GetActiveObject("SldWorks.Application")
        except Exception:
            self.sw = win32com.client.Dispatch("SldWorks.Application")
        self.sw.Visible = True
        self.sw.UserControl = True
        return self.sw

    def new_part(self):
        template = self._find_part_template()
        previous_title = ""
        if self.sw.ActiveDoc is not None:
            previous_title = safe_member(self.sw.ActiveDoc, "GetTitle", "")

        result = self.sw.NewDocument(template, 0, 0, 0)
        time.sleep(1.0)
        self.doc = result if result is not None else self.sw.ActiveDoc
        if self.doc is None:
            raise SWBuildError("NewDocument failed: ActiveDoc is None")
        self.created_doc_title = safe_member(self.doc, "GetTitle", "")
        if self.created_doc_title == previous_title and self.feature_count() > 3:
            raise SWBuildError(
                f"NewDocument did not switch to a clean part; still on {self.created_doc_title} "
                f"with {self.feature_count()} features"
            )
        return self.doc

    def _find_part_template(self) -> str:
        candidates = [
            r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot",
            r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_part.prtdot",
            r"C:\ProgramData\SolidWorks\SOLIDWORKS 2023\templates\gb_part.prtdot",
            r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2023\templates\gb_part.prtdot",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        raise SWBuildError("No SolidWorks part template found. Update _find_part_template().")

    def select_plane(self, key: str):
        names = {
            "front": ("前视基准面", "Front Plane"),
            "top": ("上视基准面", "Top Plane"),
            "right": ("右视基准面", "Right Plane"),
        }[key]

        self.doc.ClearSelection2(True)
        callout = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
        for name in names:
            try:
                if self.doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, False, 0, callout, 0):
                    return name
            except Exception:
                pass

        feat = self.doc.FirstFeature
        while feat is not None:
            fname = safe_member(feat, "Name", "")
            if fname in names:
                feat.Select2(False, 0)
                return fname
            feat = feat.GetNextFeature()

        raise SWBuildError(f"Cannot select plane: {key}; tried {names}")

    def feature_count(self) -> int:
        return int(safe_member(self.doc, "GetFeatureCount", 0) or 0)

    def assert_feature_added(self, before: int, label: str):
        self.force_rebuild()
        after = self.feature_count()
        if after <= before:
            raise SWBuildError(f"{label} failed: feature count did not increase ({before} -> {after})")
        print(f"  OK {label}: feature count {before} -> {after}")

    def force_rebuild(self):
        try:
            self.doc.ForceRebuild3(False)
        except Exception:
            _ = safe_member(self.doc, "EditRebuild3", None)

    def extrude_boss(
        self,
        depth_m: float,
        label: str,
        merge: bool = True,
        flip: bool = False,
        start_offset_m: float = 0.0,
    ):
        before = self.feature_count()
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            True, flip, False,
            0, 0,
            depth_m, 0.0,
            False, False,
            False, False,
            0.0, 0.0,
            False, False,
            False, False,
            merge,
            True, True,
            start_offset_m, False, False,
        )
        if feat is None:
            raise SWBuildError(f"{label} failed: FeatureExtrusion2 returned None")
        self.assert_feature_added(before, label)
        return feat

    def build_base(self):
        print("[1/5] Build round base")
        d = self.dims
        self.select_plane("top")
        self.doc.SketchManager.InsertSketch(True)
        self.doc.SketchManager.CreateCircle(0, 0, 0, mm(d.base_diameter / 2.0), 0, 0)
        self.doc.SketchManager.InsertSketch(True)
        self.extrude_boss(mm(d.base_height), "base cylinder", merge=False)

    def build_upright(self):
        print("[2/5] Build upright bridge and two fork ears")
        d = self.dims
        x_half = mm(d.upright_width / 2.0)
        y0 = mm(d.base_height)
        y_slot_bottom = mm(d.base_height + d.slot_bottom_above_base)
        y_center = mm(d.hole_center_y)
        y_top = mm(d.base_height + d.upright_height_above_base)
        lug_t = mm(d.ear_thickness)
        slot = mm(d.slot_width)
        pack = mm(d.ear_pack_depth)
        z_offsets = [-(slot / 2.0 + lug_t), slot / 2.0]

        self.select_plane("front")
        self.doc.SketchManager.InsertSketch(True)
        self.doc.SketchManager.CreateCornerRectangle(-x_half, y0, 0, x_half, y_slot_bottom, 0)
        self.doc.SketchManager.InsertSketch(True)
        self.extrude_boss(
            pack,
            "solid bridge below central slot",
            merge=True,
            start_offset_m=-(pack / 2.0),
        )

        for idx, z0 in enumerate(z_offsets, start=1):
            self.select_plane("front")
            self.doc.SketchManager.InsertSketch(True)
            sm = self.doc.SketchManager
            sm.CreateLine(-x_half, y_slot_bottom, 0, -x_half, y_center, 0)
            sm.Create3PointArc(-x_half, y_center, 0, x_half, y_center, 0, 0, y_top, 0)
            sm.CreateLine(x_half, y_center, 0, x_half, y_slot_bottom, 0)
            sm.CreateLine(x_half, y_slot_bottom, 0, -x_half, y_slot_bottom, 0)
            self.doc.SketchManager.InsertSketch(True)
            # StartOffset places each ear on either side of the central slot.
            before = self.feature_count()
            self.doc.FeatureManager.FeatureExtrusion2(
                True, False, False,
                0, 0,
                lug_t, 0.0,
                False, False,
                False, False,
                0.0, 0.0,
                False, False,
                False, False,
                True,
                True, True,
                z0, False, False,
            )
            self.assert_feature_added(before, f"ear {idx}")

    def try_cut_pin_hole(self):
        print("[3/5] Try through pin hole cut")
        d = self.dims
        self.select_plane("front")
        self.doc.SketchManager.InsertSketch(True)
        radius = mm(d.hole_diameter / 2.0)
        cy = mm(d.hole_center_y)
        self.doc.SketchManager.CreateCircle(0, cy, 0, radius, cy, 0)
        self.doc.SketchManager.InsertSketch(True)

        before = self.feature_count()
        try:
            cut = self.doc.FeatureManager.FeatureCut4(
                False, False, False,
                1, 1,
                0.0, 0.0,
                False, False,
                False, False,
                0.0, 0.0,
                False, False,
                False, False,
                False,
                False, False,
                False, False, False,
                0,
                0.0,
                False,
                False,
            )
            self.force_rebuild()
            after = self.feature_count()
            if cut is not None or after > before:
                print(f"  OK pin hole cut: feature count {before} -> {after}")
                return True
        except Exception as exc:
            print(f"  WARN FeatureCut4 failed: {exc}")

        print("  WARN pin hole was not cut; adding visible hole markers instead")
        self.add_hole_markers()
        return False

    def add_hole_markers(self):
        d = self.dims
        marker_depth = mm(1.0)
        radius = mm(d.hole_diameter / 2.0)
        cy = mm(d.hole_center_y)
        self.select_plane("front")
        self.doc.SketchManager.InsertSketch(True)
        self.doc.SketchManager.CreateCircle(0, cy, 0, radius, cy, 0)
        self.doc.SketchManager.InsertSketch(True)
        self.extrude_boss(marker_depth, "hole marker boss", merge=True)

    def save(self):
        print("[4/5] Save part")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, "vertical_clevis_support.SLDPRT")
        attempts = []
        if os.path.exists(path):
            os.remove(path)

        try:
            self.doc.SaveAs(path)
            attempts.append("SaveAs")
        except Exception as exc:
            attempts.append(f"SaveAs failed: {exc}")

        if not os.path.exists(path):
            try:
                result = self.doc.SaveAs3(path, 0, 2)
                attempts.append(f"SaveAs3={result}")
            except Exception as exc:
                attempts.append(f"SaveAs3 failed: {exc}")

        if not os.path.exists(path):
            try:
                errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                callout = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
                ok = self.doc.Extension.SaveAs(path, 0, 1, callout, errors, warnings)
                attempts.append(f"Extension.SaveAs={ok}, errors={errors.value}, warnings={warnings.value}")
            except Exception as exc:
                attempts.append(f"Extension.SaveAs failed: {exc}")

        saved_path = safe_member(self.doc, "GetPathName", "")
        if os.path.exists(path):
            print(f"  OK saved: {path}")
            return path
        if saved_path and os.path.exists(saved_path):
            print(f"  OK saved: {saved_path}")
            return saved_path

        raise SWBuildError(f"Save verification failed. target={path}; doc_path={saved_path}; attempts={attempts}")

    def report(self, hole_cut: bool):
        d = self.dims
        print("[5/5] Dimension summary")
        print(f"  base: diameter {d.base_diameter} mm, height {d.base_height} mm")
        print(f"  upright: width {d.upright_width} mm, height above base {d.upright_height_above_base} mm")
        print(f"  central slot: width {d.slot_width} mm, bottom {d.slot_bottom_above_base} mm above base top")
        print(f"  depth pack: total {d.ear_pack_depth} mm, each ear {d.ear_thickness} mm")
        print(f"  pin hole: diameter {d.hole_diameter} mm, center y {d.hole_center_y} mm")
        print(f"  hole cut result: {'cut feature created' if hole_cut else 'marker only; cut API unavailable'}")


def main():
    builder = VerticalClevisBuilder(ClevisSupportDims())
    try:
        builder.connect()
        builder.new_part()
        builder.build_base()
        builder.build_upright()
        hole_cut = builder.try_cut_pin_hole()
        builder.save()
        builder.report(hole_cut)
    except Exception as exc:
        print("\nOperation failed, fuse triggered.")
        print(f"error_type: {type(exc).__name__}")
        print(f"message: {exc}")
        if builder.doc is not None:
            print(f"doc: {safe_member(builder.doc, 'GetTitle', 'unknown')}")
            print(f"feature_count: {safe_member(builder.doc, 'GetFeatureCount', 'unknown')}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
