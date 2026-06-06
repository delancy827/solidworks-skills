# ⚠️ 已废弃文件 | Deprecated Files

本目录包含旧版本的技能文件，已不再维护。请使用主目录下的最新版本。

This directory contains outdated skill files that are no longer maintained. Please use the latest versions in the main directories.

## 文件对照表

| 本目录文件 | 版本 | 主目录文件 | 版本 | 说明 |
|------------|------|------------|------|------|
| `solidworks-automation.md` | v4.5.0 (C# 架构版) | `solidworks-automation/SKILL.md` | v5.1.1 | C# 架构路线已弃用，当前采用 Python+VBA 混合架构 |
| `sw-designer.md` | v2.6.0 | `sw-designer/SKILL.md` | v2.2.1 | 内容已合并到主版本 |

## 为什么废弃？

- `solidworks-automation.md` (v4.5.0) 采用 C# (.NET) 强类型早期绑定架构，但实际测试发现 Python COM + VBA 宏降级方案更灵活稳定
- 主版本 v5.1.1 包含 41 个 Section，覆盖完整的 SW 自动化知识体系，包括从 v4.5.0 迁移的所有有价值内容
- `sw-designer.md` (v2.6.0) 的增量内容已整合到 `sw-designer/SKILL.md` v2.2.1

## 如何使用

请直接使用主目录文件：
```bash
# 安装最新技能
cp -r solidworks-automation /path/to/skills/
cp -r sw-designer /path/to/skills/
```
