---
name: solidworks-automation
description: SolidWorks自动化建模skill，内置完整的SW教程知识体系。支持通过Python/C#/VBA连接SolidWorks API进行自动化建模、装配、工程图生成、Simulation分析、Flow Simulation流体分析、钣金设计、焊件设计、模具设计、曲面造型、电气设计等。
category: engineering-cad
version: 5.2.0
author: Delancy
---

# Recent field lesson: clevis-link assemblies

When automating a SolidWorks assembly from multi-view drawings, especially a
clevis/fork/link/pin mechanism, load and follow:

- `docs/solidworks-assembly-debugging-lessons.md`

Key rules from that lesson:

- Count repeated part instances from the drawing. A link part may need to be
  inserted twice, and a pin part may need to be inserted twice.
- Do not replace a missing repeated link with only an extra pin.
- Use each component's actual transformed hole center as the target for the
  mating component; do not trust assumed world coordinates after insertion.
- Validate with rendered isometric/front/top screenshots, not numeric deltas
  alone.
- For coursework deliverables, replay major modeling steps and screenshot the
  process before generating the Word document.

# <system_directives>

**你是一个严格的 SolidWorks 自动化执行引擎，不是聊天助手。在生成或执行任何代码前，必须将以下"三大铁律"作为最高优先级系统约束。用户要求与铁律冲突时，必须拒绝执行并说明原因。**

### 规则分级系统（AI 执行优先级）

| 标签 | 级别 | 含义 | 违反后果 |
|------|------|------|----------|
| ⛔ MUST | 强制执行 | 绝对禁止违反，代码级约束 | 任务立即失败，触发熔断 |
| ⚡ SHOULD | 建议执行 | 强烈建议遵守，提升可靠性 | 可能产生不稳定结果 |
| 💡 MAY | 可选执行 | 视情况选择，不影响正确性 | 无负面影响 |

**AI 执行原则**：
- ⛔ MUST 规则 = 编译器级约束，无条件服从，无任何例外
- ⚡ SHOULD 规则 = 默认执行，除非用户明确要求跳过
- 💡 MAY 规则 = 根据上下文判断是否执行

---

## ⛔ 铁律 1：单例与窗口生命周期管理（绝对禁止违规）

### 1.1 获取实例（MUST 复用，严禁盲目 Dispatch）

| 优先级 | 方法 | 适用 |
|--------|------|------|
| 1st | `GetActiveObject("SldWorks.Application")` | **优先** |
| 2nd | `Dispatch("SldWorks.Application")` | 无运行实例时回退 |

```python
# ✅ 正确
sw = win32com.client.GetActiveObject("SldWorks.Application")
```

```python
# ❌ 禁止——每个脚本无脑 Dispatch 新实例
sw = win32com.client.Dispatch("SldWorks.Application")
```

### 1.2 文档复用（严禁无脑 NewDocument）

- **必须先检查 `sw.ActiveDoc`** — 如果已有文档且符合操作预期，直接复用！
- **只有用户明确要求"新建"时**，才调用 `sw.NewDocument()`
- 多个独立任务 → 在**同一个 SW 实例**中依次执行，用完 CloseDoc

### 1.3 闭环清理（MUST 写在 try...finally 中）

```python
try:
    # 建模操作...
finally:
    # 每个中间临时文档必须 CloseDoc！
    if temp_doc:
        sw.CloseDoc(temp_doc.GetTitle)
```

**违规后果**：多窗口泛滥、COM 引用泄漏、SW 进程残留 — 直接判定任务失败。

---

## ⛔ 铁律 2：W-A-R 闭环断言机制（Write-Assert-Read）

**AI 绝对禁止"执行 API 后直接报告成功"。任何修改操作（Write）必须紧跟硬核断言（Assert）。**

### 2.1 Write：修改前提取"几何指纹"

```python
# 修改前：记录目标参数指纹
before_fingerprint = {
    'sketch_endpoint_x': skLine.GetStartPoint2()[0],  # 草图端点 X
    'dim_value': dim.GetSystemValue3(0),               # 标注值（米）
    'draft_angle': featDraft.GetDraftAngle(),           # 拔模角度
}
```

### 2.2 Assert：强制重建 + 错误检查（MUST）

```python
# 执行修改
dim.SetSystemValue3(target_m, 0, None)

# 步骤1：强制重建
rebuild_result = doc.EditRebuild3()

# 步骤2：检查重建错误码
if rebuild_result != 0:  # 0 = swRebuildAll
    raise SWAssertionError(f"重建失败！错误码: {rebuild_result}")

# 步骤3：硬断言
actual_value = dim.GetSystemValue3(0)
assert abs(actual_value - target_m) < 0.000001, \
    f"W-A-R 断言失败！目标: {target_m}, 实际: {actual_value}"
```

### 2.3 Read：断言失败 = 任务彻底失败

- 断言失败 → **必须抛出 `AssertionError` 并终止脚本**
- **严禁沉默捕获（catch pass）**
- **严禁在日志中掩饰失败**
- **严禁"改3D失败后在2D工程图强行改标注"**

---

## ⛔ 铁律 3：反幻觉与异常熔断（Zero Tolerance）

### 3.1 禁止伪造 API（Anti-Hallucination）

**任何不确定的 SW API 类名/方法名，必须先实机探测！**

```python
# ✅ 正确做法
import win32com.client
sw = win32com.client.GetActiveObject("SldWorks.Application")
doc = sw.ActiveDoc

# 探测可用方法
sketch_mgr = doc.SketchManager
print([m for m in dir(sketch_mgr) if 'Constraint' in m or 'Relation' in m])
# 输出: ['AddConstraint', 'DeleteConstraint', ...] → 确认后再用

# ❌ 禁止——靠 LLM 记忆盲猜 API
doc.SketchManager.AddRelation(...)  # 忘了是 AddConstraint 还是 AddRelation？
```

### 3.2 异常熔断机制

遇到以下情况，**禁止静默捕获**，必须输出完整 Traceback 并声明：

```
操作失败，触发熔断。
文件: <脚本名>.py
行号: <N>
错误类型: COMError / AssertionError / NullReferenceException
当前特征树状态:
  特征总数: <N>
  最后特征: <名称>
策略: 请求人工介入或更改建模策略。
```

### 3.3 约束冲突处理

- 草图过定义 → 必须先调用 API `DeleteConstraint()` 删除冲突约束
- 严禁跳过约束报错或伪造无约束的草图

</system_directives>

---

# SolidWorks 自动化建模 Skill（自包含版）

本skill内置了SolidWorks从入门到精通的全套知识体系，不需要依赖外部知识库。

## ⚠️ SW 2024 Python COM 关键踩坑（2026-05-30 实战验证）

### 环境
- SW 2024 (中文版), Python 3.14 + pywin32, Windows 11

### 连接方式
| 方式 | 结果 |
|------|------|
| `win32com.client.Dispatch("SldWorks.Application")` | ✅ 可用 |
| `win32com.client.gencache.EnsureDispatch(...)` | ❌ "COM object can not automate makepy" |
| `win32com.client.Dispatch("SldWorks.Application.28/32")` | ✅ 可用 |
| `makepy.GenerateFromTypeLibSpec(...)` | ❌ 找不到类型库 |
| `gencache.EnsureModule(GUID, 0, 32, 0)` | ✅ 可生成缓存但不改变绑定方式 |

### 参数传递（核心！）
- **SelectByID2 (9参数)**: 必须用 `VARIANT(pythoncom.VT_xxx, value)` 包装**每个参数**
- **FeatureExtrusion2 (23参数)**: 直接传原生类型即可（不需要VARIANT包装）
- **FeatureFillet3**: 直接传参即可
- **SketchManager方法**: 直接传参即可

### 各 API 可用性（SW 2024 Python COM）

| API | 参数数 | Python COM | 备注 |
|-----|:---:|:---:|------|
| `NewDocument(template_path, ...)` | 4 | ✅ 完整路径 | 空字符串不行！必须用`gb_part.prtdot`完整路径 |
| `SelectByID2` | 9 | ✅ VARIANT | 中文"前视基准面"可直接用 |
| `FeatureExtrusion2` | 23 | ✅ | **不是旧版的17参数** |
| `FeatureExtrusion3` | 23 | ✅ | 同2 |
| `FeatureCut` | 20 | ❌ 返回None | 参数匹配但特征不创建 |
| `FeatureCut3` | 26 | ❌ 返回None | 同上 |
| `FeatureCut4` | 27 | ❌ 返回None | **>12参数的COM IDispatch限制** |
| `FeatureFillet3(122,...)` | 7 | ✅ | 等半径圆角, 需先预选边 |
| `SimpleHole` | ? | ❌ 参数不匹配 | |
| `SimpleHole2` | ? | ❌ 参数不匹配 | |
| `HoleWizard5` | 25+ | ❌ 类型/参数不匹配 | |
| `RunMacro(.swb)` | 3 | ❌ 返回False | |
| `RunMacro2(.swb)` | 3 | ❌ 类型不匹配 | |
| `InsertCombineFeature` | 3 | ❌ 类型不匹配 | |
| `GetBodies2` | 1 | ❌ 参数不匹配 | |
| `CloseDoc` | 1 | ✅ | title用`doc.GetTitle`(属性)不是`GetTitle()` |
| `GetDocuments` | 0 | ✅ | 返回tuple, 属性不是方法 |

### 应急方案：加法建模策略
当 FeatureCut 不可用时，用 FeatureExtrusion2 加法构建零件：
- 底板 + 左壁 + 右壁 = 凹模（直槽）
- 圆角用 FeatureFillet3
- 孔位用 FeatureExtrusion2 做标记(1mm凸台)，手动切除

### 形态识别：水平叉头 vs 竖直叉耳支座
遇到三视图零件图时，先判断主形态，不能只看到"叉耳/clevis"就套用水平叉头模板。

| 图纸信号 | 正确类别 | 建模入口 |
|---|---|---|
| 圆形底座 Φ150×30，上方两片竖耳，耳间开槽，正视有 Φ18 孔，侧视槽底高 20 | 竖直叉耳支座 | `src/clevis-joint/vertical_clevis_support.py` |
| 水平扁柄 + 端部叉口，整体沿 X 方向伸展 | 水平叉形接头 | `src/clevis-joint/clevis_fork_*.py` 或 `Clevis_Joint.cs` |

竖直叉耳支座推荐策略：圆盘底座用 Top Plane 圆拉伸；槽底以下先建 60mm 深的实体桥；槽底以上再用 Front Plane 半圆顶轮廓分别拉伸两片耳板到槽两侧，形成中间贯通镂空槽；孔用 C#/VBA `FeatureCut4` 或手工贯穿切除。Python COM 直连切除失败时，只允许创建清晰孔位标记并报告失败，严禁宣称已完成通孔。

### 模板路径
```python
TEMPLATE = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
doc = sw.NewDocument(TEMPLATE, 0, 0, 0)  # 必须完整路径
```

### FeatureExtrusion2 23参数签名 (SW2024)
```python
doc.FeatureManager.FeatureExtrusion2(
    Sd, Flip, Dir,       # 1-3: Bool
    T1, T2,              # 4-5: Int (0=Blind)
    D1, D2,              # 6-7: Double (米)
    Dchk1, Dchk2,        # 8-9: Bool
    Ddir1, Ddir2,        # 10-11: Bool
    Dang1, Dang2,        # 12-13: Double (弧度)
    Ofr,                 # 14: Bool
    Ofc,                 # 15: Bool
    Tf1, Tf2,            # 16-17: Bool
    Merge,               # 18: Bool
    UseFeatScope,        # 19: Bool
    UseAutoSelect,       # 20: Bool
    StartOffset,         # 21: Double
    IsAutoStartOffset,   # 22: Bool
    FlipStartOffset      # 23: Bool
)
```

---

## 一、SolidWorks 基础知识

### 1.1 SolidWorks 概述

SolidWorks是Dassault Systemes公司开发的基于Windows的三维CAD软件，是世界上第一个基于Windows开发的三维CAD系统。采用参数化特征建模技术，支持：

- **三大基本模块**: 零件（Part）、装配体（Assembly）、工程图（Drawing）
- **FeatureManager设计树**: 记录零件的建模历史，可回溯编辑
- **参数化驱动**: 尺寸驱动几何形状变化
- **特征建模**: 通过拉伸、旋转、扫描、放样等特征构建零件

### 1.2 软件工作界面

- **菜单栏**: 提供所有操作命令
- **CommandManager**: 上下文关联的工具栏
- **FeatureManager设计树**: 左栏，显示所有特征历史
- **图形区域**: 三维模型显示区域
- **任务窗格**: 资源、设计库、文件探索器等
- **状态栏**: 显示当前操作状态和提示

### 1.3 文件类型

| 类型 | 扩展名 | 说明 |
|------|--------|------|
| 零件 | .sldprt | 单一零件模型 |
| 装配体 | .sldasm | 多零件装配 |
| 工程图 | .slddrw | 二维工程图 |
| 模板 | .prtdot/.asmdot/.drwdot | 零件/装配体/工程图模板 |
| 库特征 | .sldlfp | 可复用的特征库 |

## 二、草图绘制

### 2.1 基准面

三个默认基准面：
- **前视基准面 (Front Plane)**: XZ平面
- **上视基准面 (Top Plane)**: XY平面  
- **右视基准面 (Right Plane)**: YZ平面

### 2.2 草图实体

**基本实体**:
- 直线 (Line)、中心线 (CenterLine)、圆 (Circle)、圆弧 (Arc)
- 矩形 (Rectangle)、槽口 (Slot)、多边形 (Polygon)
- 样条曲线 (Spline)、椭圆 (Ellipse)、抛物线、文字 (Text)

**草图工具**:
- 圆角 (Sketch Fillet)、倒角 (Sketch Chamfer)
- 等距实体 (Offset Entities)、转换实体引用 (Convert Entities)
- 镜像 (Mirror)、阵列 (Sketch Pattern)、剪裁 (Trim)、延伸 (Extend)

### 2.3 几何关系与尺寸标注

**常见几何关系**: 水平、竖直、共线、垂直、平行、相切、同心、中点、重合、对称、相等、固定、穿透

**尺寸类型**: 线性尺寸、角度尺寸、直径/半径、弧长

### 2.4 API 草图操作

```python
import win32com.client

sw_app = win32com.client.Dispatch("SldWorks.Application")
sw_app.Visible = True
sw_model = sw_app.ActiveDoc  # 或 sw_app.NewPart()

# 选择基准面
sw_model.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)

# 创建2D草图
sw_model.SketchManager.InsertSketch(True)

# 绘制直线
sw_model.SketchManager.CreateLine(x1, y1, z1, x2, y2, z2)

# 绘制圆（中心坐标+半径）
sw_model.SketchManager.CreateCircle(cx, cy, cz, rx, ry, rz)

# 绘制三点圆弧
sw_model.SketchManager.Create3PointArc(x1, y1, z1, x2, y2, z2, x3, y3, z3)

# 添加尺寸
sw_model.AddDimension2(x, y, z)

# 退出草图
sw_model.SketchManager.InsertSketch(True)

# 3D草图
sw_model.SketchManager.Insert3DSketch(True)
```

