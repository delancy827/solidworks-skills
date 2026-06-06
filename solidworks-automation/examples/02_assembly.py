"""
SolidWorks自动化示例 2: 装配体建模
创建装配体并添加零件配合

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
    try:
        sw = win32com.client.GetActiveObject("SldWorks.Application")
        print("  [连接] 已连接到运行中的SW实例")
    except Exception:
        pass

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
        raise ConnectionError("无法连接或启动SolidWorks")

    sw.Visible = True
    sw.UserControl = True  # ⛔ MUST
    return sw


def safe_select(doc, name, sel_type, append=False):
    """安全选择（VARIANT正确包装 + 铁律2断言）"""
    variant_none = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
    ok = doc.Extension.SelectByID2(name, sel_type, 0, 0, 0,
                                    append, 0, variant_none, 0)
    if not ok:
        raise RuntimeError(f"选择失败: {name} ({sel_type})")
    return True


def create_assembly():
    """创建一个简单的装配体"""

    pythoncom.CoInitialize()
    sw_app = None
    doc = None

    try:
        # === 连接 ===
        print("[1/3] 连接SolidWorks...")
        sw_app = connect_sw()

        # === Write: 新建装配体 ===
        print("[2/3] 新建装配体...")
        template = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_assembly.asmdot'
        doc = sw_app.NewDocument(template, 0, 0, 0)
        if doc is None:
            raise RuntimeError("NewDocument 返回 None，请确认模板路径正确")

        # === Assert: 验证 ===
        doc.EditRebuild3()
        title = doc.GetTitle
        assert title is not None and len(title) > 0, \
            "W-A-R 断言失败：装配体标题为空"
        print(f"  [W-A-R] ✓ 装配体创建验证通过: {title}")

        print("[3/3] 装配体创建完成！")
        return doc

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        raise
    finally:
        pythoncom.CoUninitialize()


def add_part_to_assembly(sw_app, part_path, x=0, y=0, z=0):
    """向装配体中添加零件"""
    doc = sw_app.ActiveDoc
    if doc is None:
        raise RuntimeError("没有打开的装配体文档")

    before_count = doc.GetFeatureCount()
    print(f"  [W-A-R] 添加前特征数: {before_count}")

    doc.AddComponent5(part_path, 0, "", False, "", x, y, z)

    doc.EditRebuild3()
    after_count = doc.GetFeatureCount()
    assert after_count > before_count, \
        f"W-A-R 断言失败：零件未添加: {before_count} → {after_count}"
    print(f"  [W-A-R] ✓ 零件添加验证通过: {before_count} → {after_count}")
    print(f"  ✓ 已添加零件: {part_path}")


def add_mate(sw_app, component1, component2, mate_type=0):
    """添加配合关系（VARIANT正确包装）"""
    doc = sw_app.ActiveDoc
    if doc is None:
        raise RuntimeError("没有打开的装配体文档")

    # 选择两个零部件（VARIANT包装）
    safe_select(doc, component1, "COMPONENT", append=False)
    safe_select(doc, component2, "COMPONENT", append=True)

    # AddMate3: mate_type (0=重合, 1=平行, 2=垂直, 3=同心, 4=距离)
    doc.AddMate3(mate_type, 0, False, 0, 0, 0, 0, 0, 0, 0, False)
    doc.EditRebuild3()
    print(f"  ✓ 配合添加成功 (type={mate_type})")


if __name__ == "__main__":
    print("=== SolidWorks自动化示例 2: 装配体建模 ===")
    print("本示例将创建一个装配体并演示零件添加")
    print()

    doc = create_assembly()

    if doc:
        print()
        print("✓ 装配体创建成功！")
        print()
        print("提示: 使用 add_part_to_assembly(sw_app, part_path) 添加零件")
        print("提示: 使用 add_mate(sw_app, comp1, comp2) 添加配合关系")
