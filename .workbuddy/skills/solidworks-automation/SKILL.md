---
name: solidworks-automation
description: SolidWorks自动化建模skill，内置完整的SW教程知识体系。⚠️ 2026-05-31架构升级：Python win32com对>12参数API（如FeatureCut4）支持不全，全面转向C# (.NET) 强类型早期绑定架构。支持通过C#/VBA连接SolidWorks API进行自动化建模、装配、工程图生成、Simulation分析、Flow Simulation流体分析、钣金设计、焊件设计、模具设计、曲面造型、电气设计等。
category: engineering-cad
version: 4.1.0
author: Delancy
---

# SolidWorks 自动化建模 Skill（C# 强类型架构版）

本skill内置了SolidWorks从入门到精通的全套知识体系，**现已全面升级为C# (.NET) 强类型早期绑定架构**。

## ⚡ 架构升级声明（2026-05-31）

**问题**：Python win32com 对多参数API（FeatureCut4有27个参数）支持不全，导致返回None或静默失败。

**解决方案**：全面采用C# (.NET) 强类型早期绑定，彻底解决参数传递限制。

**后续所有SolidWorks自动化脚本，必须以C#架构为准！**

---

## ⚠️ SW 2024 Python COM 关键踩坑（历史记录，仅供对照）

### 环境
- SW 2024 (中文版), Python 3.14 + pywin32, Windows 11

### Python COM 限制
| API | 参数数 | Python COM | C# 强类型 |
|-----|:---:|:---:|------|
| `NewDocument(template_path, ...)` | 4 | ✅ 完整路径 | ✅ |
| `SelectByID2` | 9 | ✅ VARIANT | ✅ |
| `FeatureExtrusion2` | 23 | ✅ | ✅ |
| `FeatureCut` | 20 | ❌ 返回None | ✅ |
| `FeatureCut3` | 26 | ❌ 返回None | ✅ |
| `FeatureCut4` | 27 | ❌ **>12参数COM限制** | ✅ **完美支持** |
| `FeatureFillet3` | 7 | ✅ | ✅ |
| `HoleWizard5` | 25+ | ❌ 类型不匹配 | ✅ |
| `InsertCombineFeature` | 3 | ❌ 类型不匹配 | ✅ |
| `GetBodies2` | 1 | ❌ 参数不匹配 | ✅ |

**结论**：复杂特征必须用C#，Python只适合简单任务。

---

## ⚡ C# 强类型全功能调用规范（2026-05-31 架构升级）

### 规范1：早期绑定与强类型声明 (Early Binding)

**核心原则**：彻底放弃动态类型，全面采用SolidWorks原生C++接口映射。

#### C# 代码头部强制引入
```csharp
using System;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
```

#### 连接SolidWorks（必须使用强类型转换）
```csharp
// ✅ 正确：使用Marshal.GetActiveObject + 强类型转换
SldWorks swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
swApp.Visible = true;
swApp.UserControl = false;

// ❌ 错误：Python风格的动态类型（不要用！）
// dynamic sw = ...  // 不要用dynamic
```

#### 文档类型强类型转换
```csharp
ModelDoc2 swDoc = (ModelDoc2)swApp.ActiveDoc;
PartDoc partDoc = (PartDoc)swDoc;
AssemblyDoc assyDoc = (AssemblyDoc)swDoc;
DrawingDoc drawDoc = (DrawingDoc)swDoc;
```

---

### 规范2：多参数高级特征的完美对齐

**核心原则**：必须利用C#强类型优势，写满全部参数，严禁省略。

#### FeatureCut4 完整27参数调用示例
```csharp
Feature cutFeat = swDoc.FeatureManager.FeatureCut4(
    false,                              // S: 是否双向切除
    false,                              // F: 是否薄壁特征
    false,                              // D: 是否使用方向2
    (int)swEndConditions_e.swEndCondThroughAll,  // T: 终止条件1 (完全贯穿)
    (int)swEndConditions_e.swEndCondThroughAll,  // T0: 终止条件2
    0.05,                               // D1: 深度1 (50mm)
    0.05,                               // D2: 深度2
    false,                              // B: 是否拔模
    false,                              // B0: 方向1拔模角度
    false,                              // B1: 方向2拔模角度
    false,                              // B2: 方向1拔模类型
    0,                                  // D3: 拔模角度1
    0,                                  // D4: 拔模角度2
    false,                              // F0: 是否翻转拔模方向
    false,                              // F1: 是否合并结果
    false,                              // F2: 是否使用等距
    false,                              // F3: 是否反转等距
    false,                              // I: 是否起始条件
    false,                              // I0: 是否方向1起始条件
    false,                              // I1: 是否方向2起始条件
    false,                              // I2: 是否反转方向
    false,                              // R: 是否方向1反向
    false,                              // R0: 是否方向2反向
    false,                              // R1: 是否透明
    false,                              // R2: 是否使用轮廓选择
    false,                              // D0: 是否方向1草图法向
    false,                              // D1: 是否方向2草图法向
    false,                              // D2: 是否方向1等距反转
    false,                              // D3: 是否方向2等距反转
    false                               // D4: 未使用
);
```

**关键要点**：
- 所有枚举常量必须通过 `(int)` 强制转换为SolidWorks官方枚举
- 完全贯穿必须写为：`(int)swEndConditions_e.swEndCondThroughAll`
- blind深度：`(int)swEndConditions_e.swEndCondBlind`

