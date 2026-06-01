---
name: cad-automation
description: CAD自动化绘图skill，内置完整的AutoCAD二次开发知识体系。支持通过Python(pyautocad/win32com)/AutoLISP/C#/VBA连接AutoCAD进行自动化绘图、编辑、图层管理、标注、块与属性、三维建模、批量处理、文件转换等。也涵盖国产中望CAD/浩辰CAD的兼容性。
category: engineering-cad
version: 1.1.0
author: Delancy
---

# CAD 自动化绘图 Skill（自包含版）

本skill内置了AutoCAD从入门到精通的全套自动化知识体系，融合了"CAD学习知识库"(308条LISP插件)、"AI+CAD"(78篇行业前沿)、"CAD软件教程"(7份教程)、"AutoCAD知识库"(31份资料，含国产CAD兼容)四大IMA知识库的核心内容。

## ⚠️ Python AutoCAD COM 关键踩坑

### 环境
- AutoCAD 2020+ (中文版), Python 3.10+ + pyautocad/pywin32, Windows 11

### 连接方式
| 方式 | 结果 |
|------|------|
| `pyautocad.Autocad(create_if_not_exists=True)` | ✅ 推荐，自动处理COM |
| `win32com.client.Dispatch("AutoCAD.Application")` | ✅ 底层连接 |
| `win32com.client.GetActiveObject("AutoCAD.Application")` | ✅ 连接已运行的实例 |
| `win32com.client.Dispatch("AutoCAD.Application.24")` | ✅ 指定版本(2021=24,2022=24.1,2023=24.2,2024=24.3) |

### 核心踩坑
1. **pyautocad 安全数组**: 坐标必须用 `APoint(x,y,z)` 包装
2. **COM对象生命周期**: `GetActiveObject`失败则需`Dispatch`
3. **单位**: AutoCAD内部使用绘图单位，默认公制mm
4. **中文命令**: 用 `acad.doc.SendCommand("_LINE ")` 带下划线前缀
5. **选择集**: `acad.doc.SelectionSets` 使用后必须`Delete()`，否则累积报错
6. **中望/浩辰兼容**: pyautocad同样支持(COM接口兼容)，但部分VLAX函数需要适配

---

## 一、AutoCAD 基础知识

### 1.1 AutoCAD 概述

AutoCAD是Autodesk公司开发的通用CAD软件，支持建筑、机械、电气、土木等领域。

### 1.2 坐标系

- **WCS (世界坐标系)**: 绝对坐标系，原点固定
- **UCS (用户坐标系)**: 可自定义原点和方向
- **极坐标**: `@距离<角度` (如 `@100<45`)
- **相对坐标**: `@x,y` (如 `@50,30`)

### 1.3 文件类型

| 类型 | 扩展名 | 说明 |
|------|--------|------|
| 图形文件 | .dwg | 标准图形文件 |
| 交换格式 | .dxf | 文本/二进制交换格式 |
| 模板 | .dwt | 含预设样式模板 |
| 标准 | .dws | 图层/标注/文字标准 |
| 脚本 | .scr | 批量命令脚本 |
| 线型 | .lin | 自定义线型定义 |
| 填充 | .pat | 自定义填充图案 |

### 1.4 常用API对象层次

```
AutoCAD.Application
├── ActiveDocument (Document)
│   ├── ModelSpace        (模型空间)
│   ├── PaperSpace        (图纸空间)
│   ├── Layers            (图层集合)
│   ├── Linetypes         (线型集合)
│   ├── TextStyles        (文字样式)
│   ├── DimStyles         (标注样式)
│   ├── Blocks            (块集合)
│   ├── SelectionSets     (选择集)
│   ├── Groups            (组集合)
│   └── Utility           (角度/距离/坐标工具)
├── Documents
├── Preferences           (系统配置)
└── MenuGroups            (菜单组)
```

---

## 二、绘图命令 (Drawing)

### 2.1 基本图元

```python
from pyautocad import Autocad, APoint, aDouble
acad = Autocad(create_if_not_exists=True)

# 直线
line = acad.model.AddLine(APoint(0,0,0), APoint(100,50,0))

# 圆
circle = acad.model.AddCircle(APoint(50,50,0), 30)

# 圆弧 (center, radius, start_angle弧度, end_angle弧度)
arc = acad.model.AddArc(APoint(50,50,0), 30, 0, 3.14159)

# 轻量多段线 (2D, 推荐)
pts = aDouble(0,0, 100,0, 100,50, 50,50)  # x,y交替
pline = acad.model.AddLightWeightPolyline(pts)
pline.Closed = True
pline.Color = 1  # 红色

# 椭圆
ellipse = acad.model.AddEllipse(APoint(50,50,0), APoint(30,0,0), 0.5)

# 样条曲线
fit_pts = aDouble(0,0,0, 20,30,0, 50,10,0, 80,60,0, 100,0,0)
spline = acad.model.AddSpline(fit_pts, aDouble(1,1,0), aDouble(1,0,0))

# 文字
text = acad.model.AddText("设计说明", APoint(10,10,0), 5)
mtext = acad.model.AddMText(APoint(10,10,0), 50, "多行\\P文字")

# 点
point = acad.model.AddPoint(APoint(50,50,0))
```

