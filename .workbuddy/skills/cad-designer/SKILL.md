---
name: cad-designer
description: CAD设计狮——融合四大IMA CAD知识库的专业设计指导skill。专注CAD制图规范(国标)、参数化设计、图层管理系统、标注标准、批量出图策略、性能优化、AI+CAD趋势与设计检查清单。cad-automation负责写代码画图，CAD设计狮负责告诉AI"怎么设计才对"。
category: engineering-cad
version: 1.0.0
author: Delancy
---

# CAD设计狮 — CAD 专业设计指导

本skill融合了四个IMA知识库的核心设计方法论：
- **CAD学习知识库**（308条，市政公路领域）— LISP自动化实战、工程绘图模板
- **AI+CAD**（78篇前沿）— AI辅助设计趋势、Text-to-CAD、LLM+CAD
- **CAD软件教程**（7份教程）— 制图规范、图层系统
- **AutoCAD知识库**（31份，CAD自学网/周站长）— 国产CAD兼容、最佳实践

> **配合使用**: `cad-automation` skill 负责写代码自动化画图，CAD设计狮负责告诉AI"怎么设计才对"。

---

## 第一章：CAD制图规范（国标）

### 1.1 图纸幅面 (GB/T 14689)

| 幅面 | 尺寸(mm) | 适用场景 |
|------|---------|----------|
| A0 | 841×1189 | 总图、大型工程 |
| A1 | 594×841 | 总平面、系统图 |
| A2 | 420×594 | 平面图、装配图 |
| A3 | 297×420 | 零件图（最常用） |
| A4 | 210×297 | 简单零件、明细表 |

**装订边**: A0-A3留25mm，A4留20mm；其余边距均为5-10mm。

### 1.2 比例选择 (GB/T 14690)

| 类型 | 推荐比例 |
|------|---------|
| 原值 | 1:1（优先选用） |
| 放大 | 2:1, 5:1, 10:1 |
| 缩小 | 1:2, 1:5, 1:10, 1:50, 1:100 |

**原则**: 优先1:1，必须在标题栏注明比例。

### 1.3 图线规定 (GB/T 17450)

| 线型 | 线宽 | 用途 |
|------|------|------|
| 粗实线 | 0.5-0.7mm | 可见轮廓 |
| 细实线 | 0.18-0.25mm | 尺寸线、剖面线 |
| 虚线 | 0.25-0.35mm | 不可见轮廓 |
| 点划线 | 0.25-0.35mm | 轴线、对称线 |
| 双点划线 | 0.25-0.35mm | 假想轮廓 |

**线宽比**: 粗:中:细 = 4:2:1

---

## 第二章：图层管理系统

### 2.1 图层命名规范

来自"AutoCAD知识库"和工程实战的最佳实践：

```
命名格式: 专业码_主组_次组_状态
示例:    A-WALL-PRIM-D  (建筑-墙体-承重-拆除)
         M-DUCT-SUPN-N  (暖通-风管-送风-新建)
         S-STRU-COLN-E  (结构-柱-混凝土-现有)
```

### 2.2 常用图层色号国标

| 图层 | 色号 | 线型 | 说明 |
|------|------|------|------|
| 粗实线(WALL) | 7(白/黑) | Continuous | 可见轮廓 |
| 细实线(DIM) | 1(红) | Continuous | 尺寸标注 |
| 中心线(CEN) | 2(黄) | CENTER/CENTER2 | 轴线/中心线 |
| 虚线(HID) | 3(绿) | HIDDEN/HIDDEN2 | 隐藏线 |
| 剖面线(HAT) | 4(青) | Continuous | 填充图案 |
| 文字(TXT) | 5(蓝) | Continuous | 文字注释 |
| 辅助线(AUX) | 8(灰) | Continuous | 构造线 |
| 图框(TB) | 7(白) | Continuous | 图框/标题栏 |

### 2.3 图层自动化管理最佳实践

```python
# 一键创建国标图层模板
def create_gb_layers(acad):
    layers_cfg = {
        "WALL":  (7, "Continuous"),
        "DIM":   (1, "Continuous"),
        "CEN":   (2, "CENTER"),
        "HID":   (3, "HIDDEN"),
        "HAT":   (4, "Continuous"),
        "TXT":   (5, "Continuous"),
        "AUX":   (8, "Continuous"),
        "TB":    (7, "Continuous"),
    }
    for name, (color, ltype) in layers_cfg.items():
        if name not in [l.Name for l in acad.doc.Layers]:
            layer = acad.doc.Layers.Add(name)
            layer.Color = color
            linetypes = [lt.Name for lt in acad.doc.Linetypes]
            if ltype in linetypes:
                layer.Linetype = ltype
```

