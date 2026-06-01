# 连接SolidWorks并获取当前模型基本信息
import pythoncom
import win32com.client

def safe_call(obj, attr, default=None):
    """安全访问COM属性/方法"""
    try:
        val = getattr(obj, attr)
        if callable(val):
            return val()
        return val
    except:
        return default

try:
    sw = win32com.client.Dispatch("SldWorks.Application")
    rev = safe_call(sw, "RevisionNumber")
    print(f"SW版本: {rev}")
    
    doc = sw.ActiveDoc
    if doc is None:
        print("错误: SolidWorks中没有打开的文档")
    else:
        doc_type = safe_call(doc, "GetType", 0)
        type_names = {1: "零件", 2: "装配体", 3: "工程图"}
        print(f"文档类型: {type_names.get(doc_type, '未知')} ({doc_type})")
        print(f"文档名称: {safe_call(doc, 'GetTitle')}")
        print(f"文档路径: {safe_call(doc, 'GetPathName')}")
        
        if doc_type == 1:  # 零件
            # 获取特征数量
            try:
                feat_mgr = doc.FeatureManager
                root = feat_mgr.GetFeatureTreeRootItem()
                if root:
                    count = 0
                    feat = root.GetFirstChild()
                    while feat:
                        count += 1
                        feat = feat.GetNext()
                    print(f"特征数量: {count}")
            except Exception as e2:
                print(f"特征计数失败: {e2}")
            
            # 获取质量属性
            try:
                mass = doc.Extension.CreateMassProperty()
                if mass:
                    mass.UseSystemUnits = False
                    mass.SetCoordinateSystem(None)
                    vol = safe_call(mass, "Volume", 0)
                    area = safe_call(mass, "SurfaceArea", 0)
                    m = safe_call(mass, "Mass", 0)
                    print(f"体积: {vol:.4f} mm^3")
                    print(f"表面积: {area:.4f} mm^2")
                    print(f"质量: {m:.4f} kg")
            except Exception as e2:
                print(f"质量属性获取失败: {e2}")
                
            # 获取边界框
            try:
                bbox = doc.Extension.CreateBoundingBox()
                if bbox:
                    pts = bbox.GetExtremePoints()
                    if pts and len(pts) >= 6:
                        x_min, y_min, z_min, x_max, y_max, z_max = pts[0], pts[1], pts[2], pts[3], pts[4], pts[5]
                        print(f"边界框: X={x_max-x_min:.2f}, Y={y_max-y_min:.2f}, Z={z_max-z_min:.2f} mm")
            except Exception as e2:
                print(f"边界框获取失败: {e2}")
                
            # 获取草图信息
            try:
                sketches = []
                feat = doc.FirstFeature()
                while feat:
                    typename = safe_call(feat, "GetTypeName2", "")
                    if typename == "ProfileFeature":
                        sketches.append(safe_call(feat, "Name", "unnamed"))
                    feat = feat.GetNextFeature()
                print(f"草图数量: {len(sketches)}")
                if sketches:
                    print(f"草图列表: {sketches}")
            except Exception as e2:
                print(f"草图获取失败: {e2}")
                
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
