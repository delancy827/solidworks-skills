# SW自动化项目长期记忆

## C# 强类型架构规范（2026-05-31验证）

### 编译环境
- 编译器：`C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe`（仅C# 5）
- Interop路径：`E:\sw2024\SOLIDWORKS\api\redist\`
- 命令模板：`csc.exe /r:"sldworks.dll" /r:"swconst.dll" /out:xxx.exe xxx.cs`

### C# 5语法禁区
- ❌ `$"{var}"` 字符串插值 → ✅ `"" + var` 或 `string.Format()`
- ❌ 自动属性初始化 → ✅ 构造函数赋值
- ❌ Lambda表达式成员 → ✅ 普通方法

### API参数白名单（经反射探测确认）
| API | 参数数 | 验证状态 |
|-----|--------|----------|
| FeatureExtrusion2 | 23 | ✅ 通过 |
| FeatureExtrusion3 | 23 | ✅ 通过 |
| FeatureCut4 | 27 | ✅ 通过 |
| SelectByRay | 11 | ✅ 通过 |
| SelectByID2 | 9 | ✅ 通过 |
| CreateCornerRectangle | 6 | ✅ 通过 |
| CreateCircle | 6 | ✅ 通过 |

### SelectByRay 正确用法
```csharp
bool selectFace = swDoc.Extension.SelectByRay(
    0, 0, 0.2,      // 射线起点
    0, 0, -1,         // 射线方向
    0.1,               // 射线半径
    1,                  // TypeWanted = 1（swSelFACES）
    false,              // Append
    0,                  // Mark
    0                   // Option
);
```

### 权限铁律
- SW和EXE必须以**同一权限级别**运行
- 推荐：都普通权限（非管理员）
- 禁止：SW管理员 + EXE普通（COM连不上）

### 验证机制（防止假成功）
```csharp
// SW API返回值null不代表失败！
int before = swDoc.GetFeatureCount();
swDoc.ForceRebuild3(false);
int after = swDoc.GetFeatureCount();
if (after > before) { /* 实际成功 */ }
```

### 日志重定向（UAC必备）
```csharp
StreamWriter log = new StreamWriter("log.txt", false, Encoding.UTF8);
log.AutoFlush = true;
Console.SetOut(log);
```

### SW连接：Activator.CreateInstance（2026-05-31新增）
- ✅ 推荐：`Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"))`
- ❌ 不推荐：`Marshal.GetActiveObject`（权限隔离时假死）
- 铁律：SW和EXE同权限级别（都普通）
- 🔑 `swApp.Visible = true;` — 但**不要设** `UserControl = false`

### 面遍历算法（GetBodies2 — 2026-05-31突破）
```csharp
// 找 X 最小面 = 后端面
PartDoc partDoc = (PartDoc)swDoc;
object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
Body2 body = (Body2)bodies[0];
object[] faces = (object[])body.GetFaces();
foreach (Face2 face in faces) {
    double[] box = (double[])face.GetBox();
    if (box[0] < minX) { minX = box[0]; bestFace = face; }
}
// 选中: Entity ent = (Entity)face; ent.Select4(false, null);
```
- ⭐⭐⭐⭐⭐ 稳定（不依赖面名/射线），替代不可靠的 SelectByRay

### 双语基准面选择
```csharp
bool ok = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0,0,0, false, 0, null, 0);
if (!ok) ok = swDoc.Extension.SelectByID2("Front Plane", "PLANE", 0,0,0, false, 0, null, 0);
```

### 叉形接头（Clevis Joint）建模经验（2026-06-01攻克）

#### ⚠️ Interop DLL参数顺序陷阱（2026-06-01下午反射验证）
**FeatureExtrusion2真实签名**（反射确认）：
```
[Sd][Flip][Dir][T1][T2][D1][D2][Dchk1][Dchk2][Ddir1][Ddir2][Dang1][Dang2]
[OffsetRev1][OffsetRev2][TransSurf1][TransSurf2][Merge][UseFeatScope][UseAutoSelect]
[T0(StartType)][StartOffset][FlipStartOffset]
```
| 参数 | 文档位置 | 真实位置 | 说明 |
|------|----------|----------|------|
| Merge | 参数3 | **参数18** | 旧代码一直把Merge放在参数3，始终为false！ |
| StartType(T0) | 参数12 | **参数21** | Offset=1在此DLL不支持 |
| StartOffset | 参数13 | **参数22** | 不支持offset → 用InsertRefPlane代替 |

**FeatureCut4真实签名**（反射确认）：
```
[Sd=false才能工作!][Flip][Dir][T1][T2][D1][D2]...[NormalCut]...
[AssyScope][AutoSelComp][Propagate][T0][StartOffset][FlipStartOffset][Optimize]
```
- ⚠️ **Sd参数必须为false**，true会导致FeatureCut4完全失败