### 2.4 图层管理铁律

1. **按对象类型分层**: 墙/门/窗 → 标注 → 文字 → 填充，绝不混层
2. **随层(ByLayer)**: 颜色、线型、线宽全部设为"随层"，禁止硬编码到对象
3. **0层禁忌**: 不在0层绘制任何内容，0层仅用于创建块定义
4. **Defpoints层**: 自动生成，不可删除，不在上面绘图
5. **图层状态保存**: 使用`_LAYERSTATE`保存/恢复图层状态快照

---

## 第三章：标注标准与技巧

### 3.1 标注顺序（国标）

```
总体尺寸 → 定位尺寸 → 定型尺寸 → 公差 → 形位公差 → 粗糙度 → 技术要求
```

**标注三不原则**:
- ❌ 不封闭尺寸链（至少留一个开口环）
- ❌ 不重复标注同一尺寸
- ❌ 不将尺寸标注在虚线上

### 3.2 文字字高规范

| 幅面 | 尺寸字高 | 标题字高 | 技术要求字高 |
|------|---------|---------|------------|
| A0/A1 | 5mm | 7mm | 5mm |
| A2/A3 | 3.5mm | 5mm | 3.5mm |
| A4 | 2.5mm | 3.5mm | 2.5mm |

### 3.3 公差标注

```
线性公差: 50±0.1       → 50%%p0.1
极限偏差: 50+0.05/-0.02 → 50%+0.05%%-0.02
基孔制:   φ50H7        → %%c50H7
基轴制:   φ50f6        → %%c50f6
```

### 3.4 形位公差符号速查

| 符号 | 名称 | 符号 | 名称 |
|------|------|------|------|
| — | 直线度 | ◎ | 同轴度 |
| □ | 平面度 | ≡ | 对称度 |
| ○ | 圆度 | ⊕ | 位置度 |
| ⌒ | 圆柱度 | ↗ | 圆跳动 |
| ⊥ | 垂直度 | ↗↗ | 全跳动 |
| ∥ | 平行度 | ∠ | 倾斜度 |

### 3.5 粗糙度标注

```
Ra 3.2  →  一般加工面（最常用）
Ra 6.3  →  粗加工面
Ra 1.6  →  精加工面
Ra 0.8  →  研磨面
```

---

## 第四章：块(BLOCK)设计规范

### 4.1 块命名规范

```
项目前缀_类别_名称_规格
示例: GB_BOLT_M16x50    (国标螺栓)
      PROJ_VALVE_GATE_DN100  (项目阀门)
      SYM_DOOR_SINGLE_900    (符号单开门)
```

### 4.2 块创建最佳实践

1. **0层建块**: 块内对象画在0层，颜色/线型设为随层(ByLayer)，插入后与当前图层匹配
2. **基点合理**: 图框→左下角，螺栓→头部中心，门→铰链中心
3. **属性>文字**: 图框标题栏用属性定义(ATT)，不要用普通文字
4. **动态块**: 对频繁变形的组件（门宽、螺栓长度）使用动态块参数

### 4.3 属性定义示例

```lisp
;; 创建带属性的标题栏块
(defun c:make_titleblock ()
  (setq blk (vla-add (vla-get-Blocks *doc*) (vlax-3d-point '(0 0)) "TB_A3"))
  ;; 添加矩形边框
  (vla-AddLightWeightPolyline blk ...)
  ;; 添加属性
  (vla-AddAttribute blk 5.0 acAttributeModeVerify
    "请输入图纸名称:" (vlax-3d-point '(100 270)) "DWG_NAME" "图纸名称")
  (vla-AddAttribute blk 3.5 acAttributeModeVerify
    "请输入比例:" (vlax-3d-point '(350 270)) "SCALE" "1:1")
)
```

---

## 第五章：模板系统 (DWT)

### 5.1 模板应包含

一个完整的DWT模板至少包含：

- [x] 所有标准图层及线型
- [x] 标注样式（GB_DIM_35 / GB_DIM_50）
- [x] 文字样式（STANDARD→仿宋, GB_ROMANS→Romans）
- [x] 页面设置（A3/A4打印配置）
- [x] 图框+标题栏块
- [x] 常用符号块（粗糙度、基准、剖切）
- [ ] 打印样式(.ctb)

### 5.2 模板加载API

```python
# Python方式加载模板
acad.app.Documents.Add("D:/Templates/GB_A3.dwt")
# 或
acad.doc.SendCommand('_NEW "D:/Templates/GB_A3.dwt"\n')
```

### 5.3 一键模板生成LISP