### 2.2 填充 (Hatch)

```python
outer_loop = [pline]
hatch = acad.model.AddHatch(0, "ANSI31", True)
hatch.AppendOuterLoop(outer_loop)
hatch.Evaluate()
hatch.PatternScale = 2.0
hatch.PatternAngle = 0.785  # 45°
hatch.Color = 3
```

### 2.3 SendCommand 方式 (兼容性最好)

```python
acad.doc.SendCommand("_CIRCLE 50,50 30 ")
acad.doc.SendCommand("_LINE 0,0 100,50 \n")
# \n = 回车, 空格 = 结束当前输入
```

---

## 三、编辑命令 (Modify)

### 3.1 基本编辑

```python
# 移动
obj.Move(APoint(0,0,0), APoint(50,0,0))

# 复制
new_obj = obj.Copy()
new_obj.Move(APoint(0,0,0), APoint(100,0,0))

# 旋转 (基点, 角度弧度)
obj.Rotate(APoint(0,0,0), 1.5708)  # 90°

# 缩放 (基点, 比例因子)
obj.ScaleEntity(APoint(0,0,0), 2.0)

# 镜像 (镜像线两点)
obj.Mirror(APoint(0,0,0), APoint(0,100,0))

# 偏移
obj.Offset(10)  # 返回数组(可能多个结果)

# 阵列 (矩形)
obj.ArrayRectangular(3, 2, 1, 100, 50, 0)  # rows,cols,levels,row_sp,col_sp,level_sp
```

### 3.2 通过SendCommand操作

```python
acad.doc.SendCommand("_MOVE\n")       # 移动
acad.doc.SendCommand("_COPY\n")       # 复制
acad.doc.SendCommand("_ROTATE\n")     # 旋转
acad.doc.SendCommand("_SCALE\n")      # 缩放
acad.doc.SendCommand("_MIRROR\n")     # 镜像
acad.doc.SendCommand("_OFFSET 10\n")  # 偏移
acad.doc.SendCommand("_TRIM\n")       # 修剪
acad.doc.SendCommand("_EXTEND\n")     # 延伸
acad.doc.SendCommand("_FILLET R 5\n_FILLET\n")  # 圆角R5
acad.doc.SendCommand("_CHAMFER D 3 3\n_CHAMFER\n") # 倒角3x3
```

---

## 四、图层管理 (Layers)

```python
# 创建图层
layer = acad.doc.Layers.Add("WALL")
layer.Color = 1     # 红色 (ACI色号)
layer.Linetype = "Continuous"

# 设置当前图层
acad.doc.ActiveLayer = acad.doc.Layers("WALL")

# 遍历所有图层
for layer in acad.doc.Layers:
    print(f"{layer.Name}: color={layer.Color}, linetype={layer.Linetype}")

# 锁定/冻结/关闭
ref = acad.doc.Layers("WALL")
ref.Lock = True       # 锁定
ref.Freeze = False    # 冻结
ref.LayerOn = True    # 开关

# 修改对象图层
line.Layer = "DIM"

# 批量修改图层 (SendCommand)
acad.doc.SendCommand("_LAYMCH\n")       # 图层匹配
acad.doc.SendCommand("_LAYISO\n")       # 图层隔离
acad.doc.SendCommand("_LAYUNISO\n")     # 取消隔离
```

### ACI常用色号

| 色号 | 颜色 | 适用 |
|------|------|------|
| 1 | 红 | 标注/重点 |
| 2 | 黄 | 中心线 |
| 3 | 绿 | 辅助线 |
| 4 | 青 | 文字 |
| 5 | 蓝 | 轮廓 |
| 6 | 品红 | 剖面 |
| 7 | 白/黑 | 默认 |
| 8 | 灰 | 参考线 |

---

## 五、标注与文字 (Dimensions & Text)

### 5.1 标注

