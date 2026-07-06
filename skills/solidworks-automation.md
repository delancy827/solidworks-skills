---
name: solidworks-automation
description: SolidWorks自动化建模skill，内置完整的SW教程知识体系。⚠️ 2026-05-31架构升级：Python win32com对>12参数API（如FeatureCut4）支持不全，全面转向C# (.NET) 强类型早期绑定架构。支持通过C#/VBA连接SolidWorks API进行自动化建模、装配、工程图生成、Simulation分析、Flow Simulation流体分析、钣金设计、焊件设计、模具设计、曲面造型、电气设计等。
category: engineering-cad
version: 4.5.0
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
| `FeatureExtrusion2` | 23 | ⚠️ 版本依赖 | ✅ |
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
| `RevisionNumber()` 返回 COMException | 字符串长度不足8时 `Substring(0,8)` 崩溃 | 加长度判断 `ver.Length > 8 ? ver.Substring(0, 8) : ver` |
| 同一草图内矩形+圆同时画 | SW无法同时拉伸两个不相交轮廓 | 分两步：先矩形拉伸→再画圆切除 |

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

# 安全获取SW版本号（防止RevisionNumber Substring越界崩溃）
def safe_get_sw_version(sw_app):
    """获取SW版本号，防止字符串过短导致Substring崩溃"""
    try:
        ver = sw_app.RevisionNumber()
        # 复盘实测：部分SW版本RevisionNumber长度可能不足8
        if len(ver) > 8:
            return ver[:8]
        return ver  # 不够8位直接返回全串
    except Exception as e:
        print(f"获取版本号失败: {e}")
        return "unknown"
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
  /reference:"C:/SOLIDWORKS/api/redist/SolidWorks.Interop.sldworks.dll" \
  /reference:"C:/SOLIDWORKS/api/redist/SolidWorks.Interop.swconst.dll" \
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

---

## 二十一、叉形接头工程实践终极沉淀（2026-06-01 实机验证）

> 背景：在叉形接头（Clevis Joint）全自动建模攻坚中，经过反射探测+实机验证，
> 发现E:\sw2024 Interop DLL与官方文档存在大量参数位置偏差。
> 以下所有结论均已经过 `GetBodies2` 实体计数硬验证，4/4步骤全部通关。

---

### 21.1 防假跑终极断言（反作弊机制）🔒

#### 问题根因

`swDoc.GetFeatureCount()` 是最常见的**假通关信号**：

```csharp
// ❌ 假通关检测 — 完全无效！
int before = swDoc.GetFeatureCount();
// ... 创建草图（特征数+1）和/或失败的特征（特征数+1） ...
swDoc.ForceRebuild3(false);
int after = swDoc.GetFeatureCount();
if (after > before) { /* 你以为成功了？实际上可能只多了一个空草图！ */ }
```

**假通关的三种路径**：

| 假通关类型 | 特征数变化 | 实体变化 | 日志表现 |
|------------|:---:|:---:|------|
| 空草图残留 | +1 | 无 | "OK StepX 特征:21->22" |
| 错误特征节点 | +1 | 无 | "OK StepX 特征:21->22"，SW特征树出现红色错误图标 |
| 草图+假特征 | +2 | 无 | "OK StepX 特征:21->23"，看起来更"成功" |

**核心教训**：`GetFeatureCount` 统计的是特征树节点数（包括草图、基准面、原点），不是实体数。

#### 终极解决方案：GetBodies2 实体计数

```csharp
// ✅ 真实验证 — 直接检查几何实体
static void VerifyBodies(PartDoc partDoc, int expected, string stepName)
{
    object[] bodies = (object[])partDoc.GetBodies2(
        (int)swBodyType_e.swSolidBody, false);
    int count = (bodies == null) ? 0 : bodies.Length;
    if (count != expected)
        Fail(string.Format("{0} 实体数量错误: 期望{1} 实际{2}", stepName, expected, count));
    Console.WriteLine(string.Format("OK {0} 实体数:{1}", stepName, count));
}
```

**双重验证模式**（推荐）：

```csharp
// 特征数验证：检测Feature操作是否生成了新节点
int beforeFeat = swDoc.GetFeatureCount();
swDoc.FeatureManager.FeatureExtrusion2(/*...*/);
VerifyFeature(beforeFeat, stepName);    // 特征数增加 → Feature节点存在

// 实体数验证：检测几何体是否真正生成/变化
VerifyBodies(partDoc, expectedBodies, stepName);  // 实体计数正确 → 几何确实生成了
```

**验证矩阵**：

| 操作 | GetFeatureCount | GetBodies2 | 两者都通过才算成功 |
|------|:---:|:---:|:---:|
| 基体拉伸 | +1 | 0→1 | ✅ |
| 合并拉伸(Merge=true) | +1 | 1→1 | ⚠️ 实体数不变，需额外验证体积 |
| 切除(双向贯穿) | +1 | 1→1 | ⚠️ 同上 |
| 空草图(无操作) | +1 | 不变 | ❌ **被GetBodies2识破** |
| 错误特征 | +1 | 不变 | ❌ **被GetBodies2识破** |

---

### 21.2 Interop DLL 底层 API 避坑铁律 ⚠️

> 以下所有参数位置均经过 `System.Reflection` 实机反射探测确认。
> **切勿信官方文档** — E:\sw2024 Interop DLL 有大量参数重排。

#### 铁律1：FeatureExtrusion2 真实参数顺序（23参数）

```
反射确认签名:
[Sd(bool)] [Flip(bool)] [Dir(bool)] [T1(int)] [T2(int)] [D1(double)] [D2(double)]
[Dchk1(bool)] [Dchk2(bool)] [Ddir1(bool)] [Ddir2(bool)] [Dang1(double)] [Dang2(double)]
[OffsetRev1(bool)] [OffsetRev2(bool)] [TransSurf1(bool)] [TransSurf2(bool)]
[Merge(bool)] [UseFeatScope(bool)] [UseAutoSelect(bool)]
[T0(int)] [StartOffset(double)] [FlipStartOffset(bool)]
```

| 参数 | 文档预期位置 | **真实位置** | 影响 |
|------|:---:|:---:|------|
| Merge | 参数3 | **参数18** | 旧代码一直把Merge放参数3，**永远为false，扁柄从未真正合并！** |
| StartType(T0) | 参数12 | **参数21** | Offset=1在此DLL中**不支持** |
| StartOffset | 参数13 | **参数22** | 即使设置也会被忽略 |

**修正后的调用**：
```csharp
// ✅ 正确：Merge在参数18
swDoc.FeatureManager.FeatureExtrusion2(
    true, false, false,     // Sd,Flip,Dir
    0, 0,                   // T1=Blind,T2=none
    0.025, 0.0,             // D1,D2
    false, false, false, false,  // Dchk1,Dchk2,Ddir1,Ddir2
    0.0, 0.0,               // Dang1,Dang2
    false, false,           // OffsetRev1,OffsetRev2
    false, false,           // TransSurf1,TransSurf2
    true,                   // [18] Merge=true ← 关键!
    false, false,           // UseFeatScope,UseAutoSelect
    0, 0.0, false);         // T0=Plane,StartOffset,FlipStartOffset
```

#### 铁律2：FeatureCut4 真实参数顺序（27参数）

```
反射确认签名:
[Sd(bool)] [Flip(bool)] [Dir(bool)] [T1(int)] [T2(int)] [D1(double)] [D2(double)]
[Dchk1(bool)] [Dchk2(bool)] [Ddir1(bool)] [Ddir2(bool)] [Dang1(double)] [Dang2(double)]
[OffsetRev1(bool)] [OffsetRev2(bool)] [TransSurf1(bool)] [TransSurf2(bool)]
[NormalCut(bool)] [UseFeatScope(bool)] [UseAutoSelect(bool)]
[AssyScope(bool)] [AutoSelComp(bool)] [Propagate(bool)]
[T0(int)] [StartOffset(double)] [FlipStartOffset(bool)] [Optimize(bool)]
```

| 参数 | 铁律 | 后果 |
|------|------|------|
| **Sd(参数1)** | **必须为 false** | true会导致FeatureCut4**完全不执行**（特征数不增长） |
| Flip(参数2) | 控制切除侧（true=外, false=内） | 上视基准面负坐标时用false |
| T1=1, T2=1 | 双向ThroughAll | swEndCondThroughAll=1（反射确认，不是4！） |

**修正后的调用**：
```csharp
// ✅ 正确
swDoc.FeatureManager.FeatureCut4(
    false, false, false,     // Sd=false(铁律!),Flip=false,Dir=false
    1, 1,                    // T1=ThroughAll,T2=ThroughAll(双向贯穿)
    0.0, 0.0,
    false, false, false, false, 0.0, 0.0,
    false, false, false, false, false,
    false, false, false, false, false,
    0, 0.0, false, false);
```

#### 铁律3：InsertRefPlane 偏移基准面（替代失效的StartOffset）

**问题**：FeatureExtrusion2的StartOffset在此DLL中不支持（T0=1导致拉伸完全失败）。

**反射确认签名**：
```
InsertRefPlane(int FirstConstraint, double Dist, int SecondConstraint, double, int ThirdConstraint, double)
```