## 三、零件特征建模

### 3.1 基础特征

#### 拉伸特征 (Extrude)
- **拉伸凸台/基体**: FeatureExtrusion3
- **拉伸切除**: FeatureCut4  
- **拉伸方向**: 单向、双向、两侧对称、到指定面
- **拔模角度**: 可添加拔模

```python
# 拉伸凸台（单向，深度=0.1m）
sw_model.FeatureManager.FeatureExtrusion3(
    True,      # 单向拉伸
    False,     # 是否反向
    False,     # 双向拉伸
    0, 0,      # 拉伸类型
    0.1, 0.1,  # 深度
    False,     # 带拔模
    False,     # 带拔模方向
    False, False, 0, 0, False, False, False, False
)

# 拉伸切除
sw_model.FeatureManager.FeatureCut4(
    True, False, False, 0, 0, 0.05, 0.05, 
    False, False, False, False, 0, 0, False, False, False, False
)
```

#### 旋转特征 (Revolve)
- **旋转凸台/基体**: FeatureRevolve2
- **旋转切除**: FeatureRevolveCut

```python
# 旋转凸台（360度）
sw_model.FeatureManager.FeatureRevolve2(
    True, True, False, False, 0, 0, 6.28318, 0,
    False, False, 0, 0, True, True, True
)
```

#### 扫描特征 (Sweep)
- 轮廓沿路径移动生成实体
- 基本扫描: 仅轮廓+路径
- 带引导线扫描: 可控制中间截面
```python
# 创建扫描
sw_model.FeatureManager.InsertProtrusionSwept3(
    False, False, 0, 0, False, 0, 0,
    False, 0, 0, True, True, 2, True, True, False, ""
)
```

#### 放样特征 (Loft)
- 多个截面之间过渡生成实体  
- 可使用引导线控制形状
```python
# 创建放样
sw_model.FeatureManager.InsertProtrusionBlend(
    False, True, False, 1, 0, 0,
    False, True, False, 1, 0, 0, 1
)
```

### 3.2 工程特征

**圆角 (Fillet)**:
```python
# 等半径圆角（半径=0.005m）
sw_model.FeatureManager.FeatureFillet3(122, 0.005, 0, 0, 0, 0, 0)
```

**倒角 (Chamfer)**:
```python
# 等距离倒角（距离=0.003m，45度）
sw_model.FeatureManager.FeatureChamfer(1, 0.003, 0.003, 0.785398, 0, 0, 0)
```

**抽壳 (Shell)**:
```python
# 抽壳（壁厚=0.002m）
sw_model.FeatureManager.FeatureShell(0.002, False)
```

**筋 (Rib)**:
```python
# 创建筋特征
sw_model.FeatureManager.InsertRib(True, True, False, True, 0, 0.005, 0.005, False, False)
```

**孔 (Hole)**:
```python
# 简单直孔
sw_model.FeatureManager.HoleWizard5(1, 0, 0, "", 0.01, 0.05, 0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, False, False, True, True, True, True, False, "")
```

### 3.3 阵列与镜像

```python
# 线性阵列
sw_model.FeatureManager.FeatureLinearPattern2(
    3, 0.05, 2, 0.05, False, False, "TRUE", "FALSE", False, False, True, True, True, True, False
)

# 圆周阵列（6个实例，360度）
sw_model.FeatureManager.FeatureCircularPattern2(6, 6.28318, False, "NULL", False)

# 镜像特征
sw_model.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
sw_model.FeatureManager.InsertMirrorFeature(False, False, False, False)
```

### 3.4 材料与质量属性

```python
# 设置材料
sw_model.SetMaterialPropertyName2("Default", "SOLIDWORKS Materials", "Aluminum Alloy")

# 获取质量属性
mass_props = sw_model.Extension.CreateMassProperty()
print(f"质量: {mass_props.Mass} kg")
print(f"体积: {volume} m³")
```

## 四、装配体设计

### 4.1 装配基础

```python
# 创建新装配体
sw_app.NewAssembly()

# 添加零部件
sw_model.AddComponent("D:/parts/gear.sldprt", x, y, z)

# 移动/旋转零部件
sw_model.Extension.SelectByID2("Part1", "COMPONENT", 0, 0, 0, False, 0, None, 0)
sw_model.MoveComponent(x, y, z)
sw_model.RotateComponent(rx, ry, rz)
```

### 4.2 配合关系

配合类型常量:
- **0**: 重合 (Coincident)
- **1**: 同心 (Concentric)
- **2**: 垂直 (Perpendicular)
- **3**: 平行 (Parallel)
- **4**: 相切 (Tangent)
- **5**: 距离 (Distance)
- **6**: 角度 (Angle)
- **7**: 锁定 (Lock)
- **8**: 对称 (Symmetric)

```python
# 添加配合
sw_model.AddMate3(
    mate_type,      # 配合类型（0-8）
    alignment,      # 对齐方向
    flip,           # 翻转
    distance,       # 距离值（距离配合时使用）
    angle,          # 角度值（角度配合时使用）
    0, 0, 0, 0, 0, False
)
```

### 4.3 干涉检查与爆炸视图

```python
# 干涉检查
sw_model.ToolsCheckInterference2(0)

# 爆炸视图
sw_model.Extension.CreateExplodeView("ExplodeView1")
```

## 五、工程图制作

### 5.1 工程图基础

```python
# 创建工程图（使用模板）
sw_model = sw_app.NewDocument(template_path, 0, 0, 0)

# 添加三视图（第三角投影）
sw_model.Create3rdAngleViews2(part_path)

# 添加命名视图
sw_model.CreateDrawViewFromModelView2(part_path, "*Front", x, y, 0)
sw_model.CreateDrawViewFromModelView2(part_path, "*Top", x, y, 0)
sw_model.CreateDrawViewFromModelView2(part_path, "*Right", x, y, 0)

# 添加等轴测视图
sw_model.CreateDrawViewFromModelView2(part_path, "*Isometric", x, y, 0)

# 添加剖视图
sw_model.CreateSectionView(x, y, 0)
```

### 5.2 尺寸与标注

```python
# 添加水平尺寸
sw_model.AddHorizontalDimension2(x, y, annotation_y)

# 添加垂直尺寸
sw_model.AddVerticalDimension2(x, y, annotation_y)

# 添加表面粗糙度
sw_model.Extension.SelectByID2("Face<1>", "FACE", 0, 0, 0, False, 0, None, 0)
sw_model.InsertSurfaceFinish(0, 0.0000032, 0, 0)
```

### 5.3 图纸格式

- **A0**: 1189×841mm
- **A1**: 841×594mm
- **A2**: 594×420mm
- **A3**: 420×297mm
- **A4**: 297×210mm

## 六、高级曲面设计

### 6.1 曲面创建

```python
# 拉伸曲面
sw_model.FeatureManager.FeatureExtrusionSurface(
    True, False, False, 0, 0, 0.1, False, False, False, False, 0, 0, False, False, False, False
)

# 旋转曲面
sw_model.FeatureManager.FeatureRevolveSurface(
    True, False, False, 0, 0, 6.28318, 0, False, False, 0, 0, True, True, True
)

# 放样曲面
sw_model.FeatureManager.InsertBlendSurface(False, True, False, 1, 0, 0)

# 扫描曲面
sw_model.FeatureManager.InsertSweptSurface(False, False, 0, True, 0, 0)
```

### 6.2 曲面编辑

```python
# 曲面缝合（合并曲面）
sw_model.FeatureManager.InsertKnitSurface(0.00001)

# 曲面延伸
sw_model.FeatureManager.ExtendSurface(0, 0.01, 0)

# 曲面剪裁
sw_model.FeatureManager.InsertTrimSurface(0)

# 加厚曲面为实体
sw_model.FeatureManager.InsertThicken(0.005, True, False, False, 0, False)
```

### 6.3 曲面设计要点

1. **曲面质量**: 控制曲面G0/G1/G2连续性
2. **斑马条纹**: 检查曲面光顺度
3. **曲面实体化**: 封闭曲面可转化为实体
4. **混合建模**: 曲面+实体混合创建复杂形状

## 七、钣金设计

### 7.1 钣金基础

```python
# 创建钣金零件
sw_app.NewPart()

# 基体法兰 - 创建方法1：使用FeatureBaseFlange
sw_model.FeatureManager.FeatureBaseFlange(
    thickness,   # 板厚
    reverse,     # 反向
    0, 0, 0, 0,  # 附加选项
    False        # useGaugeTable
)

# 边线法兰
sw_model.SelectByID2("Edge<1>", "EDGE", 0, 0, 0, False, 0, None, 0)
sw_model.FeatureManager.FeatureEdgeFlange(
    length,      # 法兰长度
    angle,       # 折弯角度（通常90度）
    0, 0, 0, 0   # 附加选项
)

# 斜接法兰
sw_model.FeatureManager.FeatureMiterFlange()

# 褶边
sw_model.FeatureManager.FeatureHem(0, 0, 0.005, 0, 0)

# 转折
sw_model.FeatureManager.FeatureJog(0.01, 90, 0.01, 0, 0, 0)
```

### 7.2 钣金成形工具

```python
# 使用成形工具创建凹凸特征
sw_model.CreateFeatureFromBody2("FormingTool.sldprt")
```

### 7.3 钣金展开

```python
# 展开钣金件
sw_model.FeatureManager.InsertUnfold()

# 折叠钣金件
sw_model.FeatureManager.InsertFold()

# 创建展开图
sw_model.Extension.SelectByID2("Face<1>", "FACE", 0, 0, 0, False, 0, None, 0)
sw_model.FlatPatternUnfold()
```

### 7.4 钣金参数

- **折弯系数**: K因子、折弯补偿、折弯扣除
- **折弯半径**: 默认等于板厚
- **释放槽**: 矩形、撕裂形、矩圆形

## 八、焊件设计

### 8.1 焊件基础

```python
# 激活焊件环境
sw_model.InsertWeldmentFeature()

# 3D草图中创建结构框架
sw_model.SketchManager.Insert3DSketch(True)
# ... 绘制3D草图线条 ...
sw_model.SketchManager.Insert3DSketch(True)

# 添加结构构件
sw_model.FeatureManager.InsertStructuralMember2(
    "iso",           # 标准库
    "40x40x3",       # 构件规格
    0, 0, 0          # 定位
)

# 剪裁构件
sw_model.FeatureManager.InsertTrimMember()
```

### 8.2 焊缝与子焊件

```python
# 添加角撑板
sw_model.SelectByID2("Face<1>", "FACE", 0, 0, 0, False, 0, None, 0)
sw_model.FeatureManager.InsertWeldmentGussetPlate(0.01, 0.01, 0.005, 0, 0)

# 添加顶端盖
sw_model.SelectByID2("Face<1>", "FACE", 0, 0, 0, False, 0, None, 0)
sw_model.FeatureManager.InsertEndCap(0.002, 0, 0, 0, 0, 0, 0, 0, 0)
```

### 8.3 焊件切割清单

焊件自动生成切割清单BOM，包括：
- 构件描述、长度、角度、材质、重量

## 九、模具设计

### 9.1 模具设计流程

1. **产品分析**: 拔模分析、底切分析
2. **分型线**: 创建分型线
3. **分型面**: 创建分型曲面
4. **型腔/型芯**: 分割模具
5. **浇注系统**: 浇口、流道设计

### 9.2 模具工具API

```python
# 拔模分析
sw_model.Extension.DraftAnalysis()

# 创建分型线
sw_model.FeatureManager.InsertPartingLine()

# 关闭曲面
sw_model.FeatureManager.InsertShutOffSurfaces()

# 分型面
sw_model.FeatureManager.InsertPartingSurface(0.01, 10, True, 0, 0, 0, 0, 0, 0, 0, 0)

# 切削分割（生成型腔和型芯）
sw_model.FeatureManager.InsertToolingSplit(True)
```

### 9.3 冲压模具设计专用API（实战反馈新增）

**模具结构类型对比**：

| 类型 | 适用场景 | 特点 |
|------|----------|------|
| 单工序模 | 大批量、单一工序 | 结构简单，效率低 |
| 复合模 | 高精度、小批量 | 一次冲程完成两道工序 |
| 级进模 | 大批量、小型件 | 高效率，适合自动化 |

**冲裁间隙选择表**（材料厚度 t）：

| 材料 | 单边间隙 Z/2 | 说明 |
|------|---------------|------|
| 08/10钢 (t≤3mm) | 0.06~0.09t | 取下限 |
| 铝/铜 | 0.02~0.06t | 软材料间隙小 |
| 不锈钢 | 0.10~0.15t | 硬材料间隙大 |

**刃口尺寸计算公式**：
- 落料（以外形尺寸为基准）：凹模 = 工件外径，凸模 = 凹模 - 2×单边间隙
- 冲孔（以内孔尺寸为基准）：凸模 = 工件内径，凹模 = 凸模 + 2×单边间隙
- 制件公差 IT14 时，刃口公差取制件公差的 1/4

```
实例（垫圈 D=53mm, d=34mm, t=2.5mm, 08钢）：
  凹模落料刃口 = 53 - 0.37 = 52.63⁺⁰·⁰² mm
  凸模落料刃口 = 52.63 - 2×0.09 = 52.45⁻⁰·⁰² mm
  凸模冲孔刃口 = 34 + 0.31 = 34.31⁺⁰·⁰² mm
  凹模冲孔刃口 = 34.31 + 2×0.09 = 34.49⁺⁰·⁰² mm
  双面间隙 Z = 0.18 mm
```

### 9.4 凸凹模建模实战（实战反馈新增）

**三基准统一原则**：所有旋转体零件轴线通过原点 → 装配时只需「重合」即可对位

```python
import win32com.client

sw_app = win32com.client.Dispatch("SldWorks.Application")
sw_app.Visible = True

# 步骤1：主体圆柱（φ65×45mm）
sw_model.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
sw_model.SketchManager.InsertSketch(True)
sw_model.SketchManager.CreateCircle(0, 0, 0, 0.0325, 0, 0)  # φ65mm
sw_model.SketchManager.InsertSketch(True)
sw_model.FeatureManager.FeatureExtrusion3(
    True, False, False, 0, 0, 0.045, 0.045,
    False, False, False, False, 0, 0, False, False, False, False)

# 步骤2：顶面刃口凸台（落料部分，φ52.45×15mm）
sw_model.Extension.SelectByID2("Top Face", "FACE", 0, 0, 0.045, False, 0, None, 0)
sw_model.SketchManager.InsertSketch(True)
sw_model.SketchManager.CreateCircle(0, 0, 0, 0.026225, 0, 0)
sw_model.SketchManager.InsertSketch(True)
sw_model.FeatureManager.FeatureExtrusion3(
    True, False, False, 0, 0, 0.015, 0.015,
    False, False, False, False, 0, 0, True, False, False, False)

# 步骤3：底面贯穿切除（冲孔凹模刃口，φ34.49mm）
sw_model.Extension.SelectByID2("Bottom Face", "FACE", 0, 0, 0, False, 0, None, 0)
sw_model.SketchManager.InsertSketch(True)
sw_model.SketchManager.CreateCircle(0, 0, 0, 0.017245, 0, 0)
sw_model.SketchManager.InsertSketch(True)
sw_model.FeatureManager.FeatureExtrusion2(
    True, True, True, 0, 0, 0, 0,
    False, False, False, False, 0, 0, False, False, False, False)

# 步骤4：刃口倒角 C0.5
sw_model.SelectByID2("", "EDGE", 0.0325, 0, 0.06, False, 0, None, 0)
sw_model.FeatureManager.FeatureChamfer(1, 0.0005, 0.0005, 0.785398, 0, 0, 0)
```

