---
name: solidworks-automation
description: "SolidWorks automation skill with full SW tutorial knowledge base. Supports automated modeling, assembly, drawing generation, Simulation, Flow Simulation, sheet metal, weldments, mold design, surface modeling, and electrical design via Python/C#/VBA SolidWorks API. / SolidWorks 自动化建模技能，内置完整的SW教程知识体系。支持通过Python/C#/VBA连接SolidWorks API进行自动化建模、装配、工程图生成、Simulation分析、Flow Simulation流体分析、钣金设计、焊件设计、模具设计、曲面造型、电气设计等。"
category: engineering-cad
version: 3.1.0
author: Delancy
target_sw_version: "SolidWorks 2024 (verified), 2016+ (compatible)"
language: bilingual (English/中文)
github: https://github.com/delancy827/solidworks-skills
---

# solidworks-automation

## Overview | 概述

**English:**
Automate SolidWorks 3D CAD workflows via the SolidWorks API (COM/Dispatch). This skill contains a complete SolidWorks knowledge base (basics → advanced surfacing, sheet metal, weldments, mold design, Simulation FEA, Flow Simulation CFD, rendering). It generates working Python (pywin32) scripts to drive SolidWorks programmatically. Verified on **SolidWorks 2024 + Python 3.14**.

**中文：**
通过 SolidWorks API（COM/Dispatch）自动化 SolidWorks 三维CAD工作流。本技能内置完整的SolidWorks知识体系（基础→高级曲面、钣金、焊件、模具设计、Simulation有限元分析、Flow Simulation流体分析、渲染）。可生成可用的 Python（pywin32）脚本驱动 SolidWorks。已在 **SolidWorks 2024 + Python 3.14** 环境实战验证。

---

## When to Use | 适用场景

| Scenario / 场景 | Use This Skill / 使用本技能 |
|---|---|
| Automate part/assembly/drawing creation / 自动化创建零件/装配体/工程图 | ✅ |
| Generate Python script to drive SolidWorks / 生成Python脚本驱动SW | ✅ |
| Need SW API parameter signatures (SW2024 verified) / 需要SW API参数签名（SW2024实测） | ✅ |
| Workaround SW COM limitations (e.g. FeatureCut >12 params) / 绕过SW COM限制 | ✅ |
| Batch convert SLDPRT → STEP/STL / 批量格式转换 | ✅ |
| Simulation (FEA) or Flow Simulation (CFD) automation / 仿真自动化 | ✅ |
| Sheet metal / weldment / mold design automation / 钣金/焊件/模具自动化 | ✅ |

---

## Version History | 版本历史

| Version / 版本 | Date / 日期 | Changes / 变更说明 |
|---|---|---|
| 3.1.0 | 2026-05-30 | Added bilingual EN/CN front matter, GitHub link, SW version targeting, scenario table / 添加中英文前言、GitHub链接、SW版本说明、适用场景表 |
| 3.0.0 | 2026-05-30 | SW2024 Python COM实战踩坑记录，FeatureCut限制，加法建模策略 / SW2024 Python COM real-world pitfalls, FeatureCut limits, additive modeling strategy |
| 2.x | 2026-05 | Initial skill with full SW tutorial knowledge base / 初始版本，内置完整SW教程知识体系 |

---

## Installation | 安装

**English:**
Place the `solidworks-automation/` folder into your WorkBuddy skills directory:
- User-level: `~/.workbuddy/skills/solidworks-automation/`
- Project-level: `<project>/.workbuddy/skills/solidworks-automation/`

**中文：**
将 `solidworks-automation/` 文件夹放入 WorkBuddy 技能目录：
- 用户级：`~/.workbuddy/skills/solidworks-automation/`
- 项目级：`<项目>/.workbuddy/skills/solidworks-automation/`

---

## Environment & Prerequisites | 环境与前置条件

**English:**
- **SolidWorks**: 2016+ (verified on 2024)
- **Python**: 3.8+ with `pywin32` (`pip install pywin32`)
- **OS**: Windows 7/10/11 (SolidWorks is Windows-only)
- **SolidWorks must be running** before executing automation scripts

