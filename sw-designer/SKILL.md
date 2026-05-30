---
name: sw-designer
description: "SW设计狮——SolidWorks professional design guide skill, combining IMA knowledge bases 'SW设计狮'(10 articles) and 'SW教程合集'(45 tutorials). Focuses on parametric design, automation modeling, batch part design, performance optimization, design standards & best practices. / SW设计狮——SolidWorks专业设计指导技能，融合IMA知识库'SW设计狮'(10篇)和'SW教程合集'(45个教程)。专注参数化设计、自动化建模、批量零件设计、性能优化、设计规范与最佳实践。"
category: engineering-cad
version: 2.1.0
author: Delancy
target_audience: "SolidWorks users, CAD designers, mechanical engineers / SolidWorks用户、CAD设计师、机械工程师"
knowledge_bases:
  - name: "SW设计狮"
    id: 7361920738820041
    articles: 10
    topics: "Parametric design, automation pitfalls, batch design, performance optimization / 参数化设计、自动化误区、批量设计、性能优化"
  - name: "SW教程合集"
    id: 7342555410738838
    resources: 45
    topics: "Beginner to advanced complete tutorials / 入门到精通全套教程"
language: bilingual (English/中文)
github: https://github.com/delancy827/solidworks-skills
---

# SW设计狮 — SolidWorks Professional Design Guide

## Overview | 概述

**English:**
Professional SolidWorks design guidance skill that combines two IMA knowledge bases. Focuses on **design intent**, **parametric methodology**, and **best practices** rather than just API calls. Helps AI understand **how to design correctly** before automating.

**中文：**
SolidWorks 专业设计指导技能，融合两个 IMA 知识库的核心知识。专注于**设计意图**、**参数化方法论**和**最佳实践**，而不仅仅是API调用。帮助AI在自动化之前理解**"怎么设计才对"**。

---

## When to Use | 适用场景

| Scenario / 场景 | Use This Skill / 使用本技能 |
|---|---|
| Need design methodology, not just API code / 需要设计方法论，不只是API代码 | ✅ |
| Parametric design & equation setup / 参数化设计与方程式 | ✅ |
| Batch part design (design tables, configs) / 批量零件设计（设计表、配置） | ✅ |
| Performance optimization for large assemblies / 大型装配体性能优化 | ✅ |
| Design standards & drafting best practices / 设计规范与出图最佳实践 | ✅ |
| Troubleshooting modeling errors / 建模错误排查 | ✅ |
| Plan modeling strategy before automation / 自动化前的建模策略规划 | ✅ |

> **💡 Tip / 提示**: Use together with `solidworks-automation` skill — `sw-designer` tells AI **what to design**, `solidworks-automation` tells AI **how to code it**.
> 配合 `solidworks-automation` 技能使用——`sw-designer` 告诉AI **设计什么**，`solidworks-automation` 告诉AI **怎么写代码**。

---

## Version History | 版本历史

| Version / 版本 | Date / 日期 | Changes / 变更说明 |
|---|---|---|
| 2.1.0 | 2026-05-30 | Added bilingual EN/CN front matter, GitHub link, version table, scenario table / 添加中英文前言、GitHub链接、版本表、适用场景表 |
| 2.0.0 | 2026-05 | Added IMA knowledge base integration, 10+45 articles/tutorials / 添加IMA知识库集成，10+45篇文章/教程 |
| 1.x | 2026-05 | Initial skill / 初始版本 |

---

## Knowledge Base Sources | 知识库来源

| Knowledge Base / 知识库 | Content / 内容 | Quantity / 数量 |
|---|---|---|
| **SW设计狮** (ID: 7361920738820041) | Parametric design errors, automation methods, batch design, performance optimization, system requirements, parametric core principles / 参数化设计错误归类、自动化建模方法、批量设计、性能优化、系统要求、参数化核心原理 | 10 articles / 10篇文章 |
| **SW教程合集** (ID: 7342555410738838) | Quick start, parts & assemblies, drawings, advanced tutorials, surfacing, sheet metal, weldments, mold design, Simulation, Flow, electrical, PDM, MBD / 快速入门、零件装配体、工程图、高级教程、曲面、钣金、焊件、模具、Simulation、Flow、电气、PDM、MBD | 45 resources / 45个资源 |

---

## Chapter 1: Parametric Design | 第一章：参数化设计

### 1.1 Core Principle | 核心原理

**English:**
Parametric design = **drive design changes using parameters, variables & math relations** to achieve automation & intelligence.

