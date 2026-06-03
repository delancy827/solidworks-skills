"""
叉形接头自动化建模脚本 v4
策略: 嵌套轮廓（外轮廓+内轮廓槽），一次拉伸成型
"""

import win32com.client
import pythoncom
import time

class SWAuto:
    def __init__(self):
        self.sw = None
        self.doc = None

    def connect(self):
        print("=" * 70)
        print("[1/5] 连接SolidWorks...")
        self.sw = win32com.client.GetActiveObject("SldWorks.Application")
        self.sw.Visible = True
        self.sw.UserControl = False
        print("   ✓ SW连接成功")
        return self.sw

    def new_part(self):
        print("\n[2/5] 新建零件...")
        template = r'C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot'
        self.sw.NewDocument(template, 0, 0, 0)
        time.sleep(1)
        self.doc = self.sw.ActiveDoc
        print(f"   ✓ 零件: {self.doc.GetTitle}")
        return self.doc

    def select_plane(self, name):
        print(f"\n   选择基准面: {name}")
        self.doc.ClearSelection2(True)
        try:
            result = self.doc.Extension.SelectByID2(
                name, "PLANE", 0, 0, 0, False, 0,
                win32com.client.VARIANT(pythoncom.VT_DISPATCH, None), 0
            )
            if result:
                print("   ✓ SelectByID2成功")
                return True
        except:
            pass
        feat = self.doc.FirstFeature
        while feat is not None:
            if feat.Name == name:
                feat.Select2(False, 0)
                print("   ✓ 遍历选择成功")
                return True
            feat = feat.GetNextFeature
        return False

    def create_sketch(self):
        print("\n[3/5] 创建草图...")
        self.doc.SketchManager.InsertSketch(True)
        sketch = self.doc.SketchManager.ActiveSketch
        print(f"   ✓ 草图: {sketch.Name}")
        return sketch

    def draw_nested_profile(self):
        """绘制嵌套轮廓（外轮廓+内轮廓槽）"""
        print("\n[4/5] 绘制嵌套轮廓...")
        sm = self.doc.SketchManager

        R = 0.025      # 圆头半径 25mm
        L = 0.160      # 圆心距 160mm

        # === 外轮廓: 哑铃形 ===
        print("   画外轮廓...")

        # 左半圆弧
        sm.Create3PointArc(0, 0.025, 0, 0, -0.025, 0, 0.025, 0, 0)
        # 右半圆弧
        sm.Create3PointArc(0.160, -0.025, 0, 0.160, 0.025, 0, 0.135, 0, 0)
        # 上切线
        sm.CreateLine(0, 0.025, 0, 0.160, 0.025, 0)
        # 下切线
        sm.CreateLine(0.160, -0.025, 0, 0, -0.025, 0)

        print("   ✓ 外轮廓完成")

        # === 内轮廓: 槽 (作为"孔") ===
        print("   画内轮廓槽...")

        # 槽矩形: (70mm, -12.5mm) 到 (160mm, 12.5mm)
        sm.CreateCornerRectangle(0.070, -0.0125, 0, 0.160, 0.0125, 0)

        print("   ✓ 内轮廓槽完成")
        print("   注意: 内轮廓应被识别为孔，形成叉形")

    def extrude(self, depth_mm):
        print(f"\n[5/5] 拉伸 {depth_mm}mm...")
        self.doc.SketchManager.InsertSketch(True)

        before = self.doc.GetFeatureCount
        depth = depth_mm / 1000.0

        feat = self.doc.FeatureManager.FeatureExtrusion2(
            True, False, False,
            0, 0,
            depth, 0.0,
            False, False,
            False, False,
            False, False,
            0.0, 0.0,
            False,
            False,
            True,
            True, True,
            0.0,
            False, False
        )

        after = self.doc.GetFeatureCount
        print(f"   特征数: {before} -> {after}")

        if after <= before:
            raise Exception("拉伸失败")

        print(f"   ✓ 拉伸成功")
        return feat

    def create_hole(self, x, y, diam_mm, name):
        """创建孔（尝试用切除方式）"""
        print(f"\n   创建{name}: φ{diam_mm} @ ({x*1000}mm, {y*1000}mm)")

        # 选择前视基准面
        if not self.select_plane("Front Plane"):
            if not self.select_plane("前视基准面"):
                print("   ⚠ 无法选择基准面")
                return False

        # 创建草图
        self.doc.SketchManager.InsertSketch(True)

        # 画圆
        r = diam_mm / 2000.0
        self.doc.SketchManager.CreateCircleByRadius(x, y, 0, r)

        # 退出草图
        self.doc.SketchManager.InsertSketch(True)

        # 尝试拉伸切除
        before = self.doc.GetFeatureCount
        try:
            # 尝试FeatureExtrusion2 with Dir=True (某些版本中可能是切除)
            feat = self.doc.FeatureManager.FeatureExtrusion2(
                True, False, True,   # Dir=True
                0, 0,
                0.050, 0.0,          # 50mm > 25mm厚度
                False, False, False, False,
                False, False, 0.0, 0.0,
                False, False,
                True,
                True, True,
                0.0, False, False
            )
            after = self.doc.GetFeatureCount
            if after > before:
                print(f"   ✓ {name}创建成功")
                return True
        except Exception as e:
            print(f"   ⚠ 切除失败: {e}")

        print(f"   ⚠ {name}需要手动创建")
        return False


def main():
    print("=" * 70)
    print("叉形接头建模 v4 (嵌套轮廓)")
    print("=" * 70)

    sw = SWAuto()

    try:
        sw.connect()
        sw.new_part()

        if not sw.select_plane("Front Plane"):
            if not sw.select_plane("前视基准面"):
                raise Exception("无法选择基准面")

        sw.create_sketch()
        sw.draw_nested_profile()
        sw.extrude(25)

        # 尝试打孔
        sw.create_hole(0, 0, 18, "左端孔")
        sw.create_hole(0.160, 0.018, 18, "右端上孔")  # 约y=18mm
        sw.create_hole(0.160, -0.018, 18, "右端下孔") # 约y=-18mm

        print("\n" + "=" * 70)
        print("✓ 建模完成！")
        print("  请检查SolidWorks中的模型")
        print("  如有问题请截图反馈")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