#### FeatureExtrusion2 完整23参数调用示例
```csharp
Feature extrudeFeat = swDoc.FeatureManager.FeatureExtrusion2(
    false,                              // S: 是否双向拉伸
    false,                              // Flip: 是否翻转方向
    false,                              // Dir: 是否使用方向2
    (int)swEndConditions_e.swEndCondBlind,   // T1: 终止条件1
    (int)swEndConditions_e.swEndCondBlind,   // T2: 终止条件2
    0.05,                               // D1: 深度1
    0.05,                               // D2: 深度2
    false,                              // B: 是否拔模
    false,                              // B0: 方向1拔模
    false,                              // B1: 方向2拔模
    false,                              // B2: 拔模类型
    0,                                  // D3: 拔模角度1
    0,                                  // D4: 拔模角度2
    false,                              // F0: 翻转拔模
    false,                              // F1: 合并结果
    false,                              // F2: 使用等距
    false,                              // F3: 反转等距
    false,                              // I: 起始条件
    false,                              // I0: 方向1起始
    false,                              // I1: 方向2起始
    false,                              // I2: 反转方向
    false,                              // R: 方向1反向
    false,                              // R0: 方向2反向
    false                               // R1: 透明
);
```

---

### 规范3：稳固的实体表面选择机制 (SelectByRay)

**核心原则**：坚决放弃依赖不稳定的面名称（如"Face<1>"），改用绝对稳定的"空间射线拾取法"。

#### SelectByRay 方法签名
```csharp
bool result = swDoc.Extension.SelectByRay(
    double X,           // 射线起点X坐标
    double Y,           // 射线起点Y坐标
    double Z,           // 射线起点Z坐标
    double DX,          // 射线方向向量X
    double DY,          // 射线方向向量Y
    double DZ,          // 射线方向向量Z
    double RayRadius,    // 射线半径（拾取容差）
    int Append,          // 是否追加选择（0=否，1=是）
    int Mark,            // 选择标记
    int Callout          // 是否显示标注
);
```

#### 实战示例：选择拉伸实体的前表面（Z=0面）
```csharp
// 步骤1：获取实体
Body2 body = (Body2)swDoc.GetBodies2((int)swBodyType_e.swSolidBody)[0];

// 步骤2：遍历所有面，找到目标面
Face2[] faces = (Face2[])body.GetFaces();
Face2 targetFace = null;

foreach (Face2 face in faces)
{
    double[] normal = (double[])face.Normal;
    // 找到Z轴负方向的面（前表面）
    if (Math.Abs(normal[2]) > 0.99 && normal[2] < 0)
    {
        targetFace = face;
        break;
    }
}

// 步骤3：使用SelectByRay精准选择
if (targetFace != null)
{
    // 获取面的中心点
    double[] centroid = (double[])targetFace.GetCentroid();
    
    // 从面的法向反方向发射射线
    bool result = swDoc.Extension.SelectByRay(
        centroid[0], centroid[1], centroid[2],  // 射线起点（面中心）
        -normal[0], -normal[1], -normal[2],     // 射线方向（指向面）
        0.01,                                    // 射线半径（10mm容差）
        1,                                         // 追加选择
        0,                                         // 选择标记
        0                                          // 不显示标注
    );
    
    if (result)
        Console.WriteLine("✓ 表面选择成功");
    else
        Console.WriteLine("✗ 表面选择失败");
}
```

**优势**：
- ✅ 不依赖面的名称（面名称会变化）
- ✅ 通过空间坐标精准定位
- ✅ 支持容差控制（RayRadius参数）
- ✅ 100%稳定可靠

---

### C# 控制台程序标准框架

```csharp
// Program.cs - SolidWorks C# 二次开发控制台程序
// 编译命令: 
// csc /r:"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\SolidWorks.Interop.sldworks.dll" 
//     /r:"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\SolidWorks.Interop.swconst.dll" 
//     Program.cs

using System;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SWCSharpAutomation
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== SolidWorks C# 二次开发控制台程序 ===\n");

            // ============================================
            // 步骤0：连接SolidWorks
            // ============================================
            Console.WriteLine("[1/4] 连接SolidWorks...");
            
            SldWorks swApp = null;
            
            try
            {
                // 方法1：通过Marshal连接已运行的SW实例
                swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
                swApp.Visible = true;
                swApp.UserControl = false;
                Console.WriteLine("  ✓ 已连接到运行的SolidWorks实例");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  ✗ 连接失败: {ex.Message}");
                Console.WriteLine("  请确保SolidWorks已经启动");
                return;
            }

            // ============================================
            // 步骤1：新建零件
            // ============================================
            Console.WriteLine("\n[2/4] 新建零件...");
            
            try
            {
                // 使用默认零件模板
                swApp.NewPart();
                System.Threading.Thread.Sleep(1000); // 等待文档创建
                
                ModelDoc2 swDoc = (ModelDoc2)swApp.ActiveDoc;
                if (swDoc == null)
                {
                    Console.WriteLine("  ✗ 新建零件失败");
                    return;
                }
                
                Console.WriteLine($"  ✓ 零件已创建: {swDoc.GetTitle()}");
                
                // ============================================
                // 步骤2：绘制草图并拉伸
                // ============================================
                Console.WriteLine("\n[3/4] 绘制草图并拉伸...");
                
                // 选择前视基准面（中文版）
                bool selectResult = swDoc.Extension.SelectByID2(
                    "前视基准面",   // 中文版基准面名称
                    "PLANE", 
                    0, 0, 0, 
                    false, 0, null, 0
                );
                
                if (!selectResult)
                {
                    Console.WriteLine("  ✗ 选择前视基准面失败");
                    return;
                }
                
                // 创建草图
                swDoc.SketchManager.InsertSketch(true);
                
                // 绘制100x100mm矩形（中心在原点）
                swDoc.SketchManager.CreateCornerRectangle(
                    -0.05, 0.05, 0,   // 左上角 (-50mm, 50mm)
                    0.05, -0.05, 0     // 右下角 (50mm, -50mm)
                );
                
                Console.WriteLine("  ✓ 草图绘制完成: 100x100mm矩形");
                
                // 关闭草图
                swDoc.SketchManager.InsertSketch(true);
                
                // 创建拉伸特征 (50mm)
                Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
                    false, false, false,
                    (int)swEndConditions_e.swEndCondBlind,
                    (int)swEndConditions_e.swEndCondBlind,
                    0.05, 0.05,
                    false, false, false, false,
                    0, 0, false, false, false, false, false, false, false, false, false, false
                );
                
                if (feat == null)
                {
                    Console.WriteLine("  ✗ 拉伸特征创建失败");
                    return;
                }
                
                Console.WriteLine($"  ✓ 拉伸特征创建成功: {feat.Name}");
                
                // 强制重建模型
                swDoc.ForceRebuild3(false);
                Console.WriteLine("  ✓ 模型重建完成");
                
                // 停顿3秒供截图
                Console.WriteLine("  ⏸  停顿3秒供截图...");
                System.Threading.Thread.Sleep(3000);
                
                Console.WriteLine("\n=== 所有操作完成 ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n✗ 错误: {ex.Message}");
                Console.WriteLine($"  堆栈: {ex.StackTrace}");
            }
        }
    }
}
```