- Parameters = changeable quantities: dimensions (L/W/H), quantities, angles, etc.
- Variables are inter-linked; changing one variable affects others per predefined rules.
- Example: After module is set, tooth count change affects outer diameter, tooth width, etc.

**中文：**
参数化设计本质是**用参数、变量及数学关系驱动设计对象变化**，实现自动化与智能化。

- 参数是可变化的量：尺寸（长/宽/高）、数量、角度等
- 变量之间相互关联，一个变量改变会依据预设规则影响其他变量
- 例如：模数确定后，齿数变化影响外径、齿厚等参数

### 1.2 Four Parametric Tools | 参数化设计四大工具

| Tool / 工具 | EN | CN | Best For / 适用 |
|---|---|---|---|
| **Dimensions & Equations** / 尺寸驱动与方程式 | Define variables in Equations dialog; cross-feature association | 在「方程式」中定义变量；跨特征关联 | Complex parametric logic / 复杂参数逻辑 |
| **Configuration Manager** / 配置管理器 | Manual configs, suppress features for variants | 手动配置，压缩特征生成变体 | Simple variant switching / 少量规格调整 |
| **Design Table** / 设计表 | Excel-driven batch parameters (dims, materials) | 通过Excel表格批量定义参数 | Series products (bolts, bearings) / 系列化产品 |
| **API Secondary Dev** / API二次开发 | VBA/C#/Python call SW API | VBA/C#/Python调用SW API | Complex automation, batch processing / 复杂自动化、批量处理 |

### 1.3 Common Parametric Errors | 参数化设计常见错误（四大类）

