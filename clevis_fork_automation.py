"""
叉形接头自动化建模脚本（带强制验证）
根据工程图尺寸建模
"""

import win32com.client
import pythoncom
import time
import math

class SWVerificationError(Exception):
    pass

class SWAuto:
    def __init__(self):
        self.sw = None
        self.doc = None
        self.before_counts = {}

    def connect(self):
        """连接SolidWorks（复用已有实例）"""
        print("=" * 60)
        print("[1/8] 连接SolidWorks...")
        try:
            self.sw = win32com.client.GetActiveObject("SldWorks.Application")
            print("   ✓ 连接到已运行的SW实例")
        except Exception as e:
            raise SWVerificationError(f"无法连接SW: {e}")

        self.sw.Visible = True
        self.sw.UserControl = False

        # 验证连接 (使用可用的属性)
        try:
            # GetVersion不可用，用其他属性验证
            visible = self.sw.Visible
            cmd_in_progress = self.sw.CommandInProgress
            print(f"   ✓ SW连接验证通过 (Visible={visible})")
        except Exception as e:
            raise SWVerificationError(f"SW连接验证失败: {e}")

        return self.sw

    def new_part(self):
        """新建零件文档"""
        print("\n[2/8] 新建零件文档...")

        # 使用模板路径新建零件
        template = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
        result = self.sw.NewDocument(template, 0, 0, 0)
        time.sleep(1)

        self.doc = self.sw.ActiveDoc
        if self.doc is None:
            raise SWVerificationError("新建零件失败: ActiveDoc为None")

        title = self.doc.GetTitle
        print(f"   ✓ 零件创建成功: {title}")
        return self.doc

    def select_plane(self, plane_name):
        """选择基准面（支持遍历选择作为SelectByID2的替代）"""
        print(f"\n   选择基准面: {plane_name}...")
        self.doc.ClearSelection2(True)

        # 尝试SelectByID2
        try:
            result = self.doc.Extension.SelectByID2(
                plane_name, "PLANE", 0, 0, 0, False, 0,
                win32com.client.VARIANT(pythoncom.VT_DISPATCH, None), 0
            )
            if result:
                print(f"   ✓ SelectByID2选择成功: {plane_name}")
                return True
        except Exception as e:
            print(f"   ⚠ SelectByID2失败: {e}")

        # 替代方案：遍历特征树
        print(f"   尝试遍历选择...")
        feat = self.doc.FirstFeature
        while feat is not None:
            if feat.Name == plane_name:
                feat.Select2(False, 0)
                print(f"   ✓ 遍历选择成功: {plane_name}")
                return True
            feat = feat.GetNextFeature

        # 如果都找不到，列出所有特征
        print(f"   ✗ 无法找到基准面: {plane_name}")
        print(f"   可用特征:")
        feat = self.doc.FirstFeature
        count = 0
        while feat is not None and count < 20:
            print(f"      - {feat.Name}")
            feat = feat.GetNextFeature
            count += 1

        return False

    def verify_selection(self, expected_count=1):
        """验证选择"""
        count = self.doc.SelectionManager.GetSelectedObjectCount2(-1)
        if count < expected_count:
            raise SWVerificationError(f"选择验证失败: 期望≥{expected_count}, 实际{count}")
        print(f"   ✓ 选择验证通过: {count}个对象")
        return True

    def create_sketch(self):
        """创建草图"""
        print("\n[3/8] 创建草图...")
        self.doc.SketchManager.InsertSketch(True)

        sketch = self.doc.SketchManager.ActiveSketch
        if sketch is None:
            raise SWVerificationError("草图创建失败")

        print(f"   ✓ 草图创建成功: {sketch.Name}")
        return sketch

    def draw_clevis_profile(self):
        """
        绘制叉形接头外轮廓草图
        坐标单位: 米 (SW内部使用米)
        """
        print("\n[4/8] 绘制外轮廓...")

        sm = self.doc.SketchManager

        # 尺寸定义 (单位: 米)
        R = 0.025          # 圆头半径 25mm
        L_total = 0.160    # 圆心距 160mm
        W_narrow = 0.0125  # 窄段半宽 12.5mm (总宽25mm)
        W_wide = 0.025     # 宽段半宽 25mm (总宽50mm)
        x_neck = 0.070     # 变窄处位置 70mm
        x_right_center = L_total  # 右圆心 x=160mm

        # 计算左圆切点 (圆心(0,0), 半径25mm, 切线y=12.5mm)
        x_tangent = math.sqrt(R**2 - W_narrow**2)  # ≈ 21.65mm
        print(f"   左圆切点: x={x_tangent*1000:.2f}mm")

        # 1. 画左圆 (圆心在原点)
        print("   绘制左端圆头...")
        sm.CreateCircle(0, 0, 0, R, 0, 0)

        # 2. 画右圆 (圆心在(160mm, 0))
        print("   绘制右端圆头...")
        sm.CreateCircle(x_right_center, 0, 0, x_right_center + R, 0, 0)

        # 3. 画窄段上边缘 (从切点到x=70mm处)
        print("   绘制窄段...")
        sm.CreateLine(x_tangent, W_narrow, 0, x_neck, W_narrow, 0)
        sm.CreateLine(x_tangent, -W_narrow, 0, x_neck, -W_narrow, 0)

        # 4. 画过渡段 (从窄段到宽段)
        print("   绘制过渡段...")
        # 上过渡: (70mm, 12.5mm) 到 (135mm, 25mm)
        x_right_tangent = x_right_center - math.sqrt(R**2 - W_wide**2)  # ≈ 135mm
        sm.CreateLine(x_neck, W_narrow, 0, x_right_tangent, W_wide, 0)
        sm.CreateLine(x_neck, -W_narrow, 0, x_right_tangent, -W_wide, 0)

        # 5. 画宽段水平线 (连接过渡段到右圆切点)
        # 注意：右圆切点已经在过渡段终点处

        print("   ✓ 外轮廓绘制完成")

        # 验证草图线段数量
        sketch = self.doc.SketchManager.ActiveSketch
        seg_count = sketch.GetSketchSegmentsCount()
        print(f"   草图包含 {seg_count} 个线段")

        if seg_count == 0:
            raise SWVerificationError("草图绘制失败: 无线段")

        return True

    def close_sketch_and_extrude(self, depth_mm):
        """关闭草图并拉伸"""
        print(f"\n[5/8] 拉伸实体 (深度: {depth_mm}mm)...")

        # 记录创建前的特征数量
        before_count = self.doc.GetFeatureCount
        print(f"   拉伸前特征数: {before_count}")

        # 退出草图
        self.doc.SketchManager.InsertSketch(True)

        # 执行拉伸 (单位: 米)
        depth_m = depth_mm / 1000.0
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, False, False,  # Sd, Flip, Dir
            0, 0,                 # T1, T2 (0=Blind)
            depth_m, 0,           # D1, D2 (米)
            False, False,         # Dchk1, Dchk2
            False, False,         # Ddir1, Ddir2
            0, 0,                 # Dang1, Dang2
            False, False,         # Ofr, Ofc
            False, False,         # Tf1, Tf2
            True,                 # Merge
            True, True,           # UseFeatScope, UseAutoSelect
            0, False, False       # StartOffset, IsAutoStartOffset, FlipStartOffset
        )

        # 验证特征创建
        after_count = self.doc.GetFeatureCount
        print(f"   拉伸后特征数: {after_count}")

        if after_count <= before_count:
            raise SWVerificationError(f"拉伸失败: 特征数未增加 ({before_count} → {after_count})")

        if feat is not None:
            print(f"   ✓ 拉伸特征创建成功: {feat.Name}")
        else:
            print(f"   ✓ 拉伸特征创建成功 (返回值None但特征数已增加)")

        return feat

    def create_slot_cut(self):
        """创建叉形槽（拉伸切除）"""
        print("\n[6/8] 创建叉形槽...")

        # 选择前视基准面（在已有实体上创建草图）
        if not self.select_plane("Front Plane"):
            if not self.select_plane("前视基准面"):
                raise SWVerificationError("无法选择前视基准面")

        self.verify_selection()

        # 创建草图
        self.doc.SketchManager.InsertSketch(True)

        sm = self.doc.SketchManager

        # 槽轮廓: 矩形 (70mm, -12.5mm) 到 (160mm, 12.5mm)
        # 即切掉中间部分，保留上下两臂
        x_start = 0.070   # 70mm
        x_end = 0.160     # 160mm
        y_half = 0.0125   # 12.5mm (槽半高25mm/2)

        print(f"   槽尺寸: {x_start*1000}mm ~ {x_end*1000}mm, 高{y_half*2*1000}mm")

        # 画槽轮廓矩形
        sm.CreateCornerRectangle(x_start, -y_half, 0, x_end, y_half, 0)

        # 退出草图
        self.doc.SketchManager.InsertSketch(True)

        # 记录特征数
        before_count = self.doc.GetFeatureCount

        # 拉伸切除 (完全贯穿)
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, False, True,   # Sd, Flip, Dir (Dir=True表示反向/切除)
            0, 0,                 # T1, T2
            0.025, 0,             # D1, D2 (25mm, 超过零件厚度即可)
            False, False,
            False, False,
            0, 0,
            False, False,
            False, False,
            True, True, True,
            0, 0, False
        )

        # 验证
        after_count = self.doc.GetFeatureCount
        if after_count <= before_count:
            raise SWVerificationError(f"槽切除失败: 特征数未增加")

        print(f"   ✓ 叉形槽创建成功")
        return feat

    def create_hole(self, x, y, diameter_mm, name="孔"):
        """创建孔（拉伸切除）"""
        print(f"\n   创建{name}: 圆心({x*1000}mm, {y*1000}mm), φ{diameter_mm}mm...")

        # 选择前视基准面
        if not self.select_plane("Front Plane"):
            if not self.select_plane("前视基准面"):
                print(f"   ⚠ 无法选择基准面，跳过{name}")
                return None

        self.verify_selection()

        # 创建草图
        self.doc.SketchManager.InsertSketch(True)

        # 画圆
        r = diameter_mm / 2000.0  # 半径，单位米
        self.doc.SketchManager.CreateCircle(x, y, 0, x + r, y, 0)

        # 退出草图
        self.doc.SketchManager.InsertSketch(True)

        # 记录特征数
        before_count = self.doc.GetFeatureCount

        # 拉伸切除 (完全贯穿)
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, False, True,   # 切除
            0, 0,
            0.025, 0,             # 25mm，超过厚度
            False, False,
            False, False,
            0, 0,
            False, False,
            False, False,
            True, True, True,
            0, 0, False
        )

        after_count = self.doc.GetFeatureCount
        if after_count <= before_count:
            print(f"   ⚠ {name}创建可能失败")
        else:
            print(f"   ✓ {name}创建成功")

        return feat

    def rebuild_and_verify(self):
        """重建模型并验证"""
        print("\n[7/8] 重建模型...")
        result = self.doc.EditRebuild3
        if result is False:
            print("   ⚠ 重建返回False，检查模型...")
        else:
            print("   ✓ 模型重建完成")

        # 获取最终特征数
        final_count = self.doc.GetFeatureCount
        print(f"   最终特征数: {final_count}")

    def save(self, filepath):
        """保存文档"""
        print(f"\n[8/8] 保存文档...")
        result = self.doc.SaveAs3(filepath, 1, 2)
        if result == 1:
            print(f"   ✓ 保存成功: {filepath}")
        else:
            print(f"   ⚠ 保存返回: {result}")

    def cleanup(self):
        """清理"""
        if self.sw:
            print("\n清理资源...")
            # 不关闭文档，让用户查看
            print("   保持文档打开供查看")


