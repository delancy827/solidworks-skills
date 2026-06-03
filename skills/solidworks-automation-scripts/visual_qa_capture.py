"""
多角度视觉验证截图脚本
Vision-Based Multi-View QA - Screenshot Capture
"""
import os
import sys
import time
import pythoncom
import win32com.client

# 视图配置：(视图名称, 视图ID, 输出文件名)
VIEWS = [
    ('*等轴测', 7, 'Verify_Iso.jpg'),
    ('*前视', 1, 'Verify_Front.jpg'),
    ('*上视', 5, 'Verify_Top.jpg'),
    ('*右视', 4, 'Verify_Right.jpg'),
]

SAVE_DIR = r"C:\Users\Public\sw_verify"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"创建目录: {path}")

def connect_sw():
    try:
        sw = win32com.client.Dispatch("SldWorks.Application")
        print(f"已连接 SolidWorks {sw.RevisionNumber}")
        return sw
    except Exception as e:
        print(f"连接SolidWorks失败: {e}")
        return None

def get_active_doc(sw):
    doc = sw.ActiveDoc
    if doc is None:
        print("错误: SolidWorks中没有活动文档")
        return None
    title = doc.GetTitle if hasattr(doc.GetTitle, '__call__') else doc.GetTitle
    if callable(title):
        title = title()
    print(f"当前文档: {title}")
    return doc

def switch_view(doc, view_name, view_id):
    """切换视图，支持中英文命名"""
    try:
        # 先尝试中文名称
        result = doc.ShowNamedView2(view_name, view_id)
        if result is None or result == 0 or result == True:
            return True
    except:
        pass
    
    # 回退到英文名称
    english_names = {
        1: '*Front', 2: '*Back', 3: '*Left', 4: '*Right',
        5: '*Top', 6: '*Bottom', 7: '*Isometric',
        8: '*Trimetric', 9: '*Dimetric'
    }
    eng_name = english_names.get(view_id, '*Isometric')
    try:
        result = doc.ShowNamedView2(eng_name, view_id)
        if result is None or result == 0 or result == True:
            return True
    except:
        pass
    
    return False

def capture_screenshot(doc, save_path):
    """捕获截图并保存"""
    try:
        # 设置保存选项为JPG
        opts = win32com.client.Dispatch("SldWorks.SaveAsOptions")
        opts.ExportJPGHighQuality = True
        
        result = doc.SaveAs3(save_path, 0, 2)
        if result:
            size = os.path.getsize(save_path)
            print(f"  截图已保存: {save_path} ({size} bytes)")
            return True
        else:
            # 尝试SaveAs2
            result = doc.SaveAs2(save_path, 0)
            if os.path.exists(save_path):
                size = os.path.getsize(save_path)
                print(f"  截图已保存: {save_path} ({size} bytes)")
                return True
    except Exception as e:
        print(f"  截图失败: {e}")
    return False

def run_visual_qa():
    print("="*60)
    print("多角度视觉验证 - 截图捕获")
    print("="*60)
    
    ensure_dir(SAVE_DIR)
    
    sw = connect_sw()
    if not sw:
        return False
    
    doc = get_active_doc(sw)
    if not doc:
        return False
    
    # 获取模型基本信息
    try:
        doc_type = doc.GetType() if hasattr(doc.GetType, '__call__') else doc.GetType
        if callable(doc_type):
            doc_type = doc_type()
    except:
        doc_type = 0
    
    if doc_type != 1:
        print(f"警告: 当前不是零件文档 (类型={doc_type})")
    
    results = []
    for view_name, view_id, filename in VIEWS:
        print(f"\n[ {view_name} ] -> {filename}")
        
        # 切换视图
        ok = switch_view(doc, view_name, view_id)
        if not ok:
            print(f"  警告: 视图切换可能失败，继续尝试截图...")
        
        # 缩放适配
        try:
            doc.ViewZoomtofit2()
        except:
            try:
                doc.ViewZoomToFit()
            except:
                pass
        
        time.sleep(0.5)
        
        # 截图保存
        save_path = os.path.join(SAVE_DIR, filename)
        success = capture_screenshot(doc, save_path)  # 使用完整路径而非仅文件名
        if not success:
            # 尝试SaveAs直接保存
            try:
                doc.SaveAs(save_path)
                if os.path.exists(save_path):
                    size = os.path.getsize(save_path)
                    print(f"  截图已保存: {save_path} ({size} bytes)")
                    success = True
            except Exception as e:
                print(f"  SaveAs也失败: {e}")
        
        results.append({
            'view': view_name,
            'file': filename,
            'path': save_path,
            'success': success and os.path.exists(save_path)
        })
    
    # 恢复等轴测视图
    print("\n恢复等轴测视图...")
    switch_view(doc, '*等轴测', 7)
    try:
        doc.ViewZoomtofit2()
    except:
        pass
    
    # 汇总
    print("\n" + "="*60)
    print("截图汇总:")
    success_count = 0
    for r in results:
        status = "成功" if r['success'] else "失败"
        print(f"  {r['file']}: {status}")
        if r['success']:
            success_count += 1
    print(f"\n成功: {success_count}/{len(results)}")
    print("="*60)
    
    return success_count == len(results)

if __name__ == '__main__':
    run_visual_qa()