```python
p1 = APoint(0, 0, 0)
p2 = APoint(100, 0, 0)
text_pos = APoint(50, -20, 0)

# 线性标注
dim = acad.model.AddDimAligned(p1, p2, text_pos)

# 旋转标注
dim = acad.model.AddDimRotated(p1, p2, text_pos, 0)

# 半径/直径标注
dim_rad = acad.model.AddDimRadial(APoint(50,50,0), circle, 10)  # leader_length
dim_dia = acad.model.AddDimDiametric(APoint(50,50,0), circle, 10)

# 角度标注
dim_ang = acad.model.AddDimAngular(APoint(0,0,0), p1, p2, APoint(30,30,0))

# 坐标标注
dim_ord = acad.model.AddDimOrdinate(APoint(50,50,0), APoint(50,0,0), True) # X坐标

# 标注样式
dim_style = acad.doc.DimStyles.Add("GB_DIM")
dim.TextHeight = 3.5    # 字高
dim.ArrowheadSize = 2.5 # 箭头大小
dim.DecimalSeparator = "."
```

### 5.2 公差与粗糙度

```python
# 公差标注(通过SendCommand兼容性好)
acad.doc.SendCommand("_TOLERANCE\n")
# 或使用Leader+文字模拟
leader = acad.model.AddLeader(points, annotation, 0)
```

### 5.3 特殊字符

| 代码 | 字符 |
|------|------|
| %%c | φ 直径 |
| %%d | ° 度 |
| %%p | ± 正负号 |
| %%u | 下划线开关 |
| \\P | 换行(MTEXT) |

---

## 六、块与属性 (Blocks & Attributes)

### 6.1 块定义

```python
# 创建块定义
block = acad.doc.Blocks.Add(APoint(0,0,0), "MyBlock")
# 在块定义中添加对象
block.AddCircle(APoint(0,0,0), 10)
block.AddLine(APoint(-10,0,0), APoint(10,0,0))

# 插入块参照
insert_pt = APoint(50, 50, 0)
block_ref = acad.model.InsertBlock(insert_pt, "MyBlock", 1, 1, 1, 0)
```

### 6.2 带属性的块

```python
# 创建属性定义
att = block.AddAttribute(
    5,              # 字高
    0,              # 模式(0=无)
    "标签",         # 提示
    APoint(0,15,0), # 插入点
    "TAG",          # 标签
    "默认值"         # 默认值
)

# 插入后修改属性
for att in block_ref.GetAttributes():
    if att.TagString == "TAG":
        att.TextString = "零件-001"
        att.Update()
```

### 6.3 外部参照 (Xref)

```python
# 附着外部参照
xref = acad.model.AttachExternalReference(
    "D:/ref/base.dwg",  # 文件路径
    "base",              # 块名
    APoint(0,0,0),       # 插入点
    1, 1, 1, 0           # 比例和旋转
)
```

---

## 七、选择集与过滤

```python
# 创建选择集
ss = acad.doc.SelectionSets.Add("SS1")

# 全选
ss.Select(5)  # acSelectionSetAll

# 窗口选择
ss.Select(0, APoint(0,0,0), APoint(100,100,0))  # acSelectionSetWindow

# 过滤选择 (所有圆,半径>10)
import win32com.client
ft = win32com.client.VARIANT(0, [0, "CIRCLE", 40, 10.0])  # DXF组码过滤
fd = win32com.client.VARIANT(0, [0, ">="])
ss.Select(5, 0, 0, ft, fd)

# 遍历选择集
for obj in ss:
    print(f"对象类型: {obj.ObjectName}, 图层: {obj.Layer}")

# 删除选择集
ss.Delete()
```

### DXF组码常用过滤

| 组码 | 含义 | 示例 |
|------|------|------|
| 0 | 对象类型 | "CIRCLE","LINE","TEXT" |
| 8 | 图层名 | "WALL","DIM" |
| 62 | 颜色 | 1(红), 2(黄) |
| 40 | 半径(圆)/字高(文字) | 10.0 |
| 10 | 中心点/插入点 | 坐标 |

---

## 八、三维建模 (3D Modeling)

### 8.1 基本3D实体

```python
# 长方体
box = acad.model.AddBox(APoint(0,0,0), 100, 50, 30)  # 角点,长,宽,高

# 圆柱体
cyl = acad.model.AddCylinder(APoint(50,50,0), 20, 100)  # 底面中心,半径,高

# 球体
sphere = acad.model.AddSphere(APoint(50,50,30), 25)

# 圆锥体
cone = acad.model.AddCone(APoint(50,50,0), 15, 50)

# 圆环体
torus = acad.model.AddTorus(APoint(50,50,0), 30, 10)  # 中心,大半径,管半径
```

### 8.2 拉伸与旋转

