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
- 步骤3 R25圆头：用闭合轮廓切除法（`CreateArc` + 3条 `CreateLine` 构成切除区）+ `CreateCircleByRadius` 打 Φ18 孔，一次 `FeatureCut4` 完成
- 步骤4 U形槽：`CreateCornerRectangle` 的 z1/z2 必须设为 0（2D草图），用 (x1,y1) (x2,y2) 定义矩形
- 步骤5 双侧 Φ18 通孔：前视基准面画两个圆，`FeatureCut4` ThroughAll
- ⚠️ 注意：此 Interop DLL 中 `FeatureFillet3` 不存在，不可用圆角API

### 编译命令（E: 盘 SW2024）
```bash
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe \
  /r:"E:/sw2024/SOLIDWORKS/api/redist/SolidWorks.Interop.sldworks.dll" \
  /r:"E:/sw2024/SOLIDWORKS/api/redist/SolidWorks.Interop.swconst.dll" \
  /out:Clevis_Joint.exe Clevis_Joint.cs
```
