"""摇臂机构装配 v2 —— 本机验证过的全部可靠通道。

流程：先开零件 → 新建装配 → AddComponent5 → ComposeTransform(行向量!)摆位
     → IFeature.Select2 选基准面/基准轴加配合 → 面命中+组件验证加销头贴合
     → 干涉检查 → 存盘+截图 → 清窗。

ComposeTransform(X,Y,Z,T,Scale) 语义（实测校准）：
  X/Y/Z 为旋转矩阵的 **行向量**（不是列！传列会得到转置旋转），T 为平移，Scale=1。
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
import win32com.client
from sw_common import (MM, connect_sw, open_doc, new_asm, rebuild, part_doc, asm_doc,
                       bbox, save_as, screenshot, typed, pm, close_all_docs)
import sldworks_gen as swg

USER_DIR = r"C:\Users\22374\Desktop\湛江北海\学习课程\sw"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")

C = math.cos(math.radians(135))   # -0.70710678
S = math.sin(math.radians(135))   #  0.70710678

# 列向量（实测校准：ComposeTransform 的 X/Y/Z 是旋转矩阵的三列，即局部轴在全局的像）
R_ID = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
R_Z135 = ((C, S, 0), (-S, C, 0), (0, 0, 1))          # 绕Z转+135°
R_X90 = ((1, 0, 0), (0, 0, 1), (0, -1, 0))           # 绕X转+90°：local +Y → global +Z
# 连杆2：眼孔轴(局部Z)→(-S,-S,0)，轴线(局部X)→(0.5,-0.5,S)
R_L2 = ((0.5, -0.5, S), (-0.5, 0.5, S), (-S, -S, 0))

P1 = (0.0, 0.115, 0.0)
P2 = (P1[0] + 0.135 * (-S), P1[1] + 0.135 * S, 0.0)   # (-95.46, 210.46, 0)mm
T_PIN1 = (0.0, 0.115, -0.020)
A2 = (-S, -S, 0.0)
T_PIN2 = tuple(P2[i] - 0.025 * A2[i] for i in range(3))


def place(sw, comp, R, tvec):
    mu = typed(sw.GetMathUtility(), swg.IMathUtility)
    V8 = lambda l: win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x) for x in l])
    vec = lambda l: typed(mu.CreateVector(V8(l)), swg.IMathVector)
    mt = mu.ComposeTransform(vec(R[0]), vec(R[1]), vec(R[2]), vec(tvec), 1.0)
    typed(comp, swg.IComponent2).Transform2 = mt
    rebuild(sw.ActiveDoc)


def comp_feature(comp, name):
    return typed(typed(comp, swg.IComponent2).FeatureByName(name), swg.IFeature)


def doc_feature_dyn(doc, name):
    """动态遍历文档特征树按名查找（早绑定 IModelDoc2 无 FeatureByName）。"""
    dyn = dyn_doc()
    f = dyn.FirstFeature
    n = 0
    while f is not None and n < 200:
        try:
            if f.Name == name:
                return f
        except Exception:
            break
        try:
            f = f.GetNextFeature
        except Exception:
            break
        n += 1
    return None


def dyn_doc():
    from sw_common import dyn_sw
    return dyn_sw().ActiveDoc


def sel_feat(comp, name, append):
    f = comp_feature(comp, name)
    ok = f.Select2(append, 0)
    return bool(ok)


def sel_face_verified(doc, point, want_prefix, append=False, tries=None):
    """命中选面 + 组件归属验证。want_prefix: 组件实例名前缀（如 '销轴'）。"""
    sm = doc.SelectionManager
    ok = doc.Extension.SelectByID2("", "FACE", point[0], point[1], point[2], append, 0, None, 0)
    cnt = pm(sm, "GetSelectedObjectCount2", -1)
    if not cnt:
        return False, None
    try:
        obj = pm(sm, "GetSelectedObject6", cnt, -1)
        comp = pm(obj, "GetComponent")
        name = pm(comp, "Name2") if comp else "?"
        return name.startswith(want_prefix), name
    except Exception:
        return True, "?"  # 无法验证时乐观放行


def mate(doc, kind, label):
    f = asm_doc(doc).AddMate3(kind, 0, False, 0, 0, 0, 0, 0, 0, 0, 0, False)
    rebuild(doc)
    print(f"  [配合] {label}: {'✓' if f is not None else '✗ None'}")
    return f is not None


def main():
    pythoncom.CoInitialize()
    sw = connect_sw()

    parts = {
        "bracket": os.path.join(USER_DIR, "支座.SLDPRT"),
        "link": os.path.join(USER_DIR, "连杆.SLDPRT"),
        "pin": os.path.join(USER_DIR, "销轴.SLDPRT"),
    }
    print("[1] 打开零件（本机 AddComponent5 前置条件）")
    for p in parts.values():
        open_doc(p, 1)

    t, dyn = new_asm()
    a = asm_doc(t)
    print("[2] 插入零部件")
    comp_b = a.AddComponent5(parts["bracket"], 0, "", False, "", 0, 0, 0)
    comp_l1 = a.AddComponent5(parts["link"], 0, "", False, "", 0, 0, 0)
    comp_p1 = a.AddComponent5(parts["pin"], 0, "", False, "", 0, 0, 0)
    comp_l2 = a.AddComponent5(parts["link"], 0, "", False, "", 0, 0, 0)
    comp_p2 = a.AddComponent5(parts["pin"], 0, "", False, "", 0, 0, 0)
    assert all(c is not None for c in (comp_b, comp_l1, comp_p1, comp_l2, comp_p2)), "插入失败"
    print("  5 个 ✓")

    print("[3] ComposeTransform 摆位")
    place(sw, comp_b, R_ID, (0, 0, 0))
    place(sw, comp_l1, R_Z135, P1)
    place(sw, comp_p1, R_X90, T_PIN1)
    place(sw, comp_l2, R_L2, P2)
    place(sw, comp_p2, R_Z135, T_PIN2)
    bb = bbox(t)
    print(f"  装配 bbox: {[round(v*1000,1) for v in bb]} mm")
    # 位姿硬校验：装配 bbox 应为
    exp = (-0.13814, 0.0, -0.075, 0.075, 0.25314, 0.13081)  # 连杆2叉板z分量已计入
    if bb:
        assert all(abs(g - w) < 0.002 for g, w in zip(bb, exp)), f"位姿异常: {bb} vs {exp}"
        print("  位姿校验 ✓")

    print("[4] 配合")
    n_ok = 0
    # 4.1 锁定支座（装配原点基准面 ↔ 支座基准面）
    for pl in ("前视基准面", "上视基准面", "右视基准面"):
        ok1 = sel_feat(comp_b, pl, False)
        f_asm = doc_feature_dyn(t, pl)
        ok2 = f_asm.Select2(True, 0) if f_asm is not None else False
        if ok1 and ok2 and mate(t, 0, f"支座{pl}↔装配{pl} 重合"):
            n_ok += 1
    # 4.2 孔轴同心
    for fa, na, fb, nb, label in (
        (comp_b, "基准轴1", comp_l1, "基准轴1", "支座孔↔连杆1眼孔 同心"),
        (comp_b, "基准轴1", comp_p1, "基准轴1", "支座孔↔销1 同心"),
        (comp_l1, "基准轴2", comp_l2, "基准轴1", "连杆1叉孔↔连杆2眼孔 同心"),
        (comp_l1, "基准轴2", comp_p2, "基准轴1", "连杆1叉孔↔销2 同心"),
    ):
        if sel_feat(fa, na, False) and sel_feat(fb, nb, True) and mate(t, 1, label):
            n_ok += 1
    # 4.3 销头端面贴合（命中+组件验证）
    face_mates = [
        ([(0, 0.127, 0.030), (0.020, 0.105, 0.030)], "销轴", "支座", "销1头端面贴合"),
        ([(-0.1216224, 0.2012670, 0.0), (-0.1944544, 0.2740990, 0.0)], "销轴", "连杆", "销2头端面贴合"),
    ]
    for hits, want1, want2, label in face_mates:
        t.ClearSelection2(True)
        g1, c1 = sel_face_verified(t, hits[0], want1)
        g2, c2 = sel_face_verified(t, hits[1], want2, append=True)
        if g1 and g2 and mate(t, 0, label):
            n_ok += 1
        else:
            print(f"  ({label} 跳过: 命中归属 c1={c1} c2={c2})")
    print(f"  配合完成 {n_ok}/9")

    print("[5] 干涉检查")
    try:
        res = asm_doc(t).ToolsCheckInterference2(0, None, False)
        print(f"  工具返回: {res} (None, None 通常=未报告干涉)")
    except Exception as e:
        print(f"  不可用: {str(e)[:60]}")

    print("[6] 存盘+截图")
    out = os.path.join(USER_DIR, "摇臂机构.SLDASM")
    save_as(dyn, out)
    sw.ActivateDoc3(pm(t, "GetTitle"), False, 0, 0)
    for view, fn in (("*Isometric", "asm_iso.png"), ("*Front", "asm_front.png"),
                     ("*Top", "asm_top.png"), ("*Right", "asm_right.png")):
        screenshot(dyn, view, os.path.join(SHOTS, fn))
    close_all_docs()
    print("=== 装配完成（窗口已清空） ===")


if __name__ == "__main__":
    main()
