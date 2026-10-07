# COM 双接口怪癖实战手册（SolidWorks 2024 SP5 单机实证）

> 来源：2026-10-07 一次完整的「图纸 → 三零件 → 装配体」自动化实战（支座+连杆×2+销轴×2，
> 两级135°肘节，9/9 配合自动添加成功，三零件体积与理论值偏差 0.000%）。
> 全部结论在 **同一台机器**（Windows 11 x64，中文版 SW 2024 SP5 32.5.0，Python 3.14 + pywin32）上实证。
> 其它版本号/语言版本行为可能不同，但排查思路通用。

## 0. 总原则

- **动态 IDispatch 不可信**：大量成员报 `找不到成员 (-2147352573)`。用 makepy 生成
  类型库包装（`sldworks.tlb` → `sldworks_gen.py`）做**早绑定**，行为立刻稳定。
- 但早绑定也不是银弹：**带 byref 出参的方法**（`OpenDoc6`、`Extension.SaveAs`、
  `ToolsCheckInterference2` 等）在早绑定下会炸 `int() argument must be ...`，
  这类必须**回退动态 CDispatch** 调用。两者并存、按方法选用。
- **属性/方法在同一对象上不稳定**：`GetFeatureCount`、`GetTitle`、`RevisionNumber`、
  `Volume` 等在动态层是属性、在 tlb 层是方法（或相反）。一律写自适应助手：

```python
def pm(obj, name, *args):
    val = getattr(obj, name)
    return val(*args) if callable(val) else val
```

- **接口归属必须查 tlb**，凭记忆会翻车（本机实证）：
  | API | 真实宿主 |
  |---|---|
  | `GetPartBox` | `IPartDoc`（不是 IModelDoc2） |
  | `GetBodies2` | `IPartDoc` / `IComponent2` |
  | `GetBox` | `IAssemblyDoc` / IBody2 |
  | `AddComponent5` / `AddMate3` / `GetComponentCount` | `IAssemblyDoc` |
  | `CreateArc2` / `InsertAxis2` | `IModelDoc2`（SketchManager 上没有！） |
  | `GetMathUtility` | `ISldWorks` |
  | `Volume` | `IMassProperty` propget（`Extension.CreateMassProperty()` 获得） |

## 1. 草图：圆弧必须走 IModelDoc2.CreateArc2

- `ISketchManager.Create3PointArc(起, 中, 弧上)` 画出的弧**端点不与相邻线段合并**
  → 轮廓不闭合 → `FeatureExtrusion2` 静默返回 `None`（无任何报错！）。且合并约束
  `SketchAddConstraints("sgMERGEPOINTS")` 也救不回来。
- **唯一可靠姿势**：`IModelDoc2.CreateArc2(圆心, 起点, 终点, 方向)`（SketchManager 上
  没有它；`CreateArc` 是 4 参数数组版，`CreateTangentArc` 只有 6 参数，别背错签名）。
- **铁律：弧先画，线后画**。CreateArc2 的端点只向"先存在的点"合并；
  先线后弧同样轮廓不闭合。实测：同一条眼板轮廓，弧先画 → 拉伸成功；线先画 → None。
- 圆弧方向参数（1=逆时针）在部分场景被忽略，180° 半圆恒走逆时针一侧——
  用"半圆盘对拼"实验实测凸向，别猜。

## 2. FeatureExtrusion2 第 21 参是 T0 枚举，不是偏移量

tlb 真实签名（23 参）：
`FeatureExtrusion2(Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2, Dang1, Dang2,
OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2, Merge, UseFeatScope,
UseAutoSelect, **T0, StartOffset, FlipStartOffset**)`

- T0 = 起始条件枚举（`swStartConditions_e`）：0=草图面（默认），**3=swStartOffset**。
- 把偏移距离误传进 T0（如 0.0125）会被**静默截断为 0** → 偏移无效、特征照常创建
  （本机曾因此把耳板拉进已有材料，体积差出一整块耳板）。
- 本机 **Flip 参数在偏移模式下无效**（翻向被忽略）。要做"反方向偏移拉伸"，
  用**负偏移**：`StartOffset=-0.030, D1=0.0175` → 实体落在 [-30, -12.5]mm ✓。

## 3. 偏移基准面替代方案（零参考面建模法）

不要建参考基准面，全部用"起始面偏移"实现远离草图面的凸台：
- +侧：`T0=3, StartOffset=+12.5mm, D1=17.5mm`
- −侧：`T0=3, StartOffset=-30mm,  D1=17.5mm`（负偏移，不用 Flip）
- 孔一律用**外环+内环多轮廓一次拉伸**（如耳板轮廓+Ø18 内圆），零切除特征。
  注意内环必须严格在外环内部（孔圆超出边界 = 非法轮廓 = None）。

## 4. 装配

### 4.1 AddComponent5 的前置条件：零件必须先在内存里

零件文件**未打开**时 `AddComponent5` **静默失败**（返回 None、组件数 0，中文/英文路径无关，
ConfigOption 组合无关）。正确顺序：

```python
sw.OpenDoc6(part_path, 1, 0, "", errs, warns)   # 先打开
asm.AddComponent5(part_path, 0, "", False, "", x, y, z)  # 再插入 → count=1 ✓
```

### 4.2 摆位：IMathUtility.ComposeTransform 的向量是"列"