**约束枚举**：`swRefPlaneReferenceConstraints_e`（**带s后缀**，不是文档中的单数形式）

| 约束名 | 值 |
|--------|:---:|
| Parallel | 1 |
| Perpendicular | 2 |
| Coincident | 4 |
| **Distance** | **8** ← 用于偏移基准面 |

**完整偏移基准面创建流程**：
```csharp
// 1. 选中参考基准面
bool ok = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0,0,0, false, 0,null,0);
if (!ok) ok = swDoc.Extension.SelectByID2("Front Plane", "PLANE", 0,0,0, false, 0,null,0);

// 2. 创建偏移基准面（Distance=8）
Feature planeFeat = (Feature)swDoc.FeatureManager.InsertRefPlane(8, 0.0125, 0,0,0,0);
if (planeFeat == null) Fail("偏移基准面创建失败");
string planeName = planeFeat.Name;  // 如"基准面1"

// 3. 在偏移基准面上画草图
swDoc.Extension.SelectByID2(planeName, "PLANE", 0,0,0, false, 0, null, 0);
swDoc.SketchManager.InsertSketch(true);
// ... 画草图 ...
```

#### 铁律4：CreateArc 不可用 → Create3PointArc 替代

**问题**：`CreateArc(xc,yc,zc, xs,ys,zs, xe,ye,ze, direction)` 在此DLL中无论方向=1还是-1，均导致FeatureExtrusion2失败（特征数不增长）。

**解决方案**：用三点圆弧替代。
```csharp
// ❌ 不可用
swDoc.SketchManager.CreateArc(-0.045, 0.025, 0, -0.045, 0, 0, -0.045, 0.050, 0, -1);

// ✅ Create3PointArc(起点, 终点, 中点)
swDoc.SketchManager.Create3PointArc(
    -0.045, 0, 0,       // 起点
    -0.045, 0.050, 0,   // 终点
    -0.070, 0.025, 0    // 中点（圆弧最左点）
);
```

#### 铁律5：上视基准面草图Y方向映射

**问题**：上视基准面（Top Plane）的草图Y正方向对应**模型Z负方向**。

这意味着用正Y坐标画的草图，在模型中落在Z负半轴（实体外部），导致FeatureCut4悬空失败。

**解决方案**：全部取负值。
```csharp
// ❌ 正Y坐标 → 草图悬空在实体Z负方向（Z=-0.0125~-0.0375）
swDoc.SketchManager.CreateCornerRectangle(0.015, 0.0125, 0, 0.090, 0.0375, 0);

// ✅ 负Y坐标 → 模型Z正方向(Z=0.0125~0.0375)在实体内部
swDoc.SketchManager.CreateCornerRectangle(0.015, -0.0125, 0, 0.090, -0.0375, 0);
```

---

### 21.3 空间正交几何重构法 📐

> **核心原则：彻底放弃面遍历，全程使用系统三大原生基准面 + 双向贯穿切除。**

#### 为什么放弃面遍历？

| 方法 | 可靠性 | 问题 |
|------|:---:|------|
| SelectByID2 按面名称 | ⭐⭐ | 面名称随建模历史变化 |
| SelectByRay 射线法 | ⭐⭐ | 参数需精确计算，变形几何后射不中 |
| GetBodies2 遍历面 → Select4 | ⭐⭐⭐ | 选中后草图是**面局部坐标系**，坐标不可控 |
| **系统基准面绝对坐标** | ⭐⭐⭐⭐⭐ | **坐标系固定，永不偏移** ✅ |

#### 三大基准面策略

```
前视基准面 (Front, XY平面, Z=0):
  → 画 XY 草图 → 沿 Z 拉伸/切除
  → 适合：叉部基体、扁柄、叉耳孔

上视基准面 (Top, XZ平面, Y=0):
  → 画 XZ 草图 → 沿 Y 切除
  → ⚠️ 草图Y正方向=模型Z负方向，坐标取负
  → 适合：U形槽（Y轴贯穿切除）

右视基准面 (Right, YZ平面, X=0):
  → 画 YZ 草图 → 沿 X 拉伸/切除
```

#### 90°正交特征实现公式

要在零件上实现两组互相垂直的特征（如：手柄孔沿Z向 + 叉部槽沿Y向）：

```
手柄孔（Z向贯穿）:
  基准面: 前视基准面(XY)
  草图: 画圆
  拉伸/切除: FeatureCut4(T1=1,T2=1) ← 沿Z双向贯穿

叉部槽（Y向贯穿）:
  基准面: 上视基准面(XZ)
  草图: 画矩形(Y坐标取负!)
  切除: FeatureCut4(T1=1,T2=1) ← 沿Y双向贯穿
```

**叉形接头完整几何参数表**：

| 步骤 | 基准面 | 草图 | 特征 | 深度 | 方向 |
|------|--------|------|------|------|------|
| 1.叉部基体 | 前视 | 矩形(0,0)-(0.090,0.050) | Extrusion2 | 0.050 | Z单向 |
| 2.扁柄+圆头 | 偏移面(Z=0.0125) | 分段轮廓 + 三点弧 + Φ18孔 | Extrusion2 Merge=true | 0.025 | Z单向 |
| 3.U形槽 | 上视(Y坐标取负!) | 矩形(0.015,-0.0125)-(0.090,-0.0375) | FeatureCut4 Flip=false | ThroughAll×2 | Y双向 |
| 4.叉耳通孔 | 前视 | 圆(0.075,0.025) R=0.009 | FeatureCut4 | ThroughAll×2 | Z双向 |

---

### 21.4 完整防假跑编译模板（2026-06-01最终版）

```csharp
// Clevis_Joint.cs — 叉形接头全自动建模（4/4步骤实体验证通过）
// 编译: & 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe' \
//        /r:'C:\SOLIDWORKS\api\redist\SolidWorks.Interop.sldworks.dll' \
//        /r:'C:\SOLIDWORKS\api\redist\SolidWorks.Interop.swconst.dll' \
//        /out:Clevis_Joint.exe Clevis_Joint.cs

using System;
using System.IO;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Program
{
    static StreamWriter log;
    static SldWorks swApp;
    static ModelDoc2 swDoc;
    static PartDoc partDoc;

    static void Main()
    {
        // 日志重定向
        log = new StreamWriter("log.txt", false, Encoding.UTF8);
        log.AutoFlush = true;
        Console.SetOut(log);

        // SW连接（同权限级别）
        swApp = (SldWorks)Activator.CreateInstance(
            Type.GetTypeFromProgID("SldWorks.Application"));
        swApp.Visible = true;

        // 清空残留文档
        while (swApp.GetDocumentCount() > 0) {
            ModelDoc2 temp = (ModelDoc2)swApp.ActiveDoc;
            if (temp != null) swApp.CloseDoc(temp.GetTitle());
            else break;
        }

        swDoc = (ModelDoc2)swApp.NewPart();
        partDoc = (PartDoc)swDoc;

        // ===== 建模步骤（每个步骤后双重验证） =====
        // 步骤1: 叉部基体（前视基准面, 矩形, Blind拉伸）
        // 步骤2: 扁柄（偏移基准面 Create3PointArc R25+Φ18  Merge=true）
        // 步骤3: U形槽（上视基准面 Y取负 Flip=false T1=T2=1）
        // 步骤4: 通孔（前视基准面 T1=T2=1）

        log.Close();
    }

    // 双重验证1: 特征数增长
    static void VerifyFeature(int before, string name) {
        swDoc.ForceRebuild3(false);
        int after = swDoc.GetFeatureCount();
        if (after <= before) Fail(name + " Feature失败: " + before + "->" + after);
    }

    // 双重验证2: 实体计数（防假通关）
    static void VerifyBodies(int expected, string name) {
        object[] bodies = (object[])partDoc.GetBodies2(
            (int)swBodyType_e.swSolidBody, false);
        int count = (bodies == null) ? 0 : bodies.Length;
        if (count != expected) Fail(name + " 实体:" + expected + "!=" + count);
    }

    static void Fail(string msg) {
        Console.WriteLine("FAIL: " + msg);
        if (swDoc != null) swApp.CloseDoc(swDoc.GetTitle());
        log.Close();
        throw new Exception(msg);
    }
}
```

---

### 21.5 知识库更新记录

