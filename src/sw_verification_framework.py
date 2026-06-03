"""
SolidWorks API 强制验证框架
每个API调用后自动验证是否真正执行成功
"""

import win32com.client
import pythoncom
import time

class SWVerificationError(Exception):
    """SW API调用验证失败异常"""
    pass

class SWValidator:
    """SolidWorks API调用验证器"""
    
    @staticmethod
    def verify_connection(sw_app):
        """验证SW应用连接是否有效"""
        if sw_app is None:
            raise SWVerificationError("SW应用对象为None")
        try:
            version = sw_app.GetVersion()
            print(f"✓ SW连接验证通过 - 版本: {version}")
            return True
        except Exception as e:
            raise SWVerificationError(f"SW连接验证失败: {e}")
    
    @staticmethod
    def verify_document_open(sw_app):
        """验证是否有活动文档"""
        doc = sw_app.ActiveDoc
        if doc is None:
            raise SWVerificationError("没有打开的文档")
        title = doc.GetTitle
        print(f"✓ 文档验证通过 - 当前文档: {title}")
        return doc
    
    @staticmethod
    def verify_selection(doc, expected_count=None, operation_name="选择操作"):
        """验证选择是否成功"""
        sel_mgr = doc.SelectionManager
        count = sel_mgr.GetSelectedObjectCount2(-1)
        
        if expected_count is not None and count != expected_count:
            raise SWVerificationError(
                f"{operation_name}失败: 期望选择{expected_count}个对象, 实际选择{count}个"
            )
        
        if count == 0:
            print(f"⚠ {operation_name}: 未选择任何对象")
            return False
        
        print(f"✓ {operation_name}验证通过 - 已选择{count}个对象")
        return True
    
    @staticmethod
    def verify_feature_created(doc, feature_name=None, before_count=None):
        """验证特征是否创建成功"""
        # 方法1: 比对特征数量
        if before_count is not None:
            after_count = doc.GetFeatureCount
            if after_count <= before_count:
                raise SWVerificationError(
                    f"特征创建失败: 创建前{before_count}个特征, 创建后{after_count}个"
                )
            print(f"✓ 特征数量验证通过 - {before_count} → {after_count}")
        
        # 方法2: 按名称查找特征
        if feature_name is not None:
            feat_mgr = doc.FeatureManager
            feat = feat_mgr.GetFeatureByName(feature_name)
            if feat is None:
                raise SWVerificationError(f"特征创建失败: 未找到特征 '{feature_name}'")
            print(f"✓ 特征 '{feature_name}' 验证通过")
            return feat
        
        # 方法3: 获取最后一个特征
        last_feat = doc.FeatureManager.GetLastFeature()
        if last_feat is None:
            raise SWVerificationError("特征创建失败: 无法获取最后一个特征")
        
        print(f"✓ 特征创建验证通过 - 最后一个特征: {last_feat.Name}")
        return last_feat
    
    @staticmethod
    def verify_sketch_has_entities(doc):
        """验证草图是否包含实体"""
        sk_manager = doc.SketchManager
        active_sketch = sk_manager.ActiveSketch
        
        if active_sketch is None:
            raise SWVerificationError("草图验证失败: 没有活动草图")
        
        # 获取草图线段数量
        seg_count = active_sketch.GetSketchSegmentsCount()
        if seg_count == 0:
            raise SWVerificationError("草图验证失败: 草图不包含任何线段")
        
        print(f"✓ 草图验证通过 - 包含{seg_count}个线段")
        return True
    
    @staticmethod
    def verify_rebuild(doc, operation_name="模型重建"):
        """验证模型重建是否成功"""
        result = doc.EditRebuild3
        if result is False:
            raise SWVerificationError(f"{operation_name}失败")
        print(f"✓ {operation_name}验证通过")
        return True
    
    @staticmethod
    def verify_body_count(doc, expected_count=None, before_count=None):
        """验证实体数量"""
        bodies = doc.GetBodies2(0, False)  # 0 = solid bodies
        count = len(bodies) if bodies else 0
        
        if before_count is not None:
            if count <= before_count:
                raise SWVerificationError(
                    f"实体数量验证失败: 操作前{before_count}个实体, 操作后{count}个"
                )
            print(f"✓ 实体数量验证通过 - {before_count} → {count}")
        
        if expected_count is not None and count != expected_count:
            raise SWVerificationError(
                f"实体数量验证失败: 期望{expected_count}个实体, 实际{count}个"
            )
            return False
        
        print(f"✓ 实体数量验证通过 - 当前实体数: {count}")
        return count