```python
# 创建面域
regions = acad.model.AddRegion([pline])[0]

# 拉伸面域成实体
height = 50
taper_angle = 0  # 拔模角度(弧度)
solid = acad.model.AddExtrudedSolid(regions, height, taper_angle)

# 旋转面域成实体
solid = acad.model.AddRevolvedSolid(regions, APoint(0,0,0), APoint(0,0,100), 360)
```

### 8.3 布尔运算

```python
# 并集
solid1.Boolean(0, solid2)  # acUnion

# 差集
solid1.Boolean(1, solid2)  # acSubtraction

# 交集
solid1.Boolean(2, solid2)  # acIntersection
```

### 8.4 SendCommand 3D

```python
acad.doc.SendCommand("_BOX\n0,0,0\nL\n100\n50\n30\n")
acad.doc.SendCommand("_CYLINDER\n50,50,0\n20\n100\n")
acad.doc.SendCommand("_SUBTRACT\n")  # 差集
acad.doc.SendCommand("_UNION\n")     # 并集
```

---

## 九、图纸空间与打印

### 9.1 布局操作

```python
# 获取布局列表
for layout in acad.doc.Layouts:
    print(f"布局: {layout.Name}")

# 创建新布局
acad.doc.Layouts.Add("A3_打印")

# 切换布局
acad.doc.ActiveLayout = acad.doc.Layouts("A3_打印")

# 创建视口
vp = acad.doc.PaperSpace.AddPViewport(
    APoint(10,10,0),  # 中心点
    200,              # 宽
    150               # 高
)
vp.Display(True)  # 显示视口内容
```

### 9.2 打印/导出PDF

```python
# 通过SendCommand
acad.doc.SendCommand("_PLOT\n")        # 打印
acad.doc.SendCommand("_EXPORTPDF\n")   # 导出PDF

# 通过API
plot_cfg = acad.doc.Plot  # ActivePlotConfiguration
plot_cfg.ConfigName = "DWG To PDF.pc3"
plot_cfg.PaperUnits = 1   # mm
plot_cfg.StandardScale = 0  # acScaleToFit
plot_cfg.PlotType = 4      # acExtents
acad.doc.Plot.PlotToFile("D:/output.pdf")
```

---

## 十、AutoLISP 自动化 (CAD知识库核心)

### 10.1 LISP基础

来自"CAD学习知识库"的308个插件揭示了LISP在工程领域的真实生产力。

```lisp
;; 基础结构
(defun c:命令名 (/ 局部变量1 局部变量2)
  (setq var1 value1)       ; 设置变量
  (setq ss (ssget))        ; 获取选择集
  (princ "\\n提示文字")    ; 命令行输出
  (princ)                  ; 静默退出
)

;; 选择集遍历
(defun c:changecolor (/ ss i en)
  (setq ss (ssget))
  (setq i 0)
  (repeat (sslength ss)
    (setq en (ssname ss i))
    (setq ed (entget en))
    (entmod (subst (cons 62 1) (assoc 62 ed) ed))  ; 改为红色
    (setq i (1+ i))
  )
)

;; 坐标标注 (from ZBBZ.lsp)
(defun c:zbbz ()
  ;; 创建标注图层
  (entmake (list '(0 . "LAYER") '(100 . "AcDbLayerTableRecord")
    '(2 . "UserDimCoors") '(70 . 0) '(62 . 7) '(6 . "Continuous")))
  ;; 设置当前图层
  (setvar "CLAYER" "UserDimCoors")
  ;; 获取点
  (while (setq pt (getpoint "\\n拾取标注点:"))
    (setq x (rtos (car pt) 2 3))
    (setq y (rtos (cadr pt) 2 3))
    (setq str (strcat "X=" x "\\PY=" y))
    (entmake (list '(0 . "MTEXT") (cons 1 str) (cons 10 pt) '(40 . 3.5)))
  )
)
```

### 10.2 批量处理框架 (mini_系列)

CAD学习知识库中最核心的模式——`mini_`前缀系列，提供了专业级工程自动化框架：

```lisp
;; mini_ 系列的核心模式: 配置-选择-处理
(defun c:mini_任务名 ( / old_cmd config_file sel_set result)
  ;; 1. 保存当前环境
  (setq old_cmd (getvar "CMDECHO"))
  (setvar "CMDECHO" 0)
  
  ;; 2. 加载配置(如有)
  ;; (load "mini_config.lsp")
  
  ;; 3. 选择对象
  (princ "\\n选择对象: ")
  (setq sel_set (ssget))
  
  ;; 4. 处理逻辑
  ;; ... 
  
  ;; 5. 恢复环境
  (setvar "CMDECHO" old_cmd)
  (princ)
)
```