---

**后续所有SolidWorks自动化任务，必须基于这套C#强类型架构进行输出！**

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

## 十八、强制验证机制（CRITICAL - 2026-05-31新增）

### 问题背景
AI生成代码后经常报告"任务完成"，但实际上SolidWorks并未真正执行操作。必须建立**强制验证机制**，确保每个API调用后都验证结果。

---

### 18.1 验证原则（必须遵守）

| 操作类型 | 验证方法 | 代码示例 |
|---------|---------|---------|
| **连接SW** | 检查对象是否为None，获取版本号 | `sw_app.GetVersion()` |
| **打开文档** | 检查`ActiveDoc`是否为None | `doc = sw_app.ActiveDoc` |
| **选择对象** | 检查`SelectByID2`返回值 + `GetSelectedObjectCount2` | `if not result: raise Error` |
| **创建特征** | 1. 检查返回值是否为None<br>2. 比对`GetFeatureCount`<br>3. 按名称查找特征 | `if feat is None: verify by count` |
| **创建草图** | 检查`GetActiveSketch()` + `GetSketchSegmentsCount()` | `if sketch.GetSketchSegmentsCount() == 0: raise` |
| **模型重建** | 检查`EditRebuild3`返回值 | `if not doc.EditRebuild3: raise` |
| **保存文档** | 检查`Save()`/`SaveAs3`返回值 | `if result != 1: raise` |

---

### 18.2 属性 vs 方法（常见错误）

**重要**：以下API是**属性**，不是方法，调用时**不要加括号**：

```python
# ✅ 正确 - 属性直接访问
title = doc.GetTitle          # 不是 GetTitle()
count = doc.GetFeatureCount  # 不是 GetFeatureCount()
type = doc.GetType           # 不是 GetType()
docs = sw_app.GetDocuments   # 不是 GetDocuments()
feat = doc.FirstFeature      # 不是 FirstFeature()
next_feat = feat.GetNextFeature  # 不是 GetNextFeature()
rebuild = doc.EditRebuild3  # 不是 EditRebuild3()
sketch = doc.SketchManager.ActiveSketch  # 不是 ActiveSketch()

# ❌ 错误 - 这些方法不存在
doc.GetTitle()     # TypeError: 'str' object is not callable
doc.GetFeatureCount()  # TypeError
```

---

### 18.3 SelectByID2 失效替代方案

**SW 2024 SP5 + Python 3.13 已知问题**：`SelectByID2` 可能返回`False`（即使参数正确）。

#### 方案1：遍历特征树（推荐）
```python
def safe_select_by_name(doc, target_name):
    """通过遍历特征树选择对象（替代SelectByID2）"""
    feat = doc.FirstFeature
    while feat is not None:
        if feat.Name == target_name:
            feat.Select2(False, 0)
            print(f"✓ 通过遍历选择成功: {target_name}")
            return True
        feat = feat.GetNextFeature
    
    print(f"✗ 未找到特征: {target_name}")
    return False
```

#### 方案2：通过选择集
```python
# 先手动选择一次，保存到选择集，后续直接调用
sel_mgr = doc.SelectionManager
sel_set = sel_mgr.AddSelectionSet("MySelectionSet")
sel_set.AddMember(target_object)
sel_set.SelectMembers(True)
```

#### 方案3：直接获取对象引用
```python
# 能直接获取对象时，优先用 Select2 方法
feat = feat_mgr.GetFeatureByName("拉伸1")
if feat is not None:
    feat.Select2(False, 0)  # 直接选择，不依赖名称
```

---

### 18.4 完整验证框架代码

