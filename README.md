# 🔧 SolidWorks Skills — 自动化设计技能包

> **SolidWorks 自动化与设计技能包** — 让 AI Agent 真正学会用 SolidWorks 
> *Let AI Agent truly learn to use SolidWorks*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-2%20modules-orange.svg)](solidworks-automation/)
[![SolidWorks](https://img.shields.io/badge/SolidWorks-2024%2B-green.svg)](https://www.solidworks.com/)
[![Language](https://img.shields.io/badge/语言-中文/English-purple.svg)](.)
[![Contributions](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 📌 快速导航 | Quick Navigation

- [简单版介绍 | Simple Intro](#简单版介绍-simple-intro)
- [详细版介绍 | Detailed Intro](#详细版介绍-detailed-intro)
- [功能对比 | Feature Matrix](#功能对比-feature-matrix)
- [安装方法 | Installation](#安装方法-installation)
- [使用示例 | Usage Examples](#使用示例-usage-examples)
- [技术细节 | Technical Details](#技术细节-technical-details)
- [贡献指南 | Contributing](#贡献指南-contributing)
- [常见问题 | FAQ](#常见问题-faq)
- [更新日志 | Changelog](#更新日志-changelog)

---

## 简单版介绍 | Simple Intro

### 🇨🇳 中文

这是一个 **SolidWorks 技能包**，为 AI Agent 设计的 SolidWorks 自动化技能包。

**它能做什么？**
- 🤖 **自动化建模** — 用自然语言描述，AI 自动建 3D 模型
- 📐 **参数化设计** — 修改参数，模型自动更新
- 🔍 **设计审查** — AI 检查你的模型是否符合规范
- 📚 **知识库集成** — 内置 55+ 篇 SW 教程和设计指南

**适合谁？**
- 机械工程师 — 想用 AI 加速设计流程
- 学生 — 想学习 SolidWorks 最佳实践
- 开发者 — 想让 AI 帮你写建模脚本
- 研究者 — 想探索 AI + CAD 的可能性

**2 分钟上手：**
```bash
# 1. 克隆这个库
git clone https://github.com/delancy827/solidworks-skills.git

# 2. 安装到技能目录
cp -r solidworks-skills/solidworks-automation /path/to/skills/
cp -r solidworks-skills/sw-designer /path/to/skills/

# 3. 加载使用
"帮我建一个 M6 螺钉的 3D 模型"
```

---

### 🇺🇸 English

This is a **SolidWorks Skill Pack** designed for AI agents to automate SolidWorks.

**What can it do?**
- 🤖 **Automated Modeling** — Describe in natural language, AI builds 3D models
- 📐 **Parametric Design** — Change parameters, model updates automatically
- 🔍 **Design Review** — AI checks if your model follows best practices
- 📚 **Knowledge Base** — Built-in 55+ SW tutorials and design guides

**Who is it for?**
- Mechanical Engineers — Want to accelerate design with AI
- Students — Want to learn SolidWorks best practices
- Developers — Want AI to help write modeling scripts
- Researchers — Want to explore AI + CAD possibilities

**Get started in 2 minutes:**
```bash
# 1. Clone this repo
git clone https://github.com/delancy827/solidworks-skills.git

# 2. Copy skills
cp -r solidworks-skills/solidworks-automation /path/to/skills/
cp -r solidworks-skills/sw-designer /path/to/skills/

# 3. Load and use
"Build a 3D model of an M6 screw"
```

---

## 详细版介绍 | Detailed Intro

### 🇨🇳 中文详解

#### 🎯 项目背景

SolidWorks 是全球最流行的 3D CAD 软件之一，但它的 API 非常复杂：
- COM 接口有 1000+ 个方法
- Python 调用需要复杂的 VARIANT 包装
- 不同版本（2021/2024）API 参数数量不一样
- 官方文档混乱，网上教程质量参差不齐

**我们的解决方案：** 
把实战踩坑经验封装成 **AI Agent 技能包**，让 AI 真正学会用 SolidWorks，而不是靠猜。

#### 📦 技能包结构

```
solidworks-skills/
├── solidworks-automation/     # 自动化建模技能
│  ├── SKILL.md          # 技能主文档（11KB，超详细）
│  │  ├── SW 2024 API 完全指南
│  │  ├── Python COM 实战踩坑记录
│  │  ├── 参数化建模工作流
│  │  ├── 错误处理与调试技巧
│  │  └── 代码示例（4 个完整脚本）
│  └── examples/         # 可运行示例代码
│    ├── create_part.py     # 基础零件建模
│    ├── parametric_design.py  # 参数化设计
│    ├── batch_export.py     # 批量导出
│    └── advanced_features.py  # 高级特征建模
│
├── sw-designer/          # 设计指导技能
│  └── SKILL.md         # 设计指南（22KB，超详细）
│    ├── IMA 知识库集成（55 篇教程）
│    ├── 参数化设计原则
│    ├── 性能优化技巧
│    ├── 设计规范检查清单
│    └── 10 章完整设计流程
│
└── README.md           # 本文件
```

#### 🔥 核心功能

##### 1️⃣ solidworks-automation — 让 AI 会操作 SolidWorks

**已验证的 API 调用方法（SW 2024）：**
```python
# ✅ 正确：FeatureExtrusion2 需要 23 个参数（不是 17 个！）
doc.FeatureManager.FeatureExtrusion2(
  True, False, False, # Sd, Flip, Dir
  0, 0,        # T1, T2 (0=Blind)
  0.05, 0.0,     # D1, D2 (米为单位！)
  False, False,    # Dchk1, Dchk2
  False, False,    # Ddir1, Ddir2
  0.0, 0.0,     # Dang1, Dang2
  False, False,    # Ofr, Ofc
  False, False,    # Tf1, Tf2
  False,        # Merge
  False, False,    # UseFeatScope, UseAutoSelect
  0.0, False, False  # StartOffset, IsAutoStartOffset, FlipStartOffset
)

# ❌ 错误：SelectByID2 必须用 VARIANT 包装
# doc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0) # 会报错！
# ✅ 正确写法见 SKILL.md 第 127-156 行
```

**实战踩坑记录（这些都是花了一整天调试才发现的）：**
- SW 2024 的 `FeatureCut` 需要 20 个参数（不是 17 个）
- `FeatureCut3` 需要 26 个参数
- `FeatureCut4` 需要 27 个参数
- Python COM 调用 >12 个参数的方法会失败（COM 限制）
- 解决方案：**用加法建模代替减法建模**（详见 SKILL.md）

##### 2️⃣ sw-designer — 让 AI 懂设计原理

**集成的知识库：**
| 知识库名称 | 内容 | 篇数 |
|------------|------|------|
| SW设计狮 | 实战设计经验 | 10 篇 |
| SW教程合集 | 系统教程 | 45 个 |

**设计检查清单（AI 会自动提醒）：**
- ❓ 壁厚是否均匀？（避免翘曲变形）
- ❓ 圆角半径是否合理？（R=2~5mm 通用）
- ❓ 有没有倒角？（C0.5~1mm 保护棱边）
- ❓ 拉伸深度是否合适？（太深会导致加工困难）

#### 🎓 学习路径

**初学者（0-1 周）：**
1. 安装 Skill → 让 AI 帮你建一个简单零件（方块、圆柱）
2. 学习 SKILL.md 中的"API 基础"章节
3. 运行 `examples/create_part.py` 理解基本流程

**进阶（1-4 周）：**
1. 尝试参数化设计 → 修改 Excel 表格，模型自动更新
2. 学习"高级特征"章节（曲面、放样、扫描）
3. 让 AI 帮你优化现有模型（减面、加强筋、圆角优化）

**高级（1-3 月）：**
1. 批量处理 → 一次建模 100 个相似零件
2. 集成仿真 → 建模后自动跑有限元分析
3. 贡献代码 → 把你的踩坑经验提交到这个库

---

### 🇺🇸 English Details

#### 🎯 Project Background

SolidWorks is one of the world's most popular 3D CAD software, but its API is extremely complex:
- 1000+ COM interface methods
- Python calls require complex VARIANT wrapping
- Different versions (2021/2024) have different API parameter counts
- Official docs are messy, online tutorials vary in quality

**Our Solution:** 
Package real-world debugging experience into **AI Agent Skills**, letting AI truly learn SolidWorks instead of guessing.

#### 📦 Skill Pack Structure

```
solidworks-skills/
├── solidworks-automation/     # Automation skill
│  ├── SKILL.md          # Main doc (11KB, super detailed)
│  └── examples/         # Runnable examples
│
├── sw-designer/          # Design guidance skill
│  └── SKILL.md         # Design guide (22KB, super detailed)
│
└── README.md           # This file
```

#### 🔥 Core Features

**Verified API Calls (SW 2024):**
```python
# ✅ Correct: FeatureExtrusion2 needs 23 params (not 17!)
doc.FeatureManager.FeatureExtrusion2(
  True, False, False,
  0, 0,
  0.05, 0.0, # Units in METERS!
  # ... (20 more params, see SKILL.md)
)
```

**Real Debugging Notes (took days to figure out):**
- `FeatureCut` needs 20 params (not 17)
- Python COM fails for methods with >12 params (COM limitation)
- Solution: **Use additive modeling instead of subtraction** (see SKILL.md)

---

## 功能对比 | Feature Matrix

| 功能 | solidworks-automation | sw-designer |
|------|----------------------|-------------|
| 自动化建模 | ✅ Python COM 脚本 | ❌ 仅指导 |
| 参数化设计 | ✅ 完整工作流 | ✅ 设计原则 |
| 设计审查 | ⚠️ 有限支持 | ✅ 完整检查清单 |
| API 文档 | ✅ SW 2024 实测 | ❌ 不涉及 |
| 代码示例 | ✅ 4 个完整脚本 | ⚠️ 伪代码 |
| 知识库集成 | ❌ | ✅ 55 篇教程 |
| 适合场景 | 自动化任务 | 设计决策 |

**推荐用法：** 两个技能一起用！`solidworks-automation` 负责"做"，`sw-designer` 负责"检查"。

---

## 安装方法 | Installation

### 方法 1：直接复制（推荐）

```bash
# 克隆仓库
git clone https://github.com/delancy827/solidworks-skills.git
cd solidworks-skills

# 复制到 技能目录
cp -r solidworks-automation /path/to/skills/
cp -r sw-designer /path/to/skills/

# 重新加载
```

### 方法 2：作为 Git 子模块

```bash
cd /path/to/skills/
git submodule add https://github.com/delancy827/solidworks-skills.git
git submodule update --init --recursive
```

### 方法 3：手动下载 ZIP

1. 访问 https://github.com/delancy827/solidworks-skills
2. 点击绿色 "Code" 按钮 → "Download ZIP"
3. 解压后，把两个文件夹复制到 `/path/to/skills/`

---

## 使用示例 | Usage Examples

### 示例 1：自动化建模（简单零件）

**用户说：** 
> "帮我建一个 80x90x55mm 的长方体，材料是 10 钢"

**AI 执行（solidworks-automation 技能）：**
```python
import win32com.client
import pythoncom

sw = win32com.client.Dispatch("SldWorks.Application")
sw.Visible = True
doc = sw.NewDocument("C:\\ProgramData\\SolidWorks\\SOLIDWORKS 2024\\templates\\gb_part.prtdot", 0, 0, 0)

# 选择前视基准面
boolstatus = doc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0)

# 创建草图并拉伸
# ... (完整代码见 examples/create_part.py)
```

---

### 示例 2：参数化设计（修改尺寸）

**用户说：** 
> "把刚才的长方体宽度改成 100mm"

**AI 执行：**
```python
# 1. 读取现有尺寸
width = doc.Parameter("Width").Value

# 2. 修改尺寸
doc.Parameter("Width").Value = 0.1 # 米为单位

# 3. 重建模型
doc.EditRebuild3()
```

---

### 示例 3：设计审查（检查最佳实践）

**用户说：** 
> "检查这个模型有没有设计问题"

**AI 执行（sw-designer 技能）：**
```
✅ 壁厚检查：通过（2.5mm，均匀）
⚠️ 圆角检查：建议添加（棱边无圆角，应力集中风险）
❌ 倒角检查：缺失（所有孔口应加 C0.5 倒角）
📊 评分：75/100（建议优化后再出图）
```

---

## 技术细节 | Technical Details

### 系统要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| SolidWorks | 2021 | 2024 SP2+ |
| Python | 3.8 | 3.11+ |
| pywin32 | 228 | 300+ |
| Windows | 10 | 11 |
| RAM | 8GB | 16GB+ |

### API 兼容性说明

**⚠️ 重要：** SolidWorks API 在不同版本间有差异！

| API 方法 | 2021 参数数 | 2024 参数数 | 变化 |
|----------|--------------|--------------|------|
| FeatureExtrusion2 | 17 | 23 | ⚠️ 新增 6 个参数 |
| FeatureCut | 17 | 20 | ⚠️ 新增 3 个参数 |
| FeatureFillet3 | 5 | 5 | ✅ 无变化 |

**我们的技能包已针对 SW 2024 全面测试和优化。**

---

## 贡献指南 | Contributing

### 🌟 为什么需要你的参与？

SolidWorks 是一个庞大的软件，我们不可能覆盖所有功能。你的贡献可以让这个技能包变得更强大！

**特别需要：**
- 🐛 **踩坑记录** — 你遇到的 API 报错和解决方案
- 📝 **示例代码** — 你写的实用建模脚本
- 🌍 **多语言支持** — 把技能包翻译成你的语言
- 🧪 **测试用例** — 帮助我们发现 bug
- 📚 **教程链接** — 你认为有价值的 SW 学习资源

### 如何贡献

#### 1️⃣ 报告 Bug

[点击这里开 Issue](https://github.com/delancy827/solidworks-skills/issues/new?template=bug_report.md)

**请包含：**
- SolidWorks 版本号
- Python 版本号
- 完整的错误截图/日志
- 复现步骤

#### 2️⃣ 提交代码

```bash
# 1. Fork 这个仓库
# 2. 创建你的功能分支
git checkout -b feature/amazing-feature

# 3. 提交你的修改
git commit -m "Add: 支持 SW 2025 的新 API"

# 4. 推送到分支
git push origin feature/amazing-feature

# 5. 开一个 Pull Request
```

#### 3️⃣ 改进文档

即使是错别字、语法错误，我们也欢迎！

#### 4️⃣ 分享案例

把你用这个技能包完成的项目分享给我们，我们会加到 `examples/` 目录！

---

🙏 **希望大家一起来共同改进这个 skill！** 
无论是踩坑记录、代码示例、文档改进，还是新的想法，都欢迎提交。 
让我们一起把 AI + SolidWorks 的自动化做得更好！

---

## 常见问题 | FAQ

### ❓ 这个技能包免费吗？

✅ **完全免费**，MIT 开源协议。你可以：
- 用于个人项目
- 用于商业项目
- 修改并重新分发
- 用于教程/培训

只需要保留原作者信息即可。

---

### ❓ 我没有 SolidWorks 能用吗？

❌ **不能**。这个技能包是 **SolidWorks 的扩展**，需要你已经安装 SolidWorks。

**替代方案：**
- 下载 SolidWorks 学生版（如果你是在校生）
- 使用开源 CAD 软件（FreeCAD、OpenSCAD），我们可以做适配这些软件的新技能！

---

### ❓ AI 真的能学会 SolidWorks 吗？

✅ **能，但有限制。**

**AI 擅长：**
- 执行重复性任务（批量建模、导出）
- 根据参数生成模型
- 检查设计规范

**AI 不擅长：**
- 创造性设计（需要人类审美）
- 复杂曲面建模（需要经验）
- 异常处理（需要人工判断）

**最佳实践：** 让 AI 做"体力活"，你做"脑力活"。

---

### ❓ 如何获取技术支持？

- 📖 **先看文档** — SKILL.md 里有详细教程
- 🐛 **报告 Bug** — [开 Issue](https://github.com/delancy827/solidworks-skills/issues)
- 💬 **社区讨论** — [开 Discussion](https://github.com/delancy827/solidworks-skills/discussions)
- 📧 **邮件联系** — delancy827@example.com（示例邮箱）

---

## 更新日志 | Changelog

完整版本历史详见 [CHANGELOG.md](CHANGELOG.md)。

### v4.8.0 — 架构级升级：三大铁律 + W-A-R 闭环断言 (2026-06-02)

**核心突破：从"建议级约束"升级为"代码级约束"——AI 把自己当编译器而非聊天助手**

#### 🏗️ system_directives 区块（最高优先级）
- 🚨 **铁律 1：单例与窗口生命周期** — GetActiveObject 优先 / ActiveDoc 复用 / try...finally CloseDoc
- 🚨 **铁律 2：W-A-R 闭环断言** — Write(提取指纹)→Assert(重建+错误码)→Read(硬断言±1μm)
- 🚨 **铁律 3：反幻觉与异常熔断** — API 盲猜禁止 / dir() 实机探测 / 失败零容忍

#### 核心改进
- 彻底解决"多窗口泛滥"：强制复用 SW 实例和文档
- 彻底解决"假验证/假跑"：修改后必须 Read 回来比对，Assert 失败即熔断
- 彻底解决"API 脑补"：不确定的 API 必须 dir() 实机探测后才能用
- XML 标签格式：大模型 RLHF 训练对 `<system_directives>` 服从度远超 Markdown

### v4.5.0 — Python COM 底层陷阱 + 类封装架构 (2026-06-02)

**核心突破：三轮跨机验证踩坑 + Python COM 完全解码**

#### 🔴 Python COM 底层陷阱
- **SelectByID2 Callout = VDISPATCH** — 第8参数必须 `VARIANT(VT_DISPATCH, None)`，Python None 直接 TypeError
- **COM 属性/方法混淆** — GetTitle/GetFeatureCount 是属性；GetNextFeature/GetTypeName2 是方法
- **多 ProgID 回退连接** — `.32` → `.64` → `""` 三种回退确保连上 SW
- **try/finally 清理保证** — `CoUninitialize` 绝不泄漏

#### 🏗️ Python 类封装架构
- `BracketBuilder` 类封装模板（参数表驱动 + 边界框自验证）
- `VARIANTHelper` 统一包装器，消灭 VARIANT 地狱
- 步骤独立方法 + 返回值判断链路，脚本可维护性大幅提升

#### 🧪 三轮跨机验证成果
- **第一轮**：CreateLine 浮点坐标 → 强制整数 mm；SaveAs3 中文路径 → 降级 SaveAs
- **第二轮**：FeatureExtrusion2 版本依赖警告（pywin32 306 可能失败）；C# 沙箱隔离 → Python→VBA 混合架构
- **第三轮**：斜面建草图绝对禁止（6 版本全败）；双重嵌套纠错环（编译纠错 + 几何校验 + 视觉 QA）

---

### v4.1.0 — 叉形接头全自动建模通关 + 防假跑验证体系 (2026-05-31)

**核心突破：反射探测拆穿 DLL 参数陷阱 + GetBodies2 防假跑机制**

#### 🔬 Interop DLL 底层避坑
- 🚨 **Merge=参数18**（非文档的3号位！）— 旧代码一直false导致扁柄从未真正合并
- 🚨 **FeatureCut4 Sd必须为false** — true会导致切除完全不执行
- 🚨 **InsertRefPlane Distance=8**（枚举名带s后缀）— 替代FeatureExtrusion2不支持的StartOffset
- 🚨 **CreateArc不可用** → Create3PointArc替代
- 🚨 **上视基准面草图Y方向=模型Z负方向** → 坐标取负

#### 🛡️ 防假跑终极断言
- `GetFeatureCount()` 被空草图/错误特征绕过 → **GetBodies2实体计数硬验证**
- 双重验证模式：特征数增长 + 实体数量
- 4/4步骤全部通过（特征数增长+实体数恒定=1）

#### 📐 空间正交几何重构法
- 废弃面遍历 → 三大系统原生基准面绝对坐标
- 偏移基准面（InsertRefPlane）实现居中扁柄
- 90°正交：前视基准面(Z向) + 上视基准面(Y向) 双向贯穿

#### 📋 新增文件
- `Clevis_Joint.cs` — 叉形接头全自动建模（反射修正版）
- 完整技术沉淀：API参数白名单、DLL铁律5条、正交重构法

### v3.2.0 (2026-05-30)

**功能扩展**

- 新增模具设计 API（凸凹模/刃口/装配/工程图标注）
- 新增冲压模具知识（间隙/冲裁力/常见缺陷）
- 新增国标 GB 规范（IT14/粗糙度/模具标准）

### v3.1.0 / v2.1.0 (2026-05-30)

**中英双语 + 文档完善**

- 新增完整的中英双语支持
- 新增版本历史记录表
- 新增适用场景表（When to Use）
- SKILL.md 结构重组，更易阅读
- 添加更多代码示例
- 修正 API 参数数量错误
- 补充缺失的错误处理机制

---

## 致谢 | Acknowledgments

- **SolidWorks 官方文档** — 虽然很乱，但还是有参考价值的
- **pywin32 社区** — 让 Python 能调用 COM 接口
- **所有贡献者** — 你们让这个项目变得更好

---

## 许可证 | License

MIT License — 免费用于个人和商业项目。

详见 [LICENSE](LICENSE) 文件。

---

## 相关链接 | Related Links

- 🌐 **项目主页：** https://github.com/delancy827/solidworks-skills
- 📚 **SolidWorks 官方文档：** https://help.solidworks.com
- 💬 **讨论区：** https://github.com/delancy827/solidworks-skills/discussions

---

## 星星历史 | Star History

[![Star History Chart](https://api.star-history.com/svg?repos=delancy827/solidworks-skills&type=Date)](https://star-history.com/#delancy827/solidworks-skills&Date)

---

**🙏 如果你觉得这个技能包有用，请给个 Star！** 
*If you find this skill pack useful, please give it a Star!*

**🚀 让我们一起，把 AI + CAD 的边界推得更远！** 
*Let's push the boundaries of AI + CAD together!*

---

## ⚖️ 版权与免责声明 | Copyright & Disclaimer

### 版权 | Copyright

- **代码与文档**：© 2026 delancy827. 本技能包采用 [MIT License](LICENSE) 开源。
- **SolidWorks** 是 Dassault Systèmes 的注册商标，本项目与 Dassault Systèmes 无关。

### 免责声明 | Disclaimer

⚠️ **重要声明（请仔细阅读）：**

1. **本技能包按"原样"提供，不承担任何担保责任。** 
  The skill pack is provided "AS IS", without warranty of any kind.

2. **不保证适用于你的具体场景。** 
  使用者需自行测试、验证，后果自负。 
  Users must test and verify by themselves. Use at your own risk.

3. **不构成专业工程建议。** 
  本技能包生成的模型/代码仅供参考，不替代专业工程师判断。 
  Not a substitute for professional engineering judgment.

4. **SolidWorks API 调用可能导致文件损坏、数据丢失。** 
  使用前请**备份你的文件**！作者不对任何数据丢失负责。 
  Always **backup your files** before use!

5. **贡献者对其提交内容负责。** 
  如有侵权内容，请联系我们删除。 
  Contributors are responsible for their submissions.

6. **本技能包与 Dassault Systèmes 无关。** 
  我们不隶属于 SolidWorks 或其代理商。 
  This project is not affiliated with Dassault Systèmes.

---

**使用本技能包即表示你同意以上声明。** 
**By using this skill pack, you agree to the above disclaimer.**

如有问题，请联系：[delancy827@example.com](mailto:delancy827@example.com)