### 10.3 LISP常用函数速查

| 函数 | 用途 |
|------|------|
| `(ssget)` | 选择对象返回选择集 |
| `(entget en)` | 获取实体数据表 |
| `(entmod data)` | 修改实体数据 |
| `(entmake data)` | 创建新实体 |
| `(ssadd en ss)` | 添加实体到选择集 |
| `(sslength ss)` | 选择集数量 |
| `(ssname ss i)` | 获取第i个实体名 |
| `(command "CMD" ...)` | 执行AutoCAD命令 |
| `(vla-get-property obj)` | 获取ActiveX属性 |
| `(vlax-curve-getArea obj)` | 获取曲线面积 |
| `(vlax-curve-getDistAtPoint obj pt)` | 获取点到起点距离 |

### 10.4 LISP→Python 对照

| AutoLISP | Python(pyautocad) |
|----------|-------------------|
| `(setq p (getpoint))` | `p = acad.doc.Utility.GetPoint()` |
| `(command "LINE" p1 p2 "")` | `acad.model.AddLine(p1, p2)` |
| `(entget (car (entsel)))` | `acad.doc.Utility.GetEntity()` |
| `(ssget)` | `acad.doc.SelectionSets.Add("SS")` |
| `(vl-load-com)` | pyautocad自动处理 |
| `(entmod ...)` | `obj.Layer = "NEW"` 等属性赋值 |

---

## 十一、批量处理与文件操作

### 11.1 批量打开/处理/保存

```python
import os
from pyautocad import Autocad

acad = Autocad(create_if_not_exists=True)

def batch_process_dwgs(folder):
    """批量处理DWG文件"""
    for f in os.listdir(folder):
        if not f.endswith('.dwg'):
            continue
        path = os.path.join(folder, f)
        # 打开
        doc = acad.app.Documents.Open(path)
        doc = acad.app.ActiveDocument  # 确保获取最新文档
        
        # 在这里做处理...
        # 例如：清理、修改图层、添加标注等
        
        # 保存关闭
        doc.Save()
        doc.Close()
        print(f"已处理: {f}")

# 使用
batch_process_dwgs("D:/projects/drawings/")
```

### 11.2 文件格式转换

```python
import os

def convert_dwg_to_dxf(folder):
    """批量DWG→DXF"""
    for f in os.listdir(folder):
        if f.endswith('.dwg'):
            path = os.path.join(folder, f)
            out = path.replace('.dwg', '.dxf')
            acad.doc.SendCommand(f'_OPEN "{path}"\n')
            time.sleep(1)
            acad.doc.SendCommand(f'_SAVEAS DXF 2018 "{out}"\n')
            time.sleep(0.5)
            acad.doc.SendCommand('_CLOSE\n')

# 支持的导出格式
formats = {
    '.dxf': 'DXF',     # 交换格式
    '.dwt': 'DWT',     # 模板
    '.pdf': 'PDF',     # 文档
    '.dwf': 'DWF',     # 轻量浏览
    '.stl': 'STL',     # 3D打印
    '.iges': 'IGS',    # 通用三维
    '.step': 'STP',    # 通用三维
}
```

### 11.3 运行脚本

```python
# 运行SCR脚本
acad.doc.SendCommand("_SCRIPT D:/scripts/draw.scr\n")

# 加载LISP插件
acad.doc.SendCommand("(load \"D:/plugins/mytool.lsp\")\n")
acad.doc.SendCommand("MYTOOL\n")  # 执行LISP命令

# 运行VBA宏
acad.doc.SendCommand("_-VBARUN MyMacro\n")
```

---

## 十二、中望CAD/浩辰CAD兼容

### 12.1 COM接口兼容性

来自"AutoCAD知识库"的国产CAD适配经验：

```python
# 中望CAD (ZWCAD)
try:
    acad = win32com.client.Dispatch("ZWCAD.Application")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")

# 浩辰CAD (GStarCAD)
try:
    acad = win32com.client.Dispatch("GStarCAD.Application")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")

# 通用兼容写法
def get_cad():
    for progid in ["AutoCAD.Application", "ZWCAD.Application", "GStarCAD.Application"]:
        try:
            return win32com.client.Dispatch(progid)
        except:
            continue
    raise Exception("未找到可用的CAD程序")
```

### 12.2 差异点

