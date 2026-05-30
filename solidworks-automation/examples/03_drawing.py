"""
SolidWorks自动化示例 3: 工程图生成
从零件或装配体创建工程图
"""

import win32com.client
import os

def create_drawing_from_part(part_path, template_path=None):
    """从零件创建工程图"""
    
    try:
        # 连接SolidWorks
        print("正在连接SolidWorks...")
        sw_app = win32com.client.Dispatch("SldWorks.Application")
        sw_app.Visible = True
        print("SolidWorks连接成功！")
        
        # 打开零件
        print(f"打开零件: {part_path}")
        sw_model = sw_app.OpenDoc6(part_path, 1, 0, "", 0, 0)
        
        # 创建工程图
        print("创建工程图...")
        if template_path is None:
            # 使用默认模板
            sw_drawing = sw_app.NewDocument("Drawing.drwdot", 0, 0, 0)
        else:
            sw_drawing = sw_app.NewDocument(template_path, 0, 0, 0)
        
        # 添加三视图
        print("添加三视图...")
        sw_drawing.Create3rdAngleViews2(part_path)
        
        # 添加等轴测视图
        print("添加等轴测视图...")
        sw_drawing.CreateAuxiliaryViewAtCoordinate(0.2, 0.2, 0)
        
        print("工程图创建完成！")
        return sw_drawing
        
    except Exception as e:
        print(f"错误: {e}")
        return None

def add_dimensions(sw_drawing):
    """添加尺寸标注"""
    
    try:
        # 选择视图
        sw_drawing.Extension.SelectByID2("Drawing View1", "DRAWINGVIEW", 0, 0, 0, False, 0, None, 0)
        
        # 添加水平尺寸
        sw_drawing.AddHorizontalDimension2(0, 0, 0)
        
        # 添加垂直尺寸
        sw_drawing.AddVerticalDimension2(0, 0, 0)
        
        print("尺寸标注完成！")
        return True
        
    except Exception as e:
        print(f"添加尺寸失败: {e}")
        return False

def save_drawing(sw_drawing, file_path):
    """保存工程图"""
    
    try:
        print(f"保存工程图到: {file_path}")
        sw_drawing.SaveAs(file_path)
        print("工程图保存成功！")
        return True
        
    except Exception as e:
        print(f"保存失败: {e}")
        return False

if __name__ == "__main__":
    print("=== SolidWorks自动化示例 3: 工程图生成 ===")
    print("本示例将从零件创建工程图")
    print()
    
    # 示例：从零件创建工程图
    part_path = os.path.join(os.getcwd(), "cylinder_part.sldprt")
    
    if os.path.exists(part_path):
        drawing = create_drawing_from_part(part_path)
        
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