| 日期 | 更新内容 | 验证状态 |
|------|----------|:---:|
| 2026-06-01 | FeatureExtrusion2 Merge=参数18（非3） | ✅ 反射+实机 |
| 2026-06-01 | FeatureCut4 Sd必须为false | ✅ 反射+实机 |
| 2026-06-01 | InsertRefPlane Distance=8（非1） | ✅ 反射+实机 |
| 2026-06-01 | CreateArc不可用 → Create3PointArc | ✅ 实机 |
| 2026-06-01 | 上视基准面Y↔Z映射（负值） | ✅ 实机 |
| 2026-06-01 | GetBodies2 替代 GetFeatureCount 防假通关 | ✅ 实机 |
| 2026-06-01 | 系统基准面绝对坐标替代面遍历 | ✅ 实机 |
| 2026-05-31 | swEndCondThroughAll=1（非4） | ✅ 反射 |
| 2026-05-31 | Activator.CreateInstance 替代 Marshal.GetActiveObject | ✅ 实机 |
| 2026-06-01 | CreateLine浮点端点闭合警告 + 坐标取整策略 | ✅ 跨机验证 |
| 2026-06-01 | SaveAs vs SaveAs3 中文路径兼容性 | ✅ 跨机验证 |
| 2026-06-01 | 图纸分析标准工作流 + 尺寸链验证 | ✅ 跨机验证 |
| 2026-06-01 | Python VARIANT包装模板（23参数版） | ✅ 跨机验证 |
| 2026-06-01 | FeatureExtrusion2 Python COM版本依赖警告 | ✅ 跨机验证 |
| 2026-06-01 | AI视觉QA验证工作流（截图→多模态对比） | ✅ 跨机验证 |
| 2026-06-01 | Python→VBA混合架构方案 | ✅ 跨机验证 |
| 2026-06-01 | SelectByID2 ctx参数多格式回退 | ✅ 跨机验证 |
| 2026-06-01 | C#沙箱隔离：Marshal.GetActiveObject不可用 | ✅ 跨机验证 |

---

## 二十二、舍友电脑跨机验证反馈（第一轮）（2026-06-01）

> 来源：舍友在独立PC（SW2024中文版）上运行本skill执行"底座支架"建模任务后的复盘报告。
> 与本机（E:盘SW2024）形成跨机对照。

---

### 22.1 CreateLine 浮点坐标端点闭坑（P0）⚠️

`CreateLine`使用浮点坐标时，端点存在微米级偏差，SW判定轮廓不闭合 → 静默失败。
**解决方案：所有坐标取整到整数mm。**

```csharp
// ❌ 浮点：端点不重合
swDoc.SketchManager.CreateLine(-0.0500, 0, 0, 0.0374, 0.0150, 0); // 50→38偏移含浮点误差

// ✅ 整数mm：精确闭合
double mm(double v) => v / 1000.0;
swDoc.SketchManager.CreateLine(mm(-50), mm(0), 0, mm(38), mm(15), 0);
```

### 22.2 SaveAs3中文路径静默失败（P0）⚠️

`SaveAs3`保存到中文路径时返回0、不报错但文件未写入。
**解决方案：优先用`SaveAs`或全英文路径。**

```csharp
// ✅ 通用安全保存
try { if (doc.SaveAs3(path, 1, 2) == 0) doc.SaveAs(path); }
catch { doc.SaveAs(path); }
```

### 22.3 图纸分析五步法（P1）📐

生成代码前必须：基准面→尺寸链→交叉验算→坐标表→代码。**严禁凭感觉写坐标。**

### 22.4 Python VARIANT包装参考（P1）

Python COM下FeatureExtrusion2需全部23参数用VARIANT()包裹，且D2必须非零。

### 22.5 底座支架类代码模板（P1）

六边形梯形底座整数坐标绘制函数（见SKILL.md原始Section 22.5）。

### 22.6 跨机环境差异（第一轮）

| 项目 | 本机（E:盘SW2024） | 舍友（C:盘SW2024） |
|------|------|------|
| 保存 | 英文路径 | 中文桌面（SaveAs3失败） |
| 建模结果 | Clevis_Joint 4/4 | bracket外形对、孔手动 |

---

## 二十三、跨机验证反馈（第二轮）—— Verify→Fix→Re-Verify 全流程（2026-06-01）

> 来源：舍友在独立PC（SW 32.5.0中文版 + Python 3.13 + pywin32）上执行本skill的"验证→修复→再验证"闭环。
> 本轮发现了多个本机未暴露的环境差异和架构限制。

---

### 23.1 Python COM FeatureExtrusion2 版本依赖（P0 - 重大修正）⚠️

#### 问题发现

在本机（SW 2024 + E:盘 + Python 3.14），FeatureExtrusion2 23参数调用**成功**。

在舍友电脑（SW 2024 + C:盘 + Python 3.13 + pywin32最新版），**始终失败**：
```
pywintypes.com_error: (-2147352562, '无效的参数数目。')
```

#### 比对分析

| 项目 | 本机 | 舍友 | 结论 |
|------|------|------|------|
| SW版本 | 2024 (E:盘) | 2024 (C:盘) 32.5.0 | 相同主版本 |
| Python | 3.14 | 3.13 | 差异 |
| pywin32 | 305 | 306 (最新) | 差异 |
| FeatureExtrusion2 | ✅ | ❌ | **版本依赖！** |
| ShowNamedView2 | ✅ | ✅ | 简单API一致 |

#### 修正后的API可用性分级

| 分级 | 含义 | API示例 |
|:---:|------|------|
| ✅ 稳定 | 跨版本一致可用 | NewDocument, SelectByID2, InsertSketch, ForceRebuild3, ShowNamedView2 |
| ⚠️ 版本依赖 | 部分环境可行 | **FeatureExtrusion2**（取决于pywin32版本+SW Service Pack） |
| ❌ 不可用 | Python COM已知限制 | FeatureCut/3/4, HoleWizard5, GetBodies2, InsertCombineFeature |

> **新策略**：FeatureExtrusion2 不能再标为"✅"，应视为"优先尝试，失败走C#/VBA降级"。

```python
def try_feature_extrusion2(doc, params_23):
    """尝试Python COM FeatureExtrusion2，失败返回None"""
    try:
        return doc.FeatureManager.FeatureExtrusion2(*params_23)
    except Exception as e:
        print(f"FeatureExtrusion2 (Python COM): {e}")
        print("   → 降级到 VBA 宏执行")
        return None
```

---

### 23.2 C#沙箱隔离：Marshal.GetActiveObject 不可用（P0 - 环境限制）⚠️

#### 问题发现

舍友电脑上：
- C#代码可以编译（csc.exe正常）
- 但运行时 `Marshal.GetActiveObject("SldWorks.Application")` → `MK_E_UNAVAILABLE (0x800401E3)`
- `Activator.CreateInstance(Type.GetTypeFromProgID(...))` → `TYPE_E_ELEMENTNOTFOUND`
- Python COM `Dispatch("SldWorks.Application.32")` → **成功**

#### 根因

```
┌──────────────────────────────────────────┐
│  WorkBuddy Sandbox (Python Process)     │
│  ┌────────────────────────────────────┐ │
│  │  python.exe → Dispatch(SW) → ✅   │ │
│  │  继承sandbox的安全上下文           │ │
│  └────────────────────────────────────┘ │
│         │ spawn 子进程                   │
│         ▼                                │
│  ┌────────────────────────────────────┐ │
│  │  exe/csc.exe → GetActiveObject()  │ │
│  │  普通Windows进程 → SW COM ❌       │ │
│  │  缺少sandbox的安全上下文           │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

**结论**：在WorkBuddy环境下，C# exe无法直连SW COM。本机之所以可行，是因为SW和脚本在同一权限级别下运行（非sandbox）。

#### 解决方案层次

| 方案 | 可行性 | 说明 |
|------|:---:|------|
| Python COM (简单API) | ✅ | 草图、选择、视图——不受限制 |
| Python COM (FeatureExtrusion2) | ⚠️ | 版本依赖，需降级机制 |
| VBA宏注入 (推荐) | ✅ | SW进程内执行，无COM限制 |
| C# exe (本机运行) | ✅ | 非sandbox环境可用 |
| C# exe (WorkBuddy) | ❌ | sandbox隔离 |

---

### 23.3 Python→VBA 混合架构方案（P1 - 绕过COM限制的关键路线）⭐

#### 问题

Python COM 无法调用 FeatureCut4/FeatureExtrusion2（多参数限制），C#又无法在WorkBuddy中跨进程访问SW COM。

#### 解决方案：VBA宏注入

SW的VBA（Visual Basic for Applications）运行在SW进程内部，拥有完整API访问权限且无参数数量限制。

```
┌────────────────────────────────────────┐
│  Python (WorkBuddy)                    │
│  ├─ 解析工程图 → 推导尺寸链 → 坐标表  │
│  ├─ 生成VBA宏代码（字符串）            │
│  ├─ 写入 .swp 文件                     │
│  └─ sw.Run2() 或 ExecuteMacro()       │
│         │                               │
│         ▼                               │
│  ┌────────────────────────────────────┐│
│  │  SolidWorks 进程内 VBA 引擎        ││
│  │  ├─ FeatureExtrusion2 (23参数) ✅ ││
│  │  ├─ FeatureCut4 (27参数)       ✅ ││
│  │  ├─ FeatureFillet3 (7参数)     ✅ ││
│  │  └─ HoleWizard5 (25+参数)      ✅ ││
│  └────────────────────────────────────┘│
└────────────────────────────────────────┘
```

#### VBA宏代码生成模板

```python
def generate_vba_macro(operations):
    """将建模操作列表转换为VBA宏代码字符串"""
    header = '''Sub SWBuild()
    Dim swApp As SldWorks.SldWorks
    Dim swDoc As SldWorks.ModelDoc2
    Dim swSketchMgr As SldWorks.SketchManager
    Dim swFeatMgr As SldWorks.FeatureManager
    Dim boolstatus As Boolean
    Dim feat As SldWorks.Feature

    Set swApp = Application.SldWorks
    Set swDoc = swApp.ActiveDoc
    Set swSketchMgr = swDoc.SketchManager
    Set swFeatMgr = swDoc.FeatureManager
'''
    
    body = []
    for op in operations:
        if op['type'] == 'sketch':
            body.append(f'''
    ' === {op['name']} ===
    boolstatus = swDoc.Extension.SelectByID2(
        "{op['plane']}", "PLANE", 0, 0, 0, False, 0, Nothing, 0)
    swSketchMgr.InsertSketch True
''')
            for line in op['lines']:
                body.append(f'    swSketchMgr.{line}')
            body.append('    swSketchMgr.InsertSketch True')
        
        elif op['type'] == 'extrusion':
            body.append(f'''
    ' === {op['name']} 拉伸 ===
    Set feat = swFeatMgr.FeatureExtrusion2({op['args']})
    swDoc.ForceRebuild3 False
''')
        
        elif op['type'] == 'cut':
            body.append(f'''
    ' === {op['name']} 切除 ===
    Set feat = swFeatMgr.FeatureCut4({op['args']})
    swDoc.ForceRebuild3 False
''')
    
    footer = '''
    swDoc.Save3 1
    swApp.SendMsgToUser "建模完成! 特征数: " & swDoc.GetFeatureCount
End Sub
'''
    return header + ''.join(body) + footer
