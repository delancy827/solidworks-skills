# SolidWorks 二次开发核心突破与避坑铁律 v4.3.0

> 沉淀日期：2026-06-01
> 来源：Clevis_Joint 正交几何重构 + 双机跨机验证（本机 [SW安装路径] SW2024 + 跨机测试机 C:盘 SW2024 32.5.0）
> 原则：每条规则背后都有至少一次实机失败的血泪教训——任何人不得以"试试看"为由绕过。

---

## 一、启动与内存防护：多窗口泄露（下崽）与假死防御机制

### 1. 病灶

高频调试运行过程中，反复调用 `NewDocument` 极易在后台产生几十个 `零件*` 未保存文件：

```
零件1, 零件2, 零件3, ..., 零件47
```

后果：
- 内存被反复膨胀直至 SW 卡死
- COM 实例冲突导致 `GetActiveObject` 或 `Activator` 报 `MK_E_UNAVAILABLE`
- 后续建模操作在错误的文档上执行，产生不可预知的几何体

### 2. 技能固化

#### 启动即清理（首行代码）

在 C# 程序启动、连接到 `swApp` 后的**首行代码**，必须执行强制垃圾清理，关闭所有未保存的活动文档：

```csharp
// ===== 启动清理：关闭所有"下崽"文档 =====
while (swApp.GetDocumentCount() > 0)
{
    ModelDoc2 tempDoc = (ModelDoc2)swApp.ActiveDoc;
    if (tempDoc != null)
    {
        swApp.CloseDoc(tempDoc.GetTitle());
    }
    else { break; }
}
// ===== 清理完毕 =====
```

#### 熔断机制

在任何 `try-catch` 的异常退出点（`return` 前），必须显式关闭当前失败的文档，严禁在后台留下垃圾画布：

```csharp
static void Fail(string msg)
{
    Console.WriteLine("FAIL: " + msg);
    // ⚠️ 熔断：关闭当前文档，不留垃圾
    if (swDoc != null)
        swApp.CloseDoc(swDoc.GetTitle());
    log.Close();
    throw new Exception(msg);
}
```

---

## 二、几何自验证升级：基于 GetBodies2 的实体级防假跑机制

### 1. 病灶

传统的特征数比对（`GetFeatureCount`）极易被空草图/无效草图欺骗：

- 草图本身会被 SW 计入特征数 → `before=19, after=20` → 看起来"增加了一个特征"
- 但生成的却是废特征（如意图切除但实际创建了内部凸台）
- 导致代码生成失败但日志依然显示"全绿通过"

### 2. 技能固化

**必须彻底废弃单纯的特征数对比。** 在关键建模步骤后使用 `GetBodies2` 获取实体数组：

```csharp
// ✅ 实体级验证（防假跑）
static void VerifyBodies(int expected, string name)
{
    PartDoc partDoc = (PartDoc)swDoc;
    object[] bodies = (object[])partDoc.GetBodies2(
        (int)swBodyType_e.swSolidBody, false);
    int count = (bodies == null) ? 0 : bodies.Length;
    
    if (count != expected)
    {
        // 实体数不符 → 真失败，立刻熔断
        Console.WriteLine(string.Format(
            "FAIL: {0} 实体数预期{1} 实际{2}", name, expected, count));
        swApp.CloseDoc(swDoc.GetTitle());
        throw new Exception(name + " 验证失败");
    }
    Console.WriteLine(string.Format("✓ {0} 实体数={1} 通过", name, count));
}
```

### 3. 判定规则

| 场景 | 预期实体数 | 异常判定 |
|------|:---:|------|
| 第一步拉伸后 | 1 | 0=拉伸失败, >1=切碎了 |
| 后续切除后 | 1（单体零件） | 0=整个实体被切掉了, >1=切除变成了凸台 |
| 装配体 | N（零件数） | 变化=丢失或重复 |

---

## 三、空间正交重构规范：基准面投影与双向切除

### 1. 病灶

`SelectByRay` 射线选面法具有"盲人射击"的不确定性：

- 射线可能穿过多个面，选中的未必是目标面
- 面名在中文SW下不稳定（`Face<1>` vs `面<1>`）
- **更大陷阱**：选中面后，在其上新建草图采用的是该面自身的 2D 局部坐标系，极易导致绝对坐标与局部坐标混淆使草图悬空

### 2. 技能固化

#### 原则：放弃实体选面，全程系统基准面

在处理复杂正交特征（如 Clevis Joint 叉形接头）时：