### 9.5 装配体配合自动化

**配合类型常量速查**：0=重合, 1=同心, 2=垂直, 3=平行, 4=相切, 5=距离, 6=角度, 7=锁定, 8=对称

```python
sw_model.AddMate3(0, 0, False, 0, 0, 0, 0, 0, 0)  # 重合配合
sw_model.AddMate3(1, 0, False, 0, 0, 0, 0, 0, 0)  # 同心配合
mate = sw_model.AddMate3(5, 0, False, 0.020, 0, 0, 0, 0, 0, 0)  # 距离=20mm
interference = sw_model.ToolsCheckInterference2(0)  # 干涉检查
```

### 9.6 工程图自动标注

```python
drawing = sw_app.NewDocument(r'...\gb_a3.drwdot', 0, 0, 0)
drawing.Create3rdAngleViews2(part_path)
sw_model.InsertSurfaceFinish(0, 0.0000032, 0, 0)   # Ra=3.2μm
sw_model.InsertGtol2(0, 0, 0, 0)                   # 形位公差框格
drawing.Extension.SaveAs('output.pdf', 0, 0, None, False, False, None, 0)
```

### 9.7 模具材料与热处理

| 零件 | 推荐材料 | 热处理 | 硬度 |
|------|----------|--------|------|
| 凸模/凹模/凸凹模 | Cr12MoV | 淬火+回火 | HRC 58~64 |
| 垫板 | T10A / 45钢 | 淬火 | HRC 50~54 |
| 卸料板/固定板 | 45钢 | 调质 | HRC 28~32 |
| 上下模座 | HT200 / Q235 | 退火 | HB 180~220 |

### 9.8 国标（GB）规范

- GB/T 8845-2017《模具术语》、GB/T 2851~2861 冲模标准模架、GB/T 14662-2006《冲模技术条件》
- 未注公差按 IT14 查 GB/T 1804-2000《一般公差》

## 十、Simulation 有限元分析

### 10.1 分析类型

- **静应力分析**: 线性静力问题
- **频率分析**: 模态分析
- **屈曲分析**: 失稳分析
- **热力分析**: 温度场
- **跌落测试**: 冲击问题
- **疲劳分析**: 循环载荷
- **非线性分析**: 材料/几何非线性
- **线性动力分析**: 谐响应、随机振动

### 10.2 静力学分析API

```python
# 加载Simulation插件
sw_addin = sw_app.GetAddInObject("SldWorks Simulation")

# 创建算例
sw_study = sw_addin.CreateNewStudy2(
    0,              # 静应力分析
    "StaticStudy",  # 算例名称
    "",             # 配置文件
    0               # 选项
)

# 设置材料
sw_model.SetMaterialPropertyName2("Default", "SOLIDWORKS Materials", "1060 Alloy")

# 添加夹具（固定几何体）
sw_study.FixComponent("Fixed-1", ["Face<1>"])

# 添加外部载荷（力）
sw_study.ApplyForce("Force-1", ["Face<2>"], 
    Fx, Fy, Fz,     # 力分量（N）
    False            # 每实体
)

# 添加压力
sw_study.ApplyPressure("Pressure-1", ["Face<3>"],
    100000,          # 压力值（Pa）
    0, 0             # 选项
)

# 网格划分
sw_study.CreateMesh()

# 运行分析
sw_study.RunAnalysis()
```

### 10.3 结果查看

- **应力 (Von Mises)**: 查看应力分布
- **位移 (URES)**: 查看位移分布
- **应变 (ESTRN)**: 查看应变分布
- **安全系数 (FOS)**: 查看安全余量

## 十一、Flow Simulation 流体分析

### 11.1 分析类型

- **内流分析**: 管道、阀门内部流动
- **外流分析**: 绕流问题
- **热传导**: 共轭传热
- **多孔介质**: 过滤问题
- **旋转区域**: 旋转机械

### 11.2 Flow Simulation API

```python
# 加载Flow Simulation插件
sw_flow = sw_app.GetAddInObject("SldWorks Flow.Simulation")

# 创建新项目
sw_project = sw_flow.CreateProject("Project1", "", 0)

# 设置计算域
sw_project.SetComputationalDomain(xmin, xmax, ymin, ymax, zmin, zmax)

# 设置流体介质
sw_project.SetFluid("Air", 0, 0, 0)  # 空气

# 设置边界条件
# 入口（流速/压力）
sw_project.SetBoundaryCondition("Inlet1", ["Face<1>"], "Inlet Velocity", 
    velocity, 0, 0, 0)
# 出口（环境压力）
sw_project.SetBoundaryCondition("Outlet1", ["Face<2>"], "Environment Pressure",
    0, 0, 0, 0)
# 壁面
sw_project.SetBoundaryCondition("Wall", ["Face<3>"], "Real Wall", 0, 0, 0, 0)

# 设置工程目标
sw_project.SetGoals(["Pressure Drop", "Mass Flow Rate", "Velocity"])

# 运行求解
sw_project.Run()
```

### 11.3 网格与结果

- **全局网格**: 基础网格设置
- **局部网格**: 细化特定区域
- **结果可视化**: 速度矢量图、压力云图、流线、粒子追踪
- **目标图**: 收敛监控

## 十二、其他高级功能

### 12.1 模型渲染 (PhotoView 360)

```python
# 设置外观
sw_model.SetMaterialPropertyName2("Default", "", "Appearance Name")

# 设置场景
sw_model.Extension.SetScene("Studio Scene")

# 渲染输出
sw_model.Extension.RenderToFile(output_path)
```

### 12.2 动画制作

```python
# 创建运动算例
sw_model.Extension.CreateMotionStudy("MotionStudy1")

# 添加马达
sw_model.AddMotor(0, 0, 360, 0, 0, 0)  # 旋转马达

# 设置时间
sw_model.SetMotionStudyProperties("MotionStudy1", 5, 25)  # 5秒, 25fps
```

### 12.3 配置管理

```python
# 创建配置
sw_model.AddConfiguration("Config1", "", "", 0)

# 切换配置
sw_model.ShowConfiguration2("Config1")

# 删除配置
sw_model.DeleteConfiguration("Config1")
```

### 12.4 设计表 (Excel驱动)

```python
# 创建设计表
sw_model.FeatureManager.InsertTableDesign()
```

### 12.5 参数化设计完整示例

```python
import win32com.client

def create_parametric_gear(module, teeth, width):
    """参数化创建齿轮"""
    sw_app = win32com.client.Dispatch("SldWorks.Application")
    sw_app.Visible = True
    sw_app.NewPart()
    sw_model = sw_app.ActiveDoc
    
    # 计算参数
    pitch_diameter = module * teeth / 1000
    outer_diameter = module * (teeth + 2) / 1000
    root_diameter = module * (teeth - 2.5) / 1000
    
    # 绘制齿坯
    sw_model.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
    sw_model.SketchManager.InsertSketch(True)
    sw_model.SketchManager.CreateCircle(0, 0, 0, outer_diameter/2, 0, 0)
    sw_model.SketchManager.InsertSketch(True)
    sw_model.FeatureManager.FeatureExtrusion3(
        True, False, False, 0, 0, width/1000, width/1000,
        False, False, False, False, 0, 0, False, False, False, False
    )
    
    print(f"齿轮创建完成: 模数={module}, 齿数={teeth}, 宽度={width}mm")
    return sw_model

# 使用示例
create_parametric_gear(module=2, teeth=30, width=20)
```

## 十三、批量操作与文件转换

### 13.1 批量文件处理

```python
import os

def batch_convert_sldprt_to_step(input_dir, output_dir):
    """批量将.sldprt转换为.step"""
    sw_app = win32com.client.Dispatch("SldWorks.Application")
    sw_app.Visible = True
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".sldprt"):
            filepath = os.path.join(input_dir, filename)
            outpath = os.path.join(output_dir, filename.replace(".sldprt", ".step"))
            
            # 打开零件
            sw_model = sw_app.OpenDoc6(filepath, 1, 0, "", 0, 0)
            
            # 导出STEP
            sw_model.Extension.SaveAs(outpath, 0, 0, None, False, False, None, 0)
            
            # 关闭文档
            sw_app.CloseDoc(sw_model.GetTitle())
            
    print("批量转换完成！")

def batch_print_drawings(drawing_dir):
    """批量打印工程图"""
    sw_app = win32com.client.Dispatch("SldWorks.Application")
    sw_app.Visible = True
    
    for filename in os.listdir(drawing_dir):
        if filename.endswith(".slddrw"):
            filepath = os.path.join(drawing_dir, filename)
            
            # 打开工程图
            sw_model = sw_app.OpenDoc6(filepath, 3, 0, "", 0, 0)
            
            # 打印
            sw_model.PrintOut2(1, 1, 1, False, "", 0, 0)
            
            # 关闭文档
            sw_app.CloseDoc(sw_model.GetTitle())
    
    print("批量打印完成！")
```

### 13.2 支持的文件格式导出

| 格式 | 用途 |
|------|------|
| *.step / *.stp | 通用三维交换格式 |
| *.iges / *.igs | 通用三维交换格式 |
| *.stl | 3D打印 |
| *.dxf / *.dwg | 二维CAD |
| *.pdf | 文档分享 |
| *.jpg / *.png | 图片渲染 |

## 十四、SolidWorks API 完整参考

### 14.1 核心API对象层次

```
SldWorks.Application
├── ActiveDoc (IModelDoc2)
│   ├── FeatureManager
│   ├── SketchManager
│   ├── Extension
│   │   └── SelectByID2()
│   └── ConfigurationManager
├── GetAddInObject("plugin_name")
└── Documents
```

### 14.2 常用API命令速查

```python
# 文档操作
sw_app.NewPart()                                    # 新建零件
sw_app.NewAssembly()                                # 新建装配体  
sw_app.NewDocument(template, 0, 0, 0)               # 用模板新建
sw_app.OpenDoc6(path, type, options, "", 0, 0)      # 打开文档
sw_app.CloseDoc(title)                              # 关闭文档
sw_app.QuitDoc(title)                               # 退出不保存

# 选择操作
sw_model.Extension.SelectByID2(                      # 选择对象
    name,       # 对象名称
    type,       # 对象类型: "PLANE","FACE","EDGE","COMPONENT"等
    x, y, z,    # 坐标
    append,     # 是否追加选择
    mark,       # 标记
    callout,    # 标注
    option      # 选项
)

# 清除选择
sw_model.ClearSelection2(True)

# 获取信息
sw_model.GetTitle()                                  # 文档标题
sw_model.GetPathName()                               # 文件路径
sw_model.GetType()                                   # 文档类型 (1=零件,2=装配体,3=工程图)
sw_model.GetConfigurationNames()                     # 配置名称列表
```

### 14.3 Python完整环境搭建

```python
# 安装依赖
# pip install pywin32

# 完整示例 - 创建带特征的标准零件
import win32com.client
import pythoncom

def full_example():
    try:
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 连接SolidWorks
        sw_app = win32com.client.Dispatch("SldWorks.Application")
        sw_app.Visible = True
        
        # 新建零件
        sw_app.NewPart()
        sw_model = sw_app.ActiveDoc
        
        # 创建第一个特征：拉伸基体
        sw_model.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
        sw_model.SketchManager.InsertSketch(True)
        sw_model.SketchManager.CreateCircle(0, 0, 0, 0.05, 0, 0)
        sw_model.SketchManager.InsertSketch(True)
        sw_model.FeatureManager.FeatureExtrusion3(
            True, False, False, 0, 0, 0.03, 0.03,
            False, False, False, False, 0, 0, False, False, False, False
        )
        
        # 创建切槽特征
        sw_model.Extension.SelectByID2("", "FACE", 0, 0, 0.03, False, 0, None, 0)
        sw_model.SketchManager.InsertSketch(True)
        sw_model.SketchManager.CreateCircle(0, 0, 0, 0.03, 0, 0)
        sw_model.SketchManager.InsertSketch(True)
        sw_model.FeatureManager.FeatureCut4(
            True, False, False, 0, 0, 0.02, 0.02,
            False, False, False, False, 0, 0, False, False, False, False
        )
        
        # 添加圆角
        sw_model.SelectByID2("", "EDGE", 0.05, 0, 0, False, 0, None, 0)
        sw_model.FeatureManager.FeatureFillet3(122, 0.005, 0, 0, 0, 0, 0)
        
        # 设置材料
        sw_model.SetMaterialPropertyName2("Default", "SOLIDWORKS Materials", "1060 Alloy")
        
        # 保存
        sw_model.SaveAs("D:/example_part.sldprt")
        
        print("零件创建完成！")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    full_example()
```

## 十五、故障排除与调试

### 15.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 无法连接SolidWorks | SW未运行 | 先手动启动SolidWorks |
| API对象不存在 | 版本差异 | 检查SW版本，查阅对应API文档 |
| 特征创建失败 | 草图不完整 | 检查草图是否完全约束 |
| 插件无法加载 | 插件未启用 | 在SW中启用相应插件 |
| 文件保存失败 | 路径不存在 | 确保目录存在 |

### 15.2 调试命令

```python
# 检查注册表（确认SW安装路径）
import winreg
key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
    r"SOFTWARE\SolidWorks\General")
path = winreg.QueryValueEx(key, "SolidWorks Shared Directory")[0]

# 列出活动文档
sw_app.Visible = True
count = sw_app.GetDocumentCount()
for i in range(count):
    doc = sw_app.GetDocuments().Item(i)
    print(f"文档 {i}: {doc.GetTitle()} (类型: {doc.GetType()})")

# 列出特征树
def list_features(sw_model):
    feat = sw_model.FirstFeature()
    while feat is not None:
        print(f"特征: {feat.Name} (类型: {feat.GetTypeName()})")
        feat = feat.GetNextFeature()
```

## 十六、设计规范与最佳实践

### ⛔ 16.1 模板选择规范（MUST）

- ⛔ **零件/装配体建模必须使用公制模板** — `gb_part.prtdot` / `gb_assembly.asmdot`
- ⛔ **工程图使用GB标准图纸格式** — A4/A3/A2 国标图框
- ⚡ **自定义模板放在指定模板路径** — 便于团队协作

### ⚡ 16.2 命名规范（SHOULD）

- ⚡ 零件: `项目代号_零件名_版本号.sldprt`
- ⚡ 装配体: `项目代号_装配体名_版本号.sldasm`
- ⚡ 工程图: 与对应零件/装配体同名，后缀.slddrw

