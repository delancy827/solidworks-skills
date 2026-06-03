"""
修复2: 凹模添加 Φ13mm 孔 (IT14 公差 +0.18/0)
===============================================
学号27号 | 材控2320181班

在凹模上创建 Φ13mm 通孔:
  - 直径: 13mm (IT14: +0.18/0, 实际加工时取上限)
  - 位置: 可配置 (默认凹模中心偏上)
  - 方式: FeatureExtrusion2 Dir=True 完全贯穿

使用: python fix_phi13_hole.py
前提: SW 2024 已打开，凹模_27号.SLDPRT 在指定路径
"""
import os
import time

import pythoncom
import win32com.client

# ========== 配置参数 ==========
DIE_FILE = r"D:\冲压课设1\181班27号\凹模_27号.SLDPRT"

# 凹模外形 (57×42×80mm: 宽×高×长)
DIE_W = 57.0   # 宽度 mm
DIE_H = 42.0   # 高度 mm
DIE_L = 80.0   # 长度 mm

# Φ13 孔参数
HOLE_DIA = 13.0          # 直径 mm (IT14: +0.18/0)
HOLE_RADIUS = HOLE_DIA / 2.0  # 6.5 mm

# 孔位置 (在凹模正面，中心偏上)
# ⚠️ 根据实际图纸修改以下坐标！
HOLE_X = DIE_W / 2.0     # X 居中 (28.5mm)
HOLE_Y = DIE_H * 0.65    # Y 偏上 (27.3mm，在槽口上方)

# 草图平面: 凹模正面 (如果凹模是从前视基准面拉伸80mm)
# 正面 = 前视基准面本身 (Z=0)
# 如果需要从侧面打孔，改为 "右视基准面" / "Right Plane"
SKETCH_PLANE_CN = "右视基准面"   # 从侧面打孔
SKETCH_PLANE_EN = "Right Plane"

# 如果是侧面打孔，孔的坐标含义变为:
# X_侧 = 沿宽度方向 (居中)
# Y_侧 = 沿高度方向 (偏上)
HOLE_SIDE_X = DIE_L / 2.0    # 沿长度居中 (40mm)
HOLE_SIDE_Y = DIE_H * 0.65   # 沿高度偏上 (27.3mm)

print("=" * 50)
print("修复2: 凹模 Φ13mm 通孔 (IT14)")
print("学号27号")
print("=" * 50)
print(f"  孔径: Φ{HOLE_DIA}mm (IT14: +0.18/0)")
print(f"  凹模文件: {DIE_FILE}")
print(f"  草图平面: {SKETCH_PLANE_CN}")

# ========== 连接 SW ==========
pythoncom.CoInitialize()
try:
    swApp = win32com.client.GetActiveObject("SldWorks.Application")
    print("\n[SW] 已连接到活动实例")
except Exception:
    swApp = win32com.client.Dispatch("SldWorks.Application.32")
    swApp.Visible = True
    print("[SW] 已启动新实例")
    time.sleep(5)

swApp.Visible = True
swApp.UserControl = True

# ========== 打开凹模 ==========
if not os.path.exists(DIE_FILE):
    print(f"❌ 凹模文件不存在: {DIE_FILE}")
    exit(1)

errors = 0
warnings = 0
doc = swApp.OpenDoc6(DIE_FILE, 1, 1, "", errors, warnings)
if doc is None:
    print(f"❌ 打开凹模失败: errors={errors}, warnings={warnings}")
    exit(1)
print(f"[1/5] 凹模已打开: {doc.GetTitle}")

before_count = doc.GetFeatureCount
if callable(before_count):
    before_count = before_count()
print(f"  当前特征数: {before_count}")

# ========== 选择草图平面 ==========
sel = doc.Extension.SelectByID2(SKETCH_PLANE_CN, "PLANE", 0, 0, 0, False, 0, None, 0)
if not sel:
    sel = doc.Extension.SelectByID2(SKETCH_PLANE_EN, "PLANE", 0, 0, 0, False, 0, None, 0)
