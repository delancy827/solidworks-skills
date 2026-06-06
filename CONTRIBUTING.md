# 贡献指南 | Contributing

感谢你对 SolidWorks Skills 项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 1. 报告 Bug

[开 Issue](https://github.com/delancy827/solidworks-skills/issues/new) 并包含：
- SolidWorks 版本号
- Python/pywin32 版本号
- 完整的错误日志/截图
- 复现步骤

### 2. 提交代码

```bash
# 1. Fork 仓库
# 2. 创建功能分支
git checkout -b feature/amazing-feature

# 3. 提交修改
git commit -m "Add: 描述你的修改"

# 4. 推送分支
git push origin feature/amazing-feature

# 5. 开 Pull Request
```

### 3. 贡献内容

我们特别需要：
- **踩坑记录** — SW API 报错和解决方案
- **示例代码** — 实用建模脚本
- **文档改进** — 包括错别字修正
- **测试用例** — 帮助发现 bug

### 4. 代码规范

- Python 脚本遵循 23 参数 `FeatureExtrusion2`/`FeatureExtrusion3` 签名（SW 2024）
- `SelectByID2` 第8参数必须用 `VARIANT(pythoncom.VT_DISPATCH, None)` 包装
- 连接方式：`GetActiveObject` 优先 + `Dispatch` 回退（详见 SKILL.md 铁律1）
- 所有脚本设置 `UserControl = True`，防止 Python 结束后 SW 被 GC 回收
- 使用 `pythoncom.CoInitialize()` / `CoUninitialize()` 管理 COM 生命周期
- C# 脚本使用 `try/catch` 包裹 COM 清理代码
- 关键操作后添加 W-A-R 断言（Write-Assert-Read，详见 SKILL.md 铁律2）

## 许可

贡献的代码将采用 MIT License 开源。
