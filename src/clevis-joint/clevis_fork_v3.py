"""
叉形接头自动化建模脚本 v3
策略: 画封闭轮廓（圆弧+直线），然后拉伸
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

        # 遍历选择
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

    def draw_closed_profile(self):
        """绘制封闭的哑铃形轮廓"""
        print("\n[4/5] 绘制封闭轮廓...")
        sm = self.doc.SketchManager

        # 尺寸 (米)
        R = 0.025      # 圆头半径 25mm
        L = 0.160      # 两圆心距 160mm

        # 方案: 画2个半圆弧 + 2条切线 = 封闭轮廓
        # 左圆右半圆弧: 从(0,25)到(0,-25)，经过(25,0)
        # 使用3点圆弧: 起点、终点、中间点

        print("   画左半圆弧...")
        try:
            # Create3PointArc(起点, 终点, 中间点)
            sm.Create3PointArc(0, 0.025, 0, 0, -0.025, 0, 0.025, 0, 0)
            print("   ✓ 左半圆弧成功")
        except Exception as e:
            print(f"   ⚠ 左半圆弧失败: {e}")
            # 备选: 画完整圆
            sm.CreateCircleByRadius(0, 0, 0, R)
            print("   ✓ 用整圆替代")

        print("   画右半圆弧...")
        try:
            # 右圆左半圆弧: 从(160,-25)到(160,25)，经过(135,0)
            sm.Create3PointArc(0.160, -0.025, 0, 0.160, 0.025, 0, 0.135, 0, 0)
            print("   ✓ 右半圆弧成功")
        except Exception as e:
            print(f"   ⚠ 右半圆弧失败: {e}")
            sm.CreateCircleByRadius(0.160, 0, 0, R)
            print("   ✓ 用整圆替代")

        print("   画上切线...")
        sm.CreateLine(0, 0.025, 0, 0.160, 0.025, 0)

        print("   画下切线...")
        sm.CreateLine(0.160, -0.025, 0, 0, -0.025, 0)

        print("   ✓ 轮廓绘制完成")

    def extrude(self, depth_mm):
        print(f"\n[5/5] 拉伸 {depth_mm}mm...")
        self.doc.SketchManager.InsertSketch(True)

        before = self.doc.GetFeatureCount
        depth = depth_mm / 1000.0

        # 使用之前成功过的参数格式
        # FeatureExtrusion2 正确签名：23个参数 (SW 2024)
        # [Sd][Flip][Dir][T1][T2][D1][D2][Dchk1][Dchk2][Ddir1][Ddir2][Dang1][Dang2]
        # [Ofr][Ofc][Tf1][Tf2][Merge][UseFeatScope][UseAutoSelect]
        # [StartOffset][IsAutoStartOffset][FlipStartOffset]
        feat = self.doc.FeatureManager.FeatureExtrusion2(
            True, False, False,   # Sd, Flip, Dir
            0, 0,                 # T1, T2
            depth, 0.0,           # D1, D2
            False, False,         # Dchk1, Dchk2
            False, False,         # Ddir1, Ddir2
            0.0, 0.0,             # Dang1, Dang2
            False,                # Ofr
            False,                # Ofc
            False, False,         # Tf1, Tf2
            True,                 # Merge
            True, True,           # UseFeatScope, UseAutoSelect
            0.0,                  # StartOffset
            False, False          # IsAutoStartOffset, FlipStartOffset
        )

        after = self.doc.GetFeatureCount
        print(f"   特征数: {before} -> {after}")

        if after <= before:
            raise Exception("拉伸失败")

        print(f"   ✓ 拉伸成功")
        return feat


def main():
    print("=" * 70)
    print("叉形接头建模 v3")
    print("=" * 70)

    sw = SWAuto()

    try:
        sw.connect()
        sw.new_part()

        if not sw.select_plane("Front Plane"):
            if not sw.select_plane("前视基准面"):
                raise Exception("无法选择基准面")

        sw.create_sketch()
        sw.draw_closed_profile()
        sw.extrude(25)

        print("\n" + "=" * 70)
        print("✓ 基础外形完成！")
        print("  请手动完成: 1) 右侧切槽 2) 左端φ18孔 3) 右端φ18孔")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