#### InsertRefPlane偏移基准面
- 签名：`InsertRefPlane(int FirstConstraint, double Dist, int, double, int, double)` — **旧版API**
- 约束值：`Distance=8`（枚举`swRefPlaneReferenceConstraints_e`，带**s**后缀）
- 用法：先SelectByID2选中前视基准面 → InsertRefPlane(8, 0.0125, 0,0,0,0) → 获取Feature.Name作为平面名
- 替代FeatureExtrusion2不支持StartOffset的问题

#### CreateArc vs Create3PointArc
- ⚠️ `CreateArc` 在此DLL中不工作（无论方向-1还是1）
- ✅ `Create3PointArc(x1,y1,z1, x2,y2,z2, x3,y3,z3)` — 三点圆弧可用

#### 上视基准面草图坐标方向
- ⚠️ 上视基准面草图Y正方向 = **模型Z负方向**
- 画U形槽Y坐标必须取负值：`CreateCornerRectangle(0.015, -0.0125, 0, 0.090, -0.0375, 0)`

#### 真实验证：GetBodies2替代GetFeatureCount
```csharp
// GetFeatureCount增长≠实体成功！（草图本身+1，废特征+1）
// 用GetBodies2做硬验证：
object[] bodies = partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
int solidCount = (bodies == null) ? 0 : bodies.Length;
```

- **关键发现**：`swEndCondThroughAll=1`（不是4！），所有FeatureCut4必须使用枚举值而非硬编码
- **铁律**：**放弃面选草图**，全部用系统基准面(Front/Top/Right)画绝对坐标草图
- R25圆头：Create3PointArc三点弧（起点(-0.045,0)、终点(-0.045,0.050)、中点(-0.070,0.025)）
- U形槽：上视基准面画矩形(Y负坐标!)，T1=1,T2=1双向贯穿
- Φ18通孔：前视基准面(0.075,0.025)，T1=1,T2=1
- ⚠️ `FeatureFillet3` 在此 Interop DLL 中不存在
- ⚠️ `SelectByRay` TypeWanted必须=1(swSelFACES)，=2是选边

### 编译命令（E: 盘 SW2024）
```bash
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe \
  /r:"E:/sw2024/SOLIDWORKS/api/redist/SolidWorks.Interop.sldworks.dll" \
  /r:"E:/sw2024/SOLIDWORKS/api/redist/SolidWorks.Interop.swconst.dll" \
  /out:Clevis_Joint.exe Clevis_Joint.cs
```

### 跨机验证新增铁律（2026-06-01 舍友电脑反馈）

#### CreateLine 闭合铁律
- ❌ 浮点坐标 → 微米级端点间隙 → 轮廓不闭合 → FeatureExtrusion2静默失败
- ✅ 全部坐标取整到整数mm → `mm(-50), mm(50)` 而非 `-0.05, 0.05`
- 优先使用 CreateCornerRectangle（天然闭合）

#### SaveAs 中文路径铁律
- SaveAs3 中文路径返回0静默失败，SaveAs不返回错误码但有效
- 通用安全保存：先试 SaveAs3，result=0 降级到 SaveAs

#### 图纸分析五步法
1. 识别底座基准面(Y=0)
2. 建立Y轴尺寸链
3. 建立X轴对称性
4. 交叉验算尺寸链
5. 生成坐标表 → 直接映射代码

铁律：生成代码前必须纸上推导尺寸链，严禁凭看图感觉写坐标

### 跨机验证新增铁律（2026-06-01 第二轮）

#### FeatureExtrusion2 Python COM 版本依赖
- SW 32.5.0 + pywin32 306 → FeatureExtrusion2 **23参数调用失败**
- 与 pywin32版本/SW Service Pack 有关，不能假设一定可用
- 策略：优先尝试，失败降级到 VBA宏

#### C#沙箱隔离
- WorkBuddy环境下，C# exe的 `Marshal.GetActiveObject("SldWorks.Application")` → MK_E_UNAVAILABLE
- 原因：C# 子进程不在sandbox安全上下文中，无法访问SW COM
- 仅非sandbox环境（本机直接运行）C# exe可用

#### Python→VBA混合架构（三级降级策略）
- Tier 1: Python COM (简单操作：草图/选择/视图)
- Tier 2: Python→VBA宏注入 (复杂特征：FeatureCut4/FeatureExtrusion2/HoleWizard5)
- Tier 3: C# exe (非sandbox环境)

#### SelectByID2 ctx参数健壮性
- ctx 参数格式因SW/pywin32版本而异：None / () / tuple()
- 统一用 `[None, (), tuple()]` 三种格式回退

#### AI视觉验证
- 截图→AI多模态对比→差异矩阵，用于建模后标准验证