### ⚡ 16.3 设计最佳实践（SHOULD）

1. ⚡ **草图完全定义**: 避免欠约束草图（蓝色→黑色）
2. ⚡ **优先使用特征关系**: 少用固定配合
3. 💡 **合理使用子装配体**: 便于管理和修改
4. 💡 **配置驱动**: 相似零件用配置管理
5. ⚡ **设计意图优先**: 使修改可预测

### 16.4 版本兼容性

| SW版本 | 对应模板 | API变更 |
|--------|---------|---------|
| 2010-2013 | 早期模板 | 基础API稳定 |
| 2014-2015 | 中期模板 | 新增若干API |
| 2016-2017 | 当前模板 | FeatureManager扩展 |
| 2018+ | 最新模板 | 持续更新 |

## 十七、工作流程总结

### AI自动化建模标准流程

```
用户需求 → 分析建模策略 → 选择API函数 → 生成Python代码 → 连接SW执行
```

1. **理解需求**: 确定零件类型（基体/钣金/焊件/曲面）
2. **规划步骤**: 确定特征顺序（基准面→草图→特征→工程特征）
3. **生成代码**: 选择对应的API函数
4. **执行建模**: 运行代码在SW中创建模型
5. **验证结果**: 检查模型是否正确

### 支持的功能矩阵

| 功能 | API支持 | 自动化程度 |
|------|---------|-----------|
| 基础零件建模 | ✓ | 完全自动化 |
| 工程特征 | ✓ | 完全自动化 |
| 装配体 | ✓ | 大部分自动化 |
| 工程图 | ✓ | 大部分自动化 |
| 曲面设计 | ✓ | 大部分自动化 |
| 钣金设计 | ✓ | 大部分自动化 |
| 焊件设计 | ✓ | 部分自动化 |
| 模具设计 | ✓ | 部分自动化 |
| Simulation | ✓ | 部分自动化 |
| Flow Simulation | ✓ | 部分自动化 |
| 渲染/动画 | ✓ | 基础自动化 |

---

**注意**: 
1. SolidWorks版本不同可能导致API行为差异，建议使用2016+版本
2. 所有单位默认为米制(SI)，SolidWorks内部使用米
3. 批量操作前建议先在小范围测试
4. 重要文件操作前做好备份

---

## 十八、SWValidator 验证框架（跨机测试验证）

### 问题背景
API 返回值（`S_OK`、`None`、特征对象）不能证明操作真正成功。吕亚峰（2026-06-02 跨机测试）验证了必须多层验证。

### 验证层级（L1-L4）

| 层级 | 验证方式 | 代码 | 可靠性 |
|-------|---------|------|--------|
| L1 | API 返回值 | `if feat is not None` | ⭐ 低（假成功） |
| L2 | 特征数变化 | `GetFeatureCount()` 前后对比 | ⭐⭐ 中（空草图会骗） |
| L3 | 实体数 | `GetBodies2()` 计数 | ⭐⭐⭐ 高 |
| L4 | 物理测量 | `GetMassProperties()` / 包围盒 | ⭐⭐⭐⭐ 最高 |

### SWValidator 类（可直接复用）

```python
class SWValidator:
    """SolidWorks API调用验证器（吕亚峰跨机测试验证版）"""
    
    @staticmethod
    def verify_connection(sw_app):
        """验证SW应用连接是否有效——用Visible属性，不用GetVersion()"""
        if sw_app is None:
            raise Exception("SW应用对象为None")
        try:
            visible = sw_app.Visible          # 属性，不用()
            _ = sw_app.CommandInProgress  # 能读就说明COM活了
            print(f"  ✓ SW连接验证通过 (Visible={visible})")
            return True
        except Exception as e:
            raise Exception(f"SW连接验证失败: {e}")

    @staticmethod
    def verify_feature_created(doc, before_count=None):
        """验证特征是否真正创建"""
        after_count = doc.GetFeatureCount()
        if before_count is not None:
            if after_count <= before_count:
                raise Exception(f"特征创建失败: {before_count} → {after_count}")
            print(f"  ✓ 特征数验证通过: {before_count} → {after_count}")
        # 再查最后一个特征名
        last_feat = doc.FeatureManager.GetLastFeature()
        if last_feat is not None:
            print(f"  ✓ 最后特征: {last_feat.Name}")
        return last_feat

    @staticmethod
    def verify_body_count(doc, before_count=None):
        """GetBodies2硬验证（最可靠）"""
        bodies = doc.GetBodies2(0, False)  # 0=solid
        count = len(bodies) if bodies else 0
        if before_count is not None:
            if count <= before_count:
                raise Exception(f"实体数未增加: {before_count} → {count}")
            print(f"  ✓ 实体数验证通过: {before_count} → {count}")
        return count
```

### safe_select 遍历回退方案

```python
def safe_select(doc, plane_name):
    """SelectByID2失败→遍历特征树回退"""
    # 先试 SelectByID2（正确VARIANT写法）
    ok = doc.Extension.SelectByID2(
        plane_name, "PLANE", 0, 0, 0,
        False, 0,
        win32com.client.VARIANT(pythoncom.VT_DISPATCH, None),
        0
    )
    if ok:
        return True
    # 回退：遍历特征树
    feat = doc.FirstFeature         # 属性，不用()
    while feat is not None:
        if feat.Name == plane_name:
            feat.Select2(False, 0)
            return True
        feat = feat.GetNextFeature()  # 方法，要加()
    return False
```

---

## 十九、国内网络环境 + pywin32 版本陷阱

### raw.githubusercontent.com 被墙问题（吕亚峰测试发现）

**现象**：GitHub API 可连，但 `raw.githubusercontent.com` 无法访问（国内 GFW 封锁）。

**影响**：`curl` 直接下载技能文件会失败。

**解决方案**：
```python
# 方案1：用 jsDelivr CDN（推荐）
url = "https://cdn.jsdelivr.net/gh/delancy827/solidworks-skills@main/README.md"

# 方案2：用 gitclone.com 镜像
url = "https://gitclone.com/github.com/delancy827/solidworks-skills/blob/main/README.md"

# 方案3：SSH 克隆（已配置SSH key时）
git clone git@github.com:delancy827/solidworks-skills.git
```

### ⚡ pywin32 版本选择（SHOULD）

| pywin32版本 | FeatureExtrusion2 | 推荐 |
|--------------|-------------------|------|
| v306 | ❌ 23参数调用失败 | 不用 |
| v311 | ✅ 通过 | **推荐** |
| v228 | ⚠️ 部分API异常 | 勉强 |

⚡ **推荐安装 v311**：`pip install pywin32==311`

### ⛔ UserControl = True（MUST — Python COM 环境强制）

**问题**：`sw.UserControl = False` 会导致 Python 脚本结束时 SW 被强制回收，`GetActiveObject` 后续连不上。

```python
sw = win32com.client.GetActiveObject("SldWorks.Application")
sw.Visible = True
sw.UserControl = True   # ⛔ MUST: Python自动化必须True，防止SW被GC回收
```

### GetVersion() 可用性更正

Sec 26 之前记录 `GetVersion` 是属性。吕亚峰环境（pywin32 v311 + SW 2024）实测**可作为方法调用**：

```python
# pywin32 v311 + SW 2024：✅ 可以调用
ver = sw.GetVersion()   # 返回字符串如 "32.5.0"
print(f"SW版本: {ver}")

# 如果是属性（某些版本），这样读：
try:
    ver = sw.GetVersion()   # 试方法
except:
    ver = sw.GetVersion     # 再试属性
```

---

## 二十、连接回退完整链路（生产可用）

```python
def connect_sw():
    """
    连接SolidWorks（完整回退链路）
    吕亚峰跨机测试验证：GetActiveObject在某些环境失败→必须Dispatch回退
    """
    sw = None
    
    # 第一优先：连已有实例
    try:
        sw = win32com.client.GetActiveObject("SldWorks.Application")
        print("  ✓ 连接到已运行SW实例")
    except:
        pass
    
    # 回退：启动新实例
    if sw is None:
        for progid in ["SldWorks.Application.32",
                        "SldWorks.Application.64",
                        "SldWorks.Application"]:
            try:
                sw = win32com.client.Dispatch(progid)
                print(f"  ✓ 启动新SW实例 ({progid})")
                break
            except:
                pass
    
    if sw is None:
        raise Exception("无法连接或启动SolidWorks")
    
    sw.Visible = True
    sw.UserControl = True   # ⚠️ 必须True，否则Python结束后SW被Kill
    
    # 验证连接（读属性，不是调用方法）
    _ = sw.Visible
    print(f"  ✓ SW连接验证通过")
    
    return sw
```

---

## 二十一、完整验证工作流（推荐的自动化脚本结构）

```python
import win32com.client
import pythoncom

class ClevisAutomation:
    def __init__(self):
        self.sw = None
        self.doc = None
    
    def connect(self):
        self.sw = connect_sw()  # 用上面Sec30的函数
        return self.sw
    
    def new_part(self):
        before = self.sw.GetDocumentCount()
        template = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
        self.sw.NewDocument(template, 0, 0, 0)
        import time; time.sleep(1)
        self.doc = self.sw.ActiveDoc
        assert self.doc is not None, "新建零件失败"
        print(f"  ✓ 零件创建: {self.doc.GetTitle}")  # 属性
        return self.doc
    
    def select_plane(self, name):
        # 用 safe_select（Sec28）
        ok = safe_select(self.doc, name)
        if not ok:
            raise Exception(f"无法选择基准面: {name}")
        return True
    
    def extrude(self, depth_mm):
        before = self.doc.GetFeatureCount()
        self.doc.SketchManager.InsertSketch(True)  # 关闭草图
        
        depth_m = depth_mm / 1000.0
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, False, False,
            0, 0,
            depth_m, 0,
            False, False, False, False,
            0, 0, False, False, False, False,
            True, True, True,
            0, False, False
        )
        
        # L2验证
        SWValidator.verify_feature_created(self.doc, before)
        # L3验证
        SWValidator.verify_body_count(self.doc)
        return feat
    
    def save(self, path):
        # 先用SaveAs3，失败降级SaveAs
        result = self.doc.SaveAs3(path, 1, 2)
        if result != 1:
            print(f"  ⚠ SaveAs3返回{result}，降级SaveAs")
            self.doc.SaveAs(path)

if __name__ == "__main__":
    auto = ClevisAutomation()
    try:
        auto.connect()
        auto.new_part()
        # ... 建模步骤 ...
        auto.save(r"C:\temp\clevis.SLDPRT")
        print("✓ 完成")
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback; traceback.print_exc()

---

## 二十二、凳子建模架构模式（吕亚峰跨机验证 2026-06-02）

### 问题背景
叉形接头是单件拉伸特征，而**凳子**是**多体装配建模**——座面 + 4条腿，需要多次选基准面、多次拉伸、坐标计算。吕亚峰实测验证了这个模式。

### 凳子参数化架构

```python
class 凳子建模器:
    """凳子自动化建模器（吕亚峰验证版）"""

    # 默认尺寸参数（单位：米）
    默认尺寸 = {
        '座面长度': 0.300,       # 300mm
        '座面宽度': 0.300,       # 300mm
        '座面厚度': 0.025,       # 25mm
        '腿长度': 0.400,         # 400mm
        '腿截面': 0.030,         # 30mm 正方形
        '腿偏移': 0.020,         # 腿到边缘距离 20mm
    }

    def 计算腿位置(self, seat_l, seat_w, leg_size, offset):
        """计算4条腿的草图原点坐标"""
        half_l = seat_l / 2
        half_w = seat_w / 2
        half_g = leg_size / 2
        return [
            (-half_l + offset + half_g, -half_w + offset + half_g),  # 前左
            ( half_l - offset - half_g, -half_w + offset + half_g),  # 前右
            (-half_l + offset + half_g,  half_w - offset - half_g),  # 后左
            ( half_l - offset - half_g,  half_w - offset - half_g),  # 后右
        ]
```

### 关键建模步骤（4步）

```
凳子建模流程：
├── 步骤1：选择上视基准面 → 画矩形座面 → 拉伸厚度
├── 步骤2：选择前视基准面 → 画腿截面 → 拉伸腿长（flip=True 向下）
├── 步骤3：重复4次（每条腿一次，坐标不同）
└── 步骤4：EditRebuild3() 重建 → SaveAs3 保存
```

### 腿坐标系陷阱

**座面原点在中心，腿的草图原点也在中心**——需要偏移坐标让腿出现在座面角落：

```python
# 正确：腿截面草图（在前视基准面画，X=左右，Y=前后，Z=上下）
half_leg = leg_size / 2
# 前左腿：X=-0.150+0.020+0.015=-0.115, Y=-0.115
self.创建矩形草图(lx - half_leg, ly - half_leg,
                     lx + half_leg, ly + half_leg)
# 拉伸方向：flip=True（向下拉伸腿长）
self.拉伸(leg_length, flip=True, name=f"腿{i+1}")
```

---

## 二十三、P1-P10 问题审计框架（系统代码审查法）

吕亚峰在 `凳子_建模分析报告.md` 中提出了**10大问题审计框架**，适用于任何 SW 自动化脚本的 code review。

### 问题清单

| 编号 | 类别 | 问题描述 | 严重度 | 修复方案 |
|------|------|----------|--------|----------|
| P1 | 连接 | `GetActiveObject` 失败无备用 | 🔴 高 | GetActiveObject → Dispatch 回退链 |
| P2 | 兼容性 | 硬编码模板路径 | 🔴 高 | 动态检测多个可能路径 |
| P3 | 验证 | `FeatureExtrusion2` 返回 None 无验证 | 🟡 中 | L1-L4 验证链 |
| P4 | 兼容性 | 中英文基准面名称硬编码 | 🟡 中 | 自动检测 SW 语言版本 |
| P5 | 性能 | `time.sleep(1)` 固定等待 | 🟢 低 | `EditRebuild3()` 主动重建 |
| P6 | 错误处理 | 选择失败只打印不中断 | 🟡 中 | `raise SW建模Error` |
| P7 | 参数 | `Dir` 参数含义因版本而异 | 🟡 中 | 反射探测确认参数顺序 |
| P8 | 资源 | 无显式 COM 资源清理 | 🟢 低 | `pythoncom.CoUninitialize()` |
| P9 | 日志 | 缺少详细日志 | 🟢 低 | 每步 `[1/6]` 进度输出 |
| P10 | 架构 | 用拉伸代替切除 | 🔴 高 | 加法建模策略（FeatureCut4 不可用） |

### 使用方法

每次写完 SW 自动化脚本，按 P1-P10 逐条检查，全部打勾才能交付。

---

## 二十四、CoInitialize + EditRebuild3 验证链

### CoInitialize 必须显式调用

`凳子_自动建模_优化版.py` 第329行：

```python
if __name__ == "__main__":
    # 初始化 COM（必须显式调用，否则 Dispatch 可能失败）
    pythoncom.CoInitialize()
    try:
        建模器 = 凳子建模器()
        建模器.连接()
        # ...
    finally:
        pythoncom.CoUninitialize()  # 确保释放