| Error Category / 错误类别 | Typical Problem / 典型问题 | Solution / 解决方案 |
|---|---|---|
| **Parameter definition** / 参数定义错误 | Names with spaces/special chars (@#) → equations can't recognize / 名称含空格/特殊符号导致方程式无法识别 | Use only EN/numbers/underscore: `Length_1` / 只用英文/数字/下划线 |
| **Unit inconsistency** / 单位不一致 | Mixing mm and inches → calculation error / 毫米与英寸混用导致计算结果错误 | Unify units globally, or explicit convert in equation / 统一全局单位，或方程式中显式转换 |
| **Association logic** / 关联逻辑错误 | Circular reference (A=B, B=A); referencing suppressed/deleted features / 循环引用；参数引用被压缩/删除的特征 | Check equation dependencies; don't suppress features with global vars / 检查方程式依赖关系；不要压缩含全局变量的特征 |
| **Config management** / 配置管理错误 | Dimension conflicts across configs; design table format error / 不同配置尺寸冲突；设计表格式错误 | Verify config dims one by one; design table names must match SW / 逐一验证配置尺寸；设计表命名与SW一致 |
| **Operation error** / 软件操作错误 | Modified global vars but forgot to rebuild (Ctrl+Q) / 全局变量修改后未重建模型 | Always force rebuild after param changes / 修改参数后务必强制重建 |

> **⚠️ Naming Rule / 命名铁律**: Use ONLY English/numbers/underscore. NO spaces, NO special characters!
> 只用英文/数字/下划线命名。**禁止空格和特殊符号！**

---

## Chapter 2: Automation Modeling | 第二章：自动化建模方法

### 2.1 Three Automation Tiers | 三级自动化体系

| Tier / 级别 | Method / 方法 | Best Scenario / 适用场景 |
|---|---|---|
| **Basic / 初级** | Macro recording & playback / 宏录制与回放 | Simple repetitive modeling (standard parts) / 简单重复建模（标准件快速生成） |
| **Intermediate / 中级** | API secondary development / API二次开发 | Complex model auto-generation, batch modification / 复杂模型自动化生成、批量修改 |
| **Advanced / 高级** | Config-driven + API / 配置驱动+API | Product serialization, enterprise automation / 产品系列化、企业级自动化 |

### 2.2 Macro Recording & Playback | 宏录制与回放

**Steps / 操作步骤：**
1. Tools → Macro → Record / 工具 → 宏 → 录制
2. Execute modeling operations (sketch, extrude, etc.) / 执行建模操作（草图、拉伸等）
3. Stop recording, save as `.swp` file / 停止录制，保存为`.swp`文件
4. Run macro to auto-repeat recorded steps / 运行宏自动重复录制步骤

**Best for / 适用：** Simple repetitive tasks, e.g. standard part generation.
简单重复任务，如标准件快速生成。

### 2.3 API Secondary Development | API二次开发

**Tool Selection / 工具选择：**

| Tool / 工具 | Pros / 优点 | Best For / 适用 |
|---|---|---|
| **VBA** | Built-in, simplest entry / 内置，最简单的入门方式 | Learning, simple macros / 学习、简单宏 |
| **C#** | Most powerful, professional plugins / 功能最强，适合开发专业插件 | Enterprise add-ins / 企业级插件 |
| **Python (pywin32)** | Flexible, efficient, great for batch / 灵活高效，适合批量处理 | Batch processing, AI-driven automation / 批量处理、AI驱动自动化 |

**Core API Functions / 核心API功能：**
- Auto-generate parts/assemblies (`AddComponent`, `FeatureExtrusion`)
- Batch processing: traverse FeatureManager tree, auto-modify dims, patterns
- Parametric generation: auto-modeling based on input parameters

```python
# Macro recording → API conversion example / 宏录制 → API转换示例
import win32com.client
sw = win32com.client.Dispatch("SldWorks.Application")
sw.Visible = True
sw.NewPart()
model = sw.ActiveDoc
model.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
model.SketchManager.InsertSketch(True)
model.SketchManager.CreateCircle(0, 0, 0, 0.025, 0, 0)
model.SketchManager.InsertSketch(True)
model.FeatureManager.FeatureExtrusion3(
    True, False, False, 0, 0, 0.05, 0.05,
    False, False, False, False, 0, 0, False, False, False, False)
```

### 2.4 Advanced Automation Tips | 自动化进阶技巧

1. **Smart dimensioning & drawing automation**: Use `Model Items` to auto-extract design intent dims to drawings; can develop custom annotation plugins via API
2. **Config-driven advanced application**: Config Manager + Design Table to batch-control params, quick switching between specs
3. **Large assembly automation**: Lightweight + selective load + automated BOM generation
4. **SpeedPak**: Load only outer surfaces for large assembly viewing

---

## Chapter 3: Batch Part Design | 第三章：批量零件设计

### 3.1 Three Batch Methods | 三大批量方法

**Method 1: Series Part Design Table / 方法1：系列零件设计表**
- Create base part first / 先创建基础零件
- `Insert → Table → Design Table`, choose "Auto-generate" / 「插入→表格→设计表」选择"自动生成"
- Define dim/material columns in Excel; each row = one config / Excel表格中定义尺寸/材料列，每行=一种配置
- Best for: standard part libraries (bolts, nuts), serialized products / 适用：标准件库（螺栓螺母）、系列化产品

**Method 2: Configuration Manager / 方法2：配置管理器**
- Manually add new config, modify dims or suppress features / 手动添加新配置，修改尺寸或压缩特征
- Combine with Design Table: design table params link to configs / 与设计表结合：设计表参数关联配置

**Method 3: Equations + API / 方法3：方程式驱动 + API**
- Define dim variables and relations (e.g. `diameter = length / 2`) / 定义尺寸变量及关联关系
- Model auto-updates when params change / 修改参数时模型自动更新
- Loop-generate batch models via API / 结合API循环生成批量模型

### 3.2 Batch Design Best Practices | 批量设计最佳实践

1. Always create a "master part" first; manage configs via Design Table / 先做一个"母版零件"，配置尽量通过设计表管理
2. Test on small data before API batch generation / API批量生成前先在小数据量上测试
3. Always keep original config as "rollback point" / 始终保留原始配置作为"回退点"
4. After modifying global vars, ALWAYS press `Ctrl+Q` to force rebuild / 修改全局变量后务必执行「Ctrl+Q」强制重建

---

## Chapter 4: Performance Optimization | 第四章：性能优化

### 4.1 Hardware Recommendations | 硬件升级建议

| Component / 组件 | Recommendation / 建议 |
|---|---|
| **Storage / 存储** | SSD (system & SW installed here) / SSD固态硬盘（系统和SW安装在此） |
| **RAM / 内存** | 8GB+ (more = better, reduces virtual memory dependency) / 8GB以上（越大越好，减少虚拟内存依赖） |
| **GPU / 显卡** | NVIDIA/AMD professional cards (Quadro/FirePro) / NVIDIA/AMD专业卡 |
| **CPU** | Intel i5/i7, dual-core high freq 64-bit, ≥2.8GHz / Intel i5/i7，双核高主频64位 |

### 4.2 System Settings Optimization | 系统设置优化

- Turn off Windows visual effects (animations, transparency) / 关闭Windows视觉效果（动画、透明效果）
- Set virtual memory to "automatically manage" or manually increase / 虚拟内存设为「自动管理」或手动增大
- Close unnecessary background services via Task Manager / 通过任务管理器关闭非必要后台服务
- Set SW process priority to "High" / 将SW进程优先级设为「高」

### 4.3 In-Software Configuration | 软件内部配置

**Enable Lightweight Mode / 启用轻化模式：**
- System Options → Performance → "Load components lightweight" / 系统选项→性能→「以轻量化模式加载零部件」
- Large Assembly Mode: set auto-entry threshold (e.g. >500 parts) / 大型装配体模式：设置自动进入阈值（如>500个零件）

**Display Optimization / 显示优化：**
- Turn off RealView graphics / 关闭RealView图形
- Lower "Image Quality" slider / 降低"图像品质"滑块
- Turn off shadows and reflections / 关闭阴影和反射

**Large Assembly Specific / 大装配专项：**
- Use SpeedPak (load only outer surfaces) / 使用SpeedPak（只加载外表面）
- Sub-assembly grouping / 子装配体分组
- Freeze parts that don't need editing / 冻结不需要编辑的零部件

---

## Chapter 5: Pre-Modeling Planning | 第五章：建模前规划

### 5.1 Pre-Modeling Checklist | 零件建模前思考清单

| Question / 问题 | Decision / 决策 |
|---|---|
| What is this part's final use? / 这个零件最终要做什么用？ | Determines precision, material, surface treatment / 决定精度、材料、表面处理 |
| Are there symmetric features? / 有没有对称特征？ | Only model half → mirror / 只建一半再镜像 |
| Which dims might change later? / 哪些尺寸以后可能会改？ | Use global vars / equations / 用全局变量/方程式 |
| Should it be config-driven? / 要不要做成配置？ | Use config manager for similar parts / 相似零件用配置管理 |
| Which datum plane to use? / 基准面选哪个？ | Match drawing projection direction / 和工程图投影方向对上 |
| Need to reference other parts? / 要不要参考其他零件？ | Top-down design / 自顶向下设计 |

### 5.2 Modeling Strategy Selection | 建模策略选择

| Part Type / 零件类型 | Recommended Strategy / 推荐策略 |
|---|---|
| Shaft-type parts / 轴类零件 | Revolve + Pattern / 旋转 + 阵列 |
| Plate-type parts / 板类零件 | Extrude + Cut / 拉伸 + 切除 |
| Shell-type parts / 壳体零件 | Solid → Shell / 实体 → 抽壳 |
| Surface products / 曲面产品 | Surface → Thicken/Solidify / 曲面 → 加厚/实体化 |
| Tubes/wires / 管件/线材 | Sweep feature / 扫描特征 |
| Castings / 铸造件 | Base + Draft / 基体 + 拔模 |
| Plastic parts / 塑料件 | Main shell + Ribs / 主壳体 + 加强筋 |
| Sheet metal parts / 钣金件 | Sheet Metal module dedicated tools / 钣金模块专用工具 |

### 5.3 Feature Creation Golden Order | 特征创建黄金顺序

```
1. Base feature (Extrude/Revolve/Sweep/Loft)
   → 基体特征（拉/旋/扫/放）
2. Cut features / holes
   → 切除/孔特征
3. Fillet / Chamfer
   → 圆角/倒角
4. Cosmetic features
   → 装饰特征
5. Pattern / Mirror
   → 阵列/镜像
```

> ⛔ **Critical / 关键**: Fillets go LATER, not earlier!
> **圆角不要放前面！**

---

## Chapter 6: Sketch & Part Tips | 第六章：草图与零件技巧

### 6.1 Sketch Fully Defined Iron Rule | 草图完全定义铁律

- **Blue = can drag = DANGER** / 蓝色 = 能拖动 = 危险
- **Black = locked = SAFE** / 黑色 = 锁死 = 安全

### 6.2 Feature Error Quick Diagnosis | 特征报错速诊

| Error / 报错 | Cause / 原因 |
|---|---|
| Extrude "cannot generate" / 拉伸"无法生成" | Sketch crosses itself / not closed / 草图交叉/不封闭 |
| Fillet error / 圆角报错 | Radius > adjacent face size / 半径大于相邻面 |
| Shell failed / 抽壳失败 | Min fillet < wall thickness / 最小圆角 < 壁厚 |
| Loft twisted / 放样扭曲 | Each section has different point count / 各截面点数不一致 |
| Sweep deformed / 扫描变形 | Path curvature突变 / 路径曲率突变 |

---

## Chapter 7: Assembly Design | 第七章：装配体设计

1. **Bottom-up**: Model parts first, then assemble (parts independently editable) / 自底向上：先做零件再装配（零件独立可改）
2. **Top-down**: Model parts inside assembly (global linkage) / 自顶向下：装配体中建零件（整体联动）
3. **Hybrid**: Framework top-down + standard parts bottom-up / 混合策略：框架自上而下 + 标准件自下而上

**Mate Types / 配合类型**: Coincident (面贴面), Concentric (轴孔), Width (居中), Symmetric (镜像件)

**Large Assembly Optimization / 大装配优化**: Lightweight → Sub-assemblies → SpeedPak → Large Assembly Mode

---

## Chapter 8: Drawing Production | 第八章：工程图出图

### Dimension Order (GB Standard) | 标注顺序（国标）

```
Overall dims → Position dims → Form dims → Tolerances → Geometric tolerances → Surface roughness
总体尺寸 → 定位尺寸 → 定型尺寸 → 公差 → 形位公差 → 粗糙度
```

**❌ Forbidden / 禁止**: Closed dimension chains, duplicate dimensions, hidden line dims in true view.
封闭尺寸链、重复标注、真视图标隐藏线。

**Auto-dimensioning Tip / 自动化标注技巧**: Use `Model Items` to auto-extract design intent → smart dims → auto-arrange.
用「模型项目」自动提取设计意图 → 智能尺寸 → 自动排列。

---

## Chapter 9: Professional Modules Quick Reference | 第九章：专业模块速查

### Surface Design / 曲面设计
G0→G1→G2 continuity; check with zebra stripes; use solid if possible.
G0→G1→G2 连续性；斑马条纹检查；能做实体不碰曲面。

### Sheet Metal / 钣金设计
K-factor: Steel 0.44 / Stainless 0.35 / Aluminum 0.33 / Copper 0.35.
Min bend radius ≥ thickness; hole-to-bend distance ≥ 2T+R.
K因子：钢0.44 / 不锈钢0.35 / 铝0.33 / 铜0.35。最小折弯半径≥板厚；孔距折弯边≥2T+R。

### Weldment / 焊件设计
3D Sketch → Structural Member → Trim → Cut List; prefer ISO/DIN/GB standard profiles.
3D草图→结构构件→剪裁→切割清单；优先ISO/DIN/GB标准型材。

### Mold Design / 模具设计
Draft analysis → parting line → shut-off surfaces → core/cavity split.
拔模分析→分型线→关闭曲面→型腔分离。
Draft angles: ABS 1°-2° / PP 1.5°-3° / Aluminum die cast 2°-5°.
拔模角：ABS 1°-2° / PP 1.5°-3° / 铝压铸 2°-5°。

### Simulation (FEA) / 有限元分析
Simplification: remove cosmetic features → use symmetry → bolt connectors → welded joints.
简化原则：去装饰特征→对称一半→螺栓接头→焊接接合。
Safety factor > 1.5 (static load).
安全系数>1.5（静载）。

### Flow Simulation (CFD) / 流体分析
Internal flow → pressure drop + velocity distribution; External flow → drag coefficient; Conjugate heat → temperature field.
内流→压降+流速分布；外流→阻力系数；共轭传热→温度场。

---

## Chapter 10: Design Checklist | 第十章：设计检查清单

### Modeling / 建模
- [ ] All sketches fully defined / 所有草图完全定义
- [ ] No ⚠️ marked features / 无⚠️标记特征
- [ ] Material assigned / 材料已指定
- [ ] Param names valid (no spaces/special chars) / 参数命名合法（无空格/特殊符号）
- [ ] No circular references in equations / 方程式无循环引用
- [ ] Ctrl+Q rebuild after global var changes / 修改全局变量后已Ctrl+Q重建

### Assembly / 装配体
- [ ] No over-defined mates / 无过定义配合
- [ ] Interference check passed / 干涉检查通过
- [ ] Moving parts can move freely / 运动件可自由活动

### Drawing / 工程图
- [ ] Views complete, dims not missing / 视图完整、尺寸不缺
- [ ] No closed dimension chains / 无封闭尺寸链
- [ ] BOM matches model / BOM与模型一致

---

## Design Philosophy | 设计哲学

> **English:** "Think before you model. Parametric intent first, features second, code third."
> **中文：** "建模前先思考。参数化意图第一，特征第二，代码第三。"

**Cooperate with `solidworks-automation` skill:**
- `sw-designer` = **Design brain** (what & why) / 设计大脑（做什么&为什么）
- `solidworks-automation` = **Coding hands** (how) / 编码双手（怎么做）

---

## References | 参考资料

- GitHub: https://github.com/delancy827/solidworks-skills
- SW设计狮 IMA KB: ID 7361920738820041 (10 articles)
- SW教程合集 IMA KB: ID 7342555410738838 (45 resources)
- SolidWorks Official Help: https://help.solidworks.com