来自CAD学习知识库的实战思路——将重复的模板创建过程脚本化：

```lisp
(defun c:init_project (/ layers dims texts)
  ;; 创建图层
  (foreach lyr '("WALL" "DIM" "CEN" "HID" "TXT" "TB")
    (entmake (list '(0 . "LAYER") '(100 . "AcDbLayerTableRecord")
      (cons 2 lyr) '(70 . 0) '(62 . 7) '(6 . "Continuous")))
  )
  ;; 设置标注样式
  (command "_DIMSTYLE" "S" "GB_DIM" "_Y")
  ;; 加载图框
  (command "_INSERT" "TB_A3" "0,0" "1" "1" "0")
  (princ "\n项目初始化完成!")
)
```

---

## 第六章：打印与出图策略

### 6.1 打印配置

| 参数 | 推荐值 | 说明 |
|------|-------|------|
| 绘图仪 | DWG To PDF.pc3 | 最通用 |
| 图纸尺寸 | ISO A3 (420×297) | 按实际选择 |
| 打印比例 | 布满图纸/1:1 | 生产图纸用1:1 |
| 打印范围 | 窗口/范围 | 精确控制 |
| 打印样式表 | monochrome.ctb | 黑白打印 |
| 图形方向 | 横向/纵向 | 按图纸 |

### 6.2 批量打印

```python
def batch_print(folder, output_folder):
    """批量打印DWG到PDF"""
    import os
    from pyautocad import Autocad
    acad = Autocad(create_if_not_exists=True)
    for f in os.listdir(folder):
        if f.endswith('.dwg'):
            pdf = os.path.join(output_folder, f.replace('.dwg', '.pdf'))
            doc = acad.app.Documents.Open(os.path.join(folder, f))
            # 设置布局
            acad.doc.ActiveLayout.ConfigName = "DWG To PDF.pc3"
            # 打印到文件
            acad.doc.Plot.PlotToFile(pdf)
            doc.Close(False)  # 不保存
```

### 6.3 打印前检查清单

- [ ] 图层全部打开、解冻、解锁
- [ ] 所有文字使用系统字体（避免缺失）
- [ ] 标注文字大小符合图纸幅面
- [ ] 打印样式表正确（黑白→monochrome.ctb）
- [ ] 打印范围正确（窗口/范围）
- [ ] PDF预览确认无缺失

---

## 第七章：性能优化

### 7.1 CAD性能瓶颈

| 症状 | 原因 | 解决 |
|------|------|------|
| 打开慢 | 过多DGN线型/字体/注册程序 | PURGE清理+清理DGN |
| 操作卡 | 大量填充图案 | 关闭填充图层或简化图案 |
| 缩放卡 | 过多节点(样条/多段线) | 简化曲线精度 |
| 保存慢 | 过多未使用的图层/样式 | 定期PURGE |
| 崩溃 | 文件过大(>50MB) | 拆分为外部参照 |

### 7.2 优化命令

```
_PURGE All * N       → 清理所有未引用对象
_AUDIT Y             → 审计修复文件错误
_OVERKILL            → 删除重复/重叠对象
_-SCALELISTEDIT R Y  → 重置标注比例列表
_WBLOCK *            → 导出为纯净DWG
```

### 7.3 正则表达式清理LISP

CAD学习知识库中的实战工具——用正则批量处理文本标注：

```lisp
;; 批量清理文字中的多余空格
(defun c:clean_text (/ ss i en str new)
  (setq ss (ssget '((0 . "TEXT,MTEXT"))))
  (setq i 0)
  (repeat (sslength ss)
    (setq en (ssname ss i))
    (setq str (cdr (assoc 1 (entget en))))
    ;; 替换多个空格为单个
    (while (vl-string-search "  " str)
      (setq str (vl-string-subst " " "  " str)))
    ;; 去除首尾空格
    (setq str (vl-string-trim " " str))
    ;; 更新文字
    (vla-put-TextString (vlax-ename->vla-object en) str)
    (setq i (1+ i))
  )
  (princ "\n文字清理完成!")
)
```

---

## 第八章：AI+CAD工作流设计

### 8.1 AI在CAD中的三层角色

来自AI+CAD知识库的核心分析：

| 层级 | 功能 | 典型应用 |
|------|------|---------|
| **L1 特征识别** | AI看懂图纸 | Smart Blocks, 智能标注, 图元分类 |
| **L2 辅助生成** | AI辅助绘图 | Text-to-CAD, 参数推荐, 自动布局 |
| **L3 自主设计** | AI独立设计 | MecAgent, Omega, 装配体生成 |

### 8.2 AI辅助CAD工作流