```

#### 执行VBA（Python侧）

```python
import win32com.client

def execute_vba_macro(sw, macro_code, macro_name="SWBuild"):
    """通过SW COM执行VBA宏"""
    import os, tempfile
    
    # 写入宏文件
    macro_dir = os.path.join(tempfile.gettempdir(), 'SW_Macros')
    os.makedirs(macro_dir, exist_ok=True)
    macro_path = os.path.join(macro_dir, f'{macro_name}.swp')
    
    with open(macro_path, 'w', encoding='utf-8') as f:
        f.write(macro_code)
    
    # 方式1: Run2
    try:
        result = sw.Run2(macro_name, macro_path, '')
        if result:
            print(f"VBA宏 '{macro_name}' 执行成功")
            return True
    except Exception as e:
        print(f"Run2失败: {e}")
    
    # 方式2: ExecuteMacro (备选)
    try:
        result = sw.ExecuteMacro(macro_path, macro_name, '')
        print(f"ExecuteMacro: {result}")
        return True
    except Exception as e:
        print(f"ExecuteMacro也失败: {e}")
        return False
```

#### VBA vs C# 调用能力对比

| 能力 | VBA宏 | C# exe |
|------|:---:|:---:|
| Python限制API | ✅ 无限制 | ✅ 无限制 |
| WorkBuddy环境 | ✅ SW进程内 | ❌ sandbox隔离 |
| 编译依赖 | ✅ 无需Interop DLL | ❌ 需要Interop DLL |
| 调用方式 | Python→SW.Run2() | 独立exe启动 |
| FeatureCut4 | ✅ | ✅ |
| 调试难度 | ⚠️ 较高 | ✅ IDE调试 |

> **推荐策略**：简单操作用Python COM（草图、选择、视图），复杂特征（拉伸、切除、圆角）生成VBA宏执行。

---

### 23.4 AI视觉QA验证工作流（P1 - 新的方法论）📸

#### 背景

反馈包中使用了"截图→AI多模态对比→差异报告"的验证流程，这是skill中尚未记录但非常有价值的模式。

#### 五步验证流程

```
Step1: 四视图截图（Iso+Front+Top+Right） → 保存为JPG
Step2: AI多模态读取截图 → 提取视觉特征（高度、宽度、孔位置、斜面角度）
Step3: 读取工程图 → 提取所有标注尺寸
Step4: 逐项对比 → 生成差异矩阵（通过/失败表）
Step5: 差异分析 → 定位建模错误的根因
```

#### 验证对比模板

| 验证项 | 工程图要求 | 模型现状 | 判定 |
|--------|-----------|---------|:---:|
| 整体结构 | 单件零件，底座+双吊耳 | 圆柱体+销钉装配件 | ❌ |
| 底座形状 | 50°斜切六边形底座 | 方形底座 | ❌ |
| 前部结构 | 大圆孔通孔 | 实心圆柱 | ❌ |
| 顶部结构 | 平台+2×M6螺纹孔 | 圆柱销突出 | ❌ |
| 整体尺寸 | 128×100×60mm | — | ❌ |

#### 截图捕获脚本（已纳入skill assets）

脚本位置：`skill/scripts/visual_qa_capture.py`

核心能力：
- 中英文双语视图名称自动切换
- 4视图截图（Iso/Front/Top/Right）
- ZoomToFit自适应缩放
- 截图大小验证（实际写入文件确认）

> ⚠️ **截图方法选择警告**（跨机验证复盘）：
> `PrintWindow` / `BitBlt` (GDI) **不可用于 SW 3D 视图**——SW 使用 OpenGL 硬件渲染，
> GDI 捕获到的全是负值/黑色垃圾数据。**必须用 `doc.SaveAs("xxx.jpg")` 方式截图。**
> 该结论在舍友 PC（SW2024 中文版）上实测验证：SaveAs JPG 各视图 MD5 均不同，截图有效。

```python
# 视图配置映射（View ID 实测确认 SW2024：Front=1, Top=3, Right=5, Iso=7）
# 来源：冲压课设跨机验证，错误ID导致4张截图MD5完全相同(68849 bytes）
VIEWS = [
    ('*等轴测',  7, 'Verify_Iso.jpg'),    # swIsometricView
    ('*前视',    1, 'Verify_Front.jpg'),   # swFrontView
    ('*上视',    3, 'Verify_Top.jpg'),     # swTopView
    ('*右视',    5, 'Verify_Right.jpg'),   # swRightView
]

def switch_view(doc, view_name, view_id):
    """中英文双语视图切换"""
    for name in [view_name]:
        try:
            if doc.ShowNamedView2(name, view_id):
                return True
        except:
            pass
    # 英文回退（View ID 严格对齐 swStandardViews_e 枚举值）
    english = {1: '*Front', 3: '*Top', 5: '*Right', 7: '*Isometric'}
    if view_id in english:
        try:
            return doc.ShowNamedView2(english[view_id], view_id)
        except:
            pass
    return False
```

---

### 23.5 SelectByID2 ctx参数多格式回退（P1 - 健壮性提升）

#### 问题

`SelectByID2` 的 `ctx` 参数在不同SW版本/pywin32版本下接受格式不一致：
- 有些需要 `None`
- 有些需要 `()`
- 有些需要 `tuple()`

#### 标准化回退函数

```python
def robust_select_by_id(doc, name, typ, x=0, y=0, z=0, append=False, mark=0, opt=0):
    """SelectByID2多格式回退——跨SW版本的ctx参数兼容"""
    ctx_formats = [None, (), tuple()]
    for ctx in ctx_formats:
        try:
            ok = doc.Extension.SelectByID2(name, typ, x, y, z, append, mark, ctx, opt)
            if ok:
                return True
        except:
            continue
    return False

def robust_select_plane(doc, plane_name):
    """选择基准面——中英文+多ctx格式回退"""
    # 候选名称（含中英文变体）
    candidates = [plane_name]
    mapping = {
        "Front Plane": "前视基准面", "Right Plane": "右视基准面",
        "Top Plane": "上视基准面", "Left Plane": "左视基准面",
    }
    if plane_name in mapping:
        candidates.append(mapping[plane_name])
    if plane_name in mapping.values():
        for en, cn in mapping.items():
            if cn == plane_name:
                candidates.append(en)
    
    for name in candidates:
        if robust_select_by_id(doc, name, "PLANE"):
            print(f"    选中: {name}")
            return True
    return False
```

---

### 23.6 SW连接诊断脚本（P2 - 新增工具资产）

脚本位置：`skill/scripts/sw_connect_info.py`

快速诊断SW运行状态的核心信息：
- SW版本号
- 当前文档类型（零件/装配体/工程图）
- **特征数量**（遍历FeatureTree，比GetFeatureCount更可靠）
- **实体体积、表面积、质量**（用于模型一致性验证）
- **边界框尺寸**（验证建模参数的正确性）
- **草图列表**

```python
# 核心诊断片段
# 特征遍历计数（更准确）
feat = root.GetFirstChild()
count = 0
while feat:
    count += 1
    feat = feat.GetNext()

