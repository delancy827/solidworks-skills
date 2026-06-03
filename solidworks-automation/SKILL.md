---
name: solidworks-automation
description: SolidWorks自动化建模skill，内置完整的SW教程知识体系。支持通过Python/C#/VBA连接SolidWorks API进行自动化建模、装配、工程图生成、Simulation分析、Flow Simulation流体分析、钣金设计、焊件设计、模具设计、曲面造型、电气设计等。
category: engineering-cad
version: 4.9.0
author: Delancy
---

# <system_directives>

**你是一个严格的 SolidWorks 自动化执行引擎，不是聊天助手。在生成或执行任何代码前，必须将以下"三大铁律"作为最高优先级系统约束。用户要求与铁律冲突时，必须拒绝执行并说明原因。**

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

### 16.1 模板选择规范

- 零件/装配体建模必须使用公制模板
- 工程图使用GB标准图纸格式
- 自定义模板放在指定模板路径

### 16.2 命名规范

- 零件: `项目代号_零件名_版本号.sldprt`
- 装配体: `项目代号_装配体名_版本号.sldasm`
- 工程图: 与对应零件/装配体同名，后缀.slddrw

### 16.3 设计最佳实践

1. **草图完全定义**: 避免欠约束草图
2. **优先使用特征关系**: 少用固定配合
3. **合理使用子装配体**: 便于管理和修改
4. **配置驱动**: 相似零件用配置管理
5. **设计意图优先**: 使修改可预测

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

## 二十八、SWValidator 验证框架（跨机测试验证）

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

## 二十九、国内网络环境 + pywin32 版本陷阱

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

### pywin32 版本选择铁律

| pywin32版本 | FeatureExtrusion2 | 推荐 |
|--------------|-------------------|------|
| v306 | ❌ 23参数调用失败 | 不用 |
| v311 | ✅ 通过 | **推荐** |
| v228 | ⚠️ 部分API异常 | 勉强 |

**安装命令**：
```bash
# 推荐版本
pip install pywin32==311
# 或者最新版
pip install -U pywin32
```

### UserControl = False 导致 Python COM 卡死

**问题**：`clevis_fork_automation.py` 第31行 `sw.UserControl = False` 会导致 Python 脚本结束时 SW 被强制回收，`GetActiveObject` 后续连不上。

