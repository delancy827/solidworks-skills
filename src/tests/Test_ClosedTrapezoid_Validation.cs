using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace StampingDie
{
    class TestClosedTrapezoid
    {
        [STAThread]
        static void Main(string[] args)
        {
            Console.WriteLine("=== 测试闭合梯形轮廓 89.5° ===\n");

            double halfAngleDeg = 0.5;
            double halfAngleRad = halfAngleDeg * Math.PI / 180.0;
            double height = 10.0;
            double topWidth = 10.0;
            double botWidth = topWidth + 2 * height * Math.Tan(halfAngleRad);
            double dx = height * Math.Tan(halfAngleRad);

            Console.WriteLine("设计参数:");
            Console.WriteLine("  高度=" + height + " 顶宽=" + topWidth + " 底宽=" + botWidth.ToString("F4"));
            Console.WriteLine("  dx=" + dx.ToString("F6"));

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

            bool sel = Part.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!sel) sel = Part.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
            Part.SketchManager.InsertSketch(true);

            // 画闭合梯形（逆时针）
            // 顶边: (0, height) -> (topWidth, height)
            // 右斜壁: (topWidth, height) -> (topWidth + dx, 0)
            // 底边: (topWidth + dx, 0) -> (-dx, 0)
            // 左斜壁: (-dx, 0) -> (0, height)
            double x0 = 0, y0 = height;
            double x1 = topWidth, y1 = height;
            double x2 = topWidth + dx, y2 = 0;
            double x3 = -dx, y3 = 0;

            Console.WriteLine("\n传入坐标:");
            Console.WriteLine("  顶边: ({0:F6},{1:F6}) -> ({2:F6},{3:F6})", x0, y0, x1, y1);
            Console.WriteLine("  右壁: ({0:F6},{1:F6}) -> ({2:F6},{3:F6})", x1, y1, x2, y2);
            Console.WriteLine("  底边: ({0:F6},{1:F6}) -> ({2:F6},{3:F6})", x2, y2, x3, y3);
            Console.WriteLine("  左壁: ({0:F6},{1:F6}) -> ({2:F6},{3:F6})", x3, y3, x0, y0);

            Part.SketchManager.CreateLine(x0, y0, 0, x1, y1, 0);
            Part.SketchManager.CreateLine(x1, y1, 0, x2, y2, 0);
            Part.SketchManager.CreateLine(x2, y2, 0, x3, y3, 0);
            Part.SketchManager.CreateLine(x3, y3, 0, x0, y0, 0);

            Part.SketchManager.InsertSketch(true);
            Console.WriteLine("草图已退出\n");

            // 读取所有线段
            Feature feat = (Feature)Part.FirstFeature();
            while (feat != null)
            {
                if (feat.GetTypeName2() == "ProfileFeature" || feat.GetTypeName2() == "Sketch")
                {
                    Console.WriteLine("草图: " + feat.Name);
                    Sketch sk = (Sketch)feat.GetSpecificFeature2();
                    object[] segs = (object[])sk.GetSketchSegments();
                    Console.WriteLine("线段数: " + (segs != null ? segs.Length : 0));

                    if (segs != null)
                    {
                        foreach (object sobj in segs)
                        {
                            SketchSegment s = (SketchSegment)sobj;
                            if (s.GetType() == (int)swSketchSegments_e.swSketchLINE)
                            {
                                SketchLine line = (SketchLine)s;
                                SketchPoint sp = (SketchPoint)line.GetStartPoint2();
                                SketchPoint ep = (SketchPoint)line.GetEndPoint2();
                                double ddx = ep.X - sp.X;
                                double ddy = ep.Y - sp.Y;
                                double angleFromVert = Math.Atan2(Math.Abs(ddx), Math.Abs(ddy)) * 180.0 / Math.PI;
                                double angleFromHoriz = Math.Atan2(Math.Abs(ddy), Math.Abs(ddx)) * 180.0 / Math.PI;
                                Console.WriteLine("  Line: ({0:F6},{1:F6}) -> ({2:F6},{3:F6})", sp.X, sp.Y, ep.X, ep.Y);
                                Console.WriteLine("    与垂直偏差: {0:F4}°  与水平偏差: {1:F4}°", angleFromVert, angleFromHoriz);
                            }
                        }
                    }
                    break;
                }
                feat = (Feature)feat.GetNextFeature();
            }

            // 测试FeatureExtrusion2
            Console.WriteLine("\n测试FeatureExtrusion2...");
            Feature extr = Part.FeatureManager.FeatureExtrusion2(
                true, false, false, 0, 0,
                20.0, 0.0, false, false, false, false,
                0.0, 0.0, false, false, false, false,
                true, true, true, 0, 0.0, false);
            Console.WriteLine("结果: " + (extr != null ? extr.Name : "失败"));

            Part.SaveAs3("C:/temp/test_trapezoid.sldprt", 0, 0);
            Console.WriteLine("\n已保存: C:/temp/test_trapezoid.sldprt");
        }
    }
}