**中文：**
- **SolidWorks**：2016+（已在2024实测）
- **Python**：3.8+，需安装 `pywin32`（`pip install pywin32`）
- **操作系统：** Windows 7/10/11（SolidWorks仅支持Windows）
- 执行自动化脚本前**必须先启动SolidWorks**

---

## ⚠️ SW 2024 Python COM Critical Pitfalls | SW 2024 Python COM 关键踩坑

*Real-world verified 2026-05-30 / 2026-05-30 实战验证*

### Connection Methods | 连接方式

| Method / 方式 | Result / 结果 |
|---|---|
| `win32com.client.Dispatch("SldWorks.Application")` | ✅ Works / 可用 |
| `win32com.client.Dispatch("SldWorks.Application.28/32")` | ✅ Works / 可用 |
| `win32com.client.gencache.EnsureDispatch(...)` | ❌ "COM object can not automate makepy" |
| `gencache.EnsureModule(GUID, 0, 32, 0)` | ⚠️ Cache generated but still late-bound / 可生成缓存但不改变绑定方式 |

### Parameter Passing (Core!) | 参数传递（核心！）

- **SelectByID2 (9 params)**: MUST wrap **every param** with `VARIANT(pythoncom.VT_xxx, value)`
- **FeatureExtrusion2 (23 params)**: Pass native types directly (NO VARIANT wrapping needed)
- **FeatureFillet3**: Pass params directly / 直接传参即可
- **SketchManager methods**: Pass params directly / 直接传参即可

### API Availability (SW 2024 Python COM) | API可用性

| API | Param Count | Python COM | Notes / 备注 |
|---|:---:|:---:|---|
| `NewDocument(template_path, ...)` | 4 | ✅ | Must use full path, NOT empty string! / 必须用完整路径，空字符串不行！ |
| `SelectByID2` | 9 | ✅ VARIANT | Chinese names like "前视基准面" work directly / 中文名可直接用 |
| `FeatureExtrusion2` | 23 | ✅ | **NOT 17 params as in old docs! / 不是旧版的17参数！** |
| `FeatureExtrusion3` | 23 | ✅ | Same as 2 / 同2 |
| `FeatureCut` | 20 | ❌ Returns None | Params match but feature not created / 参数匹配但特征不创建 |
| `FeatureCut3` | 26 | ❌ Returns None | Same issue / 同上 |
| `FeatureCut4` | 27 | ❌ Returns None | **COM IDispatch limit for >12 params / >12参数的COM IDispatch限制** |
| `FeatureFillet3(122,...)` | 7 | ✅ | Equal-radius fillet, must pre-select edges / 等半径圆角，需先预选边 |
| `CloseDoc` | 1 | ✅ | Use `doc.GetTitle` (property), NOT `GetTitle()` / title用属性不是方法 |
| `GetDocuments` | 0 | ✅ | Returns tuple, property not method / 返回tuple，属性不是方法 |

### Workaround: Additive Modeling Strategy | 应急方案：加法建模策略

When `FeatureCut` is unavailable, build the part by adding solids:

```
Base plate (80×90×33mm) + Left wall (25×90×22mm) + Right wall (25×90×22mm)
→ Boolean Union → U-groove shape (no cut operation needed)
```

- Fillets: use `FeatureFillet3`
- Holes: use `FeatureExtrusion2` to create 1mm boss markers, then manually cut

### Template Path | 模板路径

```python
TEMPLATE = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
doc = sw.NewDocument(TEMPLATE, 0, 0, 0)  # MUST use full path / 必须完整路径
```

### FeatureExtrusion2 23-Parameter Signature (SW2024) | FeatureExtrusion2 23参数签名

