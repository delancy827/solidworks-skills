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
