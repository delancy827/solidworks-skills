# Verified Pipeline — 双接口怪癖全绕开的实证流水线

来源：2026-10-07 中文版 SW 2024 SP5 (32.5.0) + Python 3.14/pywin32 实战
（图纸 → 支座/连杆×2/销轴×2 → 两级135°装配，9/9 配合自动添加，
三零件体积与理论值偏差 0.000%）。怪癖全文见
`references/com-dualinterface-quirks.md`。

## 文件

- `make_typelib_wrapper.py` — 从 sldworks.tlb 生成 `sldworks_gen.py`（早绑定包装，先跑这个）
- `sw_common.py` — 公共库：早/动态双通道、pm() 属性方法自适应、CreateArc2 草图基元、
  T0=3 偏移拉伸、ComposeTransform 摆位、截图/保存/体积/bbox
- `assemble_two_link_arm.py` — 完整装配示例：先开零件→AddComponent5→ComposeTransform
  摆位→FeatureByName+Select2 配合 9 个→干涉→存图

## 运行顺序

```bash
python make_typelib_wrapper.py "E:\sw2024\SOLIDWORKS\sldworks.tlb"  # 按你的安装路径
# 修改 assemble_two_link_arm.py 里的 USER_DIR 为你的零件输出目录后：
python assemble_two_link_arm.py
```

## 五个最容易踩的坑（详见 quirks 文档）

1. Create3PointArc 的弧不并入轮廓 → 用 `doc.CreateArc2`，且**弧先画**
2. FeatureExtrusion2 第21参是 T0 枚举（3=偏移），第22参才是偏移距离；本机 Flip 在偏移下无效，用负偏移
3. AddComponent5 前零件必须已 OpenDoc6
4. ComposeTransform 的向量是旋转矩阵的**列**，且要传 IMathVector 对象
5. ShowNamedView2 第二参传 -1 视图不切换（等轴测=7/前视=1/上视=5/右视=4）