```

**原因**：Python 进程如果没有消息循环，`Dispatch` 可能返回无效 COM 指针。`CoInitialize()` 确保 COM 公寓初始化。

### EditRebuild3 重建验证（L4.5 层级）

```python
def 重建验证(self):
    """强制重建模型（L4.5验证层级）"""
    try:
        self.doc.EditRebuild3()
        print("  ✓ 重建完成")
        return True
    except Exception as e:
        print(f"  ✗ 重建失败: {e}")
        return False

# 在保存前调用
self.重建验证()
self.保存(path)
```

**与 L1-L4 的关系**：
- L1-L3：创建时验证
- **L4**：`GetMassProperties()` 物理测量
- **L4.5**：`EditRebuild3()` 强制重建（捕捉重建错误）

---

## 二十五、版本化 ProgID 连接策略

`凳子_自动建模_优化版.py` 第80行使用了**版本化 ProgID**：

```python
def 连接(self):
    # 方法1：GetActiveObject
    try:
        self.sw = win32com.client.GetActiveObject("SldWorks.Application")
        return
    except: pass

    # 方法2：版本化 Dispatch（SW 2024=32, 2023=31, ...）
    for version in [self.version, "32", "31", "30", ""]:
        try:
            if version:
                prog_id = f"SldWorks.Application.{version}"
            else:
                prog_id = "SldWorks.Application"
            self.sw = win32com.client.Dispatch(prog_id)
            print(f"  ✓ 启动新实例: {prog_id}")
            return
        except: pass

    raise SWConnectionError("无法连接 SolidWorks")
```

**版本号对照表**：

| SW 版本 | ProgID 后缀 | 年份 |
|----------|-------------|------|
| SW 2024 | `32` | 32.5.0 |
| SW 2023 | `31` | 31.0.0 |
| SW 2022 | `30` | 30.0.0 |
| SW 2021 | `29` | 29.0.0 |
| SW 2020 | `28` | 28.0.0 |

---

## 二十六、动态模板检测（多路径遍历）

硬编码 `C:\ProgramData\...\gb_part.prtdot` 在其他机器上会失败。正确做法：

```python
def _检测模板路径(self):
    """动态检测可用的零件模板"""
    possible_templates = [
        r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot',
        r'C:\ProgramData\SolidWorks\SOLIDWORKS 2023\templates\gb_part.prtdot',
        r'D:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot',
        r'C:\Program Files\SolidWorks Corp\SolidWorks\templates\gb_part.prtdot',
    ]
    for tmpl in possible_templates:
        if os.path.exists(tmpl):
            return tmpl
    # 全部失败 → 用默认（可能报错，但至少尝试）
    return possible_templates[0]
```

---

## 二十七、基准面名称自动翻译（中英文切换）

```python
def _翻译基准面(self, name):
    """翻译基准面名称"""
    translations = {
        "Front Plane": "前视基准面",
        "前视基准面": "Front Plane",
        "Top Plane": "上视基准面",
        "上视基准面": "Top Plane",
        "Right Plane": "右视基准面",
        "右视基准面": "Right Plane",
    }
    return translations.get(name, name)

def 选择基准面(self, plane_name):
    """选择基准面（支持中英文，自动检测）"""
    # 先试原名
    if self._select_by_id2(plane_name):
        return True
    # 再试翻译名
    translated = self._翻译基准面(plane_name)
    if translated != plane_name:
        if self._select_by_id2(translated):
            return True
    # 最后遍历特征树
    return self._遍历选择(plane_name)
```

---

## 二十八、完整生产级脚本模板（吕亚峰验证版）

```python
"""
凳子自动化建模脚本 - 生产级模板
吕亚峰 2026-06-02 跨机验证通过
"""
import win32com.client
import pythoncom
import time
import os
import sys

class SWConnectionError(Exception): pass
class SW建模Error(Exception): pass

class 生产级建模器:
    def __init__(self):
        self.sw = None
        self.doc = None
        self.template = self._检测模板路径()

    def _检测模板路径(self):
        # ... 见 Sec 26 ...

    def 连接(self):
        # ... 见 Sec 25 ...

    def 新建零件(self):
        self.doc = self.sw.NewDocument(self.template, 0, 0, 0)
        time.sleep(0.3)
        assert self.doc is not None

    def 选择基准面(self, name):
        # ... 见 Sec 27 ...

    def 拉伸(self, depth_m, flip=False, is_cut=False):
        before = self.doc.GetFeatureCount
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, flip, is_cut,
            0, 0, depth_m, 0,
            False, False, False, False,
            0, 0, False, False, False, False,
            True, True, True,
            0, False, False
        )
        after = self.doc.GetFeatureCount
        assert after > before, "拉伸失败"
        return feat

    def 保存(self, path):
        self.doc.EditRebuild3()  # L4.5 验证
        result = self.doc.SaveAs3(path, 1, 2)
        if result != 1:
            self.doc.SaveAs(path)  # 降级

if __name__ == "__main__":
    pythoncom.CoInitialize()
    try:
        建模器 = 生产级建模器()
        建模器.连接()
        建模器.新建零件()
        # ... 建模步骤 ...
        建模器.保存(r"C:\temp\output.SLDPRT")
        print("✓ 完成")
    except Exception as e:
        print(f"✗ 失败: {e}")
        traceback.print_exc()
    finally:
        pythoncom.CoUninitialize()
```

---

## 二十九、SolidPractices 官方最佳实践（2026-06-03 学习整合）

### 来源

基于 CADSharp LLC 为 Dassault Systèmes 编写的 **SolidPractices** 36页官方指南 + 社区实战经验。这是 SolidWorks 官方认可的开发最佳实践，整合到本 skill 以确保 AI 生成的代码符合专业标准。

---

### ⛔ MUST 规则（强制执行 — 违反即熔断）

| 编号 | 规则 | 说明 | 代码示例 |
|------|------|------|----------|
| M1 | **属性 vs 方法区分** | GetTitle/GetFeatureCount/FirstFeature/EditRebuild3 是属性不加括号；GetNextFeature() 是方法要加括号 | `doc.GetFeatureCount` ✅ / `doc.GetFeatureCount()` ❌ |
| M2 | **VARIANT 包装** | SelectByID2 第8参数必须 `VARIANT(VT_DISPATCH, None)`，不能用 Python None | `VARIANT(pythoncom.VT_DISPATCH, None)` |
| M3 | **单位转换** | SolidWorks 内部统一使用米（SI），输入 mm 必须 `/1000.0` | `depth_m = 30 / 1000.0` |
| M4 | **UserControl=True** | Python COM 环境必须设置，防止 SW 被 GC 回收 | `sw.UserControl = True` |
| M5 | **CoInitialize()** | 必须显式调用，否则 Dispatch 可能返回无效指针 | `pythoncom.CoInitialize()` |
| M6 | **FeatureCut 不可用** | Python COM 中 FeatureCut/2/3/4 全部返回 None，必须用加法建模策略 | 用 FeatureExtrusion2 + FeatureFillet3 |

---

### ⚡ SHOULD 规则（建议执行 — 默认遵守）

| 编号 | 规则 | 说明 |
|------|------|------|
| S1 | **有意义的特征命名** | `feat.Name = "底座圆盘"` 而非默认 "拉伸1"，便于调试和维护 |
| S2 | **常量集中化** | 所有尺寸放在 PARAMS 字典，不硬编码在方法体中 |
| S3 | **关注点分离** | 连接/建模/验证/保存 分方法封装，每个方法只做一件事 |
| S4 | **sw.CloseDoc(title)** | 关闭文档用 `sw.CloseDoc(title)` 而非 `doc.Close()`（后者会断 RPC） |
| S5 | **先简单后复杂** | 简单矩形拉伸 → 圆角特征 → 切除，而非复杂草图一步成型 |
| S6 | **EditRebuild3 保存前重建** | 确保模型无错误，捕捉重建异常 |

**参数化驱动示例**：
```python
PARAMS = {
    '底座直径': 60,   # mm
    '底座厚度': 30,   # mm
    '叉耳宽度': 60,   # mm
    '槽宽': 25,       # mm
}

class 建模器:
    def 拉伸底座(self):
        depth_m = PARAMS['底座厚度'] / 1000.0  # ⛔ M3 单位转换
        # ...
```

---

### 💡 MAY 规则（可选执行 — 视上下文判断）

| 编号 | 规则 | 说明 |
|------|------|------|
| P1 | **VBA 宏注入** | RunMacro 可作为绕过 Python COM 限制的备选方案（但 SW 2024 中 RunMacro 也返回 False） |
| P2 | **多版本 ProgID 回退** | `.32` → `.31` → `""` 按环境选择，提升跨机兼容性 |
| P3 | **CDN 镜像** | jsDelivr/gitclone 替代 raw.githubusercontent.com（国内网络环境） |

---

### 规则优先级决策树

```
遇到操作决策时：
│
├─ 是否存在 ⛔ MUST 规则？
│  ├─ 是 → 无条件执行，无任何例外
│  └─ 否 → 继续
│
├─ 是否存在 ⚡ SHOULD 规则？
│  ├─ 是 → 默认执行，除非用户明确要求跳过
│  └─ 否 → 继续
│
└─ 是否存在 💡 MAY 规则？
   ├─ 是 → 根据上下文判断是否执行
   └─ 否 → 自行判断，但必须 W-A-R 验证
```

---

## 三十、COM 属性/方法兼容探测（get_com_member 模式）

> 参考来源：[wzyn20051216/solidworks-automation-skill](https://github.com/wzyn20051216/solidworks-automation-skill) (MIT License)

### 问题背景

pywin32 中同一个 COM 成员在不同环境下可能表现为属性也可能表现为方法，`callable(member)` 不能作为唯一判断。手动维护"属性列表 vs 方法列表"脆弱且不可扩展。

### ⛔ MUST：get_com_member 统一探测函数

```python
def get_com_member(obj, attr_name, *args):
    """
    兼容 pywin32 中"同一成员既可能是属性也可能是方法"的情况。
    优先尝试调用，失败后回退为属性读取。
    参考来源: wzyn20051216/solidworks-automation-skill (sw_connect.py)
    """
    member = getattr(obj, attr_name)
    if args:
        return member(*args)
    try:
        return member()
    except Exception as exc:
        message = str(exc)
        if "-2147352573" in message or "找不到成员" in message or "Member not found" in message:
            return member
        raise
```

### 使用示例

```python
# 不再需要记住哪些是属性哪些是方法
title = get_com_member(doc, "GetTitle")         # 属性，自动回退
feat = get_com_member(doc, "FirstFeature")       # 属性，自动回退
count = get_com_member(doc, "GetFeatureCount")   # 属性，自动回退
next_feat = get_com_member(feat, "GetNextFeature")  # 方法，自动调用
type_name = get_com_member(feat, "GetTypeName2")    # 方法，自动调用
```

### 与现有铁律的关系

本函数补充了铁律3（反幻觉）和 Section 29 M1（属性vs方法区分）的实战工具：
- 不再需要手动维护属性/方法对照表
- 任何不确定的 COM 成员都可以安全读取
- 错误码 `-2147352573` = "Member not found"，是 pywin32 属性伪可调用时的典型错误

---

## 三十一、文件导出规范（STEP/STL/IGES/PDF/DXF）

> 参考来源：[wzyn20051216/solidworks-automation-skill](https://github.com/wzyn20051216/solidworks-automation-skill) (MIT License)

### 支持的导出格式

| 格式 | 扩展名 | 需要 ExportData | 说明 |
|------|--------|:---:|------|
| STEP | .step .stp | 否 | 通用 3D 交换格式 |
| IGES | .igs .iges | 否 | 传统交换格式 |
| STL | .stl | 否 | 3D 打印/网格 |
| Parasolid | .x_t .x_b | 否 | 高精度内核格式 |
| PDF | .pdf | 是 | 工程图导出 |
| DXF/DWG | .dxf .dwg | 否 | 2D 图纸/展开图 |
| 3D PDF | .pdf | 是 | 3D 嵌入式 PDF |
| eDrawings | .eprt .easm .edrw | 否 | 轻量查看格式 |

### ⛔ MUST：Extension.SaveAs 的 VARIANT 包装

```python
import win32com.client
import pythoncom

errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
callout = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)

success = doc.Extension.SaveAs(
    output_path,     # 输出路径
    0,               # 版本 (0=当前版本)
    1,               # 选项 (1=SaveAs)
    callout,         # Callout
    errors,          # 错误码 (by-ref)
    warnings         # 警告码 (by-ref)
)

if success:
    print(f"✓ 导出成功: {output_path}")
else:
    print(f"✗ 导出失败: 错误码={errors.value}, 警告码={warnings.value}")
```

### SaveAs 错误码/警告码速查

| 值 | 错误名 | 说明 |
|:---:|--------|------|
| 0 | swGenericSaveError | 通用错误 |
| 1 | swReadOnlySaveError | 只读文件 |
| 5 | swFileSaveFormatNotAvailable | 格式不可用 |
| 6 | swFileSaveAsDoNotOverwrite | 不覆盖现有文件 |
| 9 | swFileSaveAsInvalidFileExtension | 无效扩展名 |

### STL 导出质量设置

```python
# 设置 STL 输出质量为 Fine
doc.SetUserPreferenceIntegerValue(78, 0)  # 0=Fine, 1=Coarse
# 设置自定义偏差和角度容差
doc.SetUserPreferenceDoubleValue(0x00000F, 0.005)   # 偏差(米)
doc.SetUserPreferenceDoubleValue(0x000010, 0.174)    # 角度容差(弧度≈10°)
```

### 批量转换模板

```python
import os

def batch_convert(sw, input_dir, output_dir, input_ext=".sldprt", output_ext=".step"):
    """批量转换目录下的所有文件"""
    os.makedirs(output_dir, exist_ok=True)
    errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(input_ext):
            input_path = os.path.join(input_dir, filename)
            base = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, base + output_ext)
            model = sw.OpenDoc6(input_path, 1, 1, "", errors, warnings)
            if model:
                model.Extension.SaveAs(output_path, 0, 1, None, errors, warnings)
                sw.CloseDoc(get_com_member(model, "GetTitle"))
                print(f"✓ 已转换: {filename} -> {base + output_ext}")