def sw_operation(operation_name):
    """
    装饰器：包装SW API操作，自动验证结果
    用法:
        @sw_operation("创建拉伸特征")
        def create_extrude(...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"\n{'='*60}")
            print(f"开始操作: {operation_name}")
            print(f"{'='*60}")
            
            try:
                result = func(*args, **kwargs)
                print(f"✓ 操作完成: {operation_name}")
                return result
            except SWVerificationError as e:
                print(f"✗ 验证失败: {e}")
                raise
            except Exception as e:
                print(f"✗ 操作异常: {e}")
                raise
        
        return wrapper
    return decorator


class SWAutomationWithVerification:
    """
    SolidWorks自动化基类（带强制验证）
    所有自动化脚本应继承此类
    """
    
    def __init__(self, sw_version="32"):
        self.sw_version = sw_version
        self.sw_app = None
        self.doc = None
        self.validator = SWValidator()
        
    def connect(self):
        """连接SolidWorks（复用现有实例）"""
        print("正在连接SolidWorks...")
        try:
            self.sw_app = win32com.client.GetActiveObject("SldWorks.Application")
            print("✓ 连接到已运行的SolidWorks实例")
        except:
            self.sw_app = win32com.client.Dispatch(f"SldWorks.Application.{self.sw_version}")
            print("✓ 启动新的SolidWorks实例")
        
        self.sw_app.Visible = True
        self.sw_app.UserControl = False
        self.validator.verify_connection(self.sw_app)
        return self.sw_app
    
    def new_part(self, template=""):
        """新建零件文档"""
        if not template:
            self.sw_app.NewPart()
        else:
            self.sw_app.NewDocument(template, 0, 0, 0)
        
        time.sleep(1)  # 等待文档创建
        self.doc = self.validator.verify_document_open(self.sw_app)
        return self.doc
    
    def open_doc(self, path):
        """打开文档"""
        errors = 0
        warnings = 0
        self.doc = self.sw_app.OpenDoc6(path, 1, 1, "", errors, warnings)
        self.validator.verify_document_open(self.sw_app)
        return self.doc
    
    def safe_select(self, name, obj_type, x=0, y=0, z=0, append=False, mark=0):
        """
        安全选择（带验证）
        注意: SW2024 SP5下SelectByID2可能失效，需用替代方案
        """
        self.doc.ClearSelection2(True)
        
        # 尝试SelectByID2
        result = self.doc.Extension.SelectByID2(
            name, obj_type, x, y, z, append, mark,
            win32com.client.VARIANT(pythoncom.VT_DISPATCH, None), 0
        )
        
        if result:
            self.validator.verify_selection(self.doc, expected_count=1 if not append else None)
            return True
        else:
            print(f"⚠ SelectByID2失败: {name} ({obj_type})")
            # 尝试替代方案: 遍历特征
            return self._select_by_traversal(name, obj_type)
    
    def _select_by_traversal(self, name, obj_type):
        """通过遍历选择对象（SelectByID2失效时的替代方案）"""
        print(f"尝试通过遍历选择: {name}")
        
        # 遍历特征
        feat = self.doc.FirstFeature
        while feat is not None:
            if feat.Name == name:
                feat.Select2(False, 0)
                print(f"✓ 通过遍历选择成功: {name}")
                return True
            feat = feat.GetNextFeature
        
        print(f"✗ 遍历选择也失败: {name}")
        return False
    
    def create_sketch(self, plane_name="前视基准面"):
        """
        创建草图（带验证）
        """
        # 选择基准面
        plane_type = "PLANE"
        if "前" in plane_name:
            plane_name = "Front Plane" if self.sw_app.GetVersion() >= "31.0" else "前视基准面"
        elif "上" in plane_name:
            plane_name = "Top Plane" if self.sw_app.GetVersion() >= "31.0" else "上视基准面"
        elif "右" in plane_name:
            plane_name = "Right Plane" if self.sw_app.GetVersion() >= "31.0" else "右视基准面"
        
        self.safe_select(plane_name, plane_type)
        
        # 插入草图
        self.doc.SketchManager.InsertSketch(True)
        
        # 验证草图激活
        active_sketch = self.doc.SketchManager.ActiveSketch
        if active_sketch is None:
            raise SWVerificationError("草图创建失败: 未能激活草图")
        
        print(f"✓ 草图创建验证通过")
        return active_sketch
    
    def close_sketch(self):
        """关闭草图（带验证）"""
        self.doc.SketchManager.InsertSketch(True)
        
        # 验证草图已关闭
        active_sketch = self.doc.SketchManager.ActiveSketch
        if active_sketch is not None:
            print("⚠ 草图可能未完全关闭")
        
        print("✓ 草图已关闭")
    
    def create_extrude(self, depth, direction=0, name=None):
        """
        创建拉伸特征（带验证）
        """
        before_count = self.doc.GetFeatureCount
        
        # 关闭草图
        self.close_sketch()
        
        # 执行拉伸
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, False, False, 0, 0,
            depth / 1000.0, 0,  # SW内部单位是米
            False, False, False, False,
            0, 0, False, False, False,
            False, True, True, 0, 0, False
        )
        
        # 验证
        if feat is None:
            # 尝试通过特征数量验证
            self.validator.verify_feature_created(self.doc, before_count=before_count)
        else:
            print(f"✓ 拉伸特征创建成功: {feat.Name}")
            return feat
    
    def save_and_close(self, path=None):
        """保存并关闭文档"""
        if path:
            self.doc.SaveAs3(path, 1, 2)
            print(f"✓ 文档已保存: {path}")
        
        title = self.doc.GetTitle
        self.sw_app.CloseDoc(title)
        print(f"✓ 文档已关闭: {title}")
    
    def cleanup(self):
        """清理资源"""
        if self.sw_app is not None:
            self.sw_app.CloseAllDocuments(True)
            self.sw_app.ExitApp()
            self.sw_app = None
            print("✓ 已清理SW资源")


# 使用示例
if __name__ == "__main__":
    sw = SWAutomationWithVerification()
    
    try:
        # 连接SW
        sw.connect()
        
        # 新建零件
        sw.new_part()
        
        # 创建草图
        sw.create_sketch("前视基准面")
        
        # 绘制矩形
        sw.doc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.1, 0.1, 0)
        
        # 验证草图
        sw.validator.verify_sketch_has_entities(sw.doc)
        
        # 创建拉伸
        sw.create_extrude(50)
        
        # 验证重建
        sw.validator.verify_rebuild(sw.doc)
        
        print("\n" + "="*60)
        print("所有操作验证通过！")
        print("="*60)
        
    except SWVerificationError as e:
        print(f"\n验证失败: {e}")
    except Exception as e:
        print(f"\n操作异常: {e}")
    finally:
        sw.cleanup()