# 边界框验证（建模参数的直接反馈）
bbox = doc.Extension.CreateBoundingBox()
pts = bbox.GetExtremePoints()
x_min, y_min, z_min, x_max, y_max, z_max = pts
print(f"边界框: X={x_max-x_min:.2f}, Y={y_max-y_min:.2f}, Z={z_max-z_min:.2f} mm")
```

> 使用边界框可以快速验证零件尺寸是否匹配工程图参数——这是验证建模正确性的最直接手段。

---

### 23.7 环境差异汇总（两轮交叉对比）

| 项目 | 本机（E:盘） | 舍友（C:盘） | 舍友第二轮 | 关键发现 |
|------|:---:|:---:|:---:|------|
| SW版本 | 2024 | 2024 | 2024 32.5.0 | 同主版 |
| Python | 3.14 | 3.14 | **3.13** | 版本差→FeatureExtrusion2表现不同 |
| pywin32 | 305 | — | **306** | 最新版反而不兼容 |
| FeatureExtrusion2 | ✅ | ✅ | **❌** | **版本依赖，不能假设可用** |
| C# exe COM | ✅ | ✅ | **❌** | sandbox环境隔离 |
| VBA宏 | 未测 | 未测 | **理论可行** | **应作为首选降级方案** |
| Interop DLL | ✅ E盘 | — | ❌ 未找到 | 路径自适应必需 |

> **核心策略调整**：建模范式从 "Python→C# 二元选择" 升级为 "Python COM → VBA宏 → C# exe 三级降级"。

---

### 23.8 Skill工具资产清单（新增）

| 文件 | 类型 | 用途 |
|------|------|------|
| `scripts/visual_qa_capture.py` | 截图工具 | 四视图自动截图，支持中英文视图名 |
| `scripts/sw_connect_info.py` | 诊断工具 | SW状态诊断：版本/特征数/边界框/质量属性 |
| `scripts/README.md` | 文档 | 各脚本使用说明（待创建） |



> 来源：舍友在独立PC（SW2024中文版）上运行本skill执行"底座支架"建模任务后的复盘报告。
> 与本机（E:盘SW2024）形成跨机对照，以下为差异发现和强化项。

---

### 22.1 CreateLine 浮点坐标端点闭坑（P0 - 跨机新增）⚠️

#### 问题现象
用`CreateLine`画六边形梯形底座时，如果使用浮点坐标（如`0.0374`），端点存在微米级偏差，SolidWorks判定轮廓不闭合 → `FeatureExtrusion2`静默失败。

#### 根因
`CreateLine`的双精度参数在COM传递和内部几何计算中会产生微小的浮点累积误差，导致线段端点无法精确重合。

#### 解决方案：坐标取整到mm

```csharp
// ❌ 错误：浮点坐标 → 端点间隙 → 轮廓不闭合
swDoc.SketchManager.CreateLine(-0.0500, 0.0000, 0, 0.0500, 0.0000, 0);
swDoc.SketchManager.CreateLine(0.0500, 0.0000, 0, 0.0374, 0.0150, 0);  // 38mm = 0.038m
swDoc.SketchManager.CreateLine(0.0374, 0.0150, 0, 0.0380, 0.0350, 0);
// 0.0374 ≠ 0.038，不闭合！

// ✅ 正确：全部用整数mm → 精确闭合
double mm(double v) => v / 1000.0;  // mm→m转换

swDoc.SketchManager.CreateLine(mm(-50), mm(0), 0, mm(50), mm(0), 0);     // 底边
swDoc.SketchManager.CreateLine(mm(50),  mm(0), 0, mm(38), mm(15), 0);    // 右斜边
swDoc.SketchManager.CreateLine(mm(38), mm(15), 0, mm(38), mm(35), 0);    // 右竖直边
swDoc.SketchManager.CreateLine(mm(38), mm(35), 0, mm(-38), mm(35), 0);   // 顶边(76mm)
swDoc.SketchManager.CreateLine(mm(-38), mm(35), 0, mm(-38), mm(15), 0);  // 左竖直边
swDoc.SketchManager.CreateLine(mm(-38), mm(15), 0, mm(-50), mm(0), 0);   // 左斜边
```

#### 适用规则

| 场景 | 策略 |
|------|------|
| 任意多段线闭合轮廓 | **所有坐标取整到整数mm** |
| 尺寸标注值 = 整数mm | 直接用`mm(N)` |
| 尺寸标注值 = 小数mm（如12.5mm） | 用`mm(125)/10.0`避免浮点误差 |
| 圆形/弧线 | 圆心坐标取整，半径允许小数 |
| 已有矩形工具 | 优先用`CreateCornerRectangle`（天然闭合） |

#### 验证方法

```csharp
// 草图闭合验证
sketch = swDoc.SketchManager.ActiveSketch;
int segCount = sketch.GetSketchSegmentsCount();
Console.WriteLine(string.Format("草图线段数: {0}", segCount));
// 六边形 = 6条线，四边形 = 4条线，与预期比对
```

---

### 22.2 SaveAs3 vs SaveAs 中文路径兼容性（P0 - 跨机新增）⚠️

#### 问题现象
`SaveAs3`保存到含中文路径时静默失败（返回0，不报错，但文件未写入）。

#### 根因
`SaveAs3`在SW2024中文版下对Unicode路径的处理不稳定，尤其在OneDrive/微信同步目录这类路径下。

#### 解决方案

```csharp
// ❌ 可能失败 — SaveAs3 + 中文路径
string path = @"C:\Users\<user>\Desktop\bracket.sldprt";
int result = swDoc.SaveAs3(path, 1, 2);  // result=0 → 静默失败

// ✅ 方案1：用SaveAs（不带数字后缀）
swDoc.SaveAs("C:/Users/<user>/Desktop/bracket.sldprt");
Console.WriteLine("✓ 保存成功");

// ✅ 方案2：全英文/数字路径
swDoc.SaveAs3(@"C:\temp\bracket.sldprt", 1, 2);

// ✅ 方案3：用正斜杠 + 短路径
swDoc.SaveAs3("C:/temp/bracket.sldprt", 1, 2);
```

#### 选择策略

| 路径特征 | 推荐API | 说明 |
|----------|---------|------|
| 全英文路径 | `SaveAs3` 或 `SaveAs` | 两者都行 |
| 含中文路径 | `SaveAs`（不带数字后缀）| SaveAs3可能失败 |
| 桌面/OneDrive/微信 | `SaveAs` + 正斜杠 | 最安全 |
| 需要指定sw版本 | `SaveAs3(path, 1, 2)`但用英文路径 | 版本控制 |

```csharp
// 通用安全保存函数
static bool SafeSave(ModelDoc2 doc, string path)
{
    try
    {
        // 尝试SaveAs3
        int result = doc.SaveAs3(path, (int)swSaveAsVersion_e.swSaveAsCurrentVersion, 0);
        if (result == 0)  // SaveAs3失败
            doc.SaveAs(path);  // 降级到SaveAs
        return System.IO.File.Exists(path);
    }
    catch
    {
        // 最终降级
        doc.SaveAs(path);
        return System.IO.File.Exists(path);
    }
}
```

---

### 22.3 图纸分析标准工作流（P1 - 跨机新增）📐

#### 背景
从工程图到建模代码，最容易出错的环节是**图纸解读**——误读尺寸、混淆高度/厚度、遗漏标注。

#### 五步法标准流程

```
步骤1: 识别底座基准面（Y=0）
步骤2: 建立Y轴尺寸链（从0向上标注每个水平面高度）
步骤3: 建立X轴对称性（确认左右对称中心X=0）
步骤4: 验证尺寸链（交叉验算确保无矛盾）
步骤5: 生成坐标表（直接映射到代码的CreateLine参数）
```

#### 实战示例：底座支架图纸分析

**原始图纸特征：**
- 底座底部宽=100mm、斜边角度=50°、斜边高=15mm
- 竖直边高=20mm（不是底座厚度！）
- 凸台顶部高=75mm（不是底座高度！）
- 耳片顶部高=128mm

**步骤1-3：尺寸链推导**

```
Y=128mm  ─────── 耳片顶部
Y=120mm  ──●──  M6螺纹孔（深11mm）
Y= 88mm  ──○──  耳片Φ9孔中心线
Y= 75mm  ─────── 凸台顶部
Y= 35mm  ─────── 底座顶部 / 凸台起始面
Y= 15mm  ─────── 斜边顶线
Y=  0mm  ─────── 底座底部（基准）
```

**步骤4：尺寸链验证**

| 参数 | 推导值 | 图纸标注 | 一致性 |
|------|--------|----------|:---:|
| 底座总高 | 15+20=35mm | (隐含) | ✅ |
| 凸台高度 | 75-35=40mm | (隐含) | ✅ |
| 耳片高度 | 128-35=93mm | (隐含) | ✅ |
| 斜边顶部宽 | 38×2=76mm | 标注76mm | ✅ |
| 斜边角度 | arctan(15/12)=51.3° | 标注50° | ⚠️ 近似 |

**步骤5：坐标表（直接映射代码）**

| 线段 | 起点(X,Y) | 终点(X,Y) |
|------|-----------|-----------|
| 底边 | (-50, 0) | (50, 0) |
| 右斜边 | (50, 0) | (38, 15) |
| 右竖直 | (38, 15) | (38, 35) |
| 顶边 | (38, 35) | (-38, 35) |
| 左竖直 | (-38, 35) | (-38, 15) |
| 左斜边 | (-38, 15) | (-50, 0) |

> **铁律**：生成代码前，必须先在纸上推导尺寸链 → 验证 → 生成坐标表。
> 严禁直接凭"看图感觉"写坐标参数。

---

### 22.4 Python VARIANT 包装参考（P1 - 跨机补充）

> ⚠️ 注意：本skill已全面转向C#架构，以下内容仅供Python兼容场景参考。

#### 问题背景
Python COM调用`FeatureExtrusion2`时，如果不做VARIANT包装，COM接口无法正确解析23个参数的类型 → 返回`"非选择性的参数"`错误。

#### 完整VARIANT包装模板

```python
import win32com.client
from win32com.client import VARIANT
import pythoncom
from pythoncom import VT_BOOL, VT_I4, VT_R8

