"""SolidWorks 2024 COM 工具集（本机 E:\sw2024 安装实测验证）。

本机关键事实（踩坑记录）：
  1. 动态 dispatch 大量"找不到成员"→ 用 sldworks_gen.py（sldworks.tlb makepy 生成）早绑定；
     但带 byref 参数的方法（OpenDoc6/Extension.SaveAs等）早绑定会炸 → 这类必须走动态 CDispatch。
  2. 接口归属：GetPartBox→IPartDoc；GetBodies2→IPartDoc/IComponent2；GetBox→IAssemblyDoc；
     CreateArc2/InsertAxis2→IModelDoc2；Create3PointArc→ISketchManager（但其弧无法并入轮廓！）。
  3. FeatureExtrusion2 第21参是 T0 起始条件枚举（0=草图面, 3=swStartOffset），不是偏移距离；
     偏移距离在第22参 StartOffset。
  4. SketchManager.Create3PointArc 画出的弧与相邻线段不合并 → 轮廓不闭合 → FE2 返回 None；
     必须用 IModelDoc2.CreateArc2(圆心, 起点, 终点, 方向)。
  5. 单位一律米；RevisionNumber/GetFeatureCount/GetTitle 等在本机是属性不是方法。
"""
import os
import win32com.client
import pythoncom

try:
    import sldworks_gen as swg
except ImportError:
    swg = None

MM = 0.001
TPL_PART = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot"
TPL_ASM = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_assembly.asmdot"

_SW = {"typed": None, "dyn": None}


def pm(obj, name, *args):
    val = getattr(obj, name)
    if callable(val):
        return val(*args)
    if args:
        raise TypeError(f"{name} 是属性")
    return val


def connect_sw():
    """连接（复用实例优先），返回早绑定 ISldWorks。原始动态对象存 _SW['dyn']。"""
    raw = None
    try:
        raw = win32com.client.GetActiveObject("SldWorks.Application")
    except Exception:
        for progid in ("SldWorks.Application.32", "SldWorks.Application"):
            try:
                raw = win32com.client.Dispatch(progid)
                break
            except Exception:
                pass
    if raw is None:
        raise ConnectionError("无法连接 SolidWorks")
    dyn = raw if hasattr(raw, "_oleobj_") is False else win32com.client.Dispatch(raw._oleobj_)
    _SW["dyn"] = dyn
    typed = swg.ISldWorks(raw._oleobj_) if swg else raw
    _SW["typed"] = typed
    typed.Visible = True
    typed.UserControl = True
    return typed


def dyn_sw():
    return _SW["dyn"]


def typed(obj, cls):
    if swg is None or obj is None:
        return obj
    try:
        return cls(obj._oleobj_)
    except Exception:
        return obj


def active_doc():
    """(typed_doc, dyn_doc)——当前活动文档的双形态。"""
    dyn = _SW["dyn"].ActiveDoc if _SW["dyn"] else None
    t = typed(dyn, swg.IModelDoc2) if dyn is not None else None
    return t, dyn


def open_doc(path, doc_type=1):
    """打开文档（动态处理 byref），返回 (typed_doc, dyn_doc)。doc_type: 1零件 2装配 3图。"""
    errs = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warns = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    dyn = _SW["dyn"].OpenDoc6(path, doc_type, 0, "", errs, warns)
    if dyn is None:
        raise RuntimeError(f"打开失败({errs.value}): {path}")
    return typed(dyn, swg.IModelDoc2), dyn


def new_part(sw=None):
    dyn = _SW["dyn"].NewDocument(TPL_PART, 0, 0, 0)
    if dyn is None:
        raise RuntimeError("NewDocument 返回 None（零件模板不可用）")
    return typed(dyn, swg.IModelDoc2), dyn


def new_asm(sw=None):
    dyn = _SW["dyn"].NewDocument(TPL_ASM, 0, 0, 0)
    if dyn is None:
        raise RuntimeError("NewDocument 返回 None（装配模板不可用）")
    return typed(dyn, swg.IModelDoc2), dyn


def close_all_docs():
    """关闭所有打开文档（自动化残留清理）。"""
    while True:
        t, dyn = active_doc()
        if dyn is None:
            break
        title = pm(t, "GetTitle")
        _SW["dyn"].CloseDoc(title)
        t2, _ = active_doc()
        if t2 is not None and pm(t2, "GetTitle") == title:
            break


def vnull():
    """Callout 空参数：早绑定传 None，动态传 VARIANT。这里统一走动态场景的 VARIANT；
    SelectByID2 无 byref，早绑定下直接传 None 即可——由调用处决定。"""
    return None


def select(doc_typed, name, sel_type, append=False, hit=(0, 0, 0)):
    ok = doc_typed.Extension.SelectByID2(name, sel_type, hit[0], hit[1], hit[2],
                                         append, 0, None, 0)
    if not ok:
        raise RuntimeError(f"选择失败: {name} ({sel_type})")
    return True


def try_select(doc_typed, name, sel_type, append=False, hit=(0, 0, 0)):
    return doc_typed.Extension.SelectByID2(name, sel_type, hit[0], hit[1], hit[2],
                                           append, 0, None, 0)


def select_plane(doc, cn, en):
    for name in (cn, en):
        if try_select(doc, name, "PLANE"):
            return name
    raise RuntimeError(f"无法选择基准面: {cn}/{en}")


def rebuild(doc):
    doc.ForceRebuild3(False)


def feature_count(doc):
    # GetFeatureCount 在 tlb 是方法、IDispatch 层是属性——pm 自适应
    return int(pm(doc, "GetFeatureCount"))


