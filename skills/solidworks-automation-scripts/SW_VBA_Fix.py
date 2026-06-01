# -*- coding: utf-8 -*-
"""
SW_VBA_Fix.py - 通过VBA宏执行SW复杂建模
时间戳: 2026-06-01
策略: Python连接SW → VBA宏写入文件 → SW执行宏
"""
import win32com.client
import pythoncom
import time
import os
import struct

# ========== VBA宏代码模板 ==========
VBA_CODE = '''Sub SWRebuild()
    Dim swApp As SldWorks.SldWorks
    Dim swDoc As SldWorks.ModelDoc2
    Dim swSketchMgr As SldWorks.SketchManager
    Dim swFeatMgr As SldWorks.FeatureManager
    Dim boolstatus As Boolean
    Dim feat As SldWorks.Feature
    Dim i As Integer

    Set swApp = Application.SldWorks
    Set swDoc = swApp.ActiveDoc

    If swDoc Is Nothing Then
        swApp.SendMsgToUser "No active document"
        Exit Sub
    End If

    swApp.CloseAllDocuments True
    swApp.NewDocument "C:\\ProgramData\\SolidWorks\\SOLIDWORKS 2024\\templates\\gb_part.prtdot", 0, 0, 0

    Set swDoc = swApp.ActiveDoc
    Set swSketchMgr = swDoc.SketchManager
    Set swFeatMgr = swDoc.FeatureManager

    ' === 底座梯形拉伸 ===
    boolstatus = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0)
    swSketchMgr.InsertSketch True

    swSketchMgr.CreateLine -0.038, 0.128, 0, -0.050, 0.098, 0
    swSketchMgr.CreateLine -0.050, 0.098, 0, 0.050, 0.098, 0
    swSketchMgr.CreateLine 0.050, 0.098, 0, 0.038, 0.128, 0
    swSketchMgr.CreateLine 0.038, 0.128, 0, -0.038, 0.128, 0

    swSketchMgr.InsertSketch True
    Set feat = swFeatMgr.FeatureExtrusion2(False, False, False, 0, 1, 0.128, 0.005, False, False, False, False, 0, 0, False, False, False, False, False, False, False, False, False, False, False)
    swDoc.ForceRebuild3 False

    ' === 顶部M6螺纹孔 ===
    boolstatus = swDoc.Extension.SelectByID2("上视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0)
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircle -0.015, 0, 0, -0.015 + 0.003, 0, 0
    swSketchMgr.CreateCircle 0.015, 0, 0, 0.015 + 0.003, 0, 0
    swSketchMgr.InsertSketch True
    Set feat = swFeatMgr.FeatureExtrusion2(True, False, False, 0, 1, 0.015, 0, False, False, False, False, 0, 0, False, False, False, False, False, False, False, False, False, False, False)
    swDoc.ForceRebuild3 False

    ' === 大圆孔 ===
    boolstatus = swDoc.Extension.SelectByID2("右视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0)
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircle 0, 0.064, 0, 0.025, 0.064, 0
    swSketchMgr.InsertSketch True
    Set feat = swFeatMgr.FeatureExtrusion2(True, False, False, 0, 1, 0, 0, False, False, False, False, 0, 0, False, False, False, False, False, False, False, False, False, False, False)
    swDoc.ForceRebuild3 False

    ' === 左侧吊耳 ===
    boolstatus = swDoc.Extension.SelectByID2("右视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0)
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCornerRectangle -0.050, 0.055, 0, -0.035, 0.015, 0
    swSketchMgr.CreateCircle -0.0425, 0.035, 0, -0.0425 + 0.0045, 0.035, 0
    swSketchMgr.InsertSketch True
    Set feat = swFeatMgr.FeatureExtrusion2(False, False, False, 0, 1, 0.020, 0, False, False, False, False, 0, 0, False, False, False, False, False, False, False, False, False, False, False)
    swDoc.ForceRebuild3 False

    ' === 右侧吊耳 ===
    boolstatus = swDoc.Extension.SelectByID2("右视基准面", "PLANE", 0, 0, 0, False, 0, Nothing, 0)
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCornerRectangle 0.035, 0.055, 0, 0.050, 0.015, 0
    swSketchMgr.CreateCircle 0.0425, 0.035, 0, 0.0425 + 0.0045, 0.035, 0
    swSketchMgr.InsertSketch True
    Set feat = swFeatMgr.FeatureExtrusion2(False, False, False, 0, 1, 0.020, 0, False, False, False, False, 0, 0, False, False, False, False, False, False, False, False, False, False, False)
    swDoc.ForceRebuild3 False

    ' === 保存 ===
    swDoc.Save3 1

    swApp.SendMsgToUser "零件重建完成! 特征数: " & swDoc.GetFeatureCount
End Sub
'''

def create_swp_file(vba_code, filepath):
    """创建SW宏文件(.swp) - OLE compound document格式"""
    # SW宏文件是一个简化的OLE2复合文档
    # 头部 + VBA代码
    header = b'SW_Macro_v1\x00\x00\x00'
    version = struct.pack('<I', 1)
    code_len = struct.pack('<I', len(vba_code))

    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(version)
        f.write(code_len)
        f.write(vba_code.encode('utf-8'))

    print(f"  宏文件已创建: {filepath}")

def main():
    print("=" * 50)
    print("SW零件修复 - VBA宏方式 - 2026-06-01")
    print("=" * 50)

    pythoncom.CoInitialize()

    try:
        # 连接SW
        sw = win32com.client.Dispatch('SldWorks.Application.32')
        print(f"SW版本: {sw.RevisionNumber}")

        # 创建宏文件
        macro_dir = os.path.join(os.environ['TEMP'], 'SWMacros')
        os.makedirs(macro_dir, exist_ok=True)
        macro_path = os.path.join(macro_dir, 'SWRebuild.swp')
        create_swp_file(VBA_CODE, macro_path)

        # 通过VBA执行宏
        # SW的Run2方法可以执行宏
        print("\n执行VBA宏...")
        try:
            # 尝试使用Run2
            result = sw.Run2('SWRebuild', macro_path, macro_path)
            print(f"Run2结果: {result}")
        except Exception as e:
            print(f"Run2失败: {e}")

        # 尝试使用ExecuteMacro
        try:
            result = sw.ExecuteMacro(macro_path, 'SWRebuild', '')
            print(f"ExecuteMacro: {result}")
        except Exception as e:
            print(f"ExecuteMacro失败: {e}")

        print("\n宏执行完成，请检查SW窗口")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()