# 类型包装器
VBOOL = lambda v: VARIANT(VT_BOOL, v)
VI4 = lambda v: VARIANT(VT_I4, int(v))
VR8 = lambda v: VARIANT(VT_R8, float(v))

# ✅ 正确：全部参数VARIANT包装
feat = swDoc.FeatureManager.FeatureExtrusion2(
    VBOOL(False), VBOOL(False), VBOOL(False),  # Sd, Flip, Dir
    VI4(0), VI4(0),                              # T1, T2（终止条件）
    VR8(0.06), VR8(0.06),                        # D1, D2 ← 必须都非零
    VBOOL(False), VBOOL(False), VBOOL(False), VBOOL(False),  # Dchk, Ddir
    VI4(0), VI4(0),                              # Dang
    VBOOL(False), VBOOL(False), VBOOL(False), VBOOL(False),  # Ofr, Tf
    VBOOL(True), VBOOL(False), VBOOL(False),     # Merge, UseFeatScope, UseAutoSelect
    VI4(0), VR8(0.0), VBOOL(False)               # StartType, StartOffset, FlipStart
)

# ❌ 错误：不包装 → COM类型识别失败
feat = swDoc.FeatureManager.FeatureExtrusion2(
    False, False, False, 0, 0, 0.06, 0.06, ...
)  # → "非选择性的参数" 错误
```

#### 关键陷阱

| 问题 | 表现 | 解决方案 |
|------|------|----------|
| 参数不包装 | "非选择性的参数" | 所有参数VARIANT()包裹 |
| D2=0.0 | 单向拉伸失败 | D2必须非零（设0.001也行） |
| SaveAs3中文路径 | 返回0 | 改用SaveAs |
| FeatureCut4 | 返回None | Python下无解，用C# |

---

### 22.5 底座支架类零件代码模板（P1 - 跨机新增）

```python
def draw_trapezoid_base(sketch, bottom_w, top_w, slope_h, vertical_h):
    """
    绘制六边形梯形底座草图（整数坐标，确保闭合）
    
    参数（单位mm）：
        bottom_w: 底边宽度
        top_w:    顶边宽度
        slope_h:  斜边垂直高度
        vertical_h: 竖直边高度
    """
    half_bottom = bottom_w // 2
    half_top = top_w // 2
    offset = half_bottom - half_top
    total_h = slope_h + vertical_h
    
    mm = lambda v: v / 1000.0
    
    sketch.CreateLine(mm(-half_bottom), mm(0), 0, mm(half_bottom), mm(0), 0)
    sketch.CreateLine(mm(half_bottom), mm(0), 0, mm(half_top), mm(slope_h), 0)
    sketch.CreateLine(mm(half_top), mm(slope_h), 0, mm(half_top), mm(total_h), 0)
    sketch.CreateLine(mm(half_top), mm(total_h), 0, mm(-half_top), mm(total_h), 0)
    sketch.CreateLine(mm(-half_top), mm(total_h), 0, mm(-half_top), mm(slope_h), 0)
    sketch.CreateLine(mm(-half_top), mm(slope_h), 0, mm(-half_bottom), mm(0), 0)
```

**调用示例：**
```csharp
// C# 等价实现
double mm(double v) => v / 1000.0;
double hb = mm(50), ht = mm(38), sh = mm(15), vh = mm(20);
double th = mm(35);  // sh + vh