```python
doc.FeatureManager.FeatureExtrusion2(
    Sd, Flip, Dir,       # 1-3: Bool
    T1, T2,              # 4-5: Int (0=Blind)
    D1, D2,              # 6-7: Double (meters)
    Dchk1, Dchk2,        # 8-9: Bool
    Ddir1, Ddir2,        # 10-11: Bool
    Dang1, Dang2,        # 12-13: Double (radians)
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

## Supported Features Matrix | 功能支持矩阵

| Feature / 功能 | API Support | Automation Level / 自动化程度 |
|---|---|---|
| Basic part modeling / 基础零件建模 | ✓ | Fully automated / 完全自动化 |
| Engineering features (fillet, chamfer, shell...) / 工程特征 | ✓ | Fully automated / 完全自动化 |
| Assembly / 装配体 | ✓ | Mostly automated / 大部分自动化 |
| Drawing / 工程图 | ✓ | Mostly automated / 大部分自动化 |
| Surface design / 曲面设计 | ✓ | Mostly automated / 大部分自动化 |
| Sheet metal / 钣金 | ✓ | Mostly automated / 大部分自动化 |
| Weldments / 焊件 | ✓ | Partially automated / 部分自动化 |
| Mold design / 模具设计 | ✓ | Partially automated / 部分自动化 |
| Simulation (FEA) / 有限元分析 | ✓ | Partially automated / 部分自动化 |
| Flow Simulation (CFD) / 流体分析 | ✓ | Partially automated / 部分自动化 |
| Rendering / Animation / 渲染/动画 | ✓ | Basic automation / 基础自动化 |

---

## Knowledge Base Structure | 知识体系结构

```
1. SolidWorks Basics / SolidWorks 基础
2. Sketching / 草图绘制
3. Part Feature Modeling / 零件特征建模
4. Assembly Design / 装配体设计
5. Drawing Creation / 工程图制作
6. Advanced Surface Design / 高级曲面设计
7. Sheet Metal Design / 钣金设计
8. Weldment Design / 焊件设计
9. Mold Design / 模具设计
10. Simulation (FEA) / Simulation 有限元分析
11. Flow Simulation (CFD) / Flow Simulation 流体分析
12. Advanced Functions / 其他高级功能
13. Batch Operations & File Conversion / 批量操作与文件转换
14. SolidWorks API Complete Reference / SolidWorks API 完整参考
15. Troubleshooting & Debugging / 故障排除与调试
16. Design Standards & Best Practices / 设计规范与最佳实践
```

> **Note / 注意**: The full knowledge base content is omitted here for brevity. Refer to the full SKILL.md in the repository.
> 完整知识体系内容此处从略。请参阅仓库中的完整 SKILL.md 文件。

---

## Example: Create a Part via Python | 示例：通过Python创建零件

```python
import win32com.client
import pythoncom

def create_part():
    pythoncom.CoInitialize()
    try:
        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = True

        TEMPLATE = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
        doc = sw.NewDocument(TEMPLATE, 0, 0, 0)

        # Select sketch plane / 选择草图基准面
        doc.Extension.SelectByID2(
            "Front Plane", "PLANE",
            win32com.client.VARIANT(pythoncom.VT_R8, 0),
            win32com.client.VARIANT(pythoncom.VT_R8, 0),
            win32com.client.VARIANT(pythoncom.VT_R8, 0),
            win32com.client.VARIANT(pythoncom.VT_BOOL, False),
            win32com.client.VARIANT(pythoncom.VT_I4, 0),
            None,
            win32com.client.VARIANT(pythoncom.VT_I4, 0)
        )

        # Draw circle & extrude / 画圆并拉伸
        doc.SketchManager.InsertSketch(True)
        doc.SketchManager.CreateCircle(0, 0, 0, 0.05, 0, 0)
        doc.SketchManager.InsertSketch(True)

        doc.FeatureManager.FeatureExtrusion2(
            True, False, False,
            0, 0,
            0.05, 0.05,
            False, False,
            False, False,
            0.0, 0.0,
            False, False,
            False, False,
            True,
            False, True,
            0.0, False, False
        )

        doc.SaveAs("C:/Users/Public/part1.sldprt")
        print("Part created successfully! / 零件创建成功！")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    create_part()
```

---

## References | 参考资料

- GitHub: https://github.com/delancy827/solidworks-skills
- SolidWorks API Help: https://help.solidworks.com/2024/english/api/sldworks_api/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorksMembers.html
- PyWin32 docs: https://github.com/mhammond/pywin32