def part_doc(doc):
    return typed(doc, swg.IPartDoc)


def asm_doc(doc):
    return typed(doc, swg.IAssemblyDoc)


def bbox(doc):
    """零件/装配统一包围盒，米。"""
    for call in (lambda: part_doc(doc).GetPartBox(True),  # True=不做单位换算，恒为米
                 lambda: asm_doc(doc).GetBox(0)):
        try:
            vals = list(call())
            if len(vals) == 6 and all(abs(v) < 100 for v in vals):
                return tuple(vals)
        except Exception:
            continue
    return None


def volume(doc):
    """体积 m³（IMassProperty.Volume propget）。"""
    try:
        ext = typed(doc.Extension, swg.IModelDocExtension)
        mp = typed(ext.CreateMassProperty(), swg.IMassProperty)
        v = mp.Volume
        return float(v() if callable(v) else v)
    except Exception:
        try:
            b = part_doc(doc).GetBodies2(-1, True)
            b = b[0] if isinstance(b, tuple) else b
            return float(typed(b, swg.IBody2).Volume)
        except Exception:
            return None


VDISP_NULL = None


def _vdisp():
    global VDISP_NULL
    if VDISP_NULL is None:
        VDISP_NULL = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
    return VDISP_NULL


def save_as(doc_dyn, path):
    """SaveAs（byref 走动态；ExportData 需 VT_DISPATCH 空 VARIANT）。"""
    errs = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warns = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    ok = doc_dyn.Extension.SaveAs(path, 0, 1, _vdisp(), errs, warns)
    assert ok, f"SaveAs 失败({errs.value}/{warns.value}): {path}"
    assert os.path.exists(path) and os.path.getsize(path) > 0, f"保存后文件缺失: {path}"
    print(f"  [保存] {path} ({os.path.getsize(path)} bytes)")


def screenshot(doc_dyn, sw_view, path_png):
    """切命名视图并导出 PNG（SaveAs byref 走动态）。"""
    t, _ = active_doc()
    t.ShowNamedView2(sw_view, -1)
    t.ViewZoomtofit2()
    t.ForceRebuild3(False)
    errs = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warns = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    ok = doc_dyn.Extension.SaveAs(path_png, 0, 1, _vdisp(), errs, warns)
    good = bool(ok) and os.path.exists(path_png) and os.path.getsize(path_png) > 0
    print(f"  [截图] {os.path.basename(path_png)}: {'✓' if good else '✗(' + str(errs.value) + ')'}")
    return good


# ---------- 草图基元（早绑定下 SketchManager 直接可用） ----------

def sk_line(doc, x1, y1, x2, y2):
    doc.SketchManager.CreateLine(x1, y1, 0, x2, y2, 0)


def sk_circle(doc, cx, cy, r):
    doc.SketchManager.CreateCircle(cx, cy, 0, cx + r, cy, 0)


def sk_arc(doc, cx, cy, xs, ys, xe, ye, ccw=True):
    """IModelDoc2.CreateArc2(圆心, 起点, 终点, 方向)。"""
    seg = doc.CreateArc2(cx, cy, 0, xs, ys, 0, xe, ye, 0, 1 if ccw else 0)
    if seg is None:
        raise RuntimeError("CreateArc2 返回 None")
    return seg


def extrude(doc, d1, d2=0.0, sd=True, flip=False, start_offset=0.0, merge=True):
    """FeatureExtrusion2（23参，tlb签名）。T0=第21参（3=偏移起始），StartOffset=第22参。"""
    t0 = 3 if start_offset else 0
    feat = doc.FeatureManager.FeatureExtrusion2(
        sd, flip, False, 0, 0, d1, d2,
        False, False, False, False, 0.0, 0.0,
        False, False, False, False,
        merge, False, False,
        t0, start_offset, False)
    if feat is None:
        raise RuntimeError("FeatureExtrusion2 返回 None")
    return feat


def feature_names(doc, limit=50):
    out = []
    try:
        f = pm(doc, "FirstFeature")
    except Exception:
        return out
    n = 0
    while f is not None and n < limit:
        try:
            if not hasattr(f, "GetTypeName2") and not hasattr(f, "Name"):
                break  # FirstFeature 返回的是方法对象而非特征时退出
            out.append((pm(f, "Name"), pm(f, "GetTypeName2")))
        except Exception:
            break
        f = pm(f, "GetNextFeature")
        n += 1
    return out


def add_axis_on_face(doc, hit_xyz, name="AXIS_HOLE"):
    """选中圆柱面 → IModelDoc2.InsertAxis2（本机返回 bool）。
    新轴名通过动态遍历特征树中最后一个 RefAxis 类型特征获得。"""
    ok = doc.Extension.SelectByID2("", "FACE", hit_xyz[0], hit_xyz[1], hit_xyz[2],
                                   False, 0, None, 0)
    assert ok, f"无法选中面 @{hit_xyz}"
    doc.InsertAxis2(True)
    rebuild(doc)
    # 动态遍历（早绑定 IFeature 迭代在本机不可用）
    dyn = dyn_sw().ActiveDoc
    axis_names = []
    f = dyn.FirstFeature
    n = 0
    while f is not None and n < 100:
        try:
            if f.GetTypeName2 == "RefAxis":
                axis_names.append(f.Name)
        except Exception:
            pass
        try:
            f = f.GetNextFeature
        except Exception:
            break
        n += 1
    assert axis_names, "未找到 RefAxis 特征"
    return axis_names[-1]