1. **禁止** `SelectByRay` 选面
2. **禁止** 在实体面上新建草图
3. **强制** 全程直接选中原生的系统三大基准面（前视/上视/右视基准面）作为作图面
4. 利用世界绝对坐标（X/Y/Z）完美绘制闭合草图

```csharp
// ✅ 系统基准面选择（中英文兼容）
bool ok = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0,0,0, false, 0, null, 0);
if (!ok) ok = swDoc.Extension.SelectByID2("Front Plane", "PLANE", 0,0,0, false, 0, null, 0);
```

#### 终极切除方法：双向贯穿

调用 `FeatureCut4` 时，必须将终止条件设为 `swEndCondThroughAllBoth`（双向贯穿，值为 **1**），让切除实体从几何中心向两侧对穿轰炸，彻底屏蔽坐标偏置问题：

```csharp
Feature feat = swDoc.FeatureManager.FeatureCut4(
    false,   // Sd = false ← 必须！
    false,   // Flip
    false,   // Dir
    1,       // T1 = 1 = swEndCondThroughAllBoth
    1,       // T2 = 1 = swEndCondThroughAllBoth
    0, 0,    // D1, D2 (through-all 不需要深度值)
    false, false, false, false,  // Dchk1, Dchk2, Ddir1, Ddir2
    0, 0,    // Dang1, Dang2
    false, false, false, false,  // OffsetRev1, OffsetRev2, TransSurf1, TransSurf2
    false,   // NormalCut
    false,   // AssyScope
    false,   // AutoSelComp
    false,   // Propagate
    0, 0,    // T0, StartOffset
    false,   // FlipStartOffset
    false    // Optimize（27个参数完）
);
```

---

## 四、5 大 Interop DLL 隐藏地雷与平替方案

> ⚠️ 以下 5 条绝对不能再犯！每条都是实机反射验证过的硬性雷区。

---

### 💣 地雷 1：Merge 参数位错位

**现象**：拉伸的实体没有合并（Merge），零件变成多实体。
**根因**：`FeatureExtrusion2` 的合并实体（Merge）参数在 API 签名中是 **第 18 个参数**，绝对不是第 3 个！

```csharp
// ❌ 错误：Merge 放第3位 → 始终为 false
FeatureExtrusion2(Sd, Flip, false/* ← 这其实是Dir，不是Merge */, ...);

// ✅ 正确：FeatureExtrusion2 真实签名（反射确认）
// [Sd][Flip][Dir][T1][T2][D1][D2][Dchk1][Dchk2][Ddir1][Ddir2][Dang1][Dang2]
// [OffsetRev1][OffsetRev2][TransSurf1][TransSurf2]
// [Merge ← 第18个！][UseFeatScope][UseAutoSelect]
// [T0(StartType)][StartOffset][FlipStartOffset]
```

---

### 💣 地雷 2：StartOffset 废弃——用 InsertRefPlane 平替

**现象**：设置 `T0=1`（偏置起点）后调用致死性错误。
**根因**：当前 Interop 动态库不支持 `T0=1` 偏置起点。

**平替方案**：

```csharp
// ❌ 不可用
FeatureExtrusion2(..., T0=1, offset=0.0125, ...);

// ✅ 平替：先创建物理偏移基准面
swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0,0,0, false, 0, null, 0);
Feature refPlaneFeat = swDoc.FeatureManager.InsertRefPlane(
    8,          // Distance = swRefPlaneReferenceConstraints_Distance
    0.0125,     // 偏移距离(米)
    0, 0, 0, 0);
// 然后用 refPlaneFeat.Name 作为新基准面名来建草图
```

---

### 💣 地雷 3：FeatureCut4 的 Sd 参数必须为 false

**现象**：设置 `Sd=true` 后 FeatureCut4 **完全失败**（返回 null）。
**根因**：经反射验证，此 DLL 中的 FeatureCut4 不支持 `Sd=true` 的多向切除模式。

```csharp
// ❌ FeatureCut4(Sd=true, ...) → null
// ✅ FeatureCut4(Sd=false, ...) → 正常工作
```

---

### 💣 地雷 4：CreateArc 弧线失效——全面使用 Create3PointArc

**现象**：`CreateArc` 在 C# 下极不稳定，无论方向参数设为 -1 还是 1，弧线都可能不生成。
**根因**：当前 Interop DLL 版本下 `CreateArc` 的圆心+半径+起止角参数映射不可靠。

**平替方案**：

