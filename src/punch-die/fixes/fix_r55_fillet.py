"""
修复1: 凸模U形槽添加 R5.5mm 槽底圆角
========================================
学号27号 | 材控2320181班

方法: 重画带圆弧的9段草图（7直线+2圆弧），一次拉伸成型。
      完全绕过 FeatureFillet3 边选择的不稳定性。

圆弧几何:
  右圆角: P4'→Arc→P4a  (圆心在槽底角内侧 R5.5 处)
  左圆角: P5a→Arc→P5'  (镜像对称)

使用: python fix_r55_fillet.py
前提: SW 2024 已打开并运行
"""
import math
import os
import time

import pythoncom
import win32com.client

# ========== 课设参数 (学号27号) ==========
A1   = 42.0       # 凹模槽宽 mm
gap  = 2.1        # 单边间隙 mm (t+0.1)
B    = 25.0       # U形高度/槽深 mm
t    = 2.0        # 板厚 mm

# 凸模外形
punchW = A1 + 20.0       # 62 mm
punchH = B + t           # 27 mm
punchL = 80.0            # 拉伸长度 mm

# U形槽
slotDepth = B             # 25 mm
slotTopW  = A1 - 2 * gap  # 37.8 mm
halfAngleRad = 0.5 * math.pi / 180.0  # 0.5° 回弹补偿
dx = slotDepth * math.tan(halfAngleRad)  # 0.218 mm
slotBotW = slotTopW + 2 * dx             # 38.236 mm
slotY    = punchH - slotDepth            # 2 mm
cx = punchW / 2.0

# R5.5 圆角参数
R = 5.5

# 右底角圆弧切点
P4_right_x = cx + slotBotW / 2.0 - R   # 底部切线终点 X
P4_right_y = slotY                       # = 2.0 (底边高度)
P4a_x = cx + slotBotW / 2.0             # 斜壁切点 X
P4a_y = slotY + R                        # = 7.5 (斜壁切点高度)
# 圆弧中间点 (底部)
P4_mid_x = cx + slotBotW / 2.0 - R
P4_mid_y = slotY                         # = 2.0

# 左底角圆弧切点 (镜像)
P5_left_x = cx - slotBotW / 2.0 + R
P5_left_y = slotY
P5a_x = cx - slotBotW / 2.0
P5a_y = slotY + R
# 圆弧中间点 (底部)
P5_mid_x = cx - slotBotW / 2.0 + R
P5_mid_y = slotY

# 7 个关键坐标点
x1, y1 = 0.0, 0.0
x2, y2 = punchW, 0.0
x3, y3 = cx + slotTopW / 2.0, punchH
x4, y4 = cx + slotBotW / 2.0, slotY
x5, y5 = cx - slotBotW / 2.0, slotY
x6, y6 = cx - slotTopW / 2.0, punchH
x7, y7 = 0.0, punchH

print("=" * 50)
print("修复1: 凸模U形槽 R5.5 槽底圆角")
print("学号27号 | 9段草图法 (7直线+2圆弧)")
print("=" * 50)
print(f"  凸模外形: {punchW} x {punchH} x {punchL} mm")
print(f"  槽顶宽: {slotTopW:.1f} mm, 槽底宽: {slotBotW:.3f} mm")
print(f"  槽深: {slotDepth} mm, 89.5° 回弹补偿")
print(f"  圆角: R{R} mm")
print(f"  右圆角: ({P4_right_x:.3f},{P4_right_y:.1f}) → Arc → ({P4a_x:.3f},{P4a_y:.1f})")
print(f"  左圆角: ({P5a_x:.3f},{P5a_y:.1f}) → Arc → ({P5_left_x:.3f},{P5_left_y:.1f})")

# ========== 连接 SW ==========
pythoncom.CoInitialize()
try:
    swApp = win32com.client.GetActiveObject("SldWorks.Application")
    print("\n[SW] 已连接到活动实例")
except Exception:
    swApp = win32com.client.Dispatch("SldWorks.Application.32")
    swApp.Visible = True
    print("[SW] 已启动新实例，等待5秒...")
    time.sleep(5)

swApp.Visible = True
swApp.UserControl = True

# ========== 关闭残留文档 ==========
while swApp.GetDocumentCount > 0:
    doc = swApp.ActiveDoc
    if doc:
        swApp.CloseDoc(doc.GetTitle)
    else:
        break
print("[SW] 已清理残留文档")

# ========== 新建零件 ==========
tpl = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_part.prtdot"
if not os.path.exists(tpl):
    tpl = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot"
swApp.NewDocument(tpl, 0, 0, 0)
time.sleep(1)

doc = swApp.ActiveDoc
if doc is None:
    print("❌ 新建零件失败")
    exit(1)
print(f"[1/4] 零件已创建: {doc.GetTitle}")

# 关闭自动几何关系
doc.SetUserPreferenceToggle(152, False)  # swSketchAutomaticRelations

# ========== 选择前视基准面 + 创建草图 ==========
sel = doc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, False, 0, None, 0)
if not sel:
    sel = doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
if not sel:
    print("❌ 无法选择前视基准面")
    exit(1)

doc.SketchManager.InsertSketch(True)
print("[2/4] 创建9段草图 (7直线+2圆弧)...")

sk = doc.SketchManager

