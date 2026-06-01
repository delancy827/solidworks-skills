# Changelog

## 2026-06-01（晚间：跨机验证 + 知识库固化 + 双环架构）

### solidworks-automation v4.2.0 → v4.4.0

#### 第一轮跨机验证反馈（舍友电脑SW2024中文版）

- 🚨 **CreateLine 闭合铁律**：浮点坐标→微米级端点间隙→轮廓不闭合，全部坐标取整到整数mm
- 🚨 **SaveAs中文路径**：SaveAs3中文路径返回0静默失败，降级SaveAs
- 📐 **图纸分析五步法**：基准面→尺寸链→交叉验算→坐标表→代码
- 📦 **Python VARIANT包装参考**：D2必须非零

#### 第二轮跨机验证反馈（舍友SW 32.5.0 + pywin32 306）

- 🚨 **FeatureExtrusion2 版本依赖警告**：pywin32 306下23参数调用失败，修正API表为"⚠️版本依赖"
- 🚨 **C#沙箱隔离发现**：WorkBuddy环境下C# exe无法Marshal.GetActiveObject(SW)
- ⭐ **Python→VBA混合架构**：绕过Python COM限制和C#沙箱隔离的关键路线
- 📸 **AI视觉QA验证工作流**：截图→多模态对比→差异矩阵
- 🔧 **SelectByID2 ctx多格式回退**：None/()/tuple()三种回退

#### Section 24：五大核心铁律速查
- 铁律0：启动清理（关闭孤儿文档）
- 铁律1：实体计数验证（废弃特征数）
- 铁律2：系统基准面绝对坐标
- 铁律3-7：五大Interop雷区速查表
- 铁律8：三级降级策略

#### Section 25：双重嵌套纠错环验证系统
- 内环：编译纠错（csc.exe → stderr → AI重写，最大5轮）
- 外环-A：几何内核物理校验（GetBodies2/包围盒/体积）
- 外环-B：多模态视觉VLM裁判（三视图截图→5项审查→PASS/FAIL/MODIFY）
- 自适应迭代优化（最大3-8轮，同类型错误3次→熔断）

#### Skill资产
- `scripts/visual_qa_capture.py`：四视图自动截图
- `scripts/sw_connect_info.py`：SW诊断工具
- `scripts/SW_VBA_Fix.py`：VBA宏注入参考模板
- `scripts/SW_Final_Fix.py`：FeatureExtrusion2完整参数示例

### sw-designer v2.3.0 → v2.5.0

#### 第十四章：正交几何设计六大铁律
- 设计环境净化原则、实体级验证取代特征数验证
- 基准面选择的设计决策、双向贯穿的设计意图
- 上视坐标Y↔Z翻转认知、设计-实现转换五雷区

#### 第十五章：双重嵌套纠错环—设计验证层级体系
- L1-L4四级信任层级（API返回值→特征数→物理测量→视觉QA）

### swskills.md（项目级知识库）
- 九大章节集中归档：五大雷区 + GetBodies2防假跑 + 三级降级 + 双环验证 + 编译环境速查

### 代码交付
- `Part1_Base.cs`, `Part2_Clevis.cs`, `Part3_Pin.cs`, `Pin_Shaft.cs`
- `swskills.md`（项目根目录，322行）

---

## 2026-06-01（下午：叉形接头全自动建模通关）

#### 下午突破：反射探测拆穿5个DLL参数陷阱 🔬

- 🚨 **Merge=参数18** — 实测FeatureExtrusion2的参数18才是Merge（非文档3号位），旧代码参数3=false焊接从未生效
- 🚨 **FeatureCut4 Sd必须为false** — 反射确认参数1=true时切除完全不执行
- 🚨 **InsertRefPlane Distance=8** — 枚举名`swRefPlaneReferenceConstraints_e`（带s），签名`(int,double,int,double,int,double)`旧版API
- 🚨 **CreateArc不可用** → `Create3PointArc` 三点圆弧替代
- 🚨 **上视基准面草图Y正方向=模型Z负方向** → 坐标必须取负值

