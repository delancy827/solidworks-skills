"""
SolidWorks自动化示例 1: 基础零件建模
创建一个直径50mm、高100mm的圆柱体零件并保存

遵守 SKILL.md 三大铁律：
- 铁律1：GetActiveObject优先 + try...finally清理 + UserControl=True
- 铁律2：W-A-R闭环断言（Write-Assert-Read）
- 铁律3：反幻觉（使用已验证的API签名）
"""

import win32com.client
import pythoncom
import os


def connect_sw():
    """连接SolidWorks（铁律1: GetActiveObject优先 + Dispatch回退）"""
    sw = None
    # 第一优先：连已有实例
    try:
        sw = win32com.client.GetActiveObject("SldWorks.Application")
        print("  [连接] 已连接到运行中的SW实例")
    except Exception:
        pass

    # 回退：启动新实例
    if sw is None:
        for progid in ["SldWorks.Application.32",
                        "SldWorks.Application.64",
                        "SldWorks.Application"]:
            try:
                sw = win32com.client.Dispatch(progid)
                print(f"  [连接] 启动新SW实例 ({progid})")
                break
            except Exception:
                pass

    if sw is None:
        raise ConnectionError("无法连接或启动SolidWorks，请确认SW已安装并运行")

    sw.Visible = True
    sw.UserControl = True  # ⛔ MUST: 防止Python结束后SW被GC回收
    return sw


def safe_select_plane(doc, plane_name_cn="前视基准面", plane_name_en="Front Plane"):
    """选择基准面（中英文回退 + VARIANT正确包装）"""
    variant_none = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)

    # 先试中文名（中文版SW）
    ok = doc.Extension.SelectByID2(plane_name_cn, "PLANE", 0, 0, 0,
                                    False, 0, variant_none, 0)
    if ok:
        print(f"  [选择] 已选择基准面: {plane_name_cn}")
        return True

    # 回退：英文名
    ok = doc.Extension.SelectByID2(plane_name_en, "PLANE", 0, 0, 0,
                                    False, 0, variant_none, 0)
    if ok:
        print(f"  [选择] 已选择基准面: {plane_name_en}")
        return True

    raise RuntimeError(f"无法选择基准面: {plane_name_cn}/{plane_name_en}")


def create_cylinder_part():
    """创建一个直径50mm、高100mm的圆柱体零件"""

    pythoncom.CoInitialize()  # ⛔ MUST: COM公寓初始化
    sw_app = None
    doc = None

    try:
        # === 连接 ===
        print("[1/6] 连接SolidWorks...")
        sw_app = connect_sw()

        # === 新建零件 ===
        print("[2/6] 新建零件...")
        template = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
        doc = sw_app.NewDocument(template, 0, 0, 0)
        if doc is None:
            raise RuntimeError("NewDocument 返回 None，请确认模板路径正确")

        # === Write: 记录修改前指纹 ===
        before_count = doc.GetFeatureCount()
        print(f"  [W-A-R] 修改前特征数: {before_count}")

        # === 选择基准面 + 创建草图 ===
        print("[3/6] 选择前视基准面并创建草图...")
        safe_select_plane(doc)
        doc.SketchManager.InsertSketch(True)

        # 绘制直径50mm的圆（半径25mm = 0.025m）
        print("[4/6] 绘制圆（R=25mm）...")
        doc.SketchManager.CreateCircle(0, 0, 0, 0.025, 0, 0)
        doc.SketchManager.InsertSketch(True)

        # === 拉伸100mm（0.1m）— 完整23参数签名 ===
        print("[5/6] 拉伸特征（100mm）...")
        sw_feature = doc.FeatureManager.FeatureExtrusion2(
            True, False, False,       # 1-3: Sd, Flip, Dir
            0, 0,                     # 4-5: T1, T2 (0=Blind)
            0.1, 0.0,                 # 6-7: D1=100mm, D2 (米)
            False, False,             # 8-9: Dchk1, Dchk2
            False, False,             # 10-11: Ddir1, Ddir2
            0.0, 0.0,                 # 12-13: Dang1, Dang2
            False,                    # 14: Ofr
            False,                    # 15: Ofc
            False, False,             # 16-17: Tf1, Tf2
            False,                    # 18: Merge
            False, False,             # 19-20: UseFeatScope, UseAutoSelect
            0.0, False, False         # 21-23: StartOffset, IsAuto, FlipStart
        )

        # === Assert: 验证特征已创建 ===
        doc.EditRebuild3()
        after_count = doc.GetFeatureCount()
        assert after_count > before_count, \
            f"W-A-R 断言失败！特征数未增加: {before_count} → {after_count}"
        print(f"  [W-A-R] ✓ 特征数验证通过: {before_count} → {after_count}")

        # === Read: 读取结果确认 ===
        print(f"  [W-A-R] 最后特征: {doc.FeatureManager.GetLastFeature().Name}")

        # === 保存零件 ===
        print("[6/6] 保存零件...")
        file_path = os.path.join(os.getcwd(), "cylinder_part.sldprt")
        doc.SaveAs(file_path)
        print(f"  ✓ 已保存到: {file_path}")

        return doc

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        raise
    finally:
        # ⛔ 铁律1.3: 闭环清理
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    print("=== SolidWorks自动化示例 1: 基础零件建模 ===")
    print("本示例将创建一个直径50mm、高100mm的圆柱体零件")
    print()

    model = create_cylinder_part()

    if model:
        print()
        print("✓ 零件创建成功！")
        print(f"  零件名称: {model.GetTitle}")
        print(f"  文件路径: {model.GetPathName()}")
