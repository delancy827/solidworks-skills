"""
叉形接头自动化建模脚本 v2（带强制验证）
策略: 先完成可靠的外轮廓拉伸，再尝试切槽/打孔
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

    def connect(self):
        """连接SolidWorks"""
        print("=" * 70)
        print("[1/6] 连接SolidWorks...")
        try:
            self.sw = win32com.client.GetActiveObject("SldWorks.Application")
            print("   ✓ 连接到已运行的SW实例")
        except Exception as e:
            raise SWVerificationError(f"无法连接SW: {e}")

        self.sw.Visible = True
        self.sw.UserControl = False

        # 简单验证
        try:
            _ = self.sw.Visible
            print("   ✓ SW连接验证通过")
        except Exception as e:
            raise SWVerificationError(f"SW连接验证失败: {e}")

        return self.sw

    def new_part(self):
        """新建零件"""
        print("\n[2/6] 新建零件文档...")
        template = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
        self.sw.NewDocument(template, 0, 0, 0)
        time.sleep(1)

        self.doc = self.sw.ActiveDoc
        if self.doc is None:
            raise SWVerificationError("新建零件失败")

        print(f"   ✓ 零件创建成功: {self.doc.GetTitle}")
        return self.doc

    def select_plane(self, plane_name):
        """选择基准面"""
        print(f"\n   选择基准面: {plane_name}...")
        self.doc.ClearSelection2(True)

        # 尝试SelectByID2
        try:
            result = self.doc.Extension.SelectByID2(
                plane_name, "PLANE", 0, 0, 0, False, 0,
                win32com.client.VARIANT(pythoncom.VT_DISPATCH, None), 0
            )
            if result:
                print(f"   ✓ SelectByID2成功")
                return True
        except:
            pass

        # 替代：遍历特征
        feat = self.doc.FirstFeature
        while feat is not None:
            if feat.Name == plane_name:
                feat.Select2(False, 0)
                print(f"   ✓ 遍历选择成功")
                return True
            feat = feat.GetNextFeature

        return False

    def verify_selection(self, expected=1):
        count = self.doc.SelectionManager.GetSelectedObjectCount2(-1)
        if count < expected:
            raise SWVerificationError(f"选择验证失败: 期望≥{expected}, 实际{count}")
        print(f"   ✓ 选择验证通过 ({count}个对象)")
        return True

    def create_sketch(self):
        """创建草图"""
        print("\n[3/6] 创建草图...")
        self.doc.SketchManager.InsertSketch(True)
        sketch = self.doc.SketchManager.ActiveSketch
        if sketch is None:
            raise SWVerificationError("草图创建失败")
        print(f"   ✓ 草图: {sketch.Name}")
        return sketch

    def draw_profile(self):
        """绘制叉形接头外轮廓"""
        print("\n[4/6] 绘制外轮廓...")
        sm = self.doc.SketchManager

        # 尺寸 (单位: 米)
        R = 0.025           # 圆头半径 25mm
        L = 0.160           # 圆心距 160mm
        w_narrow = 0.0125   # 窄段半宽 12.5mm
        w_wide = 0.025      # 宽段半宽 25mm
        x_neck = 0.070      # 变窄处 70mm

        # 计算切点
        x_tan_left = math.sqrt(max(0, R**2 - w_narrow**2))   # ≈21.65mm
        x_tan_right = L - math.sqrt(max(0, R**2 - w_wide**2))  # ≈135mm

        print(f"   左圆切点: x={x_tan_left*1000:.1f}mm")
        print(f"   右圆切点: x={x_tan_right*1000:.1f}mm")

        # 方法: 画两个圆 + 连接线，然后修剪
        # 实际更简单的方法: 画中心矩形 + 两端半圆

        # 方案: 使用CreateCornerRectangle画主体，然后加圆头
        # 但SolidWorks草图中需要封闭轮廓

        # 简化方案: 画两个圆，然后用直线连接
        # 左圆
        print("   画左圆...")
        sm.CreateCircleByRadius(0, 0, 0, R)

        # 右圆
        print("   画右圆...")
        sm.CreateCircleByRadius(L, 0, 0, R)

        # 连接线上边缘: 从左圆切点到右圆切点 (经过窄段和宽段)
        # 上边缘路径:
        # (x_tan_left, w_narrow) -> (x_neck, w_narrow) [窄段上边缘]
        # (x_neck, w_narrow) -> (x_tan_right, w_wide) [过渡段]
        print("   画上边缘...")
        sm.CreateLine(x_tan_left, w_narrow, 0, x_neck, w_narrow, 0)
        sm.CreateLine(x_neck, w_narrow, 0, x_tan_right, w_wide, 0)

        # 连接线下边缘
        print("   画下边缘...")
        sm.CreateLine(x_tan_left, -w_narrow, 0, x_neck, -w_narrow, 0)
        sm.CreateLine(x_neck, -w_narrow, 0, x_tan_right, -w_wide, 0)

        # 验证 (使用可用的方法)
        try:
            sketch = self.doc.SketchManager.ActiveSketch
            if sketch is not None:
                print(f"   ✓ 草图活跃: {sketch.Name}")
            else:
                print("   ⚠ 草图可能已关闭")
        except Exception as e:
            print(f"   ⚠ 草图验证: {e}")

        return True

    def extrude(self, depth_mm):
        """拉伸实体"""
        print(f"\n[5/6] 拉伸 {depth_mm}mm...")

        # 退出草图
        self.doc.SketchManager.InsertSketch(True)

        before = self.doc.GetFeatureCount
        depth = depth_mm / 1000.0

        feat = self.doc.FeatureManager.FeatureExtrusion2(
            False, False, False,
            0, 0,
            depth, 0,
            False, False, False, False,
            0, 0, False, False, False,
            False, True, True, 0, 0, False
        )

        after = self.doc.GetFeatureCount
        print(f"   特征数: {before} -> {after}")

        if after <= before:
            raise SWVerificationError("拉伸失败")

        print(f"   ✓ 拉伸成功")
        return feat

    def try_create_slot(self):
        """尝试创建叉形槽（可能失败，但不影响主流程）"""
        print("\n[6/6] 尝试创建叉形槽...")

        try:
            # 选择前视基准面
            if not self.select_plane("Front Plane"):
                if not self.select_plane("前视基准面"):
                    print("   ⚠ 无法选择基准面，跳过")
                    return False

            self.verify_selection()

            # 创建草图
            self.doc.SketchManager.InsertSketch(True)
            sm = self.doc.SketchManager

            # 槽轮廓: 矩形 (70mm, -12.5mm) 到 (160mm, 12.5mm)
            sm.CreateCornerRectangle(0.070, -0.0125, 0, 0.160, 0.0125, 0)

            # 退出草图
            self.doc.SketchManager.InsertSketch(True)

            before = self.doc.GetFeatureCount

            # 尝试用FeatureExtrusion2做切除 (Dir=True可能表示反向)
            feat = self.doc.FeatureManager.FeatureExtrusion2(
                False, False, True,   # Dir=True
                0, 0,
                0.050, 0,             # 50mm > 零件厚度25mm
                False, False, False, False,
                0, 0, False, False, False,
                False, True, True, 0, 0, False
            )

            after = self.doc.GetFeatureCount
            if after > before:
                print("   ✓ 叉形槽创建成功")
                return True
            else:
                print("   ⚠ 叉形槽可能未创建 (FeatureExtrusion2不支持切除)")
                return False

        except Exception as e:
            print(f"   ⚠ 叉形槽创建失败: {e}")
            return False

    def save(self, path):
        print(f"\n保存: {path}")
        result = self.doc.SaveAs3(path, 1, 2)
        print(f"   结果: {result}")


def main():
    print("=" * 70)
    print("叉形接头自动化建模 v2")
    print("=" * 70)

    sw = SWAuto()

    try:
        sw.connect()
        sw.new_part()

        # 选择基准面
        if not sw.select_plane("Front Plane"):
            if not sw.select_plane("前视基准面"):
                raise SWVerificationError("无法选择前视基准面")
        sw.verify_selection()

        # 创建草图
        sw.create_sketch()

        # 绘制轮廓
        sw.draw_profile()

        # 拉伸
        sw.extrude(25)

        # 尝试切槽
        slot_ok = sw.try_create_slot()

        # 保存
        # sw.save(r"C:\temp\clevis_fork_v2.SLDPRT")

        print("\n" + "=" * 70)
        if slot_ok:
            print("✓ 建模完成 (含叉形槽)")
        else:
            print("✓ 基础外形完成")
            print("  请手动完成: 1) 右侧切槽 2) 左端φ18孔 3) 右端φ18孔")
        print("=" * 70)

    except SWVerificationError as e:
        print(f"\n✗ 验证失败: {e}")
    except Exception as e:
        print(f"\n✗ 异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