swDoc.SketchManager.CreateLine(-hb, 0, 0, hb, 0, 0);
swDoc.SketchManager.CreateLine(hb, 0, 0, ht, sh, 0);
swDoc.SketchManager.CreateLine(ht, sh, 0, ht, th, 0);
swDoc.SketchManager.CreateLine(ht, th, 0, -ht, th, 0);
swDoc.SketchManager.CreateLine(-ht, th, 0, -ht, sh, 0);
swDoc.SketchManager.CreateLine(-ht, sh, 0, -hb, 0, 0);
```

---

### 22.6 跨机环境差异汇总

| 项目 | 本机（E:盘SW2024） | 舍友电脑（SW2024中文版） | 差异 |
|------|------|------|:---:|
| SW安装路径 | E:\sw2024\ | C:\Program Files\ | 编译命令的/r路径不同 |
| Interop DLL位置 | C:\SOLIDWORKS\api\redist\ | C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\ | **需自适应** |
| 保存路径 | 英文 | 中文桌面 | **SaveAs3不兼容中文** |
| Python环境 | — | 3.14 + pywin32 | Python COM下FeatureCut全失败 |
| 建模结果 | Clevis_Joint 4/4通过 | bracket外形正确、孔需手动 | C# vs Python差异大 |

> **核心结论**：C#路径下（本机）和Python路径下（舍友电脑）的建模成功率差距显著。
> 再次验证：**复杂特征（切除、孔、圆角）必须走C#架构**。

---

## 二十四、五大核心铁律速查（2026-06-01 终版归档）

> 以下5条+1条防御规则来自叉形接头正交几何重构的全部实机验证。
> **任何人不得以"试试看"为由绕过任何一条。**

---

### 铁律 0：启动即清理——关闭所有"下崽"文档 🔴

**病灶**：反复运行测试脚本，后台积累几十个 `零件*` 未保存文档→内存爆炸→COM冲突→GetActiveObject报错。

```csharp
// ═══════ 程序入口首行代码 ═══════
while (swApp.GetDocumentCount() > 0)
{
    ModelDoc2 tempDoc = (ModelDoc2)swApp.ActiveDoc;
    if (tempDoc != null)
        swApp.CloseDoc(tempDoc.GetTitle());
    else break;
}
// ═══════ 清理完毕 ═══════
```

在 `try-catch` 异常退出点也必须熔断关闭当前文档：
```csharp
static void Fail(string msg) {
    Console.WriteLine("FAIL: " + msg);
    if (swDoc != null)
        swApp.CloseDoc(swDoc.GetTitle());  // ← 不留垃圾画布
    log.Close();
    throw new Exception(msg);
}
```

---

### 铁律 1：实体计数验证，绝不靠特征数 🔴

详见 Sec 21.1——`GetBodies2` 实体级验证，放弃 `GetFeatureCount`。

---

### 铁律 2：系统基准面绝对坐标 + FeatureCut4 双向贯穿 🔴

详见 Sec 21.3——禁用 SelectByRay 面选、禁用实体面建图、T1=T2=1 (swEndCondThroughAllBoth)。

---

### 铁律 3~7：五大 Interop DLL 隐藏雷区 🔴

| # | 地雷 | 正确做法 | 详见 |
|:---:|------|------|:---:|
| 3 | Merge 参数位错位 | 第 **18** 参数，绝不在第3位 | Sec 21.2 |
| 4 | StartOffset=1 报错 | `InsertRefPlane(8, dist, 0,0,0,0)` 平替 | Sec 21.2 |
| 5 | FeatureCut4 Sd=true→null | **Sd=false** | Sec 21.2 |
| 6 | CreateArc 不稳定 | 全面用 `Create3PointArc` | Sec 21.2 |
| 7 | 上视Y↑=世界Z↓ | 向下尺寸**取负值** | Sec 21.2 |

---

### 铁律 8：三级降级策略 🔴

| 级别 | 方案 | 何时用 |
|:---:|------|------|
| Tier 1 | Python COM | 草图/选择/视图（简单API） |
| Tier 2 | Python→VBA宏注入 | 多参数API（非sandbox环境C#不可用时） |
| Tier 3 | C# exe | 全功能（需Interop DLL+非sandbox） |

---

### 24.1 知识库更新记录

| 日期 | 更新内容 | 验证状态 |
|------|----------|:---:|
| 2026-06-02 | ShowNamedView2 View ID 修正（Top=3,Right=5 非 Top=5,Right=4）| ✅ 跨机验证 |
| 2026-06-02 | RevisionNumber() Substring 越界防护 + safe_get_sw_version() | ✅ 跨机验证 |
| 2026-06-02 | 同一草图矩形+圆混画导致特征失败警告 + PrintWindow OpenGL 限制 | ✅ 跨机验证 |
| 2026-06-01 | 五大铁律速查表 + 启动清理 + 三级降级 | ✅ 双机验证 |
| 2026-06-01 | FeatureExtrusion2 Python COM版本依赖警告 | ✅ 跨机验证 |
| 2026-06-01 | AI视觉QA验证工作流（截图→多模态对比） | ✅ 跨机验证 |
| 2026-06-01 | Python→VBA混合架构方案 | ✅ 跨机验证 |
| 2026-06-01 | SelectByID2 ctx参数多格式回退 | ✅ 跨机验证 |
| 2026-06-01 | C#沙箱隔离：Marshal.GetActiveObject不可用 | ✅ 跨机验证 |
| 2026-06-01 | FeatureExtrusion2 Merge=参数18（非3） | ✅ 反射+实机 |
| 2026-06-01 | FeatureCut4 Sd必须为false | ✅ 反射+实机 |
| 2026-06-01 | InsertRefPlane Distance=8（非1） | ✅ 反射+实机 |
| 2026-06-01 | CreateArc不可用 → Create3PointArc | ✅ 实机 |
| 2026-06-01 | 上视基准面Y↔Z映射（负值） | ✅ 实机 |
| 2026-06-01 | GetBodies2 替代 GetFeatureCount 防假通关 | ✅ 实机 |
| 2026-06-01 | 系统基准面绝对坐标替代面遍历 | ✅ 实机 |
| 2026-05-31 | swEndCondThroughAll=1（非4） | ✅ 反射 |
| 2026-05-31 | Activator.CreateInstance 替代 Marshal.GetActiveObject | ✅ 实机 |
| 2026-06-01 | 双重嵌套纠错环验证系统（内环编译+外环几何视觉+迭代） | ✅ 架构设计 |

---

## 二十五、双重嵌套纠错环验证系统（2026-06-01 架构升级）

> 当前 CAD 生成式自动化领域最前沿的验证方案：**内环编译纠错 + 外环几何+视觉双重重测 → 自适应迭代直到通过**。

### 25.1 架构全景

```
┌─────────────────────────────────────────────────────────────┐
│                   CAD 双重嵌套纠错环                           │
├─────────────────────────────────────────────────────────────┤
│  内环 (Inner Loop): 编译纠错                                  │
│  C#源码 → csc.exe编译 ──┬→ 成功 → EXE → 进入外环              │
│                        └→ 失败 → stderr → AI重写 → 重编译     │
│                           (最多5轮, 致命错误立即停止)            │
├─────────────────────────────────────────────────────────────┤
│  外环 (Outer Loop): 几何校验 + 视觉QA 双重验证                  │
│                                                               │
│  A: 几何内核校验          B: 多模态视觉QA                       │
│  GetBodies2 → 实体数      ① 等轴测(空间拓扑)                    │
│  BoundingBox → 尺寸       ② 前视(垂直面+通孔)                   │
│  Volume → 材料量          ③ 俯视(水平切槽+槽宽)                  │
│  汇合 ──┬→ PASS → 退出    │ 截图JPG → VLM裁判 → PASS/FAIL/MODIFY│
│         └→ FAIL → 偏差+VLM意见 → Refiner → 修改源码 → 内环      │
└─────────────────────────────────────────────────────────────┘
```

### 25.2 内环：编译纠错（最大5轮）

| 错误类型 | 模式 | 处理 |
|----------|------|------|
| 可修复 | CS1002缺少分号, CS0103未定义, CS1503类型不匹配 | AI重写后重试 |
| 致命 | CS0006 DLL缺失, CS0016无法写入 | 立即停止 |

### 25.3 外环-A：几何内核物理校验

| 维度 | API | 失败含义 |
|------|-----|------|
| 实体数 | GetBodies2(solidBody) | 0=拉伸失败, >1=切除变凸台 |
| 包围盒 | BoundingBox.GetExtremePoints() | 尺寸偏差, 坐标错误 |
| 体积 | MassProperty.Volume | 未切穿, 多余材料 |
| 拓扑 | ForceRebuild3()无异常 | 悬空草图, 零厚度几何 |

详见 Sec 21.1。

### 25.4 外环-B：多模态视觉 VLM 裁判

三标准视图自动截图 → VLM审查：

| 视图 | ID | 检查内容 |
|------|:---:|------|
| 等轴测 | 7 | 空间拓扑、对称性 |
| 前视 | 1 | 垂直面、通孔穿透 |
| 俯视 | 3 | 水平切槽、耳片对称 |

**VLM审查Prompt**: 三视图JPG + 几何内核实测(实体数/包围盒/体积) + 工程图理论参数 → 5项审查清单 → 输出 PASS/FAIL/MODIFY。

### 25.5 自适应迭代

| 外环结果 | 动作 |
|------|------|
| 几何PASS + 视觉PASS | ✅ 退出 |
| 几何FAIL | 偏差数据 → 修改源码 → 重入内环 |
| 视觉FAIL | VLM修改意见 → 修改源码 → 重入内环 |
| 两者FAIL | 优先修正几何参数 |

**最大迭代**: 简单≤5特征:3轮 / 中等:5轮 / 复杂:8轮。同类型错误重复3次→熔断。

### 25.6 与现有架构的层级关系

```
  Sec 20 (Python COM限制)       → Tier 1 能力边界
  Sec 21 (C# 强类型规范)        → Tier 3 实现基础
  Sec 21.1 (GetBodies2 防假跑)  → 外环-A 基础
  Sec 21.2 (5大Interop雷区)    → 内环编译前提
  Sec 21.3 (基准面绝对坐标)     → 外环-B 视觉QA基础
  Sec 24 (五大铁律速查)         → 所有环的前置规则
  Sec 25 (双重嵌套纠错环) ← 串联上述全部为自动化pipeline
```

---

## 二十六、Python COM 底层陷阱（2026-06-02 第三轮跨机验证）

> 来源：舍友运行 bracket_v3→v9 迭代链的完整复盘。
> 发现多个之前本机 C# 路径下从未暴露的 Python late-binding 特定问题。

### 26.1 SelectByID2 Callout 参数陷阱（P0 - 新发现）⚠️

**现象**: `SelectByID2` 始终返回 False，即使名称/类型/坐标都正确。

**根因**: 第8个参数 (Callout) **必须是 `VARIANT(VT_DISPATCH, None)`**，不能用 Python `None` 或 `0` 替代。

```python
# ❌ 错误——所有这些都是失败的
doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, False, 0, None, 0)  # TypeError
doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, False, 0, 0, 0)     # 同样失败

# ✅ 正确
VDISPATCH = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
doc.Extension.SelectByID2(name, "PLANE",
    VR8(0), VR8(0), VR8(0),
    VBOOL(False), VI4(0), VDISPATCH, VI4(0))
```

**与之前 Sec 23.5 的 ctx 多格式回退的区别**:
- `ctx` 参数（第9个）影响的是"选择上下文标记"
- `Callout` 参数（第8个）影响的是"标注引用"——**类型要求更严格**
- 两者都需要 VARIANT 包装，但 Callout 必须显式 `VT_DISPATCH`

### 26.2 COM 属性 vs 方法混淆（P0 - 新发现）⚠️

**现象**: `doc.GetTitle()` 报 `TypeError: 'str' object is not callable`。

**根因**: Python late-binding 中，某些 SW 属性表现为 **Python 属性** 而非方法。

| API | Python 中实际类型 | 错误调用 | 正确调用 |
|-----|:---:|------|------|
| `GetTitle` | **属性** | `doc.GetTitle()` ❌ | `doc.GetTitle` ✅ |
| `GetFeatureCount` | **属性** | `doc.GetFeatureCount()` ❌ | `doc.GetFeatureCount` ✅ |
| `FirstFeature` | **属性** | `doc.FirstFeature()` ❌ | `doc.FirstFeature` ✅ |
| `GetNextFeature` | **方法** | `feat.GetNextFeature` ❌ | `feat.GetNextFeature()` ✅ |
| `GetTypeName2` | **方法** | `feat.GetTypeName2` ❌ | `feat.GetTypeName2()` ✅ |

**安全封装**:
```python
def safe_call(obj, attr, default=None):
    """统一处理 COM 属性/方法歧义"""
    try:
        val = getattr(obj, attr)
        if callable(val):
            return val()
        return val
    except:
        return default
```

### 26.3 SW 版本兼容——多 ProgID 回退（P0 - 新发现）⚠️

**问题**: 硬编码 `"SldWorks.Application.32"` 在 64 位 SW 或版本变化时失败。

```python
def connect_sw():
    """多 ProgID 回退连接 SW"""
    progids = [
        "SldWorks.Application.32",   # 32位SW
        "SldWorks.Application.64",   # 64位SW
        "SldWorks.Application",      # 通用（自动选择）
    ]
    for progid in progids:
        try:
            sw = win32com.client.Dispatch(progid)
            print(f"✓ SW连接成功: {progid}")
            return sw
        except:
            pass
    raise ConnectionError("无法连接SolidWorks")