`ComposeTransform(XVec, YVec, ZVec, TransVec, Scale)` 的 X/Y/Z 是旋转矩阵的**三列**
（= 局部轴在全局坐标的像），不是行！传错会得到转置旋转（绕同轴反角），bbox 一看便知。
向量参数要传 **IMathVector 对象**（`mu.CreateVector(VT_ARRAY|VT_R8 数组)`），不是裸数组；
裸数组传进去会被静默错拆（16 元数组里的平移跑到天边）。

```python
mu = sw.GetMathUtility()
V8 = lambda l: VARIANT(VT_ARRAY | VT_R8, [float(x) for x in l])
vec = lambda l: mu.CreateVector(V8(l))
mt = mu.ComposeTransform(vec([c,-s,0]), vec([s,c,0]), vec([0,0,1]), vec([0, 0.115, 0]), 1.0)
comp.Transform2 = mt   # 然后必须 ForceRebuild3(False)
```

摆位后**用装配体 bbox 做位姿硬校验**（手算期望 bbox，逐项 ±2mm 断言）。
读回 `Transform2.ArrayData` 的布局是 `[R(9), T(3), 1,0,0,0]`（平移在下标 9..11），
与输入布局不同，别拿它直接做格式推断。

### 4.3 配合：IComponent2.FeatureByName + IFeature.Select2，绕开 SelectByID2

装配上下文里 `SelectByID2("前视基准面@支座-1", "PLANE", ...)` **返回 False 且选不中**
（本机实证，实例名、类型字符串 PLANE/AXIS/EXTPLANE/DATUMAXIS 全试过）。
可靠姿势——组件内按名取特征再选中：

```python
f = IComponent2.FeatureByName("基准轴1")   # 基准面/基准轴/原点都是特征
f.Select2(False, 0)                        # 第一实体
f2.Select2(True, 0)                        # 追加第二实体
asm.AddMate3(1, 0, False, 0,0,0,0,0,0,0,0, False)  # 1=同心；0=重合（12参签名）
```

装配体自身的基准面用动态特征树按名遍历（早绑定 IModelDoc2 没有 FeatureByName）。
命中选面（`SelectByID2("", "FACE", x,y,z, ...)`）在装配上下文**可用**，但返回值不可信，
要读 `SelectionManager.GetSelectedObjectCount2(-1)` 确认，并用
`GetSelectedObject6(cnt,-1).GetComponent().Name2` 验证归属组件。

本机实证 9/9 配合一次通过：3 个基准面重合（锁支座）+ 4 个基准轴同心 + 2 个销头端面重合。

### 4.4 零件内先建基准轴

建模时选中孔的圆柱面 → `IModelDoc2.InsertAxis2(True)`（**返回 bool 不是特征**！）
→ 新轴名靠动态遍历特征树找 `GetTypeName2 == "RefAxis"` 的最后一个。
这些轴就是装配同心配合的稳定命名实体。

## 5. 视图与截图

- `ShowNamedView2(名字, **视图ID**)`：第二个参数传 **-1 视图根本不切换**（截图三张一模一样
  的坑）。正确：等轴测=7、前视=1、上视=5、右视=4；中文版名字用 "*等轴测" "*前视" "*上视" "*右视"。
- 截图前必须 `sw.ActivateDoc3(装配体标题)`——`Extension.SaveAs(png)` 导出的是**活动窗口**
  文档，不是你手里引用的文档对象。本机曾把装配截图存成了最后打开的零件。
- PNG/BMP 导出：`doc.Extension.SaveAs(path, 0, 1, VARIANT(VT_DISPATCH,None), errs, warns)`
  （动态调用 + byref 出参 + ExportData 占位 null VARIANT，三者缺一不可）。

## 6. 杂项硬经验

- `GetPartBox(NoConversion)`：**True = 恒定 SI 米**；False 会跟随文档单位
  （不同文档单位不同 → 同一数值一会儿米一会儿毫米）。断言一律用 True。
- 体积：`doc.Extension.CreateMassProperty()` → `mp.Volume`（propget）。
  备选 `IPartDoc.GetBodies2(-1,True)` → `IBody2.Volume`。
- 干涉：`asm.ToolsCheckInterference2(0, None, False)` 返回 `(None, None)` = 未报告干涉。
- **窗口纪律**：每次 `NewDocument` 失败/脚本崩溃都会留窗。脚本必须
  「建完即存、存完即截、截完即关」（`sw.CloseDoc(title)`），全程最多 1~2 个窗口。
  残留窗用 `ActiveDoc` 循环 CloseDoc 清空。
- 早绑定包装生成：`makepy.main()` + tlb 文件路径（SW 装在非 C 盘时注册表里可能没登记
  typelib 版本，EnsureModule 会报"库没有注册"，直接拿 tlb 文件生成再 import 最稳）。
- 模板：`C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot` /
  `gb_assembly.asmdot`。

## 7. 排查套路（比结论更重要）

1. **报 None 先怀疑轮廓/几何合法性**，别怀疑 COM：单独画最小轮廓复现。
2. **变量隔离矩阵**：位置×轮廓×参数逐项开关，8 组对照一轮定位（本机定位弧合并问题只花了 8 次）。
3. **行为实验替代文档**：半圆盘对拼测弧向、平移校准测变换布局、bbox 测摆位——数值会骗人，
   几何实验不会。
4. **接口归属查 tlb**：`grep "def XXX" sldworks_gen.py` 再 `awk` 找所属 class，比全网搜快。
5. 体积/包围盒/特征树三重断言：体积查"材质多少"，bbox 查"在哪"，特征树查"留了什么垃圾"。
