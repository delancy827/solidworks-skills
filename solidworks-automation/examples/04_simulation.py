"""
SolidWorks自动化示例 4: Simulation 静力学分析
对零件进行静力学有限元分析
"""

import win32com.client
import os

def run_static_study(part_path):
    """运行静力学分析"""
    
    try:
        # 连接SolidWorks
        print("正在连接SolidWorks...")
        sw_app = win32com.client.Dispatch("SldWorks.Application")
        sw_app.Visible = True
        print("SolidWorks连接成功！")
        
        # 打开零件
        print(f"打开零件: {part_path}")
        sw_model = sw_app.OpenDoc6(part_path, 1, 0, "", 0, 0)
        
        # 获取Simulation插件
        print("加载Simulation插件...")
        sw_addin = sw_app.GetAddInObject("SldWorks Simulation")
        
        if sw_addin is None:
            print("错误: 无法加载Simulation插件，请确保在SolidWorks中已启用该插件")
            return None
        
        print("Simulation插件加载成功！")
        
        # 创建静力学分析算例
        print("创建静力学分析算例...")
        sw_study = sw_addin.CreateNewStudy2(0, "StaticStudy1", "", 0)
        
        if sw_study is None:
            print("错误: 无法创建分析算例")
            return None
        
        # 应用材料
        print("应用材料: Aluminum Alloy")
        sw_study.Material("Default", "Aluminum Alloy", "")
        
        # 添加夹具（固定约束）
        print("添加夹具: 固定约束")
        sw_study.FixComponent("Fixed-1", ["Face<1>"])
        
        # 添加载荷（力）
        print("添加载荷: 1000N 力")
        sw_study.ApplyForce("Force-1", ["Face<2>"], 0, 0, -1000, False)
        
        # 划分网格
        print("划分网格...")
        sw_study.CreateMesh()
        
        # 运行分析
        print("运行分析...")
        sw_study.RunAnalysis()
        
        # 获取结果
        print("获取分析结果...")
        sw_result = sw_study.GetResults(0)
        
        print("✓ 静力学分析完成！")
        return sw_result
        
    except Exception as e:
        print(f"错误: {e}")
        return None

def get_study_results(sw_study):
    """获取分析算例的结果"""
    
    try:
        # 获取应力结果
        stress = sw_study.GetResults(1)  # 1 = 应力
        print(f"最大应力: {stress}")
        
        # 获取位移结果
        displacement = sw_study.GetResults(0)  # 0 = 位移
        print(f"最大位移: {displacement}")
        
        # 获取安全系数
        safety_factor = sw_study.GetResults(2)  # 2 = 安全系数
        print(f"最小安全系数: {safety_factor}")
        
        return {
            "stress": stress,
            "displacement": displacement,
            "safety_factor": safety_factor
        }
        
    except Exception as e:
        print(f"获取结果失败: {e}")
        return None

if __name__ == "__main__":
    print("=== SolidWorks自动化示例 4: Simulation 静力学分析 ===")
    print("本示例将对零件进行静力学有限元分析")
    print()
    
    # 示例：分析零件
    part_path = os.path.join(os.getcwd(), "cylinder_part.sldprt")
    
    if os.path.exists(part_path):
        results = run_static_study(part_path)
        
        if results:
            print()
            print("✓ 分析完成！")
            print(f"  结果: {results}")
    else:
        print("未找到零件文件，请先运行 01_basic_part.py 创建零件")