```python
import win32com.client
import pythoncom

class SWValidator:
    """SolidWorks API调用验证器"""
    
    @staticmethod
    def verify_connection(sw_app):
        """验证SW应用连接"""
        if sw_app is None:
            raise Exception("SW应用对象为None")
        version = sw_app.GetVersion()
        print(f"✓ SW连接验证通过 - 版本: {version}")
        return True
    
    @staticmethod
    def verify_document(doc):
        """验证文档是否打开"""
        if doc is None:
            raise Exception("文档验证失败: ActiveDoc为None")
        title = doc.GetTitle
        print(f"✓ 文档验证通过 - {title}")
        return True
    
    @staticmethod
    def verify_selection(doc, expected_count=None):
        """验证选择是否成功"""
        sel_mgr = doc.SelectionManager
        count = sel_mgr.GetSelectedObjectCount2(-1)
        
        if expected_count is not None and count != expected_count:
            raise Exception(f"选择验证失败: 期望{expected_count}个, 实际{count}个")
        
        if count == 0:
            print(f"⚠ 警告: 未选择任何对象")
            return False
        
        print(f"✓ 选择验证通过 - 已选择{count}个对象")
        return True
    
    @staticmethod
    def verify_feature_created(doc, before_count=None, feat_name=None):
        """验证特征是否创建成功"""
        # 方法1: 比对特征数量
        if before_count is not None:
            after_count = doc.GetFeatureCount
            if after_count <= before_count:
                raise Exception(f"特征创建失败: {before_count} → {after_count}")
            print(f"✓ 特征数量验证通过: {before_count} → {after_count}")
        
        # 方法2: 按名称查找
        if feat_name is not None:
            feat_mgr = doc.FeatureManager
            feat = feat_mgr.GetFeatureByName(feat_name)
            if feat is None:
                raise Exception(f"特征创建失败: 未找到 '{feat_name}'")
            print(f"✓ 特征 '{feat_name}' 验证通过")
            return feat
        
        # 方法3: 获取最后一个特征
        last_feat = doc.FeatureManager.GetLastFeature()
        if last_feat is None:
            raise Exception("特征创建失败: 无法获取最后一个特征")
        
        print(f"✓ 特征创建验证通过: {last_feat.Name}")
        return last_feat
    
    @staticmethod
    def verify_sketch_has_entities(doc):
        """验证草图是否包含实体"""
        sketch = doc.SketchManager.ActiveSketch
        if sketch is None:
            raise Exception("草图验证失败: 没有活动草图")
        
        seg_count = sketch.GetSketchSegmentsCount()
        if seg_count == 0:
            raise Exception("草图验证失败: 草图不包含任何线段")
        
        print(f"✓ 草图验证通过: {seg_count}个线段")
        return True
    
    @staticmethod
    def verify_rebuild(doc):
        """验证模型重建"""
        result = doc.EditRebuild3
        if result is False:
            raise Exception("模型重建失败")
        print(f"✓ 模型重建验证通过")
        return True

# 使用示例
validator = SWValidator()

# 连接SW
sw_app = win32com.client.GetActiveObject("SldWorks.Application")
validator.verify_connection(sw_app)

# 新建零件
sw_app.NewPart()
doc = sw_app.ActiveDoc
validator.verify_document(doc)

# 选择基准面
result = doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
if not result:
    raise Exception("选择前视基准面失败")
validator.verify_selection(doc, expected_count=1)

# 创建草图
doc.SketchManager.InsertSketch(True)
validator.verify_sketch_has_entities(doc)

# 绘制矩形
doc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.1, 0.1, 0)

# 关闭草图
doc.SketchManager.InsertSketch(True)

# 创建拉伸特征
before_count = doc.GetFeatureCount
feat = doc.FeatureManager.FeatureExtrusion2(
    False, False, False, 0, 0,
    0.05, 0, False, False, False, False,
    0, 0, False, False, False,
    False, True, True, 0, 0, False
)

# 验证特征创建
if feat is None:
    validator.verify_feature_created(doc, before_count=before_count)
else:
    print(f"✓ 拉伸特征创建成功: {feat.Name}")

# 验证模型重建
validator.verify_rebuild(doc)
```

---

### 18.5 标准自动化脚本模板（带强制验证）

```python
"""
SolidWorks自动化脚本模板（带强制验证）
每个操作后都必须验证，确保真正执行成功
"""

import win32com.client
import pythoncom
import time

class SolidWorksAutomation:
    def __init__(self, sw_version="32"):
        self.sw_version = sw_version
        self.sw_app = None
        self.doc = None
        self.validator = None
        
    def connect(self):
        """连接SolidWorks（复用现有实例）"""
        print("正在连接SolidWorks...")
        try:
            self.sw_app = win32com.client.GetActiveObject("SldWorks.Application")
            print("✓ 连接到已运行的SolidWorks实例")
        except:
            self.sw_app = win32com.client.Dispatch(f"SldWorks.Application.{self.sw_version}")
            print("✓ 启动新的SolidWorks实例")
        
        self.sw_app.Visible = True
        self.sw_app.UserControl = False
        
        # 验证连接
        if self.sw_app is None:
            raise Exception("SW应用对象为None")
        version = self.sw_app.GetVersion()
        print(f"✓ SW连接验证通过 - 版本: {version}")
        
        # 导入验证器
        from sw_verification_framework import SWValidator
        self.validator = SWValidator()
        
        return self.sw_app
    
    def new_part(self, template=""):
        """新建零件文档"""
        if not template:
            self.sw_app.NewPart()
        else:
            self.sw_app.NewDocument(template, 0, 0, 0)
        
        time.sleep(1)  # 等待文档创建
        
        self.doc = self.sw_app.ActiveDoc
        self.validator.verify_document(self.doc)
        
        return self.doc
    
    def safe_select(self, name, obj_type, x=0, y=0, z=0):
        """安全选择（带验证 + 替代方案）"""
        self.doc.ClearSelection2(True)
        
        # 尝试SelectByID2
        result = self.doc.Extension.SelectByID2(
            name, obj_type, x, y, z, False, 0,
            win32com.client.VARIANT(pythoncom.VT_DISPATCH, None), 0
        )
        
        if result:
            self.validator.verify_selection(self.doc, expected_count=1)
            return True
        else:
            print(f"⚠ SelectByID2失败: {name}")
            # 尝试遍历选择
            return self._select_by_traversal(name)
    
    def _select_by_traversal(self, target_name):
        """通过遍历选择（SelectByID2失效时的替代方案）"""
        print(f"尝试通过遍历选择: {target_name}")
        
        feat = self.doc.FirstFeature
        while feat is not None:
            if feat.Name == target_name:
                feat.Select2(False, 0)
                print(f"✓ 通过遍历选择成功: {target_name}")
                self.validator.verify_selection(self.doc, expected_count=1)
                return True
            feat = feat.GetNextFeature
        
        raise Exception(f"遍历选择也失败: {target_name}")
    
    def create_extrude(self, depth_mm, name=None):
        """创建拉伸特征（带验证）"""
        before_count = self.doc.GetFeatureCount
        
        # 关闭草图
        self.doc.SketchManager.InsertSketch(True)
        
        # 执行拉伸（SW内部单位是米）
        depth_m = depth_mm / 1000.0
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, False, False, 0, 0,
            depth_m, 0, False, False, False, False,
            0, 0, False, False, False,
            False, True, True, 0, 0, False
        )
        
        # 验证
        if feat is None:
            # 返回值None不代表失败，需要通过特征数量验证
            self.validator.verify_feature_created(self.doc, before_count=before_count)
        else:
            print(f"✓ 拉伸特征创建成功: {feat.Name}")
            return feat
    
    def save_and_close(self, path=None):
        """保存并关闭文档"""
        if path:
            result = self.doc.SaveAs3(path, 1, 2)
            if result != 1:
                raise Exception(f"保存失败: 错误码 {result}")
            print(f"✓ 文档已保存: {path}")
        
        title = self.doc.GetTitle
        self.sw_app.CloseDoc(title)
        print(f"✓ 文档已关闭: {title}")
    
    def cleanup(self):
        """清理资源"""
        if self.sw_app is not None:
            self.sw_app.CloseAllDocuments(True)
            self.sw_app.ExitApp()
            self.sw_app = None
            print("✓ 已清理SW资源")

# 使用示例
if __name__ == "__main__":
    sw = SolidWorksAutomation()
    
    try:
        sw.connect()
        sw.new_part()
        
        # 创建草图
        sw.safe_select("Front Plane", "PLANE")
        sw.doc.SketchManager.InsertSketch(True)
        sw.validator.verify_sketch_has_entities(sw.doc)
        
        # 绘制矩形
        sw.doc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.1, 0.1, 0)
        
        # 创建拉伸
        sw.create_extrude(50)
        
        # 验证重建
        sw.validator.verify_rebuild(sw.doc)
        
        print("\n" + "="*60)
        print("✓ 所有操作验证通过！")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 操作失败: {e}")
    finally:
        sw.cleanup()
```

