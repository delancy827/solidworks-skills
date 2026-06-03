using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace StampingDie
{
    class TestNotchedProfile
    {
        [STAThread]
        static void Main(string[] args)
        {
            Console.WriteLine("=== 测试单轮廓凹口法创建U形槽 ===\n");

            // 参数
            double W = 62.0;   // 凸模宽
            double H = 27.0;   // 凸模高
            double L = 80.0;   // 凸模长
            double slotDepth = 25.0;
            double slotTopW = 37.8;
            double halfAngleRad = 0.5 * Math.PI / 180.0;
            double dx = slotDepth * Math.Tan(halfAngleRad);
            double slotBotW = slotTopW + 2 * dx;
            double slotY = H - slotDepth; // 2mm
            double cx = W / 2;

            Console.WriteLine("参数: W={0} H={1} L={2}", W, H, L);
            Console.WriteLine("槽: 顶宽={0:F3} 底宽={1:F3} 深度={2} 底Y={3}", slotTopW, slotBotW, slotDepth, slotY);
            Console.WriteLine("dx={0:F6}\n", dx);

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

            bool sel = Part.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!sel) sel = Part.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
            Part.SketchManager.InsertSketch(true);

            // 单轮廓凹口（逆时针）
            // 1. 左下 (0,0)
            // 2. 右下 (W,0)
            // 3. 右中槽口右沿 (cx + slotTopW/2, H) = (31+18.9, 27) = (49.9, 27)
            // 4. 右斜壁底 (cx + slotBotW/2, slotY) = (31+19.118, 2) = (50.118, 2)
            // 5. 左斜壁底 (cx - slotBotW/2, slotY) = (31-19.118, 2) = (11.882, 2)
            // 6. 左中槽口左沿 (cx - slotTopW/2, H) = (31-18.9, 27) = (12.1, 27)
            // 7. 左上 (0,H)
            // 回到 (0,0)
            double x1 = 0, y1 = 0;
            double x2 = W, y2 = 0;
            double x3 = cx + slotTopW / 2, y3 = H;
            double x4 = cx + slotBotW / 2, y4 = slotY;
            double x5 = cx - slotBotW / 2, y5 = slotY;
            double x6 = cx - slotTopW / 2, y6 = H;
            double x7 = 0, y7 = H;

            Console.WriteLine("轮廓顶点:");
            Console.WriteLine("  P1({0:F3},{1:F3}) 左下", x1, y1);
            Console.WriteLine("  P2({0:F3},{1:F3}) 右下", x2, y2);
            Console.WriteLine("  P3({0:F3},{1:F3}) 槽口右上", x3, y3);
            Console.WriteLine("  P4({0:F3},{1:F3}) 右斜壁底", x4, y4);
            Console.WriteLine("  P5({0:F3},{1:F3}) 左斜壁底", x5, y5);
            Console.WriteLine("  P6({0:F3},{1:F3}) 槽口左上", x6, y6);
            Console.WriteLine("  P7({0:F3},{1:F3}) 左上\n", x7, y7);

            Part.SketchManager.CreateLine(x1, y1, 0, x2, y2, 0);
            Part.SketchManager.CreateLine(x2, y2, 0, x3, y3, 0);
            Part.SketchManager.CreateLine(x3, y3, 0, x4, y4, 0);
            Part.SketchManager.CreateLine(x4, y4, 0, x5, y5, 0);
            Part.SketchManager.CreateLine(x5, y5, 0, x6, y6, 0);
            Part.SketchManager.CreateLine(x6, y6, 0, x7, y7, 0);
            Part.SketchManager.CreateLine(x7, y7, 0, x1, y1, 0);

            Part.SketchManager.InsertSketch(true);
            Console.WriteLine("草图已退出");

            // 读取验证
            Feature feat = (Feature)Part.FirstFeature();
            while (feat != null)
            {
                if (feat.GetTypeName2() == "ProfileFeature" || feat.GetTypeName2() == "Sketch")
                {
                    Sketch sk = (Sketch)feat.GetSpecificFeature2();
                    object[] segs = (object[])sk.GetSketchSegments();
                    Console.WriteLine("线段数: " + (segs != null ? segs.Length : 0));
                    if (segs != null)
                    {
                        int idx = 0;
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
                                Console.WriteLine("  Line[{0}]: ({1:F4},{2:F4})->({3:F4},{4:F4}) 垂直偏差={5:F4}°",
                                    idx, sp.X, sp.Y, ep.X, ep.Y, angleFromVert);
                            }
                            idx++;
                        }
                    }
                    break;
                }
                feat = (Feature)feat.GetNextFeature();
            }

            // FeatureExtrusion2
            Console.WriteLine("\nFeatureExtrusion2...");
            Feature extr = Part.FeatureManager.FeatureExtrusion2(
                true, false, false, 0, 0,
                L, 0.0, false, false, false, false,
                0.0, 0.0, false, false, false, false,
                true, true, true, 0, 0.0, false);
            Console.WriteLine("结果: " + (extr != null ? extr.Name : "失败"));

            if (extr != null)
            {
                Part.ForceRebuild3(false);
                PartDoc partDoc = (PartDoc)Part;
                object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
                Console.WriteLine("实体数: " + (bodies != null ? bodies.Length : 0));
                if (bodies != null && bodies.Length > 0)
                {
                    Body2 body = (Body2)bodies[0];
                    object[] faces = (object[])body.GetFaces();
                    Console.WriteLine("面数: " + faces.Length);

                    // 找斜壁面
                    foreach (object fobj in faces)
                    {
                        Face2 face = (Face2)fobj;
                        Surface surf = (Surface)face.GetSurface();
                        if (surf.IsPlane())
                        {
                            double[] norm = (double[])surf.PlaneParams;
                            double nx = norm[0], ny = norm[1], nz = norm[2];
                            // 斜壁面法向应该接近 (±cos(0.5°), sin(0.5°), 0)
                            double angleFromVert = Math.Atan2(Math.Abs(nx), Math.Abs(ny)) * 180.0 / Math.PI;
                            if (angleFromVert > 0.1 && angleFromVert < 2.0 && Math.Abs(nz) < 0.1)
                            {
                                Console.WriteLine("  斜壁面法向: ({0:F4},{1:F4},{2:F4}) 垂直偏差={3:F4}°",
                                    nx, ny, nz, angleFromVert);
                            }
                        }
                    }
                }
            }

            Part.SaveAs3("C:/temp/test_notched.sldprt", 0, 0);
            Console.WriteLine("\n已保存: C:/temp/test_notched.sldprt");
        }
    }
}
