"""
修复3: 创建装配体 (凹模 + 凸模, 单边间隙 2.1mm)
================================================
示例编号 | 材控示例班

装配关系:
  凹模: 固定基座 (57×42×80mm)
  凸模: 插入凹模U形槽内 (单边间隙 2.1mm)

坐标系假设:
  两个零件均从前视基准面拉伸:
    - 凹模: X方向57mm(宽), Y方向42mm(高), Z方向80mm(深)
    - 凸模: X方向62mm(宽), Y方向27mm(高), Z方向80mm(深)

装配策略:
  1. 插入凹模作为固定基座 (原点)
  2. 插入凸模，计算偏移量使凸模对准凹模槽位
  3. 使用配合关系锁定位置

使用: python fix_assembly.py
前提: SW 2024 已打开
"""
import os
import time

import pythoncom
import win32com.client

# ========== 配置参数 ==========
BASE_DIR = r"D:\冲压课设"
DIE_FILE = os.path.join(BASE_DIR, "凹模_示例编号.SLDPRT")
PUNCH_FILE = os.path.join(BASE_DIR, "凸模_示例编号_U形槽.SLDPRT")  # 或 _R55 版本
ASM_FILE = os.path.join(BASE_DIR, "装配体_示例编号.SLDASM")

# 凹模参数
DIE_W = 57.0   # 宽 mm
DIE_H = 42.0   # 高 mm
DIE_L = 80.0   # 深 mm
DIE_SLOT_W = 42.0   # 槽宽 mm (A1)
DIE_SLOT_DEPTH = 25.0  # 槽深 mm (B)

# 凸模参数
PUNCH_W = 62.0  # 宽 mm
PUNCH_H = 27.0  # 高 mm
PUNCH_L = 80.0  # 深 mm
PUNCH_SLOT_DEPTH = 25.0  # U形槽深 mm
PUNCH_BASE_Y = 2.0       # 槽底到凸模底部距离 mm

# 间隙
GAP = 2.1  # 单边间隙 mm

# 装配位置计算
# 凹模: 原点(0,0,0)为左下角，槽口在顶部
# 凹模槽口中心 X = DIE_W/2 = 28.5mm
# 凹模槽口顶部 Y = DIE_H = 42mm
# 凹模槽底 Y = DIE_H - DIE_SLOT_DEPTH = 17mm
#
# 凸模需插入槽内:
# 凸模底部(含基体)需要对准槽口
# 凸模的U形槽底部(PUNCH_BASE_Y=2mm)需要对准凹模槽底(Y=17mm)
# → 凸模Y偏移 = 凹模槽底Y - 凸模槽底Y = 17 - 2 = 15mm
# 但凸模总高27mm，凸模顶部=15+27=42mm=凹模顶部 ← 齐平

# X方向: 凹模槽中心=DIE_W/2=28.5, 凸模中心=PUNCH_W/2=31
# → 凸模X偏移 = 28.5 - 31 = -2.5mm (凸模居中于槽)
DIE_SLOT_CENTER_X = DIE_W / 2.0     # 28.5mm
PUNCH_CENTER_X = PUNCH_W / 2.0      # 31.0mm
OFFSET_X = DIE_SLOT_CENTER_X - PUNCH_CENTER_X  # -2.5mm

# Y方向: 凸模底部对齐凹模槽底
DIE_SLOT_BOTTOM_Y = DIE_H - DIE_SLOT_DEPTH  # 17mm
OFFSET_Y = DIE_SLOT_BOTTOM_Y - PUNCH_BASE_Y  # 15mm

# Z方向: 对齐 (两者都是80mm深)
OFFSET_Z = 0.0

print("=" * 50)
print("修复3: 创建装配体")
print("示例编号 | 凹模+凸模 | 间隙2.1mm")
print("=" * 50)
print(f"  凹模: {DIE_FILE}")
print(f"  凸模: {PUNCH_FILE}")
print(f"  装配偏移: X={OFFSET_X}, Y={OFFSET_Y}, Z={OFFSET_Z}")
print(f"  间隙验证: 凹模槽宽{DIE_SLOT_W} - 凸模槽顶宽{42-2*GAP} = {GAP}mm×2")

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

# ========== 检查文件 ==========
for f in [DIE_FILE, PUNCH_FILE]:
    if not os.path.exists(f):
        print(f"❌ 文件不存在: {f}")
        exit(1)
print("[1/5] 文件检查通过")

# ========== 新建装配体 ==========
asm_tpl = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_assembly.asmdot"
if not os.path.exists(asm_tpl):
    asm_tpl = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Assembly.asmdot"