---

### 18.6 调试技巧

#### 问题1：特征创建失败但返回None
```python
# FeatureExtrusion2返回None不代表失败
feat = doc.FeatureManager.FeatureExtrusion2(...)

if feat is None:
    # 需要进一步验证
    before_count = ...  # 创建前的特征数量
    after_count = doc.GetFeatureCount
    
    if after_count > before_count:
        print("特征实际创建成功（返回值None是SW API的正常行为）")
    else:
        print("特征创建失败")
```

#### 问题2：SelectByID2在SW2024失效
```python
# 方案1：遍历特征树
def select_by_traversal(doc, target_name):
    feat = doc.FirstFeature
    while feat is not None:
        if feat.Name == target_name:
            feat.Select2(False, 0)
            return True
        feat = feat.GetNextFeature
    return False

# 方案2：使用SelectionManager
sel_mgr = doc.SelectionManager
# ... 手动选择后保存到选择集
```

#### 问题3：如何确认草图是否真正创建
```python
# 验证1：检查ActiveSketch
sketch = doc.SketchManager.ActiveSketch
if sketch is not None:
    print(f"草图激活: {sketch.Name}")

# 验证2：检查草图线段数量
seg_count = sketch.GetSketchSegmentsCount()
print(f"草图包含 {seg_count} 个线段")

# 验证3：检查特征树中是否有草图特征
feat = doc.FeatureManager.GetFeatureByName("草图1")
if feat is not None:
    print("草图特征已创建")
```

---

**总结**：每个API调用后都必须验证，不能假设成功。使用本文档提供的验证框架，确保真正完成任务。

---

## 二十、2026-05-31 实战突破 — C# 高级自动化架构升级

> **背景**：在叉形接头（Clevis Joint）全自动建模攻坚中，经过多轮迭代调试，总结出以下实战经验。所有方法均已实机验证通过。

---

### 20.1 进程与权限隔离避坑指南 ⚡

#### 问题背景
`Marshal.GetActiveObject("SldWorks.Application")` 会因为 Windows UAC 权限错配（SW 管理员 vs EXE 普通权限）导致连接假死——返回的对象非 null，但实际无法操作任何文档。

#### 根因
COM 在不同权限级别下运行在不同的 Window Station，`GetActiveObject` 只能连到同权限级别的 COM 实例。

#### 推荐方案
```csharp
// ✅ 正确：用 Activator.CreateInstance 强行拉起与 EXE 权限绝对一致的干净 SW 实例
Type swType = Type.GetTypeFromProgID("SldWorks.Application");
swApp = (SldWorks)Activator.CreateInstance(swType);
swApp.Visible = true;
// swApp.UserControl = false;  // ⚠️ 不要设置！否则 SW 窗口不可操作

// ❌ 错误：Marshal.GetActiveObject 权限隔离时会假死
// swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
```

#### 使用规则
| 场景 | 方案 |
|------|------|
| SW 已开（同权限） | `Marshal.GetActiveObject` ✅ |
| SW 未开 / 权限不明 | `Activator.CreateInstance` ✅ 最安全 |
| 任何自动化脚本 | **首选 Activator.CreateInstance** |

#### 新建零件规范
```csharp
// ✅ 正确：NewDocument + 备用模板路径
string partTemplate = swApp.GetUserPreferenceStringValue(
    (int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
if (string.IsNullOrEmpty(partTemplate)) 
    partTemplate = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\零件.prtdot";
swApp.NewDocument(partTemplate, 0, 0, 0);
swDoc = (ModelDoc2)swApp.ActiveDoc;
```

