"""
SolidWorks自动化示例 2: 装配体建模
创建装配体并添加零件配合
"""

import win32com.client
import os

def create_assembly():
    """创建一个简单的装配体"""
    
    try:
        # 连接SolidWorks
        print("正在连接SolidWorks...")
        sw_app = win32com.client.Dispatch("SldWorks.Application")
        sw_app.Visible = True
        print("SolidWorks连接成功！")
        
        # 创建新装配体
        print("创建新装配体...")
        sw_app.NewAssembly()
        sw_model = sw_app.ActiveDoc
        
        print("装配体创建完成！")
        print(f"装配体名称: {sw_model.GetTitle()}")
        
        return sw_model
        
    except Exception as e:
        print(f"错误: {e}")
        return None

def add_part_to_assembly(sw_app, part_path, x=0, y=0, z=0):
    """向装配体中添加零件"""
    
    try:
        sw_model = sw_app.ActiveDoc
        
        # 添加零件
        print(f"添加零件: {part_path}")
        sw_model.AddComponent(part_path, x, y, z)
        
        print("零件添加成功！")
        return True
        
    except Exception as e:
        print(f"添加零件失败: {e}")
        return False

def add_mate(sw_app, component1, component2, mate_type=0):
    """添加配合关系"""
    
    try:
        sw_model = sw_app.ActiveDoc
        
        # 选择两个零部件
        sw_model.Extension.SelectByID2(component1, "COMPONENT", 0, 0, 0, False, 0, None, 0)
        sw_model.Extension.SelectByID2(component2, "COMPONENT", 0, 0, 0, True, 0, None, 0)
        
        # 添加配合（0=重合，1=平行，2=垂直，3=同心，4=距离）
        sw_model.AddMate3(mate_type, 0, False, 0, 0, 0, 0, 0, 0, 0, False)
        
        print("配合添加成功！")
        return True
        
    except Exception as e:
        print(f"添加配合失败: {e}")
        return False

if __name__ == "__main__":
    print("=== SolidWorks自动化示例 2: 装配体建模 ===")
    print("本示例将创建一个装配体并添加零件")
    print()
    
    # 创建装配体
    sw_app = win32com.client.Dispatch("SldWorks.Application")
    sw_app.Visible = True
    sw_app.NewAssembly()
    sw_model = sw_app.ActiveDoc
    
    print("✓ 装配体创建成功！")
    print()
    print("提示: 使用 add_part_to_assembly() 函数添加零件")
    print("提示: 使用 add_mate() 函数添加配合关系")