```csharp
// ❌ 不稳定
swDoc.SketchManager.CreateArc(cx, cy, cz, rx, ry, rz, dx, dy, dz, direction);

// ✅ 全面使用三点圆弧
swDoc.SketchManager.Create3PointArc(
    x1, y1, z1,  // 起点
    x2, y2, z2,  // 终点
    x3, y3, z3   // 弧上中点
);

// 实战：R25圆头
sketch.Create3PointArc(
    mm(-45), mm(0), 0,          // 起点
    mm(-45), mm(50), 0,         // 终点
    mm(-70), mm(25), 0          // 弧上中点（半径25mm）
);
```

---

### 💣 地雷 5：上视基准面坐标映射取负

**现象**：在上视基准面画的向下延伸特征，实际生成后方向不对。
**根因**：上视基准面（Top Plane）的 **Y 轴正方向**，在模型世界坐标系中对应的是 **Z 轴的负方向**。

```csharp
// ⚠️ 上视基准面草图坐标系 =/= 世界坐标系
// 上视 Y↑ = 世界 Z↓

// 任何向下延伸的几何尺寸必须在代数上取负值
// ✅ CreateCornerRectangle(0.015, -0.0125, 0, 0.090, -0.0375, 0)
//                              ↑x1    ↑y1(取负!) ↑x2   ↑y2(取负!)
```

| 基准面 | 草图 X→ | 草图 Y→ | 世界映射 |
|--------|:------:|:------:|------|
| 前视 (Front) | 世界 X | 世界 Y | 正常（无翻转） |
| 上视 (Top) | 世界 X | 世界 Z | **Y 正向 = Z 负向（取负！）** |
| 右视 (Right) | 世界 Z | 世界 Y | 正常（无翻转） |

---

## 五、Python→VBA→C# 三级降级策略

> 来源：2026-06-01 双机跨机验证

| 级别 | 方案 | 适用场景 | 限制 |
|:---:|------|------|------|
| **Tier 1** | Python COM | 草图绘制、基准面选择、视图切换 | 多参数API不可用 |
| **Tier 2** | Python → VBA宏注入 | FeatureExtrusion2/FeatureCut4/HoleWizard5 | .swp文件格式需适配 |
| **Tier 3** | C# exe (非sandbox) | 全功能建模 | 需Interop DLL + 非sandbox环境 |

---

## 六、双重嵌套纠错环验证系统

> 内环编译纠错 + 外环几何视觉双重重测 → 自适应迭代直到通过。

### 内环：编译纠错（最大5轮）
C#源码 → csc.exe编译 → 失败则捕获stderr → AI重写 → 重编译。致命错误(CS0006 DLL缺失)立即停止。

### 外环-A：几何内核物理校验（无需看图）
| 维度 | API | 失败含义 |
|------|-----|------|
| 实体数 | GetBodies2 | 0=拉伸失败, >1=切除变凸台 |
| 包围盒 | BoundingBox | 尺寸偏差, 坐标错误 |
| 体积 | MassProperty | 未切穿, 多余材料 |

### 外环-B：多模态视觉 VLM 裁判
自动截图三标准视图（等轴测/前视/俯视）→ VLM审查 5项清单→ 输出 PASS/FAIL/MODIFY。

### 自适应迭代
- 几何PASS + 视觉PASS → ✅ 退出
- 任一FAIL → 合并偏差数据+VLM意见 → 修改源码 → 重入内环
- 最大迭代: 简单3轮/中等5轮/复杂8轮。同类型错误3次→熔断。

---

## 八、编译环境速查

| 项目 | 值 |
|------|-----|
| 编译器 | `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe` |
| C# 版本 | C# 5（无 `$` 插值，用 `string.Format`） |
| Interop DLL | `[SW安装路径]\SOLIDWORKS\api\redist\*.dll` |
| 编译命令 | `csc.exe /r:"sldworks.dll" /r:"swconst.dll" /out:xxx.exe xxx.cs` |

---

## 九、知识库更新记录

| 版本 | 日期 | 核心变更 |
|:---:|------|------|
| v4.3.0 | 2026-06-01 | 固化五大雷区、GetBodies2防假跑、三级降级策略、启动清理 |
| v4.2.0 | 2026-06-01 | CreateLine闭合警告、SaveAs中文路径、图纸分析工作流 |
| v4.1.0 | 2026-05-31 | C#强类型架构升级、FeatureCut4 27参数反射验证 |

---

✅ 技能库已固化更新，版本升级至 v4.3.0