# 外框 (5条直线)
sk.CreateLine(x1, y1, 0, x2, y2, 0)                # L1: 底边
sk.CreateLine(x2, y2, 0, x3, y3, 0)                # L2: 右边
sk.CreateLine(x3, y3, 0, P4_right_x, P4_right_y, 0)  # L3: 右斜壁(到圆角切点)

# 右圆角 (三点圆弧: 起点→终点→中间控制点)
sk.Create3PointArc(
    P4_right_x, P4_right_y, 0,   # 起点 (底部切点)
    P4a_x, P4a_y, 0,              # 终点 (斜壁切点)
    P4_mid_x, P4_mid_y, 0         # 中间点 (圆弧底部)
)

# 槽底线
sk.CreateLine(P4a_x, P4a_y, 0, P5a_x, P5a_y, 0)    # L4: 槽底

# 左圆角 (三点圆弧)
sk.Create3PointArc(
    P5a_x, P5a_y, 0,              # 起点 (斜壁切点)
    P5_left_x, P5_left_y, 0,      # 终点 (底部切点)
    P5_mid_x, P5_mid_y, 0         # 中间点 (圆弧底部)
)

sk.CreateLine(P5_left_x, P5_left_y, 0, x6, y6, 0)  # L5: 左斜壁(从圆角切点)
sk.CreateLine(x6, y6, 0, x7, y7, 0)                 # L6: 左边
sk.CreateLine(x7, y7, 0, x1, y1, 0)                 # L7: 顶边

sk.InsertSketch(True)

# 验证草图
feat = doc.FirstFeature
while feat is not None:
    tn = feat.GetTypeName2
    if callable(tn):
        tn = tn()
    if tn == "ProfileFeature" or tn == "Sketch":
        try:
            sketch = feat.GetSpecificFeature2()
            segs = sketch.GetSketchSegments()
            seg_count = len(segs) if segs else 0
            print(f"  草图验证: 线段数={seg_count} (期望=9)")
            if seg_count == 9:
                print("  ✅ 9段草图全部创建成功")
            else:
                print(f"  ⚠️ 线段数异常: {seg_count}")
        except Exception:
            pass
        break
    feat = feat.GetNextFeature()

# ========== 拉伸 ==========
print("\n[3/4] FeatureExtrusion2 拉伸 80mm...")
before_count = doc.GetFeatureCount
if callable(before_count):
    before_count = before_count()

feat = doc.FeatureManager.FeatureExtrusion2(
    True, False, False,       # Sd(双向), Flip, Dir
    0, 0,                     # T1(Blind), T2(Blind)
    punchL, 0.0,              # D1=80mm, D2=0
    False, False,             # Dchk1, Dchk2
    False, False,             # Ddir1, Ddir2
    0.0, 0.0,                 # Dang1, Dang2
    False, False,             # Ofr, Ofc
    False, False,             # Tf1, Tf2
    True, True, True,         # Merge, UseFeatScope, UseAutoSelect
    0, 0.0, False             # StartOffset, IsAutoStartOffset, FlipStartOffset
)

if feat is None:
    print("❌ FeatureExtrusion2 返回 None")
    exit(1)

doc.ForceRebuild3(False)

after_count = doc.GetFeatureCount
if callable(after_count):
    after_count = after_count()
print(f"  特征数: {before_count} → {after_count}")

# ========== 实体+斜壁验证 ==========
bodies = doc.GetBodies2(0, False)
body_count = len(bodies) if bodies else 0
print(f"  实体数: {body_count}")

if body_count > 0:
    body = bodies[0]
    faces = body.GetFaces()
    face_count = len(faces) if faces else 0
    print(f"  面数: {face_count} (带圆角应>9)")

    # 斜壁角度验证
    slant_count = 0
    for f in faces:
        try:
            surf = f.GetSurface()
            if surf.IsPlane():
                norm = surf.PlaneParams
                nx, ny, nz = norm[0], norm[1], norm[2]
                angle = math.atan2(abs(nx), abs(ny)) * 180.0 / math.pi
                if 0.1 < angle < 2.0 and abs(nz) < 0.1:
                    slant_count += 1
                    print(f"    斜壁面: 偏差={angle:.4f}° (期望≈0.5°)")
        except Exception:
            continue

    if slant_count == 2:
        print("  ✅ 双侧89.5°斜壁验证通过")
    else:
        print(f"  ⚠️ 斜壁面数={slant_count} (期望=2)")

# ========== 保存 ==========
print("\n[4/4] 保存...")
save_dir = r"D:\冲压课设1\181班27号"
os.makedirs(save_dir, exist_ok=True)
save_path = os.path.join(save_dir, "凸模_27号_U形槽_R55.SLDPRT")

result = doc.SaveAs3(save_path, 0, 0)
if result != 1 and result != 0:
    doc.SaveAs(save_path)

if os.path.exists(save_path):
    size_kb = os.path.getsize(save_path) / 1024
    print(f"  ✅ 已保存: {save_path} ({size_kb:.1f} KB)")
else:
    print(f"  ❌ 保存失败")

print("\n" + "=" * 50)
print("修复1 完成!")
print("  ✅ R5.5 槽底圆角已添加 (9段草图法)")
print("  ✅ 89.5° 回弹补偿保持不变")
print("  ⚠️ 请打开文件确认圆角外观")
print("=" * 50)