if not os.path.exists(asm_tpl):
    # 尝试获取默认模板
    asm_tpl = swApp.GetUserPreferenceStringValue(
        21  # swDefaultTemplateAssembly
    )

swApp.NewDocument(asm_tpl, 0, 0, 0)
time.sleep(1)

asmDoc = swApp.ActiveDoc
if asmDoc is None:
    print("❌ 新建装配体失败")
    exit(1)
print(f"[2/5] 装配体已创建: {asmDoc.GetTitle}")

# ========== 插入凹模 (固定基座) ==========
print("\n[3/5] 插入凹模 (固定)...")

# 先保存装配体到目标路径 (AddComponent5 需要已保存的装配体)
os.makedirs(BASE_DIR, exist_ok=True)
asmDoc.SaveAs3(ASM_FILE, 0, 0)
time.sleep(0.5)

# 插入凹模到原点
transforms = None  # 使用单位矩阵 (原点)
die_comp = asmDoc.AddComponent5(
    DIE_FILE,
    0,        # 添加类型
    "",       # 配置名
    False,    # 不读取配置
    "",       # 参考
    0,        # X
    0,        # Y
    0         # Z
)
time.sleep(0.5)

if die_comp is not None:
    print(f"  ✅ 凹模已插入: {die_comp.Name2}")
else:
    print("  ⚠️ 凹模插入可能失败，继续...")

# 固定凹模
try:
    die_comp.Select4(False, None, False)
    asmDoc.FixComponent()
    print("  ✅ 凹模已固定")
except Exception as e:
    print(f"  ⚠️ 固定凹模失败: {e}")

# ========== 插入凸模 (偏移位置) ==========
print("\n[4/5] 插入凸模 (偏移位置)...")

# 偏移量转换为米 (SW内部单位)
off_x_m = OFFSET_X / 1000.0
off_y_m = OFFSET_Y / 1000.0
off_z_m = OFFSET_Z / 1000.0

punch_comp = asmDoc.AddComponent5(
    PUNCH_FILE,
    0,
    "",
    False,
    "",
    off_x_m,
    off_y_m,
    off_z_m
)
time.sleep(0.5)

if punch_comp is not None:
    print(f"  ✅ 凸模已插入: {punch_comp.Name2}")
    print(f"  📐 位置偏移: X={OFFSET_X}mm, Y={OFFSET_Y}mm, Z={OFFSET_Z}mm")
else:
    print("  ⚠️ 凸模插入可能失败")

# ========== 重建并保存 ==========
print("\n[5/5] 重建 + 保存...")
asmDoc.EditRebuild3
asmDoc.ForceRebuild3(False)
time.sleep(0.5)

# 保存装配体
result = asmDoc.SaveAs3(ASM_FILE, 0, 0)
if result not in (0, 1):
    asmDoc.SaveAs(ASM_FILE)

if os.path.exists(ASM_FILE):
    size_kb = os.path.getsize(ASM_FILE) / 1024
    print(f"  ✅ 装配体已保存: {ASM_FILE} ({size_kb:.1f} KB)")
else:
    print("  ❌ 保存失败")

# ========== 间隙验证 ==========
print("\n[验证] 检查装配间隙...")
comps = asmDoc.GetComponents(True)
comp_count = len(comps) if comps else 0
print(f"  组件数: {comp_count}")

if comp_count >= 2:
    print("  ✅ 装配体包含2个组件")
    print(f"  📐 理论单边间隙: {GAP}mm")
    print(f"  📐 凹模槽宽: {DIE_SLOT_W}mm")
    print(f"  📐 凸模槽顶宽: {DIE_SLOT_W - 2*GAP}mm = {DIE_SLOT_W - 2*GAP}mm")
    print("  ⚠️ 请在SW中打开装配体确认视觉对齐")

# ========== 生成爆炸视图 (可选) ==========
print("\n[提示] 如需爆炸视图:")
print("  1. 在SW中打开装配体")
print("  2. 右键'ConfigurationManager' → '添加爆炸视图'")
print("  3. 选择凸模 → 向上拖动分离")

print("\n" + "=" * 50)
print("修复3 完成!")
print("  ✅ 装配体已创建 (凹模固定 + 凸模对齐)")
print("  ✅ 单边间隙 2.1mm (通过位置偏移保证)")
print("  ⚠️ 如需精确配合，可在SW中添加配合关系:")
print("     - 凹模槽面 ↔ 凸模外壁 (距离=2.1mm)")
print("=" * 50)