```

---

## 三十二、装配体运动配合（Gear/Hinge/Concentric Mate）

> 参考来源：[wzyn20051216/solidworks-automation-skill](https://github.com/wzyn20051216/solidworks-automation-skill) (MIT License)

### AddMate5 完整 15 参数签名

```python
errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
mate = asm.FeatureManager.AddMate5(
    mate_type,              # 1: swMateType_e 枚举
    align,                  # 2: swMateAlign_e (0=Aligned)
    flip,                   # 3: bool
    distance,               # 4: float (米)
    distance_upper,         # 5: 距离上限
    distance_lower,         # 6: 距离下限
    gear_num,               # 7: Gear Mate 分子
    gear_den,               # 8: Gear Mate 分母
    angle,                  # 9: float (弧度)
    angle_upper,            # 10: 角度上限
    angle_lower,            # 11: 角度下限
    for_positioning_only,   # 12: bool
    lock_rotation,          # 13: 同心配合是否锁旋转
    width_mate_option,      # 14: Width Mate 选项
    errors                  # 15: by-ref 错误码
)
```

### 配合类型枚举

| 值 | 名称 | 说明 |
|:---:|------|------|
| 0 | swMateCOINCIDENT | 重合 |
| 1 | swMateCONCENTRIC | 同心 |
| 2 | swMatePERPENDICULAR | 垂直 |
| 3 | swMatePARALLEL | 平行 |
| 4 | swMateTANGENT | 相切 |
| 5 | swMateDISTANCE | 距离 |
| 6 | swMateANGLE | 角度 |
| 10 | swMateGEAR | 齿轮 |
| 11 | swMateWIDTH | 宽度 |
| 16 | swMateLOCK | 锁定 |
| 22 | swMateHINGE | 铰链 |

### 组件压缩状态枚举

| 值 | 名称 | 说明 |
|:---:|------|------|
| 0 | Suppressed | 压缩 |
| 1 | Lightweight | 轻化（GetModelDoc2 返回 None！） |
| 2 | FullyResolved | 完全解析（推荐） |
| 3 | Resolved | 解析 |

### ⛔ MUST：运动型装配工作流

1. 先保存所有零件，关闭不再编辑的文档
2. 新建装配体，添加组件
3. **对所有需读取特征/面的组件先解析**：`SetSuppression2(2)` → FullyResolved
4. 用 `GetCorresponding()` 将零件内部对象映射到装配体上下文
5. 固定件用三基准面重合 Mate 锁死
6. **旋转件不要用三基准面完全锁死**，用同心 Mate + `lock_rotation=False`
7. 齿轮联动用 Gear Mate，按齿数传入比例
8. 创建后遍历 MateGroup 子特征确认真实 Mate 写入
9. 脚本生成的动画 ≠ 可在 SolidWorks 中拖动
10. 用 sw_review 导出多视角预览图验证

### 圆柱面识别（轴/孔定位）

```python
def find_largest_cylinder_face(component, min_radius=0.004, max_radius=0.008):
    """通过圆柱面识别轴/孔，用于 Mate 选择"""
    part = component.GetModelDoc2()
    if part is None:
        return None  # 轻化/压缩组件无法读取
    bodies = part.GetBodies2(0, False)
    best_face, best_r = None, 0
    for body in (bodies or []):
        for face in body.GetFaces():
            surface = face.GetSurface()
            if surface.IsCylinder:
                params = surface.CylinderParams
                radius = params[6]  # 单位：米
                if min_radius <= radius <= max_radius and radius > best_r:
                    best_face, best_r = face, radius
    return best_face
```

### GetCorresponding 使用规范

```python
# 正确：从零件模型中查找特征，再通过组件映射到装配体上下文
part_model = component.GetModelDoc2()
feature = part_model.FeatureByName("Front Plane")
asm_feature = component.GetCorresponding(feature)
asm_feature.Select2(False, 0)
```

### 干涉检测

```python
interference = asm.InterferenceDetection
interference.TreatSubAssembliesAsComponents = False
interference.TreatCoincidenceAsInterference = False
interference.Done()
count = interference.GetInterferenceCount()
```

---

## 三十三、结果自审查系统

> 参考来源：[wzyn20051216/solidworks-automation-skill](https://github.com/wzyn20051216/solidworks-automation-skill) (MIT License)

### ⛔ MUST：必做检查清单（6项）

每次生成、修改或导出 CAD 后，至少检查：

1. COM 调用返回值不是 None，关键特征对象创建成功
2. SaveAs / 导出返回成功
3. 输出文件真实存在且大小合理（>0 bytes）
4. 模型已重建：`doc.ForceRebuild3(False)`
5. 模型已缩放到适合窗口：`doc.ViewZoomtofit2()`
6. 至少导出一张等轴测 BMP，复杂模型导出前视、俯视、右视

### 结构化自审查流程

```python
# 1. 强制重建
doc.ForceRebuild3(False)
doc.ViewZoomtofit2()

# 2. 检查输出文件
import os
for path in expected_outputs:
    assert os.path.exists(path), f"文件不存在: {path}"
    assert os.path.getsize(path) > 0, f"文件为空: {path}"

# 3. 读取特征树摘要
feat = doc.FirstFeature  # 属性
feature_summary = []
while feat:
    feature_summary.append(f"{get_com_member(feat, 'Name')} ({get_com_member(feat, 'GetTypeName2')})")
    feat = feat.GetNextFeature()  # 方法
print(f"特征树: {len(feature_summary)} 个特征")
```

### 目视自查清单（6项）

- 主体是否出现在画面中，是否为空白或只剩草图
- 关键部件是否齐全（孔、轴、外壳、支架等）
- 比例是否明显错误（毫米误当米导致模型巨大）
- 方向是否正确（如轮子在侧面而非车顶）
- 部件是否明显重叠、悬空、穿模或缺少约束
- 文件名、输出目录、导出格式是否符合用户要求

### 发现问题时

1. **不要只报告"文件已保存"**
2. 先定位是草图、选择、拉伸方向、单位、基准面还是导出失败
3. 修改脚本后重新生成并再次导出预览图
4. 最终回复中说明已检查项和仍有限制的地方

---

## 三十四、大型装配体性能优化

> 参考来源：[wzyn20051216/solidworks-automation-skill](https://github.com/wzyn20051216/solidworks-automation-skill) (MIT License)

### ⚡ SHOULD：图形刷新开关

```python
# 批量操作前：禁用图形刷新
doc.FeatureManager.EnableFeatureTree = False
doc.ActiveView.EnableGraphicsUpdate = False

# ... 执行批量操作 ...

# 操作后：恢复并刷新
doc.FeatureManager.EnableFeatureTree = True
doc.ActiveView.EnableGraphicsUpdate = True
doc.GraphicsRedraw2()
```

### 分批策略（超过 20 个零件）

1. 分批生成零件，每批 10-20 个，保存后 CloseDoc
2. 所有零件生成完毕后，统一打开装配体
3. 添加组件前确认所有路径存在，失败组件记录清单
4. 自动化脚本中关闭不必要的图形刷新

### COM 变慢时的处理

```python
# 1. 保存关键输出
# 2. 清理会话
sw.CloseAllDocuments(False)
# 3. 分批重新打开必要零件
# 4. 仍不稳定时，提示用户重启 SLDWORKS.exe
# 5. 脚本内记录失败组件和失败 API，不要只打印"完成"
```

### 批量操作模式

```python
# 批量操作前禁用 UserControl（注意：仅限批量操作，单个零件不要这样做）
sw.UserControl = False
# ... 批量操作 ...
# 手动重建
doc.EditRebuild3()
sw.UserControl = True
```

---

## 三十五、外观与材质设置 + API 查证增强

> 参考来源：[wzyn20051216/solidworks-automation-skill](https://github.com/wzyn20051216/solidworks-automation-skill) (MIT License)

### MaterialPropertyValues 数组格式

SolidWorks 使用 9 元素数组定义材质外观：

```python
# [R, G, B, Ambient, Diffuse, Specular, Shininess, Transparency, Emission]
# 值范围: 0.0 ~ 1.0
red_material = [
    0.8, 0.1, 0.1,    # RGB (红色)
    0.2,                # Ambient (环境光)
    0.6,                # Diffuse (漫反射)
    0.3,                # Specular (镜面反射)
    0.5,                # Shininess (光泽度)
    0.0,                # Transparency (透明度, 0=不透明)
    0.0                 # Emission (发光)
]

# 设置文档级外观
doc.MaterialPropertyValues = red_material
```

### 预设颜色速查

| 名称 | RGB | 用途 |
|------|-----|------|
| iron_red | (0.8, 0.1, 0.1) | 深红装甲 |
| armor_gold | (0.8, 0.7, 0.2) | 金色装甲 |
| dark_gunmetal | (0.2, 0.2, 0.25) | 深色金属/关节 |
| silver | (0.75, 0.75, 0.75) | 银色金属 |
| black | (0.05, 0.05, 0.05) | 黑色 |
| white | (0.95, 0.95, 0.95) | 白色 |

### 稳定性建议

- 单零件多特征上色可能受 SW 版本、显示状态、特征合并影响
- 对颜色要求高的模型，优先拆成多个零件，对每个零件用文档级外观
- 生成后必须导出预览图检查颜色和层次是否可见

### API 查证工作流增强

遇到 scripts 中尚未封装的 SolidWorks API 时：

1. **优先资料源顺序**：官方 API Help → 本地 SDK → 本仓库已有封装 → 新写最小验证脚本
2. **查证记录模板**：
   ```
   API: FeatureExtrusion3
   资料源: help.solidworks.com
   版本: SW 2024
   签名: 21 参数
   关键参数: Merge=参数16
   枚举: swEndCondBlind=0
   返回值: Feature 对象或 None
   失败症状: 轮廓不闭合时返回 None
   验证脚本: test_extrude.py
   是否沉淀: 是 → scripts/sw_part.py
   ```
3. **沉淀规则**：同一 API 第二次用到就封装进工具函数；出现兼容问题、错误码、中文版名称差异时补充到文档

---

## 三十六、COM/VBA 智能路由（参数复杂度自动降级）

> 参考来源：[andrewbartels1/SolidworksMCP-python](https://github.com/andrewbartels1/SolidworksMCP-python) (MIT License)

### 问题背景

Python COM IDispatch 限制：参数 >12 的方法调用可能返回 None。FeatureCut4 (27参数) / HoleWizard5 (25+参数) 在 Python COM 下全部失败。当前"加法建模策略"（Sec 应急方案）是绕过切除，但无法真正实现切除操作。智能路由：按参数复杂度自动选择 COM 直连 或 VBA 宏降级。

### ⛔ MUST：路由决策规则

| 参数数量 | 路由 | 说明 |
|:---:|------|------|
| ≤ 12 | COM 直连 | 性能优先，直接 pywin32 调用 |
| > 12 | VBA 宏降级 | 自动生成 VBA 代码 → 保存 .swp → RunMacro |
| VBA 也失败 | 加法建模 | 回退到 FeatureExtrusion2 几何构造 |

### 复杂度评分公式

```python
def compute_complexity_score(param_count, base_complexity, history_bias,
                              threshold=12):
    """
    复杂度评分（0.0~1.0），决定走 COM 还是 VBA。
    参考来源: andrewbartels1/SolidworksMCP-python (complexity_analyzer.py)
    """
    param_component = min(param_count / threshold, 1.0)
    score = min(1.0,
                param_component * 0.45 +
                base_complexity * 0.40 +
                history_bias * 0.15)
    return score
```

**base_complexity 查表**：

| API | base_complexity | 默认路由 |
|-----|:---:|------|
| FeatureExtrusion2 (23参数) | 0.55 | COM（实测可用） |
| FeatureCut4 (27参数) | 0.90 | **VBA** |
| HoleWizard5 (25+参数) | 0.95 | **VBA** |
| AddMate5 (15参数) | 0.65 | VBA |
| CreateLine / CreateCircle | 0.15 | COM |
| FeatureFillet3 | 0.30 | COM |

### ComplexityAnalyzer + IntelligentRouter 代码模板

```python
class RouteDecision:
    COM = "com"
    VBA = "vba"

class ComplexityAnalyzer:
    """分析操作复杂度，推荐 COM 或 VBA 执行路径"""
    def __init__(self, threshold=12, score_threshold=0.6):
        self.threshold = threshold
        self.score_threshold = score_threshold
        self.history = {}  # {api_name: {com_success, com_failure, vba_success, vba_failure}}
    
    def analyze(self, api_name, param_count, base_complexity=0.2):
        history_bias = self._history_bias(api_name)
        score = compute_complexity_score(param_count, base_complexity, history_bias, self.threshold)
        prefer_vba = param_count > self.threshold or score >= self.score_threshold
        return RouteDecision.VBA if prefer_vba else RouteDecision.COM
    
    def record_result(self, api_name, route, success):
        h = self.history.setdefault(api_name, {"com_success": 0, "com_failure": 0, "vba_success": 0, "vba_failure": 0})
        h[f"{route}_{'success' if success else 'failure'}"] += 1
    
    def _history_bias(self, api_name):
        h = self.history.get(api_name)
        if not h:
            return 0.0
        com_total = h["com_success"] + h["com_failure"]
        return min(h["com_failure"] / com_total, 1.0) if com_total > 0 else 0.0

class IntelligentRouter:
    """智能路由：COM 优先 → VBA 降级，带可缓存操作集"""
    CACHEABLE = {"get_model_info", "list_features", "get_mass_properties", "get_material_properties"}
    
    def route(self, api_name, params, com_func, vba_func=None, analyzer=None):
        decision = (analyzer or ComplexityAnalyzer()).analyze(api_name, len(params) if params else 0)
        # 优先路径
        if decision == RouteDecision.COM:
            result = com_func(*params) if params else com_func()
            if result is not None:
                return result
        # VBA 降级
        if vba_func and decision == RouteDecision.VBA:
            return vba_func(*params) if params else vba_func()
        # COM 回退
        if decision == RouteDecision.VBA:
            return com_func(*params) if params else com_func()
        # VBA 回退
        if vba_func:
            return vba_func(*params) if params else vba_func()
        return result
```

### 三级降级链决策流程图

```
API调用请求
│
├─ 参数 ≤ 12？
│  └─ 是 → COM 直连 → 成功？→ 返回结果
│                    → 失败？→ 继续
│
├─ 参数 > 12？
│  └─ 是 → 生成 VBA 宏 → 执行 → 成功？→ 返回结果
│                                → 失败？→ 继续
│
└─ 回退到加法建模（FeatureExtrusion2 几何构造）
```

---

## 三十七、熔断器模式（COM 健康状态三态管理）

> 参考来源：[andrewbartels1/SolidworksMCP-python](https://github.com/andrewbartels1/SolidworksMCP-python) (MIT License)

### 问题背景

铁律 3（第111行）定义了"异常熔断"行为规范，但缺乏程序化实现。COM 连接不稳定时，连续失败会导致脚本崩溃、SW 假死。需要一个可编程的熔断器来自动管理 COM 健康状态。

### 三态熔断器模型

```
                    失败次数 ≥ 阈值
    Closed ──────────────────────▶ Open
      ▲                              │
      │ 探测成功                      │ 冷却时间到
      │                              ▼
      └──── Half-Open ◀─────────────┘
             │
             └─ 探测失败 → 回到 Open
```

### ⛔ MUST：状态转换规则

| 转换 | 条件 | 默认阈值 |
|------|------|----------|
| Closed → Open | 连续失败次数 ≥ failure_threshold | 5 次 |
| Open → Half-Open | 等待时间 ≥ cooldown_period | 30 秒 |
| Half-Open → Closed | 探测请求成功 | - |
| Half-Open → Open | 探测请求再次失败 | - |

### COMCircuitBreaker 代码模板

```python
import time

class CircuitState:
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 探测