#### 防假跑机制 🛡️

- `GetFeatureCount()` 被空草图/错误特征节点绕过 → **GetBodies2实体计数**做硬验证
- 双重验证：特征数增长 + 实体数量
- 4/4步骤全部通过，实体数恒定=1

#### 空间正交几何重构法 📐

- 废弃面遍历，全程三大系统基准面绝对坐标
- 偏移基准面(`InsertRefPlane(8,0.0125,...)`)替代不支持StartOffset
- 90°正交：前视(Z向) + 上视(Y向) 双向ThroughAll

#### 上午攻关（已完成）

- 闭合轮廓切除法：`CreateArc` + 多条 `CreateLine` 组合成闭合切除区，替代 `FeatureFillet3`（此 Interop 版本不存在）
- R25 圆头 + Φ18 通孔：一次 `FeatureCut4` 完成端部圆角+打孔
- U 形槽坐标修正：`CreateCornerRectangle` 的 z 参数必须为 0（2D草图约束）
- 双侧 Φ18 通孔：前视基准面画两个 `CreateCircleByRadius` 圆，`FeatureCut4` 贯穿切除
- 额外发现：`FeatureFillet3` 在 E: 盘 SW2024 Interop DLL 中不存在

## 2026-05-31

### solidworks-automation v4.1.0

**新增第二十章：C# 高级自动化架构升级**

- **进程与权限隔离**：`Activator.CreateInstance` 替代 `Marshal.GetActiveObject`，彻底解决 Windows UAC 权限错配导致连接假死的问题
- **中英文双语基准面选择**：`SelectByID2` 中文名 + 英文名兜底机制，兼容多语言 SW 环境
- **实体面遍历算法**：`GetBodies2` → `GetFaces` → `GetBox` 几何极值定位，替代不稳定的 `SelectByRay` 射线法，实现精准盲选定位
- **C# 5 语法规范**：确认系统 CSC 编译器（.NET 4.0）仅支持 C# 5，文档化全部禁区（字符串插值、自动属性初始化等）
- **FeatureExtrusion2 / FeatureCut4 精确签名**：经反射探测实机确认 23 / 27 参数，提供可编译的完整调用模板
- **叉形接头建模实战**：步骤1（叉部 90×50×50mm）+ 步骤2（柄部 70×50×25mm 居中）验证通过

### sw-designer v2.3.0

**新增第十三章：SW 自动化设计避坑指南**

- 叉形接头分段建模策略（四段式：叉部→柄部→圆头打孔→U形槽）
- 草图坐标系映射说明
- 面选择方案对比（SelectByID2 / SelectByRay / GetBodies2 遍历法）
- 尺寸居中公式与开发流程最佳实践

### 代码交付

- `Clevis_Joint.cs` — 叉形接头自动建模脚本（步骤1+2 通过）
- `Probe_Sig.cs` — API 签名反射探测工具

### 仓库维护

- 新增 `CHANGELOG.md`
- 隐私审查：移除硬编码用户路径，排除运行时日志

---

## 2026-05-31 (上午)

### solidworks-automation v3.4.0 → v4.0.0

- **架构升级**：Python win32com → C# (.NET) 强类型早期绑定
- **Stage1+2 验证通过**：`FeatureExtrusion2`（23参数）+ `FeatureCut4`（27参数）
- API 参数白名单：经反射探测确认 7 个常用 API 的精确参数数
- 新增 C# 编译命令模板与连接规范

### sw-designer v2.2.0 → v2.3.0

- 新增架构选择决策树（Python vs C#）
- 验证机制章节（防止 API 调用假成功）

---

## 初始版本

### solidworks-automation v3.1.0 → v3.2.0

- 新增模具设计API（凸凹模/刃口/装配/工程图标注）
- 新增冲压模具知识（间隙/冲裁力/缺陷）
- 新增国标 GB 规范（IT14/粗糙度）
- 双语中英文 README

### v3.1.0 / v2.1.0

- 双语 CN/EN、版本历史、场景表

### 初始提交

- solidworks-automation 和 sw-designer 技能创建