| 特性 | AutoCAD | 中望CAD | 浩辰CAD |
|------|---------|---------|---------|
| COM Dispatch | ✅ | ✅ | ✅ |
| pyautocad | ✅ | ✅ | ✅ |
| AutoLISP | ✅ | ✅ | ✅ |
| VLISP扩展 | ✅ | 部分支持 | 部分支持 |
| ObjectARX | ✅ | ZRX | GRX |
| SendCommand | ✅ | ✅ | ✅ |
| 三维建模 | ✅ | ✅ | ✅ |

---

## 十三、AI+CAD 前沿 (AI+CAD知识库)

### 13.1 Text-to-CAD / AI生成CAD

目前主流的AI+CAD方向：

1. **自然语言→CAD模型**: CADAM、Leo AI、MecAgent等
2. **LLM生成CAD代码**: 通过大模型生成AutoLISP/Python/C#代码，再由AutoCAD执行
3. **特征识别**: AI识别工程图中的几何特征
4. **智能标注**: 自动提取模型项目生成标注

### 13.2 AI辅助CAD工作流

```python
# 通过AI生成AutoCAD脚本
# 示例：用户说 "画一个100x50的矩形，四周倒角R5"
# AI自动生成：

def ai_create_rounded_rect(length=100, width=50, radius=5):
    """AI生成的带倒角矩形"""
    acad = Autocad(create_if_not_exists=True)
    # 画矩形
    pts = aDouble(0,0, length,0, length,width, 0,width)
    pline = acad.model.AddLightWeightPolyline(pts)
    pline.Closed = True
    # 倒角
    acad.doc.SendCommand(f"_FILLET R {radius}\n_FILLET P\n")
    # 选择多段线
    pline.Highlight(True)
    acad.doc.SendCommand("P L\n")
    return pline

# 结合LLM的CAD Agent模式
# 1. LLM解析用户意图
# 2. 生成CAD操作序列
# 3. 通过COM/SendCommand执行
# 4. 验证结果反馈
```

### 13.3 重要开源项目

| 项目 | 说明 |
|------|------|
| Pointer-CAD | DeepSeek+港大,LLM生成B-Rep实体 |
| Zero-to-CAD | Autodesk, 大规模CAD构造序列 |
| text-to-cad | Jake, 自然语言→可编辑CAD |
| VideoCAD | MIT, 视频学习CAD操作 |
| WHUCAD | 武大, 首个CAD智能核心开源 |
| LLM4CAD | UT Austin, 多模态LLM→3D CAD |
| CADAM | 自然语言→参数化3D模型 |

---

## 十四、常见问题与调试

### 14.1 常见错误

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| pyautocad连接失败 | AutoCAD未运行 | 手动启动,或用`create_if_not_exists=True` |
| COM错误"RPC服务器不可用" | AutoCAD已关闭 | 重新dispatch |
| 选择集"已存在" | 未Delete旧选择集 | 每次用完`ss.Delete()` |
| SendCommand无反应 | 命令格式错误 | 空格代替回车确认, `\n`代替回车 |
| 中文乱码 | 编码问题 | SendCommand前确保AutoCAD设为GBK |
| LISP加载失败 | 路径含中文 | 用英文路径或`(findfile)` |
| 三维操作报错 | 未切换到3D视图 | `acad.doc.SendCommand("_VSCURRENT _R\n")` |

### 14.2 调试技巧

```python
# 查看所有对象属性
obj = acad.model(0)  # 第一个对象
for prop in dir(obj):
    if not prop.startswith('_'):
        try:
            val = getattr(obj, prop)
            print(f"{prop} = {val}")
        except:
            pass

# 列出所有文档
for i in range(acad.app.Documents.Count):
    doc = acad.app.Documents(i)
    print(f"文档 {i}: {doc.Name}")

# 查看选择集内容
ss = acad.doc.SelectionSets.Add("DEBUG")
ss.Select(5)  # 全选
print(f"当前图形有 {ss.Count} 个对象")

# 逐个查看类型
for obj in ss:
    print(f"  {obj.ObjectName}: Layer={obj.Layer}, Color={obj.Color}")
ss.Delete()
```

---

## 十五、工作流程总结

### AI自动化CAD标准流程

```
用户需求 → 分析绘图策略 → 选择APILISP/SendCommand → 生成代码 → 连接CAD执行 → 验证结果
```

### 功能矩阵

| 功能 | Python | LISP | SendCommand | 
|------|:---:|:---:|:---:|
| 基本绘图 | ✅ | ✅ | ✅ |
| 编辑操作 | ✅ | ✅ | ✅ |
| 图层管理 | ✅ | ✅ | ✅ |
| 标注 | ✅ | ✅ | ✅ |
| 块/属性 | ✅ | ✅ | ✅ |
| 选择集过滤 | ✅ | ✅ | ✅ |
| 三维建模 | ✅ | ⚠️ | ✅ |
| 图纸空间 | ✅ | ⚠️ | ✅ |
| 批量处理 | ✅ | ✅ | ⚠️ |
| 文件转换 | ✅ | ⚠️ | ✅ |
| 外部参照 | ✅ | ✅ | ✅ |