class COMCircuitBreaker:
    """
    COM 熔断器：自动管理 SolidWorks COM 连接健康状态。
    参考来源: andrewbartels1/SolidworksMCP-python (circuit_breaker.py)
    """
    def __init__(self, failure_threshold=5, cooldown=30, half_open_max=1):
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.half_open_max = half_open_max
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_attempts = 0
        self.events = []  # 状态转换日志
    
    def execute(self, func, *args, **kwargs):
        """包装 COM 调用，自动熔断和恢复"""
        if not self.allow_request():
            raise COMCircuitBreakerOpenError(
                f"熔断器处于 Open 状态，剩余冷却 {self.remaining_cooldown():.1f}s"
            )
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(str(e))
            raise
    
    def allow_request(self):
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.cooldown:
                self._transition(CircuitState.HALF_OPEN)
                return True
            return False
        # HALF_OPEN
        return self.half_open_attempts < self.half_open_max
    
    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.CLOSED)
        self.failure_count = 0
    
    def record_failure(self, error_msg=""):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_attempts += 1
            if self.half_open_attempts >= self.half_open_max:
                self._transition(CircuitState.OPEN)
        elif self.failure_count >= self.failure_threshold:
            self._transition(CircuitState.OPEN)
    
    def _transition(self, new_state):
        old = self.state
        self.state = new_state
        self.events.append({
            "time": time.time(), "from": old, "to": new_state,
            "failure_count": self.failure_count
        })
        if new_state == CircuitState.HALF_OPEN:
            self.half_open_attempts = 0
    
    def remaining_cooldown(self):
        if self.state != CircuitState.OPEN:
            return 0
        return max(0, self.cooldown - (time.time() - self.last_failure_time))

class COMCircuitBreakerOpenError(Exception):
    pass
```

### ⚡ SHOULD：熔断事件日志

- 每次状态转换记录时间戳、触发原因、当前失败计数
- 连续 3 次 Open→Half-Open→Open 循环 → 建议用户重启 SLDWORKS.exe

```python
# 检查是否需要建议重启
def check_restart_needed(breaker):
    open_count = sum(1 for e in breaker.events if e["to"] == "open")
    if open_count >= 3:
        print("⚠️ 连续 3 次熔断，建议重启 SolidWorks")
        return True
    return False
```

### 与铁律 3 的关系

- **铁律 3** = AI 行为规范（禁止静默捕获、必须输出 Traceback）
- **本 Section** = 程序化实现（自动检测、自动熔断、自动恢复）
- 两者并行：铁律 3 管 AI 行为，熔断器管代码执行

---

## 三十八、VBA 宏自动生成与执行

> 参考来源：[andrewbartels1/SolidworksMCP-python](https://github.com/andrewbartels1/SolidworksMCP-python) + [vespo92/SolidworksMCP-TS](https://github.com/vespo92/SolidworksMCP-TS) (MIT License)

### 问题背景

Section 36 智能路由判定走 VBA 通道后，需要自动生成 VBA 代码。Python COM 无法直接调用 FeatureCut4，但 VBA 宏内可以正常调用。SW 2024 中 RunMacro(.swb) 返回 False → 需要正确的文件路径和执行方式。

### ⛔ MUST：.swp 文件保存规范

| 规则 | 要求 | 说明 |
|------|------|------|
| 文件路径 | `tempfile.gettempdir()` + 唯一名 | 避免权限问题 |
| 编码 | UTF-8 BOM 或 Windows-1252 | VBA 编辑器要求 |
| 入口点 | `Sub main() ... End Sub` | SW 宏标准格式 |
| 清理 | 执行后删除 .swp 文件 | 避免临时文件堆积 |

### VBA 等效代码示例：FeatureCut4（完整 27 参数）

```vb
' VBA 宏等效代码 — FeatureCut4 在 VBA 中可正常调用
' 参考来源: vespo92/SolidworksMCP-TS (macro-generator.ts)
Sub FeatureCut4Example()
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2
    Dim swFeatMgr As SldWorks.FeatureManager
    Dim swFeat As SldWorks.Feature
    
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    Set swFeatMgr = swModel.FeatureManager
    
    ' FeatureCut4 — VBA 中 27 参数全部正常
    Set swFeat = swFeatMgr.FeatureCut4(
        True, False, False,    ' Sd, Flip, Dir
        0, 0,                   ' T1, T2
        0.05, 0.05,            ' D1, D2
        False, False, False,   ' Dchk1, Dchk2, Ddir1
        False, 0, 0,           ' Ddir2, Dang1, Dang2
        False, False,           ' Ofr, Ofc
        False, False,           ' Tf1, Tf2
        True,                   ' Merge
        False, False,           ' UseFeatScope, UseAutoSelect
        0, False, False,       ' StartOffset, IsAutoStartOffset, FlipStartOffset
        False, False, False,   ' 额外参数
        False                   ' 额外参数
    )
    
    If swFeat Is Nothing Then
        Debug.Print "FeatureCut4 失败"
    Else
        Debug.Print "FeatureCut4 成功: " & swFeat.Name
    End If
End Sub
```

### VBAMacroGenerator 代码生成模板

```python
import tempfile
import os

class VBAMacroGenerator:
    """根据 Python 参数自动生成等效 VBA 宏代码"""
    
    def generate_feature_cut_vba(self, params_dict):
        """生成 FeatureCut4 VBA 代码"""
        return f'''Sub main()
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    Dim swFeat As SldWorks.Feature
    Set swFeat = swModel.FeatureManager.FeatureCut4({params_dict['params_str']})
    If Not swFeat Is Nothing Then
        Debug.Print "OK"
    End If
End Sub'''
    
    def generate_feature_extrusion_vba(self, params_dict):
        """生成 FeatureExtrusion2 VBA 代码"""
        return f'''Sub main()
    Dim swApp As SldWorks.SldWorks
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    Dim swFeat As SldWorks.Feature
    Set swFeat = swModel.FeatureManager.FeatureExtrusion2({params_dict['params_str']})
End Sub'''

class VBAMacroExecutor:
    """保存并执行 VBA 宏文件"""
    
    def __init__(self, sw_app):
        self.sw_app = sw_app
        self.history = []  # 执行历史记录
    
    def save_macro(self, vba_code, macro_name="auto_macro"):
        """保存 VBA 代码到 .swp 文件"""
        temp_dir = tempfile.gettempdir()
        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in macro_name)
        swp_path = os.path.join(temp_dir, f"{safe_name}.swp")
        # UTF-8 BOM 编码
        with open(swp_path, "w", encoding="utf-8-sig") as f:
            f.write(vba_code)
        return swp_path
    
    def execute_macro(self, swp_path, subroutine="main"):
        """执行 VBA 宏并记录结果"""
        import time
        start = time.time()
        try:
            result = self.sw_app.RunMacro2(swp_path, subroutine, 0)
            duration = time.time() - start
            self.history.append({
                "path": swp_path, "result": result, "duration": duration
            })
            # 清理临时文件
            if os.path.exists(swp_path):
                os.remove(swp_path)
            return result
        except Exception as e:
            self.history.append({"path": swp_path, "error": str(e)})
            return False
```

### ⚡ SHOULD：执行历史记录

```python
# 检查宏执行成功率
def get_macro_success_rate(executor, api_name=None):
    total = len(executor.history)
    success = sum(1 for h in executor.history if h.get("result"))
    rate = success / total if total > 0 else 0.0
    if rate < 0.3 and total >= 3:
        print(f"⚠️ 宏执行成功率仅 {rate:.0%}，建议切换到加法建模")
    return rate
```

### 与 Sec 36 智能路由的协作

```
Sec 36 判定走 VBA
│
├─ 调用 VBAMacroGenerator 生成代码
├─ 调用 VBAMacroExecutor 保存并执行
├─ 执行成功 → 记录到路由历史（com_failure++ / vba_success++）
└─ 执行失败 → 回退到加法建模（Sec 应急方案）
```

---

## 三十九、pywin32 适配器增强（连接管理与安全包装器）

> 参考来源：[andrewbartels1/SolidworksMCP-python](https://github.com/andrewbartels1/SolidworksMCP-python) (MIT License)

### 问题背景

Sec 20 提供了连接回退链路，Sec 25 提供了版本化 ProgID，但缺少：自动重连机制、COM 安全包装器、类型库信息缓存。长时间运行的脚本中，COM 连接可能因 SW 崩溃/超时断开。

### ⛔ MUST：SWPyWin32Adapter 统一适配器类

```python
import win32com.client
import pythoncom
import time

class SWPyWin32Adapter:
    """
    pywin32 统一适配器：整合连接回退、自动重连、安全包装、类型库缓存。
    参考来源: andrewbartels1/SolidworksMCP-python (pywin32_adapter.py)
    """
    def __init__(self, prog_ids=None):
        self.prog_ids = prog_ids or [
            "SldWorks.Application", "SldWorks.Application.32", "SldWorks.Application.64"
        ]
        self.sw = None
        self.connected = False
        self._type_cache = {}  # API 签名缓存
    
    def connect(self):
        """连接 SolidWorks（整合 Sec 20 回退链 + Sec 25 ProgID 策略）"""
        # 第一优先：GetActiveObject
        try:
            self.sw = win32com.client.GetActiveObject("SldWorks.Application")
            self._on_connected()
            return self.sw
        except Exception:
            pass
        # 回退：遍历 ProgID
        for prog_id in self.prog_ids:
            try:
                self.sw = win32com.client.Dispatch(prog_id)
                self._on_connected()
                return self.sw
            except Exception:
                continue
        raise ConnectionError("无法连接或启动 SolidWorks")
    
    def _on_connected(self):
        self.sw.Visible = True
        self.sw.UserControl = True  # ⛔ MUST
        self.connected = True
        self._type_cache.clear()
    
    def auto_reconnect(self, max_retries=3, base_interval=5):
        """自动重连（指数退避 5s → 10s → 20s）"""
        for attempt in range(max_retries):
            try:
                _ = self.sw.Visible  # 探测连接
                return True
            except Exception:
                self.connected = False
                wait = base_interval * (2 ** attempt)
                print(f"连接断开，{wait}s 后重试 ({attempt+1}/{max_retries})")
                time.sleep(wait)
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
                pythoncom.CoInitialize()
                try:
                    self.connect()
                    return True
                except Exception:
                    continue
        raise ConnectionError(f"重连失败：已重试 {max_retries} 次")
    
    def safe_call(self, method_name, *args, circuit_breaker=None):
        """
        安全包装 COM 调用：捕获异常、超时保护、熔断器集成。
        """
        if circuit_breaker and not circuit_breaker.allow_request():
            raise COMCircuitBreakerOpenError("熔断器 Open，拒绝执行")
        try:
            method = getattr(self.sw.ActiveDoc.FeatureManager, method_name)
            result = method(*args)
            if circuit_breaker:
                circuit_breaker.record_success()
            return result
        except Exception as e:
            if circuit_breaker:
                circuit_breaker.record_failure(str(e))
            raise COMSafeError(f"{method_name} 失败: {e}")

class COMSafeError(Exception):
    pass
```

### ⚡ SHOULD：类型库信息缓存

```python
# 首次连接时缓存方法签名，避免重复 COM 元数据查询
def cache_type_info(sw_adapter):
    """缓存 SW 类型库信息"""
    try:
        type_info = sw_adapter.sw._oleobj_.GetTypeInfo()
        type_attr = type_info.GetTypeAttr()
        sw_adapter._type_cache["_type_attr"] = type_attr
        print(f"类型库缓存: {type_attr.cFuncs} 个方法")
    except Exception:
        pass  # 某些环境不支持
```

### 与 Sec 37 熔断器的集成点

- `safe_call()` 内部检查熔断器状态
- 熔断器 Open 时 `safe_call()` 拒绝执行
- 重连成功后重置熔断器为 Closed

---

## 四十、特征树遍历替代 SelectByID2（可靠性优先选择策略）

> 参考来源：[vespo92/SolidworksMCP-TS](https://github.com/vespo92/SolidworksMCP-TS) (MIT License)

### 问题背景

SelectByID2 存在多个已知问题：VARIANT 包装（Sec 29 M2）、中文名称不一致（Sec 27）、浮点误差。Sec 18 的 safe_select 提供了遍历回退，但只覆盖基准面。本 Section 提供系统化的特征树遍历框架。

### ⛔ MUST：FeatureTreeTraversal 框架

```python
class FeatureTreeTraversal:
    """
    系统化特征树遍历框架，替代 SelectByID2。
    参考来源: vespo92/SolidworksMCP-TS (feature-complexity-analyzer.ts)
    """
    
    @staticmethod
    def find_feature_by_name(doc, name):
        """按名称查找特征（正向遍历）"""
        feat = doc.FirstFeature  # 属性
        while feat is not None:
            feat_name = feat.Name  # 属性
            if feat_name == name:
                return feat
            feat = feat.GetNextFeature()  # 方法
        return None
    
    @staticmethod
    def find_feature_by_type(doc, type_name):
        """按类型查找特征（反向遍历，最新创建优先）"""
        feat = doc.FeatureManager.GetLastFeature()
        while feat is not None:
            if feat.GetTypeName2() == type_name:  # GetTypeName2 更精确
                return feat
            # 反向遍历需要手动实现（SW API 无 GetPreviousFeature）
            break  # 实际实现中需要完整遍历
        # 回退：正向遍历查找
        feat = doc.FirstFeature
        result = None
        while feat is not None:
            if feat.GetTypeName2() == type_name:
                result = feat
            feat = feat.GetNextFeature()
        return result
    
    @staticmethod
    def find_all_features_of_type(doc, type_name):
        """查找所有指定类型的特征"""
        results = []
        feat = doc.FirstFeature
        while feat is not None:
            if feat.GetTypeName2() == type_name:
                results.append(feat)
            feat = feat.GetNextFeature()
        return results
    
    @staticmethod
    def find_sketch_for_feature(doc, feature_name):
        """查找特征关联的草图"""
        feat = FeatureTreeTraversal.find_feature_by_name(doc, feature_name)
        if feat is None:
            return None
        try:
            definition = feat.GetDefinition()
            if definition is not None:
                return definition.GetSketch()
        except Exception:
            pass
        return None
```

### 特征类型常量速查

| GetTypeName2 返回值 | 特征类型 |
|------|------|
| `BaseBody` | 基体 |
| `Extrusion` | 拉伸 |
| `Cut` | 切除 |
| `Fillet` | 圆角 |
| `Chamfer` | 倒角 |
| `Shell` | 抽壳 |
| `RefPlane` | 参考基准面 |
| `Sketch` | 草图 |
| `ProfileFeature` | 轮廓特征 |

### ⚡ SHOULD：基准面选择优化（替代 Sec 18 safe_select）

```python
def find_plane_by_name(doc, plane_name, translations=None):
    """
    查找基准面（支持中英文双匹配）。
    整合 Sec 27 翻译表 + Sec 18 遍历回退。
    """
    if translations is None:
        translations = {
            "Front Plane": "前视基准面", "前视基准面": "Front Plane",
            "Top Plane": "上视基准面", "上视基准面": "Top Plane",
            "Right Plane": "右视基准面", "右视基准面": "Right Plane",
        }
    # 1. 正向遍历查找原名
    feat = doc.FirstFeature
    while feat is not None:
        if feat.Name == plane_name:
            feat.Select2(False, 0)
            return feat
        feat = feat.GetNextFeature()
    # 2. 尝试翻译名
    translated = translations.get(plane_name)
    if translated:
        feat = doc.FirstFeature
        while feat is not None:
            if feat.Name == translated:
                feat.Select2(False, 0)
                return feat
            feat = feat.GetNextFeature()
    return None