---

### 20.2 中英文双语环境健壮性 🏗️

#### 问题背景
`SelectByID2("前视基准面", "PLANE", ...)` 在英文 SW 下静默返回 `false`，没有任何错误提示。

#### 标准防错逻辑
```csharp
// ✅ 正确：双语兜底选择基准面
bool planeOK = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
if (!planeOK) 
    planeOK = swDoc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
if (!planeOK) 
{
    Console.WriteLine("✗ 未找到前视基准面");
    return;
}
Console.WriteLine("✓ 前视基准面选中");
```

#### 注意事项
- ⚠️ `ModelDoc2.FeatureByName()` 在此 Interop 版本中不存在（编译错误）
- ⚠️ `SldWorks` 类（具体类）和 `ISldWorks` 接口方法签名不同，编译时必须对齐
- ⚠️ `swApp.NewPart()` 方法不存在，必须用 `NewDocument()`

---

### 20.3 实体面遍历算法（GetBodies2）

> **核心突破**：`SelectByRay` 射线法在复杂几何上容易脱靶，
> 改用 **GetBodies2 → GetFaces → 几何极值** 实现精准定位。

#### 为什么 SelectByRay 不可靠？
- 射线起点/方向参数需要精确计算，一个人工错误就射不中
- 在拉伸/切除后的变形几何上，之前计算的面坐标已经失效
- 叉形接头的后端面、顶面用射线法反复失败

#### 推荐方案：遍历实体面 + 几何极值定位

```csharp
// 找 X 坐标最小的面（后端面）
static object FindFaceByMinX(ModelDoc2 swDoc)
{
    PartDoc partDoc = (PartDoc)swDoc;
    object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
    if (bodies == null || bodies.Length == 0) return null;
    
    Body2 body = (Body2)bodies[0];
    object[] faces = (object[])body.GetFaces();
    if (faces == null || faces.Length == 0) return null;

    Face2 bestFace = null;
    double minX = double.MaxValue;
    foreach (Face2 face in faces)
    {
        double[] box = (double[])face.GetBox();
        // box[0] = minX, box[1] = minY, box[2] = minZ
        // box[3] = maxX, box[4] = maxY, box[5] = maxZ
        if (box[0] < minX) { minX = box[0]; bestFace = face; }
    }
    return bestFace;
}

// 找 Y 坐标最大的面（顶面）
static object FindFaceByMaxY(ModelDoc2 swDoc)
{
    // 同上结构，判断条件改为 box[4] > maxY
}
```

#### 选中面（通过 Entity.Select4）
```csharp
static void SelectFace(object faceObj)
{
    Face2 face = (Face2)faceObj;
    Entity ent = (Entity)face;
    ent.Select4(false, null);  // false = 不追加，null = 无标记数据
}
```

#### 优势总结
| 方法 | 稳定性 | 复杂度 | 适用场景 |
|------|:---:|:---:|------|
| `SelectByID2` 按名称 | ⭐⭐ | 低 | 已知名称的基准面 |
| `SelectByRay` 射线法 | ⭐⭐ | 高 | 简单几何体 |
| **`GetBodies2` 遍历法** | ⭐⭐⭐⭐⭐ | 中 | **任何复杂几何** ✅ |

---

### 20.4 C# 5 语法规范（编译器兼容）

#### 硬性规定
```csharp
// ❌ C# 6+ 字符串插值 → 在 CSC 4.0 编译报错
// Console.WriteLine($"错误: {ex.Message}");

// ✅ C# 5 写法
Console.WriteLine(string.Format("错误: {0}", ex.Message));

// ❌ 自动属性初始化
// public int Count { get; set; } = 0;

// ✅ 构造函数赋值
public int Count { get; set; }
public Program() { Count = 0; }
```

#### 实际编译命令（E: 盘 SW2024）
```bash
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe \
  /reference:"E:/sw2024/SOLIDWORKS/api/redist/SolidWorks.Interop.sldworks.dll" \
  /reference:"E:/sw2024/SOLIDWORKS/api/redist/SolidWorks.Interop.swconst.dll" \
  /out:Clevis_Joint.exe \
  Clevis_Joint.cs
```

---

### 20.5 FeatureExtrusion2 精确 23 参数 + FeatureCut4 精确 27 参数

#### 背景
**反射探测验证**（`Probe_Signature.exe` 实机运行确认）：
- `FeatureExtrusion2` 真实参数数：**23**（不是 22，不是 21）
- `FeatureCut4` 真实参数数：**27**
- 两个 API 参数顺序在 E: 盘 SW2024 Interop DLL 中与官方文档不完全一致

#### FeatureExtrusion2 23 参数（实战可编译版）
```csharp
// ✅ 此签名已通过 csc.exe 编译验证（Stage2_Test.cs）
Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
    false,                               // Sd 双向
    false,                               // Flip 翻转方向
    false,                               // Dir 方向2
    (int)swEndConditions_e.swEndCondBlind,   // T1 终止条件1
    (int)swEndConditions_e.swEndCondBlind,   // T2 终止条件2
    0.050,                               // D1 深度1 (米)
    0.050,                               // D2 深度2 (米)
    false,                               // Dchk1 拔模1
    false,                               // Dchk2 拔模2
    false,                               // Ddir1 拔模方向1
    false,                               // Ddir2 拔模方向2
    0.0,                                 // Dang1 拔模角度1
    0.0,                                 // Dang2 拔模角度2
    false,                               // OffsetReverse1
    false,                               // OffsetReverse2
    false,                               // TranslateSurface1
    false,                               // TranslateSurface2
    false,                               // Merge 合并
    false,                               // UseFeatScope
    false,                               // UseAutoSelect
    0,                                   // T0 起始条件
    0.0,                                 // StartOffset
    false                                // FlipStartOffset
);
```