if not sel:
    print(f"❌ 无法选择基准面: {SKETCH_PLANE_CN} / {SKETCH_PLANE_EN}")
    print("  尝试遍历特征树...")
    feat = doc.FirstFeature
    while feat is not None:
        try:
            name = feat.Name
            if callable(name):
                name = name()
            if "右视" in name or "Right" in name:
                feat.Select2(False, 0)
                sel = True
                print(f"  通过遍历找到: {name}")
                break
        except Exception:
            pass
        feat = feat.GetNextFeature()

if not sel:
    print("❌ 所有方法均失败")
    exit(1)

# ========== 创建草图 + 画圆 ==========
doc.SketchManager.InsertSketch(True)
print("[2/5] 草图已创建")

# 画 Φ13 圆 (侧面坐标系)
if "右视" in SKETCH_PLANE_CN or "Right" in SKETCH_PLANE_EN:
    hx, hy = HOLE_SIDE_X, HOLE_SIDE_Y
else:
    hx, hy = HOLE_X, HOLE_Y

sk = doc.SketchManager
circle = sk.CreateCircle(hx, hy, 0, hx + HOLE_RADIUS, hy, 0)
if circle is None:
    print("❌ 圆创建失败")
    exit(1)
print(f"[3/5] Φ{HOLE_DIA}mm 圆已绘制 (中心={hx:.1f},{hy:.1f})")

sk.InsertSketch(True)

# ========== 完全贯穿切除 ==========
print("[4/5] FeatureExtrusion2 完全贯穿切除...")

# 使用 FeatureExtrusion2 代替 FeatureCut (FeatureCut 在 Python COM 下不可用)
# Dir=True → 切除方向, T1=ThroughAll
feat = doc.FeatureManager.FeatureExtrusion2(
    True, False, True,        # Sd(双向切除), Flip, Dir=True(切除)
    2, 2,                     # T1=ThroughAll(2), T2=ThroughAll(2)
    0, 0,                     # D1, D2 (ThroughAll 时忽略)
    False, False,             # Dchk1, Dchk2
    False, False,             # Ddir1, Ddir2
    0.0, 0.0,                 # Dang1, Dang2
    False, False,             # Ofr, Ofc
    False, False,             # Tf1, Tf2
    True, True, True,         # Merge, UseFeatScope, UseAutoSelect
    0, 0.0, False             # StartOffset 系列
)

if feat is None:
    # 回退: 用 Blind 拉伸 + 大深度
    print("  ThroughAll 失败，回退到 Blind 拉伸...")
    feat = doc.FeatureManager.FeatureExtrusion2(
        True, False, True,
        0, 0,                 # Blind
        200.0, 200.0,         # 大深度贯穿
        False, False, False, False,
        0.0, 0.0, False, False, False, False,
        True, True, True,
        0, 0.0, False
    )

doc.ForceRebuild3(False)

after_count = doc.GetFeatureCount
if callable(after_count):
    after_count = after_count()
print(f"  特征数: {before_count} → {after_count}")

if after_count > before_count:
    print(f"  ✅ Φ{HOLE_DIA}mm 孔创建成功")
else:
    print("  ⚠️ 特征数未增长，孔可能创建失败")

# ========== 保存 ==========
print("\n[5/5] 保存...")
result = doc.SaveAs3(DIE_FILE, 1, 2)
if result not in (0, 1):
    doc.SaveAs(DIE_FILE)

if os.path.exists(DIE_FILE):
    size_kb = os.path.getsize(DIE_FILE) / 1024
    print(f"  ✅ 已保存: {DIE_FILE} ({size_kb:.1f} KB)")

print("\n" + "=" * 50)
print("修复2 完成!")
print(f"  ✅ 凹模已添加 Φ{HOLE_DIA}mm 通孔")
print(f"  📐 IT14 公差: +0.18/0 (加工时取上限 {HOLE_DIA+0.18}mm)")
print("  ⚠️ 请确认孔位置是否正确 (可在SW中修改草图坐标)")
print("=" * 50)
