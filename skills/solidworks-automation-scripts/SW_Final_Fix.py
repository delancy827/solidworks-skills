# -*- coding: utf-8 -*-
"""
SW_Final_Fix.py - 最终版垫圈模具零件修复
时间戳: 2026-06-01
策略: Python COM - 仅用FeatureExtrusion2(23参数)，避开FeatureExtrusion3
"""
import win32com.client
import pythoncom
import time, os

TOT_H = 0.128
BASE_W = 0.100
TOP_W = 0.076
SIDE_HOLE_Y = 0.015
CHAMFER_Y = TOT_H - 0.020 - 0.010
HOLE_D = 0.009
MAIN_HOLE_D = 0.050
TH_D = 0.006
TH_DEPTH = 0.015

def call(obj, name, *args):
    """安全调用COM方法"""
    try:
        return getattr(obj, name)(*args)
    except Exception as e:
        print(f"    ERROR {name}: {e}")
        return None

def sel_plane(doc, name):
    """选择基准面"""
    candidates = [name]
    if "Plane" in name:
        candidates.append(name.replace("Plane", "基准面"))
    if "基准面" in name:
        candidates.append(name.replace("基准面", "Plane"))

    for n in candidates:
        if not n:
            continue
        try:
            # Try different ctx formats
            for ctx in [(), None, tuple()]:
                try:
                    ok = doc.Extension.SelectByID2(n, "PLANE", 0,0,0, False, 0, ctx, 0)
                    if ok:
                        print(f"    选中: {n}")
                        return True
                except:
                    pass
        except Exception as e:
            print(f"    选择{n}失败: {e}")
    return False

def main():
    print("=" * 50)
    print("SW零件修复 - 2026-06-01")
    print("=" * 50)

    pythoncom.CoInitialize()
    try:
        sw = win32com.client.Dispatch('SldWorks.Application.32')
        print(f"SW: {sw.RevisionNumber}")
        sw.Visible = True

        # 新建零件
        tmpl = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
        sw.NewDocument(tmpl, 0, 0, 0)
        time.sleep(1.0)
        doc = sw.ActiveDoc
        print(f"新建: {doc.GetTitle}")

        # === 底座梯形拉伸 ===
        print("\n[1] 底座梯形拉伸...")
        sel_plane(doc, "前视基准面")
        doc.SketchManager.InsertSketch(True)

        hw_top = TOP_W / 2
        hw_bot = BASE_W / 2
        doc.SketchManager.CreateLine(-hw_top, TOT_H, 0, -hw_bot, CHAMFER_Y, 0)
        doc.SketchManager.CreateLine(-hw_bot, CHAMFER_Y, 0, hw_bot, CHAMFER_Y, 0)
        doc.SketchManager.CreateLine(hw_bot, CHAMFER_Y, 0, hw_top, TOT_H, 0)
        doc.SketchManager.CreateLine(hw_top, TOT_H, 0, -hw_top, TOT_H, 0)

        doc.SketchManager.InsertSketch(True)

        # FeatureExtrusion2: 23参数签名 [Sd][Flip][Dir][T1][T2][D1][D2][Dchk1][Dchk2][Ddir1][Ddir2]
        # [Dang1][Dang2][Ofr][Ofc][Tf1][Tf2][Merge][UseFeatScope][UseAutoSelect][StartOffset][IsAutoStartOffset][FlipStartOffset]
        feat = doc.FeatureManager.FeatureExtrusion2(
            False, False, False, 0, 1, TOT_H, 0.005,
            False, False, False, False, 0.0, 0.0,
            False, False, False, False,
            False, False, False, 0.0, False, False)
        print(f"  底座: {'OK' if feat else 'FAIL'}")
        doc.ForceRebuild3(False)
        time.sleep(0.3)

        # === M6螺纹孔 ===
        print("\n[2] M6螺纹孔(2个)...")
        sel_plane(doc, "上视基准面")
        doc.SketchManager.InsertSketch(True)

        r = TH_D / 2
        doc.SketchManager.CreateCircle(-0.015, 0, 0, -0.015 + r, 0, 0)
        doc.SketchManager.CreateCircle(0.015, 0, 0, 0.015 + r, 0, 0)

        doc.SketchManager.InsertSketch(True)

        feat = doc.FeatureManager.FeatureExtrusion2(
            True, False, False, 0, 1, TH_DEPTH, 0.0,
            False, False, False, False, 0.0, 0.0,
            False, False, False, False,
            False, False, False, 0.0, False, False)
        print(f"  M6孔: {'OK' if feat else 'FAIL'}")
        doc.ForceRebuild3(False)
        time.sleep(0.3)

        # === 大圆孔 ===
        print("\n[3] 大圆孔(φ50mm)...")
        sel_plane(doc, "右视基准面")
        doc.SketchManager.InsertSketch(True)

        hy = TOT_H / 2
        hr = MAIN_HOLE_D / 2
        doc.SketchManager.CreateCircle(0, hy, 0, hr, hy, 0)

        doc.SketchManager.InsertSketch(True)

        feat = doc.FeatureManager.FeatureExtrusion2(
            True, False, False, 0, 1, 0.0, 0.0,
            False, False, False, False, 0.0, 0.0,
            False, False, False, False,
            False, False, False, 0.0, False, False)
        print(f"  大圆孔: {'OK' if feat else 'FAIL'}")
        doc.ForceRebuild3(False)
        time.sleep(0.3)

        # === 两侧吊耳+φ9孔 ===
        print("\n[4] 两侧吊耳及φ9通孔...")
        lw = 0.015
        lh = 0.040
        lx = BASE_W / 2 - lw / 2
        lb = SIDE_HOLE_Y
        lt = lb + lh
        r9 = HOLE_D / 2

        for side, label in [(-1, "左"), (1, "右")]:
            print(f"  {label}侧...")
            sel_plane(doc, "右视基准面")
            doc.SketchManager.InsertSketch(True)

            x1 = side * lx - lw / 2
            x2 = side * lx + lw / 2
            doc.SketchManager.CreateCornerRectangle(x1, lt, 0, x2, lb, 0)
            cx = side * lx
            cy = (lb + lt) / 2
            doc.SketchManager.CreateCircle(cx, cy, 0, cx + r9, cy, 0)

            doc.SketchManager.InsertSketch(True)

            feat = doc.FeatureManager.FeatureExtrusion2(
                False, False, False, 0, 1, 0.020, 0.0,
                False, False, False, False, 0.0, 0.0,
                False, False, False, False,
                False, False, False, 0.0, False, False)
            print(f"    吊耳: {'OK' if feat else 'FAIL'}")
            doc.ForceRebuild3(False)
            time.sleep(0.3)

        # === 保存 ===
        print("\n[5] 保存...")
        save_path = os.path.join(os.environ.get('TEMP', '.'), 'bracket_fixed_20260601.SLDPRT')
        try:
            doc.SaveAs(save_path)
            print(f"  保存: {save_path}")
        except Exception as e:
            print(f"  SaveAs: {e}")
            doc.Save3(1)

        print("\n" + "=" * 50)
        print(f"完成! 特征数: {doc.GetFeatureCount()}")
        print("=" * 50)

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()
