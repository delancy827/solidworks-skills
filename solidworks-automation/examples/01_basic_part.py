"""
SolidWorks自动化示例 1: 基础零件建模
创建一个简单的圆柱体零件并保存
"""

import win32com.client
import pythoncom
import os

def create_cylinder_part():
    """创建一个直径50mm、高100mm的圆柱体零件"""
    
    try:
        # 连接SolidWorks
        print("正在连接SolidWorks...")
        sw_app = win32com.client.Dispatch("SldWorks.Application")
        sw_app.Visible = True
        print("SolidWorks连接成功！")
        
        # 创建新零件
        print("创建新零件...")
        sw_app.NewPart()
        sw_model = sw_app.ActiveDoc
        
        # 选择前视基准面
        print("选择前视基准面...")
        sw_model.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, None, 0)
        
        # 创建草图
        print("创建草图...")
        sw_model.SketchManager.InsertSketch(True)
        
        # 绘制直径50mm的圆（半径25mm = 0.025m）
        print("绘制圆...")
        sw_model.SketchManager.CreateCircle(0, 0, 0, 0.025, 0, 0)
        
        # 退出草图
        print("退出草图...")
        sw_model.SketchManager.InsertSketch(True)
        
        # 拉伸100mm（0.1m）
        print("拉伸特征...")
        sw_feature = sw_model.FeatureManager.FeatureExtrusion3(
            True, False, False,  # 单向拉伸
            0, 0,  # 拉伸类型
            0.1, 0.1,  # 深度
            False, False, False,  # 其他选项
            0, 0,  # 方向
            False, False, False, False  # 更多选项
        )
        
        print("圆柱体零件创建完成！")
        
        # 保存零件
        file_path = os.path.join(os.getcwd(), "cylinder_part.sldprt")
        print(f"保存零件到: {file_path}")
        sw_model.SaveAs(file_path)
        
        return sw_model
        
    except Exception as e:
        print(f"错误: {e}")
        return None

if __name__ == "__main__":
    print("=== SolidWorks自动化示例 1: 基础零件建模 ===")
    print("本示例将创建一个直径50mm、高100mm的圆柱体零件")
    print()
    
    # 创建圆柱体零件
    model = create_cylinder_part()
    
    if model:
        print()
        print("✓ 零件创建成功！")
        print(f"  零件名称: {model.GetTitle()}")
        print(f"  文件路径: {model.GetPathName()}")
    else:
        print("✗ 零件创建失败！")