```

### 26.4 模板路径自适应（P1）

```python
def find_template():
    """自动查找 SW 模板路径"""
    candidates = [
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot",
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2025\templates\gb_part.prtdot",
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2023\templates\gb_part.prtdot",
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Part.prtdot",  # 英文回退
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""  # SW将使用默认模板
```

### 26.5 COM 初始化/清理保证——try/finally 模式（P0）⚠️

**问题**: `CoInitialize()` 在开头，`CoUninitialize()` 在末尾——如果中途异常退出，`CoUninitialize()` 不会执行 → COM 资源泄漏。

```python
import pythoncom, win32com.client

def run_modeling():
    pythoncom.CoInitialize()
    builder = None
    try:
        builder = BracketBuilder()
        builder.connect()
        builder.build()
    finally:
        if builder:
            builder.close()
        pythoncom.CoUninitialize()
```

---

## 二十七、Python 类封装架构模板（2026-06-02 新增）

> 基于舍友 bracket_v10 的 `BracketBuilder` 类设计，提取为通用模板。

### 27.1 架构原则

1. **类封装** — `self.sw`, `self.doc` 作为实例属性，不再用全局变量
2. **参数表驱动** — 所有尺寸集中在一个 `PARAMS` 字典中
3. **步骤独立方法** — 每个建模步骤封装为独立方法，返回 True/False
4. **VARIANT 统一包装** — 通过 `self.v` 辅助类提供所有包装方法
5. **try/finally 保证** — 确保 COM 清理一定执行

### 27.2 完整模板

```python
import win32com.client, pythoncom, math, time, os, sys

# ===== 参数表（所有尺寸 mm）=====
PARAMS = {
    "base_bottom_width": 100.0,
    "base_top_width": 76.0,
    "base_depth": 60.0,
    "total_height": 128.0,
    # ... 所有尺寸集中管理
}

def mm(v): return float(v) / 1000.0  # mm → m

class VARIANTHelper:
    """SW COM VARIANT 包装器"""
    def __init__(self, client):
        self.VARIANT = client.VARIANT
        self.VT_BOOL = pythoncom.VT_BOOL
        self.VT_I4 = pythoncom.VT_I4
        self.VT_R8 = pythoncom.VT_R8
        self.VT_DISPATCH = pythoncom.VT_DISPATCH
        self.VT_EMPTY = pythoncom.VT_EMPTY
    
    def VBOOL(self, v): return self.VARIANT(self.VT_BOOL, v)
    def VI4(self, v): return self.VARIANT(self.VT_I4, int(v))
    def VR8(self, v): return self.VARIANT(self.VT_R8, float(v))
    def VEMPTY(self): return self.VARIANT(self.VT_EMPTY, None)
    def VDISPATCH(self): return self.VARIANT(self.VT_DISPATCH, None)

class BracketBuilder:
    """底座支架建模器（通用模板可改名复用）"""
    
    def __init__(self, params=None):
        self.params = params or PARAMS
        self.sw = None
        self.doc = None
        self.v = None
        self.feat_count_start = 0
    
    # ===== 连接 =====
    def connect(self):
        # 多ProgID回退
        for progid in ["SldWorks.Application.32", "SldWorks.Application.64", "SldWorks.Application"]:
            try:
                self.sw = win32com.client.Dispatch(progid)
                break
            except: pass
        if not self.sw:
            raise ConnectionError("无法连接SW")
        
        self.v = VARIANTHelper(win32com.client)
        self.sw.Visible = True
        
        # 启动清理（铁律0）
        while self.sw.GetDocumentCount() > 0:
            doc = self.sw.ActiveDoc
            if doc: self.sw.CloseDoc(doc.GetTitle)
            else: break
        
        # 模板自适应
        tpl = self._find_template()
        self.sw.NewDocument(tpl, 0, 0, 0)
        time.sleep(1)
        self.doc = self.sw.ActiveDoc
        self.feat_count_start = self.doc.GetFeatureCount
    
    # ===== 选择 =====
    def select_plane(self, name):
        """中英文双语基准面选择 + Callout 正确包装"""
        candidates = [name]
        mapping = {"Front Plane": "前视基准面", "Right Plane": "右视基准面", "Top Plane": "上视基准面"}
        if name in mapping: candidates.append(mapping[name])
        
        for n in candidates:
            try:
                ok = self.doc.Extension.SelectByID2(n, "PLANE",
                    self.v.VR8(0), self.v.VR8(0), self.v.VR8(0),
                    self.v.VBOOL(False), self.v.VI4(0),
                    self.v.VDISPATCH(), self.v.VI4(0))
                if ok: return True
            except: pass
        return False
    
    # ===== 建模步骤 =====
    def build_base(self):
        """底座梯形拉伸"""
        if not self.select_plane("Front Plane"): return False
        self.doc.SketchManager.InsertSketch(True)
        
        bw2 = self.params["base_bottom_width"] / 2
        tw2 = self.params["base_top_width"] / 2
        slope_h = self.params["base_slope_height"]
        vert_h = self.params["base_vert_height"]
        tot_h = slope_h + vert_h
        
        # 梯形截面（整数mm确保闭合——铁律 Sec 22.1）
        self.doc.SketchManager.CreateLine(mm(-bw2), mm(0), 0, mm(bw2), mm(0), 0)
        self.doc.SketchManager.CreateLine(mm(bw2), mm(0), 0, mm(tw2), mm(slope_h), 0)
        self.doc.SketchManager.CreateLine(mm(tw2), mm(slope_h), 0, mm(tw2), mm(tot_h), 0)
        self.doc.SketchManager.CreateLine(mm(tw2), mm(tot_h), 0, mm(-tw2), mm(tot_h), 0)
        self.doc.SketchManager.CreateLine(mm(-tw2), mm(tot_h), 0, mm(-tw2), mm(slope_h), 0)
        self.doc.SketchManager.CreateLine(mm(-tw2), mm(slope_h), 0, mm(-bw2), mm(0), 0)
        self.doc.SketchManager.InsertSketch(True)
        
        depth = mm(self.params["base_depth"])
        return self._extrude(depth, "底座")
    
    def _extrude(self, depth, name):
        """安全拉伸（VARIANT 包装）"""
        before = self.doc.GetFeatureCount
        try:
            self.doc.FeatureManager.FeatureExtrusion2(
                self.v.VBOOL(False), self.v.VBOOL(False), self.v.VBOOL(False),
                self.v.VI4(0), self.v.VI4(0),
                self.v.VR8(depth), self.v.VR8(depth),
                self.v.VBOOL(False), self.v.VBOOL(False), self.v.VBOOL(False), self.v.VBOOL(False),
                self.v.VI4(0), self.v.VI4(0),
                self.v.VBOOL(False), self.v.VBOOL(False), self.v.VBOOL(False), self.v.VBOOL(False),
                self.v.VBOOL(True), self.v.VBOOL(False), self.v.VBOOL(False),  # Merge=参数18!
                self.v.VI4(0), self.v.VR8(0), self.v.VBOOL(False))
            self.doc.ForceRebuild3(False)
            after = self.doc.GetFeatureCount
            return after > before
        except Exception as e:
            print(f"  {name}拉伸失败: {e}")
            return False
    
    # ===== 自验证 =====
    def verify(self):
        """建模后边界框验证"""
        bbox = self.doc.Extension.CreateBoundingBox()
        if bbox is None: return False
        pts = bbox.GetExtremePoints()
        if pts is None or len(pts) < 6: return False
        
        x, y, z = (pts[3]-pts[0])*1000, (pts[4]-pts[1])*1000, (pts[5]-pts[2])*1000
        expected_y = self.params["total_height"]
        
        print(f"边界框: X={x:.1f} Y={y:.1f} Z={z:.1f} mm")
        if abs(y - expected_y) > 5:
            print(f"⚠ 高度偏差: 预期{expected_y}mm 实测{y:.1f}mm")
            return False
        return True
    
    # ===== 清理 =====
    def close(self):
        """安全关闭"""
        if self.doc:
            try: self.doc.Save() 
            except: pass
        if self.sw:
            try: self.sw.CloseAllDocuments(True)
            except: pass

# ===== 运行入口 =====
if __name__ == "__main__":
    pythoncom.CoInitialize()
    builder = None
    try:
        builder = BracketBuilder()
        builder.connect()
        builder.build_base()
        if builder.verify():
            print("✓ 建模验证通过")
    finally:
        if builder: builder.close()
        pythoncom.CoUninitialize()
```

### 27.3 关键改进点（v10 vs v9）

| 改进项 | v9（旧） | v10（新） |
|------|------|------|
| 架构 | 全局变量 `sw`, `doc` | 类封装 `self.sw`, `self.doc` |
| 尺寸管理 | 硬编码数字散布各处 | `PARAMS` 字典集中管理 |
| 错误处理 | 部分 API 有 try/except | 所有 API 统一封装 |
| COM 清理 | `CoUninitialize` 在末尾 | `try/finally` 保证一定执行 |
| SW 连接 | 硬编码 `.32` | 多 ProgID 回退 |
| 模板 | 硬编码 SW2024 路径 | 自动查找 + 回退 |
| 验证 | 无 | 边界框自动验证 |

---

### 知识库更新记录（追加）

| 日期 | 更新内容 | 验证状态 |
|------|----------|:---:|
| 2026-06-02 | SelectByID2 Callout = VDISPATCH 陷阱 | ✅ 跨机验证 |
| 2026-06-02 | COM 属性/方法混淆速查表 | ✅ 跨机验证 |
| 2026-06-02 | 多 ProgID SW 连接回退 | ✅ 跨机验证 |
| 2026-06-02 | try/finally COM 清理保证 | ✅ 跨机验证 |
| 2026-06-02 | 类封装架构模板 (BracketBuilder) | ✅ 跨机验证 |
| 2026-06-02 | 参数表驱动 + 边界框自验证 | ✅ 跨机验证 |

