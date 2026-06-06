"""
SolidWorks自动化示例 4: Simulation 静力学分析
对零件进行静力学有限元分析

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


def run_static_study(sw_app, part_path):
    """运行静力学分析"""

    # === Write: 打开零件 ===
    print(f"[1/7] 打开零件: {part_path}")
    doc = sw_app.OpenDoc6(part_path, 1, 0, "", 0, 0)
    if doc is None:
        raise RuntimeError(f"无法打开零件: {part_path}")

    # === Write: 获取Simulation插件 ===
    print("[2/7] 加载Simulation插件...")
    sw_addin = sw_app.GetAddInObject("SldWorks Simulation")
    if sw_addin is None:
        raise RuntimeError(
            "无法加载Simulation插件，请确保：\n"
            "  1. SolidWorks中已安装Simulation\n"
            "  2. 插件已启用（工具→插件→SOLIDWORKS Simulation）"
        )
    print("  [W-A-R] ✓ Simulation插件加载验证通过")

    # === Write: 创建静力学分析算例 ===
    print("[3/7] 创建静力学分析算例...")
    sw_study = sw_addin.CreateNewStudy2(0, "StaticStudy1", "", 0)
    if sw_study is None:
        raise RuntimeError("无法创建分析算例")
    print("  [W-A-R] ✓ 算例创建验证通过")

    # === Write: 应用材料 ===
    print("[4/7] 应用材料: Aluminum Alloy...")
    sw_study.Material("Default", "Aluminum Alloy", "")

    # === Write: 添加夹具（固定约束）===
    print("[5/7] 添加夹具: 固定约束...")
    sw_study.FixComponent("Fixed-1", ["Face<1>"])

    # === Write: 添加载荷（力）===
    print("[6/7] 添加载荷: 1000N 力...")
    sw_study.ApplyForce("Force-1", ["Face<2>"], 0, 0, -1000, False)

    # === Write: 划分网格 + 运行分析 ===
    print("[7/7] 划分网格并运行分析...")
    sw_study.CreateMesh()
    sw_study.RunAnalysis()

    # === Assert: 验证分析完成 ===
    print("  [W-A-R] 获取分析结果...")
    sw_result = sw_study.GetResults(0)
    assert sw_result is not None, "W-A-R 断言失败：分析结果为空"
    print("  [W-A-R] ✓ 静力学分析完成并验证通过")

    return sw_study, sw_result


def get_study_results(sw_study):
    """获取分析算例的结果"""
    results = {}

    # 位移
    displacement = sw_study.GetResults(0)
    results["displacement"] = displacement
    print(f"  最大位移: {displacement}")

    # 应力
    stress = sw_study.GetResults(1)
    results["stress"] = stress
    print(f"  最大应力: {stress}")

    # 安全系数
    safety_factor = sw_study.GetResults(2)
    results["safety_factor"] = safety_factor
    print(f"  最小安全系数: {safety_factor}")

    return results


if __name__ == "__main__":
    print("=== SolidWorks自动化示例 4: Simulation 静力学分析 ===")
    print("本示例将对零件进行静力学有限元分析")
    print()

    pythoncom.CoInitialize()
    sw_app = None

    try:
        sw_app = connect_sw()

        part_path = os.path.join(os.getcwd(), "cylinder_part.sldprt")

        if os.path.exists(part_path):
            sw_study, results = run_static_study(sw_app, part_path)

            if sw_study:
                print()
                print("✓ 分析完成！")
                study_results = get_study_results(sw_study)
                print(f"  结果摘要: {study_results}")
        else:
            print("未找到零件文件，请先运行 01_basic_part.py 创建零件")

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        raise
    finally:
        pythoncom.CoUninitialize()