#### FeatureCut4 27 参数（实战可编译版）
```csharp
// ✅ 此签名已通过 csc.exe 编译验证（Stage2_Test.cs）
Feature cutFeat = swDoc.FeatureManager.FeatureCut4(
    false, false, false,
    (int)swEndConditions_e.swEndCondThroughAll,
    (int)swEndConditions_e.swEndCondThroughAll,
    0.0, 0.0,
    false, false, false, false, 0.0, 0.0,
    false, false, false, false,
    false, false, false,
    false, false, false,
    0, 0.0, false, false
);
```

---

### 20.6 验证机制（防止假成功）

```csharp
// SW API 返回值 null 不代表失败！
int before = swDoc.GetFeatureCount();
swDoc.ForceRebuild3(false);
int after = swDoc.GetFeatureCount();
if (after > before) 
    Console.WriteLine("✓ 特征实际创建成功");
else 
    Console.WriteLine("✗ 特征创建失败");
```

---

### 20.7 当前残余 Bug 记录（2026-05-31）

| Bug | 描述 | 优先级 |
|-----|------|:---:|
| **步骤3 圆弧偏移** | `CreateArc` 半圆切除位置偏置，导致切成"拱门"形状。圆心坐标需精确对齐柄部末端 X=-0.045m。 | P0 |
| **步骤4 U形槽坐标** | `CreateCornerRectangle` 参数需要与叉部顶面对齐，Z 轴 0.0125~0.0375m 居中。 | P0 |
| **Φ18 通孔** | 步骤3 的 Φ18 通孔和步骤4 的双侧通孔尚未在代码中实现。 | P1 |

#### 明天攻克计划
1. 步骤3 半圆切除：圆心 (X=-0.045m, Z=0.025m)，用 `CreateCircleByRadius` 替代 `CreateArc`
2. 步骤4 U形槽：确认 `CreateCornerRectangle` 的 X/Y/Z 坐标系映射
3. Φ18 通孔：用 `CreateCircleByRadius` + `FeatureCut4` 实现贯穿切除

---

### 20.8 标准日志重定向模板

```csharp
string logPath = @".\log.txt";
System.IO.StreamWriter swLog = new System.IO.StreamWriter(
    logPath, false, System.Text.Encoding.UTF8);
swLog.AutoFlush = true;
Console.SetOut(swLog);
Console.SetError(swLog);
```

**用途**：将所有 `Console.WriteLine` 输出重定向到 log.txt，方便远程调试
（SW 由 `Activator.CreateInstance` 拉起后，控制台输出不可见）。

---

## 十九、窗口管理规则（CRITICAL - 2026-05-31新增）

### 问题背景
每次运行脚本如果都用 `Dispatch` 新建SW实例，或者运行完不关闭文档，会导致大量SW窗口堆积，占用内存，最终崩溃。

---

### 19.1 连接原则（必须遵守）

```python
# ✅ 正确：复用已有实例
sw = win32com.client.GetActiveObject('SldWorks.Application')
print("✓ 复用已有SW实例")

# ❌ 错误：每次都开新窗口
sw = win32com.client.Dispatch('SldWorks.Application')  # 不要用！
```

---

### 19.2 文档关闭规则

| 场景 | 正确做法 | 错误做法 |
|------|----------|----------|
| 单文档用完 | `sw.CloseDoc(doc.GetTitle)` | 不关闭，让窗口残留 |
| 所有文档用完 | `sw.CloseAllDocuments(True)` | 直接ExitApp |
| 保存后关闭 | `doc.SaveAs3(path, 1, 2)` 再 `CloseDoc` | 不保存直接关 |
| 脚本结束清理 | `sw.CloseAllDocuments(True)` 然后 `sw.ExitApp()` | 只关文档不退出 |

---

### 19.3 标准模板（每次脚本必须带）

```python
class SolidWorksAutomation:
    def __init__(self):
        self.sw = None
        self.doc = None
    
    def connect(self):
        """连接SW（复用已有实例）"""
        try:
            self.sw = win32com.client.GetActiveObject('SldWorks.Application')
            print("✓ 连接到已运行的SW实例")
        except:
            self.sw = win32com.client.Dispatch('SldWorks.Application')
            print("✓ 启动新的SW实例（仅当SW未运行时）")
        self.sw.Visible = True
        self.sw.UserControl = False
        return self.sw
    
    def cleanup(self):
        """清理资源（每次脚本结束必须调用）"""
        if self.sw is not None:
            # 关闭所有文档（True=保存修改）
            self.sw.CloseAllDocuments(True)
            print("✓ 所有文档已关闭")
            # 退出SW
            self.sw.ExitApp()
            self.sw = None
            print("✓ SW已退出")

# 使用方式
sw = SolidWorksAutomation()
try:
    sw.connect()
    # ... 执行建模操作 ...
finally:
    sw.cleanup()  # 必须调用，防止窗口泄漏
```

---

### 19.4 验证窗口数量

```python
def check_sw_windows(sw):
    """检查SW打开的文档数量"""
    docs = sw.GetDocuments  # 属性，不是方法
    if docs is not None:
        # 遍历统计
        count = 0
        for doc in docs:
            if doc is not None:
                count += 1
        print(f"当前打开文档数: {count}")
        return count
    return 0

# 如果文档数 > 3，发出警告
count = check_sw_windows(sw)
if count > 3:
    print(f"⚠ 警告：打开了{count}个文档，建议清理！")
    sw.CloseAllDocuments(True)
```

---

### 19.5 强制清理函数（可直接调用）

