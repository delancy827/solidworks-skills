using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace StampingDie
{
    class TestOpenAngle
    {
        [STAThread]
        static void Main(string[] args)
        {
            Console.WriteLine("=== 测试 CreateLine 开放轮廓 89.5° ===\n");

            SldWorks swApp = new SldWorks();
            swApp.Visible = true;
            System.Threading.Thread.Sleep(3000);

            string tpl = swApp.GetUserPreferenceStringValue(
                (int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
            if (string.IsNullOrEmpty(tpl))
                tpl = @"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_part.prtdot";
            swApp.NewDocument(tpl, 0, 0, 0);
            System.Threading.Thread.Sleep(1000);

            ModelDoc2 Part = (ModelDoc2)swApp.ActiveDoc;
            Part.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swSketchAutomaticRelations, false);
            Console.WriteLine("自动几何关系: 已关闭");

            // 选择前视基准面
            bool sel = Part.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!sel)
                sel = Part.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
            Console.WriteLine("选择前视面: " + sel);

            Part.SketchManager.InsertSketch(true);
            Console.WriteLine("草图已创建");

            // 画两条开放的线，形成89.5°角
            // 底边水平，从左到右
            // 斜线从右端点向上，与垂直方向偏差0.5°（即与水平方向夹角89.5°）
            double baseLen = 10.0;
            double wallHeight = 10.0;
            double halfAngleDeg = 0.5;
            double halfAngleRad = halfAngleDeg * Math.PI / 180.0;
            double dx = wallHeight * Math.Tan(halfAngleRad); // 水平偏移

            // 点A(0,0) -> 点B(10,0) 水平底边
            // 点B(10,0) -> 点C(10-dx, 10) 左倾斜壁（89.5°，即向左侧倾斜0.5°）
            // 如果dx>0，斜壁顶部向左侧偏移，形成"开口向右的V"形状
            double ax = 0, ay = 0;
            double bx = baseLen, by = 0;
            double cx = bx - dx, cy = wallHeight; // 左倾

            Console.WriteLine("设计参数:");
            Console.WriteLine("  底边: (0,0) -> (10,0)");
            Console.WriteLine("  斜壁: (10,0) -> ({0:F6},{1:F6})", cx, cy);
            Console.WriteLine("  角度偏差: " + halfAngleDeg + "°");
            Console.WriteLine("  dx = " + dx);

            SketchSegment seg1 = (SketchSegment)Part.SketchManager.CreateLine(ax, ay, 0, bx, by, 0);
            SketchSegment seg2 = (SketchSegment)Part.SketchManager.CreateLine(bx, by, 0, cx, cy, 0);
            Console.WriteLine("seg1 created: " + (seg1 != null));
            Console.WriteLine("seg2 created: " + (seg2 != null));

            // 退出草图
            Part.SketchManager.InsertSketch(true);
            Console.WriteLine("草图已退出");

            // 读取草图中的线段
            Feature feat = (Feature)Part.FirstFeature();
            while (feat != null)
            {
                if (feat.GetTypeName2() == "ProfileFeature" || feat.GetTypeName2() == "Sketch")
                {
                    Console.WriteLine("\n找到草图特征: " + feat.Name);
                    Sketch sk = (Sketch)feat.GetSpecificFeature2();
                    object[] segs = (object[])sk.GetSketchSegments();
                    Console.WriteLine("  线段数: " + (segs != null ? segs.Length : 0));

                    if (segs != null)
                    {
                        for (int i = 0; i < segs.Length; i++)
                        {
                            SketchSegment s = (SketchSegment)segs[i];
                            if (s.GetType() == (int)swSketchSegments_e.swSketchLINE)
                            {
                                SketchLine line = (SketchLine)s;
                                SketchPoint sp = (SketchPoint)line.GetStartPoint2();
                                SketchPoint ep = (SketchPoint)line.GetEndPoint2();
                                double sx = sp.X, sy = sp.Y;
                                double ex = ep.X, ey = ep.Y;
                                double ddx = ex - sx;
                                double ddy = ey - sy;
                                double len = Math.Sqrt(ddx*ddx + ddy*ddy);
                                double angleDeg = Math.Atan2(Math.Abs(ddx), Math.Abs(ddy)) * 180.0 / Math.PI;
                                Console.WriteLine("  Line[" + i + "]: (" + sx.ToString("F6") + "," + sy.ToString("F6") + ") -> (" + ex.ToString("F6") + "," + ey.ToString("F6") + ")");
                                Console.WriteLine("    长度=" + len.ToString("F4") + " 角度(与垂直偏差)=" + angleDeg.ToString("F4") + "°");
                            }
                        }
                    }
                    break;
                }
                feat = (Feature)feat.GetNextFeature();
            }

            // 保存
            Part.SaveAs3("C:/temp/test_open_angle.sldprt", 0, 0);
            Console.WriteLine("\n已保存: C:/temp/test_open_angle.sldprt");
            Console.WriteLine("\n结论: 如果斜壁角度=0.5°则CreateLine有效; 如果=0°则无效");
        }
    }
}