### 选择指南

- **快速原型**: SendCommand（最通用，中望/浩辰全兼容）
- **生产自动化**: Python + pyautocad（类型安全，逻辑复杂）
- **插件开发**: AutoLISP（AutoCAD原生，用户自定义命令）
- **企业级**: C# .NET API（性能最强，DLL部署）
- **AI辅助**: LLM → Python/LISP代码 → COM执行

---

**知识来源**: 
- CAD学习知识库 (308条LISP，市政公路领域)
- AI+CAD (78篇前沿文章，AI辅助产品设计)
- CAD软件教程 (7份教程)
- AutoCAD知识库 (31份资料，CAD自学网/周站长)

**注意**: 所有代码单位为绘图单位（默认mm），使用前确认AutoCAD图形单位设置。国产CAD(中望/浩辰)COM接口基本兼容，部分VLAX函数差异请查阅对应API文档。

---

## 十六、CAD 核心铁律速查（2026-06-01 从 SW skill 架构移植）

> 以下铁律来自 solidworks-automation v4.4.0 的成功验证模式，针对 CAD 场景做了适配。

---

### 铁律 0：启动即清理——关闭孤儿文档 + 清理选择集 🔴

**SW对应**: solidworks-automation Sec 24 铁律0 (CloseDoc 启动清理)

**CAD病灶**: 反复调试运行时，AutoCAD 同样会积累未保存的 Drawing*.dwg，且 COM 选择集(SelectionSets)使用后不 Delete() 会累积导致后续操作报错。

```python
# ═══════ CAD启动首行代码 ═══════
import win32com.client
acad = win32com.client.Dispatch("AutoCAD.Application")

# 1. 清理所有孤儿选择集
for ss in acad.ActiveDocument.SelectionSets:
    try:
        ss.Delete()
    except:
        pass

# 2. 如果当前文档为空(Drawing1.dwg)，新建正式文档
doc = acad.ActiveDocument
if doc.Name.startswith("Drawing") and doc.ModelSpace.Count == 0:
    # 用模板新建
    doc.New("acadiso.dwt")
```

**LISP 等效**:
```lisp
;; 启动清理
(defun startup_clean ()
  ;; 清除所有选择集
  (while (setq ss (ssget "_X"))
    (setq ss nil))
  ;; 确保在模型空间
  (setvar "TILEMODE" 1)
  (princ)
)
```

---

### 铁律 1：选择集用完必 Delete——CAD 的"GetBodies2 防假跑" 🔴

**SW对应**: GetBodies2 实体计数验证

**CAD病灶**: `SelectionSets.Add("SS1")` 使用后不 Delete，再次运行同名选择集会报 "已存在" → 程序中断。

```python
# ✅ 安全选择集模式（用完即删）
def safe_select(acad, filter_type=None):
    ss_name = "TEMP_SS"
    # 删除已存在的同名选择集
    try:
        acad.ActiveDocument.SelectionSets(ss_name).Delete()
    except:
        pass
    ss = acad.ActiveDocument.SelectionSets.Add(ss_name)
    ss.Select(5)  # 全选
    result = list(ss)
    ss.Delete()  # ← 铁律：用完必删
    return result
```

**验证机制——CAD 等效于 GetBodies2**:
```python
def verify_drawing(acad, expected_objects: int = None):
    """验证图纸状态——CAD 的 GetBodies2 等效"""
    model = acad.ActiveDocument.ModelSpace
    count = model.Count
    
    doc = acad.ActiveDocument
    doc.SendCommand("_AUDIT Y\n")  # 审计修复
    doc.SendCommand("_PURGE A * N\n")  # 清理垃圾
    
    # 计算实体数（不含选择集内的辅助对象）
    ss = safe_select(acad)
    obj_count = len(ss)
    
    return {
        "object_count": obj_count,
        "model_count": count,
        "passed": expected_objects is None or obj_count >= expected_objects
    }
```

---

### 铁律 2：三级执行策略——CAD 等效于 Python→VBA→C# 🔴