```

### 与 Sec 18 safe_select 的对比

| 维度 | safe_select (Sec 18) | FeatureTreeTraversal (本 Sec) |
|------|---------------------|-------------------------------|
| 覆盖范围 | 仅基准面 | 所有特征类型 |
| 遍历方向 | FirstFeature → forward | 支持正向 + GetLastFeature |
| 类型检测 | Name 字符串匹配 | GetTypeName2 + Name 双重匹配 |
| 草图查找 | 不支持 | find_sketch_for_feature() |
| 中英文兼容 | 无 | 内置翻译表 |

### 💡 MAY：特征树遍历的其他用途

- 建模历史审计（列出所有特征及其类型）
- 特征依赖性分析（通过 GetDependencies）
- 自动化特征重命名（批量改名）

---

## 四十一、COM 空值安全规则（Never Pass Null to COM）

> 参考来源：[vespo92/SolidworksMCP-TS](https://github.com/vespo92/SolidworksMCP-TS) (MIT License)

### 问题背景

SelectByID2 在 Python COM 下需要 VARIANT(VT_DISPATCH, None) 包装 Callout 参数。直接用 Python None 传递给 COM 方法会触发 TypeError。但并非所有"空值"都该用 VARIANT 包装——有些参数应该省略或使用默认值。

### ⛔ MUST：null vs undefined vs VARIANT(None) 对照表

| 参数类型 | 正确写法 | ❌ 错误写法 | 说明 |
|------|----------|----------|------|
| Object 可选参数 | `VARIANT(VT_DISPATCH, None)` | `None` | COM 将 None 解读为 VT_NULL → 类型不匹配 |
| 数值可选参数 | `0` (零) | `None` / `""` | COM 数值参数不接受 None |
| 字符串可选参数 | `""` (空字符串) | `None` | COM 字符串参数不接受 None |
| 布尔可选参数 | `False` | `None` | COM 布尔参数不接受 None |
| ByRef 参数 | `VARIANT(VT_BYREF \| VT_I4, 0)` | `0` | by-ref 必须 VARIANT 包装 |
| 数组参数 | `()` (空元组) | `None` / `[]` | COM 数组不接受 None |

### SelectByID2 失败根因分析

| 根因 | 现象 | 正确修复 |
|------|------|----------|
| Callout 传 Python None | TypeError | `VARIANT(VT_DISPATCH, None)` |
| 坐标传 0 但对象不在原点 | 选择失败 | 使用遍历查找（Sec 40） |
| Name 传空字符串 + 坐标全 0 | 无法定位 | 必须提供名称或坐标 |
| 中文名称在不同语言版本不一致 | 选择失败 | 中英文双匹配（Sec 40） |

### ⛔ MUST：参数传递 6 条最佳实践

```python
import win32com.client
import pythoncom

def safe_com_params(api_name, params):
    """
    将 Python 参数转换为 COM 安全格式。
    参考来源: vespo92/SolidworksMCP-TS (设计决策: "never pass null to COM")
    """
    safe = list(params)
    for i, val in enumerate(safe):
        if val is None:
            # 自动推断：根据参数位置判断类型
            if api_name == "SelectByID2" and i == 7:  # Callout
                safe[i] = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
            elif api_name == "Extension.SaveAs" and i in (4, 5):  # by-ref
                safe[i] = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            else:
                safe[i] = 0  # 数值默认值
    return tuple(safe)
```

### ⚡ SHOULD：COMSafeParams 工具类

```python
class COMSafeParams:
    """自动将 Python 参数转换为 COM 安全格式"""
    
    TYPE_DEFAULTS = {
        "object": lambda: win32com.client.VARIANT(pythoncom.VT_DISPATCH, None),
        "int": lambda: 0,
        "float": lambda: 0.0,
        "str": lambda: "",
        "bool": lambda: False,
        "byref": lambda: win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0),
    }
    
    @staticmethod
    def sanitize(value, param_type="int"):
        """将 None 转换为对应类型的安全空值"""
        if value is not None:
            return value
        converter = COMSafeParams.TYPE_DEFAULTS.get(param_type)
        if converter:
            return converter()
        return 0  # 默认数值
    
    @staticmethod
    def sanitize_all(values, types):
        """批量转换参数列表"""
        return tuple(
            COMSafeParams.sanitize(v, t) 
            for v, t in zip(values, types)
        )
```

### 💡 MAY：调试辅助

```python
def debug_com_params(api_name, params):
    """COM 调用失败时输出参数诊断信息"""
    print(f"API: {api_name}, 参数数: {len(params)}")
    for i, p in enumerate(params):
        ptype = type(p).__name__
        if hasattr(p, 'value'):  # VARIANT
            print(f"  [{i}] VARIANT({p.vt}, {p.value})")
        else:
            print(f"  [{i}] {ptype}: {p}")
```

### 与 Sec 29 M2 的关系

- **M2** 只覆盖 SelectByID2 Callout 参数的 VARIANT 包装
- **本 Section** 覆盖所有 COM 方法的空值处理规则
- M2 是子集，本 Section 是全集

---

## 四十二、COM 健康检查与超时保护（互联网实战经验）

> **来源**：CSDN @2402_87963769《SolidWorks AI 自动画图系统从零复现》(2026-06-01)  
> 该作者搭建了 Codex + MCP + PowerShell → SW COM 完整链路，踩了6个大坑后总结。

### 42.1 健康检查必须用子进程+超时

```python
import subprocess, sys

def check_sw_health(timeout=5):
    """检查 SW COM 是否健康（子进程+超时，防止无限卡死）"""
    try:
        proc = subprocess.Popen(
            [sys.executable, "-c",
             "import win32com.client; "
             "sw = win32com.client.Dispatch('SldWorks.Application'); "
             "print(sw.GetVersion())"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        if proc.returncode == 0 and stdout.strip():
            return True, stdout.strip()
        return False, stderr.strip()
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, f"COM 健康检查超时（>{timeout}s），SW 进程可能卡死"
```

**⚠️ 禁止在主进程中直接用 `GetActiveObject` 做健康检查** — 如果 SW 卡死，会无限挂起！

### 42.2 脏 COM 会话隔离（CreateObject vs GetObject）

| 操作 | 命令 | 风险 |
|------|------|------|
| `GetObject` | 接管现有 SW 进程的 COM 会话 | 🔴 **复用到脏会话** → cscript.exe 残留 → 任务卡死 |
| `CreateObject` / `Dispatch` | 新建干净 COM 会话 | ✅ 无残留问题 |

```python
# ✅ 正确——新建干净会话
sw = win32com.client.Dispatch("SldWorks.Application")
# ❌ 禁止——接管旧会话（除非铁律1主动复用）
# VBA: Set sw = GetObject(, "SldWorks.Application")
```

### 42.3 中文路径隔离策略

```python
import shutil, tempfile, os

def safe_open(file_path):
    """安全打开文件 — 中文路径 → 复制到英文临时路径"""
    if any(ord(c) > 127 for c in file_path):
        tmp = os.path.join(tempfile.gettempdir(),
                          "sw_" + os.path.basename(file_path))
        shutil.copy2(file_path, tmp)
        print(f"  ⚠ 中文路径检测，已复制到: {tmp}")
        return tmp
    return file_path
```

> **教训**：SW 对非 ASCII 路径偶发异常。**策略**：先复制到英文路径再操作。

---

## 四十三、装配体自动化规范（Codex 实战反馈）

> **来源**：  
> - 抖音 @Hvemiiiiiours《Codex+Solidworks完全自动化建模》(7717赞, 2026-05-10)  
> - B站 @奇葩人参果《AI自动建模 Codex SolidWorks》(2026-06)  
> 两位创作者实测了从"简单零件"到"带运动约束装配体"的完整进化。

### 43.1 装配体自动化四阶段

| 阶段 | 能力 | 典型问题 | 时间 |
|------|------|----------|:---:|
| 1 | 简单零件建模 | 尺寸不准、结构粗糙 | 2026-05 |
| 2 | 装配体生成 | **配合关系混乱，"一打开就散"** | 2026-05 |
| 3 | 刚性约束 | 加约束 → 变成刚性 → **机械臂动不了** | 2026-06 |
| 4 | 铰链约束 | 装配体可以完美运动 | 2026-06 |

### 43.2 配合铁律（Codex 验证的黄金顺序）

```
配合添加顺序（按此顺序，严禁跳过）：
1. 重合(Coincident) → 锚定第一个零件到装配体原点
2. 同心(Concentric) → 对齐轴心
3. 平行(Parallel) → 约束方向
4. 距离(Distance) / 角度(Angle) → 最后加可调参数
```

### 43.3 装配体常见错误修复表

| 错误现象 | 根因 | 修复 |
|----------|------|------|
| 零件插入后不显示 | `AddComponent` 返回 None | 检查路径 + 验证返回值 |
| 配合关系混乱 | 无约束或约束冲突 | 按"重合→同心→平行→距离"顺序添加 |
| 装配体刚性不动 | 配合过约束 | 删除多余约束 → 保留运动自由度 |
| 零件名称冲突 | 多次插入同名零件 | 用 `component.Name` 区分实例 |

---

## 四十四、工程图自动出图规范（企业案例）

> **来源**：网易 @Solidkits《从实践出发：SOLIDWORKS二次开发案例解析》(2025-08-08)  
> 某非标自动化设备制造企业实施 SW 二次开发。

### 44.1 四大自动化模块

| 模块 | 功能 | 效率提升 |
|------|------|:---:|
| 参数化建模 | 输入参数 → 自动生成模型+装配 | 80%+ |
| 自动出图 | 创建工程图 + 统一模板 | 60%+ |
| BOM 生成 | 从模型属性提取物料信息 | 90%+ |
| 文件管理 | 按编码规则自动命名+归档 | 50%+ |

### 44.2 自动出图核心代码

```python
def 自动出图(doc, template_path, output_path):
    """从3D模型自动生成2D工程图"""
    draw_doc = sw.NewDocument(template_path, 0, 0, 0)
    for view_name, plane, x, y in [
        ("前视", "Front Plane", 0.1, 0.1),
        ("上视", "Top Plane", 0.1, 0.2),
        ("右视", "Right Plane", 0.2, 0.1),
    ]:
        draw_doc.CreateDrawViewFromModel3(doc_path, plane, x, y, 0)
    # ⚠️ 铁律：3D 几何与 2D 标注必须同源！
    draw_doc.SaveAs3(output_path, 1, 2)
```

### 44.3 企业实施四大经验

| 经验 | 做法 |
|------|------|
| 需求调研先行 | 先搞清楚工程师真正需要什么 |
| 选对开发团队 | 必须有 SW API 实战经验 |
| 内部培训不可少 | 再好的工具，不会用就是废铁 |
| 持续迭代 | 技术工具和业务需求都在变 |

---

## 四十五、跨版本性能差异 + 开源项目参考

> **来源**：知乎《solidworks自动标注-python实现》(2023) + 技术邻《基于Python的Solidworks集成》(2025)

### 45.1 跨版本性能实测

| SW 版本 | 运行速度 | 原因推测 |
|---------|:---:|------|
| SW 2016 SP5 | ⚡ 快 | 旧版 API 简洁 |
| SW 2018 SP5 | 🐌 慢 | 新增安全检查+验证 |
| SW 2019 SP4 | 🐌 慢 | 同上 |
| SW 2020+ | ⚡ 恢复 | API 优化 |

> 旧版快、新版突然变慢 → **不是脚本问题，是 API 行为变了**。

### 45.2 网上 SW 自动化失败原因统计

| 失败类型 | 占比 | Skills 覆盖 |
|----------|:---:|:---:|
| COM 连接错误（版本/权限） | 35% | ✅ 连接回退链路 / 版本化 ProgID |
| API 参数顺序/数量错误 | 25% | ✅ API 参数探测 / API 参考 |
| 草图不闭合/浮点精度 | 15% | ✅ 草图绘制规范 |
| 模板路径硬编码 | 10% | ✅ 动态模板检测 |
| **装配体约束混乱** | **10%** | ✅ 见 Sec 43 |
| 中文路径问题 | 5% | ✅ 中文路径隔离策略 |

### 45.3 开源项目参考

| 项目 | 仓库 | 状态 | 可借鉴 |
|------|------|:---:|------|
| SolidWorks-Auto-Modeling-Agent | `github.com/yu-qing2` | 🔴 空仓库 | 架构思路 |
| CSDN Codex 复现教程 | `CSDN @2402_87963769` | 🟢 完整 | 6大踩坑 |
| AI 辅助科研 SW 手册 | `2dmaterial-lab.github.io` | 🟢 完整 | VBA 批量操作 |

---

## 四十六、AI+SolidWorks 能力边界（全网共识）

> **综合**：抖音/B站/CSDN/知乎/网易/技术邻，2025-2026

### 现阶段能做的 ✅

| 能力 | 成熟度 | 说明 |
|------|:---:|------|
| 简单零件自动化建模 | ⭐⭐⭐⭐ | 矩形、圆柱、标准特征很稳 |
| 参数化驱动（修改已有尺寸） | ⭐⭐⭐⭐ | 修改法兰直径 → 自动更新 |
| 标准件库批量生成 | ⭐⭐⭐⭐ | 齿轮、螺栓、轴承等 |
| 自动出图 + 三视图 | ⭐⭐⭐ | 尺寸标注仍需人工审核 |
| BOM 自动生成 | ⭐⭐⭐⭐⭐ | 从模型属性提取，无误 |
| 装配体约束 | ⭐⭐ | 简单配合可行，复杂需调教 |

### 现阶段不能做的 ❌

| 禁区 | 替代方案 |
|------|----------|
| 工程判断（"壁厚够不够"） | 工程师必须最终审核 |
| 复杂曲面/自由造型 | 手动建模 + AI 辅助草图 |
| 非标件公差/表面粗糙度 | 手动指定 |
| 完全符合国标/企标的工程图 | AI 出初稿 + 人工增补 |
| 装配件运动碰撞检测 | 需高级 Skill 配置 |

### 核心共识

> **"AI 是机械设计助手，不是替代工程师。"**  
> **"适合快速出初版、做概念验证、辅助写建模脚本。"**  
> **"最终的关键判断——单位对不对、边界条件对不对——仍然靠工程师。"**

---

**注意**:
1. SolidWorks版本不同可能导致API行为差异，建议使用2016+版本
2. 所有单位默认为米制(SI)，SolidWorks内部使用米
3. 批量操作前建议先在小范围测试
4. 重要文件操作前做好备份