```
[工程师意图] → [LLM解析] → [设计方案] → [代码生成] → [CAD执行] → [验证反馈]
     ↑                                                              |
     └──────────────── 迭代优化 ←───────────────────────────────────┘
```

**关键原则**: AI生成代码→人工审查→CAD执行→结果验证→修正提示→重新生成

### 8.3 常用AI+CAD工具矩阵

| 工具 | 能力 | 成熟度 |
|------|------|--------|
| CADAM | 自然语言→参数化3D模型 | ⭐⭐⭐ |
| Pointer-CAD | LLM→B-Rep实体 | ⭐⭐⭐⭐ |
| text-to-cad | 自然语言→可编辑CAD | ⭐⭐⭐ |
| Leo AI | 文本→零件+装配体 | ⭐⭐⭐ |
| MecAgent | 技术规格→CAD模型 | ⭐⭐⭐ |
| VideoCAD | 视频学习→CAD操作 | ⭐⭐ |
| WHUCAD | 开源CAD智能核心 | ⭐⭐⭐ |

### 8.4 提示词工程(CAD场景)

```
[角色] 你是一个AutoCAD自动化专家
[任务] 根据以下工程参数生成DWG图纸
[参数] 矩形: 500×300mm, 壁厚5mm, 圆角R10, 四角M6螺孔
[格式] 生成Python pyautocad代码
[约束] 图层: 轮廓→WALL层(白色), 中心线→CEN层(黄色), 标注→DIM层(红色)
[标注] 国标格式, 字高3.5mm, 标注样式GB_DIM
```

---

## 第九章：行业模板速查

### 9.1 机械制图

- **零件图**: 三视图+轴测图，含公差/粗糙度/形位公差
- **装配图**: 明细表+序号，标配合关系
- **四类图**: 轮廓图(WALL)→标注图(DIM)→中心线(CEN)→剖面图(HAT)

### 9.2 建筑制图

- **平面图**: 轴线→墙体→门窗→标注→文字
- **图层示例**: A-WALL / A-DOOR / A-WINDOW / A-DIM / A-TEXT
- **比例**: 平面1:100, 立面1:100, 详图1:20

### 9.3 市政/公路 (CAD学习知识库重点)

- **桩位图**: 轴线定位→桩位编号→坐标标注→桩表
- **道路纵横**: 桩号标注→坡度→高程→填挖方
- **管网**: 管径标注→流向→管底标高

### 9.4 电气制图

- **原理图**: 元件符号→连线→端子号
- **布局图**: 设备位置→线槽→标注
- **软件**: EPLAN(专用)或AutoCAD Electrical(含图库)

---

## 第十章：设计检查清单

### 10.1 图形内容

- [ ] 所有图层按规范创建和命名
- [ ] 对象颜色/线型/线宽均为"随层(ByLayer)"
- [ ] 0层无内容（仅用于块定义）
- [ ] 无多余图层、样式、块定义（PURGE清理）
- [ ] 所有块正确命名且基点合理

### 10.2 标注与文字

- [ ] 总体尺寸→定位尺寸→定型尺寸顺序正确
- [ ] 无封闭尺寸链
- [ ] 无重复标注
- [ ] 文字字高符合幅面要求
- [ ] 特殊符号正确(%%c, %%d, %%p)

### 10.3 打印出图

- [ ] 打印样式表正确(黑白打印=monochrome.ctb)
- [ ] 打印范围内含所有图形和图框
- [ ] 线宽比例正确（粗:中:细=4:2:1）
- [ ] Defpoints层已检查(该层不打印)
- [ ] PDF预览无误

### 10.4 文件管理

- [ ] 文件名格式: 项目号_图号_名称_版本.dwg
- [ ] 外部参照路径正确(相对路径优先)
- [ ] 字体文件与图形绑定或使用通用字体
- [ ] 图纸已AUDIT审计无错误
- [ ] 备份文件已生成(.bak/.sv$)

---

## 知识来源

| 知识库 | 内容 | 量 |
|--------|------|-----|
| CAD学习知识库 | LISP插件(坐标标注、桩位、土方、批量处理等工程自动化) | 308条 |
| AI+CAD | AI辅助设计趋势、Text-to-CAD、LLM+CAD、工业软件Agent化 | 78篇 |
| CAD软件教程 | 制图规范、图层系统、打印配置 | 7份 |
| AutoCAD知识库 | 国产CAD兼容、操作技巧、进阶教程 | 31份 |

**贡献者**: 市政公路领域、AI辅助产品设计、工作读书交流、CAD自学网(周站长)

---
**配合使用**: `cad-automation` skill — 本skill提供设计方法论，cad-automation提供代码实现。