**SW对应**: Sec 24 铁律8 (Tier 1 Python COM → Tier 2 VBA宏 → Tier 3 C# exe)

| 级别 | 方案 | 适用场景 | 限制 |
|:---:|------|------|------|
| **Tier 1** | Python + pyautocad | 图元创建、图层管理、标注 | COM 对象生命周期管理 |
| **Tier 2** | SendCommand / SCR 脚本 | 复杂编辑（TRIM/FILLET/CHAMFER） | 异步执行、错误处理弱 |
| **Tier 3** | AutoLISP / C# .NET | 插件开发、性能敏感、批量 | LISP 调试困难；C# 需 AutoCAD .NET SDK |

**降级逻辑**:
```python
def try_execute(operation, *args):
    """CAD 三级降级执行"""
    # Tier 1: pyautocad
    try:
        return operation(*args)
    except:
        pass
    # Tier 2: SendCommand
    try:
        cmd = build_sendcommand(operation, *args)
        acad.doc.SendCommand(cmd)
        return True
    except:
        pass
    # Tier 3: 加载 LISP 脚本
    try:
        acad.doc.SendCommand(f'(load "fallback.lsp")\n')
        acad.doc.SendCommand(f'FALLBACK\n')
        return True
    except:
        return False
```

---

### 铁律 3：CAD 六大隐藏地雷 ⚡

**SW对应**: Sec 21.2 五大 Interop DLL 地雷

| # | 地雷 | 现象 | 正确做法 |
|:---:|------|------|------|
| 1 | 选择集不 Delete | "选择集已存在" 错误 | 用完立即 `ss.Delete()` |
| 2 | SendCommand 编码 | 中文命令乱码/无效 | 用英文命令+下划线前缀 `_LINE` |
| 3 | UCS 混淆 | 坐标与实际位置不符 | `SendCommand("_UCS _W\n")` 先切到世界坐标系 |
| 4 | 对象捕捉干扰 | SendCommand 点选位置错误 | `SendCommand("_NON\n")` 临时关闭对象捕捉 |
| 5 | LISP `command` 与 `vl-cmdf` | command 受 UNDO 影响 | 批量操作用 `vl-cmdf` |
| 6 | pyautocad APoint 缺失 | 类型错误 | 所有坐标必须 `APoint(x,y,z)` 包装 |

```python
# 地雷3-4 的防护模板
def safe_sendcommand(acad, cmd):
    """发送命令前先重置 UCS + 关闭对象捕捉"""
    # 固定世界坐标系
    acad.doc.SendCommand("_UCS _W\n")
    # 临时关闭对象捕捉（避免吸附到错误位置）
    acad.doc.SendCommand("_NON\n")
    time.sleep(0.05)
    acad.doc.SendCommand(cmd)
```

---

### 铁律 4：执行后强制审计——CAD 的 ForceRebuild3 🔴

**SW对应**: ForceRebuild3 + GetBodies2 双重验证

```python
def verify_and_audit(acad):
    """CAD 执行后验证——等效于 SW 的 ForceRebuild3"""
    doc = acad.ActiveDocument
    
    # 1. 审计
    doc.SendCommand("_AUDIT Y\n")
    time.sleep(0.2)
    
    # 2. 清理（去除垃圾对象）
    doc.SendCommand("_PURGE A * N\n")
    time.sleep(0.2)
    
    # 3. 缩放范围（检查视觉完整性）
    doc.SendCommand("_ZOOM _E\n")
    time.sleep(0.2)
    
    # 4. 重生成（刷新显示）
    doc.SendCommand("_REGENALL\n")
    
    return True
```

---

### 铁律 5：编码与坐标系——SendCommand 两条前置命令 🔴

**每次 SendCommand 前强制执行的固定管线**:

```python
def sendcommand_pipeline(acad, *commands):
    """SendCommand 安全管线——两条前置 + N条主命令"""
    # === 前置1: 锁定WCS ===
    acad.doc.SendCommand("_UCS _W\n")
    time.sleep(0.05)
    
    # === 前置2: 关闭对象捕捉 ===
    acad.doc.SendCommand("_NON\n")
    time.sleep(0.05)
    
    # === 主命令 ===
    for cmd in commands:
        acad.doc.SendCommand(cmd)
        time.sleep(0.1)
    
    # === 后置: 重生成 ===
    acad.doc.SendCommand("_REGENALL\n")
```

---

### 十六、知识库更新记录

| 版本 | 日期 | 核心变更 | 来源 |
|:---:|------|------|------|
| v1.1.0 | 2026-06-01 | 新增铁律速查：启动清理/选择集防泄漏/三级降级/六大地雷/审计验证/SendCommand管线 | SW skill 架构移植 |
| v1.0.0 | 2026-05-24 | 初始版本，含14大章节：绘图/编辑/图层/标注/块/选择集/3D/打印/LISP/批量/AI+CAD | 4个IMA知识库融合 |


