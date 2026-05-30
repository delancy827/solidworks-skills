---
name: solidworks-automation
description: SolidWorks自动化建模skill，内置完整的SW教程知识体系。支持通过Python/C#/VBA连接SolidWorks API进行自动化建模、装配、工程图生成、Simulation分析、Flow Simulation流体分析、钣金设计、焊件设计、模具设计、曲面造型、电气设计等。
category: engineering-cad
version: 3.0.0
author: Delancy
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