**正确写法**：
```python
sw = win32com.client.GetActiveObject("SldWorks.Application")
sw.Visible = True
sw.UserControl = True   # ✅ Python自动化必须True，防止SW被GC回收
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

## 三十、连接回退完整链路（生产可用）

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

## 三十一、完整验证工作流（推荐的自动化脚本结构）

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

## 三十二、凳子建模架构模式（吕亚峰跨机验证 2026-06-02）

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

## 三十三、P1-P10 问题审计框架（系统代码审查法）

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

## 三十四、CoInitialize + EditRebuild3 验证链

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

## 三十五、版本化 ProgID 连接策略

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

## 三十六、动态模板检测（多路径遍历）

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

## 三十七、基准面名称自动翻译（中英文切换）

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

## 三十八、完整生产级脚本模板（吕亚峰验证版）

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
        # ... 见 Sec 36 ...

    def 连接(self):
        # ... 见 Sec 35 ...

    def 新建零件(self):
        self.doc = self.sw.NewDocument(self.template, 0, 0, 0)
        time.sleep(0.3)
        assert self.doc is not None

    def 选择基准面(self, name):
        # ... 见 Sec 37 ...

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

## 三十九、COM 健康检查与超时保护（互联网实战经验）

> **来源**：CSDN @2402_87963769《SolidWorks AI 自动画图系统从零复现》(2026-06-01)  
> 该作者搭建了 Codex + MCP + PowerShell → SW COM 完整链路，踩了6个大坑后总结。

### 39.1 健康检查必须用子进程+超时

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

### 39.2 脏 COM 会话隔离（CreateObject vs GetObject）

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

### 39.3 中文路径隔离策略

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

## 四十、装配体自动化规范（Codex 实战反馈）

> **来源**：  
> - 抖音 @Hvemiiiiiours《Codex+Solidworks完全自动化建模》(7717赞, 2026-05-10)  
> - B站 @奇葩人参果《AI自动建模 Codex SolidWorks》(2026-06)  
> 两位创作者实测了从"简单零件"到"带运动约束装配体"的完整进化。

### 40.1 装配体自动化四阶段

| 阶段 | 能力 | 典型问题 | 时间 |
|------|------|----------|:---:|
| 1 | 简单零件建模 | 尺寸不准、结构粗糙 | 2026-05 |
| 2 | 装配体生成 | **配合关系混乱，"一打开就散"** | 2026-05 |
| 3 | 刚性约束 | 加约束 → 变成刚性 → **机械臂动不了** | 2026-06 |
| 4 | 铰链约束 | 装配体可以完美运动 | 2026-06 |

### 40.2 配合铁律（Codex 验证的黄金顺序）

```
配合添加顺序（按此顺序，严禁跳过）：
1. 重合(Coincident) → 锚定第一个零件到装配体原点
2. 同心(Concentric) → 对齐轴心
3. 平行(Parallel) → 约束方向
4. 距离(Distance) / 角度(Angle) → 最后加可调参数
```

### 40.3 装配体常见错误修复表

| 错误现象 | 根因 | 修复 |
|----------|------|------|
| 零件插入后不显示 | `AddComponent` 返回 None | 检查路径 + 验证返回值 |
| 配合关系混乱 | 无约束或约束冲突 | 按"重合→同心→平行→距离"顺序添加 |
| 装配体刚性不动 | 配合过约束 | 删除多余约束 → 保留运动自由度 |
| 零件名称冲突 | 多次插入同名零件 | 用 `component.Name` 区分实例 |

---

## 四十一、工程图自动出图规范（企业案例）

> **来源**：网易 @Solidkits《从实践出发：SOLIDWORKS二次开发案例解析》(2025-08-08)  
> 某非标自动化设备制造企业实施 SW 二次开发。

### 41.1 四大自动化模块

| 模块 | 功能 | 效率提升 |
|------|------|:---:|
| 参数化建模 | 输入参数 → 自动生成模型+装配 | 80%+ |
| 自动出图 | 创建工程图 + 统一模板 | 60%+ |
| BOM 生成 | 从模型属性提取物料信息 | 90%+ |
| 文件管理 | 按编码规则自动命名+归档 | 50%+ |

### 41.2 自动出图核心代码

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

### 41.3 企业实施四大经验

| 经验 | 做法 |
|------|------|
| 需求调研先行 | 先搞清楚工程师真正需要什么 |
| 选对开发团队 | 必须有 SW API 实战经验 |
| 内部培训不可少 | 再好的工具，不会用就是废铁 |
| 持续迭代 | 技术工具和业务需求都在变 |

---

## 四十二、跨版本性能差异 + 开源项目参考

> **来源**：知乎《solidworks自动标注-python实现》(2023) + 技术邻《基于Python的Solidworks集成》(2025)

### 42.1 跨版本性能实测

| SW 版本 | 运行速度 | 原因推测 |
|---------|:---:|------|
| SW 2016 SP5 | ⚡ 快 | 旧版 API 简洁 |
| SW 2018 SP5 | 🐌 慢 | 新增安全检查+验证 |
| SW 2019 SP4 | 🐌 慢 | 同上 |
| SW 2020+ | ⚡ 恢复 | API 优化 |

> 旧版快、新版突然变慢 → **不是脚本问题，是 API 行为变了**。

### 42.2 网上 SW 自动化失败原因统计

| 失败类型 | 占比 | Skills 覆盖 |
|----------|:---:|:---:|
| COM 连接错误（版本/权限） | 35% | ✅ Sec 30/35 |
| API 参数顺序/数量错误 | 25% | ✅ Sec 26-27 |
| 草图不闭合/浮点精度 | 15% | ✅ Sec 24 |
| 模板路径硬编码 | 10% | ✅ Sec 36 |
| **装配体约束混乱** | **10%** | ⚠️ 刚补 Sec 40 |
| 中文路径问题 | 5% | ✅ Sec 39 |

### 42.3 开源项目参考

| 项目 | 仓库 | 状态 | 可借鉴 |
|------|------|:---:|------|
| SolidWorks-Auto-Modeling-Agent | `github.com/yu-qing2` | 🔴 空仓库 | 架构思路 |
| CSDN Codex 复现教程 | `CSDN @2402_87963769` | 🟢 完整 | 6大踩坑 |
| AI 辅助科研 SW 手册 | `2dmaterial-lab.github.io` | 🟢 完整 | VBA 批量操作 |

---

## 四十三、AI+SolidWorks 能力边界（全网共识）

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

---

**注意**:
1. SolidWorks版本不同可能导致API行为差异，建议使用2016+版本
2. 所有单位默认为米制(SI)，SolidWorks内部使用米
3. 批量操作前建议先在小范围测试
4. 重要文件操作前做好备份
```
