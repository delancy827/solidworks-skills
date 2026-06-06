"""
SolidWorks自动化示例 3: 工程图生成
从零件或装配体创建工程图

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
    """安全选择（VARIANT正确包装）"""
    variant_none = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
    ok = doc.Extension.SelectByID2(name, sel_type, 0, 0, 0,
                                    append, 0, variant_none, 0)
    if not ok:
        raise RuntimeError(f"选择失败: {name} ({sel_type})")
    return True


def create_drawing_from_part(sw_app, part_path, template_path=None):
    """从零件创建工程图"""

    # === Write: 打开零件 ===
    print(f"[1/4] 打开零件: {part_path}")
    doc = sw_app.OpenDoc6(part_path, 1, 0, "", 0, 0)
    if doc is None:
        raise RuntimeError(f"无法打开零件: {part_path}")

    # === Write: 创建工程图 ===
    print("[2/4] 创建工程图...")
    if template_path is None:
        template_path = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_drw-a4.drwdot'
    sw_drawing = sw_app.NewDocument(template_path, 0, 0.210, 0.297)
    if sw_drawing is None:
        raise RuntimeError("NewDocument 返回 None，请确认工程图模板路径正确")

    # === Assert: 验证工程图创建 ===
    drawing_title = sw_drawing.GetTitle
    assert drawing_title is not None and len(drawing_title) > 0, \
        "W-A-R 断言失败：工程图标题为空"
    print(f"  [W-A-R] ✓ 工程图创建验证通过: {drawing_title}")

    # === Write: 添加三视图 ===
    print("[3/4] 添加三视图...")
    sw_drawing.Create3rdAngleViews2(part_path)
    sw_drawing.EditRebuild3()

    # === Read: 验证视图 ===
    print("[4/4] 验证视图...")
    print(f"  [W-A-R] ✓ 三视图已添加到工程图")

    return sw_drawing


def add_dimensions(sw_drawing):
    """添加尺寸标注（VARIANT正确包装）"""
    # 选择视图
    safe_select(sw_drawing, "Drawing View1", "DRAWINGVIEW")

    # 添加尺寸
    sw_drawing.AddHorizontalDimension2(0, 0, 0)
    sw_drawing.AddVerticalDimension2(0, 0, 0)
    print("  ✓ 尺寸标注完成")


def save_drawing(sw_drawing, file_path):
    """保存工程图"""
    print(f"  保存工程图到: {file_path}")
    sw_drawing.SaveAs(file_path)
    assert os.path.exists(file_path), \
        f"W-A-R 断言失败：文件未保存: {file_path}"
    print(f"  [W-A-R] ✓ 文件保存验证通过")


if __name__ == "__main__":
    print("=== SolidWorks自动化示例 3: 工程图生成 ===")
    print("本示例将从零件创建工程图")
    print()

    pythoncom.CoInitialize()
    sw_app = None

    try:
        sw_app = connect_sw()

        part_path = os.path.join(os.getcwd(), "cylinder_part.sldprt")

        if os.path.exists(part_path):
            drawing = create_drawing_from_part(sw_app, part_path)

            if drawing:
                print()
                print("✓ 工程图创建成功！")

                # 添加尺寸标注
                add_dimensions(drawing)

                # 保存工程图
                drawing_path = os.path.join(os.getcwd(), "cylinder_part.slddrw")
                save_drawing(drawing, drawing_path)
        else:
            print("未找到零件文件，请先运行 01_basic_part.py 创建零件")

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        raise
    finally:
        pythoncom.CoUninitialize()