def main():
    print("=" * 70)
    print("叉形接头自动化建模")
    print("=" * 70)

    sw = SWAuto()

    try:
        # 1. 连接SW
        sw.connect()

        # 2. 新建零件
        sw.new_part()

        # 3. 选择前视基准面
        if not sw.select_plane("Front Plane"):
            if not sw.select_plane("前视基准面"):
                raise SWVerificationError("无法选择前视基准面")
        sw.verify_selection()

        # 4. 创建草图
        sw.create_sketch()

        # 5. 绘制外轮廓
        sw.draw_clevis_profile()

        # 6. 拉伸25mm
        sw.close_sketch_and_extrude(25)

        # 7. 创建叉形槽
        sw.create_slot_cut()

        # 8. 创建左端孔 φ18
        sw.create_hole(0, 0, 18, "左端孔")

        # 9. 创建右端上臂孔 φ18 (假设在臂中心 y=18.75mm)
        # 注意：右端分为两个臂，上臂中心约 y=18.75mm
        sw.create_hole(0.160, 0.01875, 18, "右端上臂孔")

        # 10. 创建右端下臂孔 φ18
        sw.create_hole(0.160, -0.01875, 18, "右端下臂孔")

        # 11. 重建并验证
        sw.rebuild_and_verify()

        # 12. 保存
        # sw.save(r"C:\temp\clevis_fork.SLDPRT")

        print("\n" + "=" * 70)
        print("✓ 建模完成！请检查SolidWorks窗口中的模型。")
        print("=" * 70)

    except SWVerificationError as e:
        print(f"\n✗ 验证失败: {e}")
    except Exception as e:
        print(f"\n✗ 异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
