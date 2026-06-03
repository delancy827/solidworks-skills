"""
叉形接头自动化建模脚本 - 最终版
自动完成: 基础外形 (哑铃形实体)
手动完成: 切槽、打孔
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
        print("[1/4] 连接SolidWorks...")
        self.sw = win32com.client.GetActiveObject("SldWorks.Application")
        self.sw.Visible = True
        self.sw.UserControl = False
        print("   ✓ SW连接成功")
        return self.sw

    def new_part(self):
        print("\n[2/4] 新建零件...")
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
        print("\n[3/4] 创建草图...")
        self.doc.SketchManager.InsertSketch(True)
        sketch = self.doc.SketchManager.ActiveSketch
        print(f"   ✓ 草图: {sketch.Name}")
        return sketch

    def draw_profile(self):
        """绘制哑铃形外轮廓"""
        print("\n   绘制外轮廓...")
        sm = self.doc.SketchManager

        R = 0.025   # 25mm
        L = 0.160   # 160mm

        # 左半圆弧
        sm.Create3PointArc(0, 0.025, 0, 0, -0.025, 0, 0.025, 0, 0)
        # 右半圆弧
        sm.Create3PointArc(0.160, -0.025, 0, 0.160, 0.025, 0, 0.135, 0, 0)
        # 上切线
        sm.CreateLine(0, 0.025, 0, 0.160, 0.025, 0)
        # 下切线
        sm.CreateLine(0.160, -0.025, 0, 0, -0.025, 0)

        print("   ✓ 轮廓完成")

    def extrude(self, depth_mm):
        print(f"\n[4/4] 拉伸 {depth_mm}mm...")
        self.doc.SketchManager.InsertSketch(True)

        before = self.doc.GetFeatureCount
        depth = depth_mm / 1000.0

        feat = self.doc.FeatureManager.FeatureExtrusion2(
            True, False, False,
            0, 0,
            depth, 0.0,
            False, False, False, False,
            False, False, 0.0, 0.0,
            False, False,
            True,
            True, True,
            0.0, False, False
        )

        after = self.doc.GetFeatureCount
        print(f"   特征数: {before} -> {after}")

        if after <= before:
            raise Exception("拉伸失败")

        print(f"   ✓ 拉伸成功")
        return feat

    def save(self, path):
        print(f"\n保存: {path}")
        self.doc.SaveAs3(path, 1, 2)
        print("   ✓ 已保存")


def main():
    print("=" * 70)
    print("叉形接头自动化建模")
    print("=" * 70)

    sw = SWAuto()

    try:
        sw.connect()
        sw.new_part()

        if not sw.select_plane("Front Plane"):
            if not sw.select_plane("前视基准面"):
                raise Exception("无法选择基准面")

        sw.create_sketch()
        sw.draw_profile()
        sw.extrude(25)

        # 保存
        save_path = r"C:\Users\22374\Desktop\clevis_fork_base.SLDPRT"
        sw.save(save_path)

        print("\n" + "=" * 70)
        print("✓ 基础外形完成！")
        print(f"  已保存: {save_path}")
        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  请手动完成以下操作:")
        print("")
        print("  1) 切槽（形成叉形）:")
        print("     - 在前视基准面新建草图")
        print("     - 画矩形: 从(70mm, -12.5mm) 到 (160mm, 12.5mm)")
        print("     - 拉伸切除 → 完全贯穿")
        print("")
        print("  2) 左端打孔:")
        print("     - 在前视基准面新建草图")
        print("     - 画圆: 圆心(0, 0), 直径18mm")
        print("     - 拉伸切除 → 完全贯穿")
        print("")
        print("  3) 右端上臂打孔:")
        print("     - 画圆: 圆心(160mm, 18.75mm), 直径18mm")
        print("     - 拉伸切除 → 完全贯穿")
        print("")
        print("  4) 右端下臂打孔:")
        print("     - 画圆: 圆心(160mm, -18.75mm), 直径18mm")
        print("     - 拉伸切除 → 完全贯穿")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")
        print("  尺寸汇总:")
        print("     厚度: 25mm")
        print("     左端圆头: φ50mm")
        print("     右端圆头: φ50mm")
        print("     总长: 210mm (含两端圆头)")
        print("     圆心距: 160mm")
        print("     中间窄段: 宽25mm")
        print("     槽尺寸: 90mm × 25mm")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