```python
def force_close_all_sw_docs():
    """强制关闭所有SW文档（给用户用的急救函数）"""
    import win32com.client
    try:
        sw = win32com.client.GetActiveObject('SldWorks.Application')
        result = sw.CloseAllDocuments(True)
        if result:
            print("✓ 所有SW文档已强制关闭")
        else:
            print("⚠ 部分文档关闭失败（可能有未保存修改）")
    except Exception as e:
        print(f"错误: {e}")

# 用户说"关掉多余窗口"时调用这个函数
```

---

### 19.6 防止窗口泄漏的检查清单

每次写完脚本，检查是否做到以下几点：

- [ ] 用 `GetActiveObject` 而不是 `Dispatch`（除非SW确实没运行）
- [ ] 脚本开头用 `sw.CloseAllDocuments(True)` 清理之前的文档
- [ ] 每个 `NewPart()` / `NewDocument()` 后都有对应的关闭逻辑
- [ ] 脚本用 `try...finally` 保证 `cleanup()` 一定被调用
- [ ] 不在循环里反复调用 `NewPart()` / `Dispatch`
- [ ] 保存文档后再关闭（`SaveAs3` 返回1表示成功）

---

**总结**：SW窗口泄漏是Python自动化最常见问题。每次运行脚本前先清理，运行后必关闭。

---

## 二十、本次踩坑经验（2026-05-31积累）

### 20.1 SW 2024 + Python 3.13 已知问题

| 问题 | 现象 | 解决方案 |
|------|------|----------|
| `GetVersion()` 不可用 | `TypeError: 'str' object is not callable` | 用 `Visible` / `CommandInProgress` 属性验证连接 |
| `NewPart()` 可能失败 | 不报错但文档未创建 | 用 `NewDocument(template_path, 0, 0, 0)` 指定模板 |
| `FeatureCut` 完全不可用 | 返回None或COM错误 | 只做拉伸添加材料，切除手动完成 |
| 嵌套轮廓无法识别 | 拉伸失败："轮廓无效" | 不做嵌套轮廓，复杂孔手动切除 |
| `SelectByID2` 有时失效 | 返回False | 用遍历特征树替代（见18.3节） |

---

### 20.2 属性 vs 方法（本次踩坑记录）

以下API是**属性**，调用时**不要加括号**（）：

```python
# ✅ 正确 - 直接访问属性
title = doc.GetTitle           # 不是 GetTitle()
count = doc.GetFeatureCount   # 不是 GetFeatureCount()
doc_type = doc.GetType        # 不是 GetType()
docs = sw.GetDocuments       # 不是 GetDocuments()
feat = doc.FirstFeature      # 不是 FirstFeature()
next_feat = feat.GetNextFeature  # 不是 GetNextFeature()
rebuild = doc.EditRebuild3  # 不是 EditRebuild3()
sketch = doc.SketchManager.ActiveSketch  # 不是 ActiveSketch()
part_num = doc.GetPartNumber      # 不是 GetPartNumber()
custom_info = doc.GetCustomInfo   # 不是 GetCustomInfo()
```

**记忆口诀**：SW API中，`Get` 开头的**不一定都是方法**，需要查文档确认。

---

### 20.3 验证机制（本次总结）

每个操作后都必须验证，不能假设成功：

```python
# 连接验证（不用GetVersion）
assert sw.Visible is not None, "SW连接失败"

# 文档验证
doc = sw.ActiveDoc
assert doc is not None, "文档创建失败"

# 特征验证：比对数量
before = doc.GetFeatureCount
# ... 执行创建 ...
after = doc.GetFeatureCount
assert after > before, "特征创建失败"

# 草图验证
segs = doc.SketchManager.ActiveSketch.GetSketchSegmentsCount()
assert segs > 0, "草图没有线段"

# 重建验证
assert doc.EditRebuild3 is True, "模型重建失败"
```

---

### 20.4 中文版SW注意事项

```python
# ✅ 中文版基准面名称
plane_names = ["前视基准面", "上视基准面", "右视基准面"]

# ❌ 英文版名称（中文版不可用）
plane_names = ["Front Plane", "Top Plane", "Right Plane"]

# 检测语言版本
try:
    result = doc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, False, 0, None, 0)
    is_chinese = True
except:
    is_chinese = False
```

---

### 20.5 本次叉形接头建模经验

**任务**：自动化建模叉形接头（厚度25mm，左端φ50圆头带φ18孔，右端叉形带双φ18孔）

**成功部分**：
- ✅ 哑铃形轮廓拉伸（左端φ50圆 + 中间25×25矩形 + 右端25×37.5矩形）
- ✅ 使用 `CreateCornerRectangle` + `CreateCircle` 绘制草图
- ✅ `FeatureExtrusion2` 23参数版本可用

**失败部分**：
- ❌ `FeatureCut` 所有版本都返回None（SW 2024 Python COM环境限制）
- ❌ 嵌套轮廓（外轮廓+内孔轮廓）拉伸失败
- ❌ 无法自动化切除操作

**结论**：
> 对于需要切除的零件，当前API环境下只能自动完成**添加材料**部分，切除操作需要手动完成或在skill中给出清晰的手动指导。

---

### 20.6 下次改进方向

1. 研究 `IExtrudeFeatureData` 接口（可能支持切除）
2. 研究 `IBody2` 布尔运算（可能绕过FeatureCut）
3. 测试 `SelectByID2` 选择边线/面的参数格式
4. 建立标准切除特征创建流程

---

**注意**: 
1. SolidWorks版本不同可能导致API行为差异，建议使用2016+版本
2. 所有单位默认为米制(SI)，SolidWorks内部使用米
3. 批量操作前建议先在小范围测试
4. 重要文件操作前做好备份
5. **每次运行脚本前先调用 `force_close_all_sw_docs()` 清理多余窗口**

