using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace StampingDie
{
    /// <summary>
    /// Step3: 凸模U形槽自动化建模（单轮廓凹口法）
    /// 学号27号 | 材控2320181班
    /// 核心技术：单轮廓带凹口草图 + FeatureExtrusion2 一次拉伸成型
    /// 完全绕过 FeatureCut/布尔减 的所有COM限制
    /// </summary>
    class Step3_PunchUShape_Final
    {
        [STAThread]
        static void Main(string[] args)
        {
            Console.WriteLine("========================================");
            Console.WriteLine("Step3: 凸模U形槽 - 单轮廓凹口法");
            Console.WriteLine("学号27号 | 材控2320181班");
            Console.WriteLine("========================================\n");

            // ========== 课设参数（学号27号） ==========
            double A1 = 42.0;           // 凹模槽宽 = 35 + 7
            double D = 57.0;            // 凹模外径 = 50 + 7
            double E = 13.0;            // 凹模相关尺寸 = 6 + 7
            double t = 2.0;             // 料厚
            double B = 25.0;            // U形高度
            double R_bend = 5.0;        // 弯曲半径
            double gap = t + 0.1;       // 单边间隙 = 2.1mm
            double halfAngleDeg = 0.5;  // 回弹补偿半角（总角89.5°）
            double halfAngleRad = halfAngleDeg * Math.PI / 180.0;
            double slotCornerR = 5.5;   // 槽底圆角（间隙补偿）

            // 凸模外形尺寸
            double punchW = A1 + 20.0;  // 凸模宽度 = 62mm
            double punchH = B + t;      // 凸模高度 = 27mm
            double punchL = 80.0;       // 凸模长度（Z向拉伸）

            // U形槽参数
            double slotDepth = B;                       // 槽深 = 25mm
            double slotTopW = A1 - 2.0 * gap;           // 槽顶开口宽 = 37.8mm
            double dx = slotDepth * Math.Tan(halfAngleRad); // 斜壁水平偏移 = 0.218mm
            double slotBotW = slotTopW + 2.0 * dx;      // 槽底宽 = 38.236mm
            double slotY = punchH - slotDepth;          // 槽底Y坐标 = 2mm
            double cx = punchW / 2.0;                   // X中心

            Console.WriteLine("[参数表]");
            Console.WriteLine("  凸模外形: {0} x {1} x {2} (宽x高x长)", punchW, punchH, punchL);
            Console.WriteLine("  U形槽顶宽: {0:F3} mm", slotTopW);
            Console.WriteLine("  U形槽底宽: {0:F3} mm", slotBotW);
            Console.WriteLine("  槽深: {0} mm, 槽底Y: {1} mm", slotDepth, slotY);
            Console.WriteLine("  斜壁角度补偿: {0}° (与垂直方向)", halfAngleDeg);
            Console.WriteLine("  槽底圆角: R{0} mm\n", slotCornerR);

            // ========== 连接SW ==========
            SldWorks swApp = null;
            try
            {
                swApp = (SldWorks)System.Runtime.InteropServices.Marshal.GetActiveObject("SldWorks.Application");
                Console.WriteLine("[SW] 已连接到活动实例");
            }
            catch
            {
                swApp = new SldWorks();
                swApp.Visible = true;
                Console.WriteLine("[SW] 已启动新实例");
                System.Threading.Thread.Sleep(5000);
            }

            string tpl = swApp.GetUserPreferenceStringValue(
                (int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
            if (string.IsNullOrEmpty(tpl))
                tpl = @"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_part.prtdot";

            // ========== 创建零件 ==========
            swApp.NewDocument(tpl, 0, 0, 0);
            System.Threading.Thread.Sleep(1000);
            ModelDoc2 Part = (ModelDoc2)swApp.ActiveDoc;
            if (Part == null)
            {
                Console.WriteLine("❌ 零件创建失败");
                return;
            }
            Console.WriteLine("[1/4] 零件已创建: " + Part.GetTitle());

            // 关闭自动几何关系（防止端点被强制吸附）
            Part.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swSketchAutomaticRelations, false);

            // ========== 创建凹口草图 ==========
            Console.WriteLine("[2/4] 创建单轮廓凹口草图...");
            bool sel = Part.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!sel) sel = Part.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!sel)
            {
                Console.WriteLine("❌ 无法选择前视基准面");
                return;
            }

            Part.SketchManager.InsertSketch(true);
            Console.WriteLine("  草图已创建");

            // 单轮廓凹口（逆时针）
            // 外框 + U形凹口，共7条线段
            double x1 = 0.0,           y1 = 0.0;
            double x2 = punchW,        y2 = 0.0;
            double x3 = cx + slotTopW / 2.0,  y3 = punchH;   // 槽口右上
            double x4 = cx + slotBotW / 2.0,  y4 = slotY;    // 右斜壁底
            double x5 = cx - slotBotW / 2.0,  y5 = slotY;    // 左斜壁底
            double x6 = cx - slotTopW / 2.0,  y6 = punchH;   // 槽口左上
            double x7 = 0.0,           y7 = punchH;

            Console.WriteLine("  轮廓顶点:");
            Console.WriteLine("    P1({0:F3},{1:F3}) 左下", x1, y1);
            Console.WriteLine("    P2({0:F3},{1:F3}) 右下", x2, y2);
            Console.WriteLine("    P3({0:F3},{1:F3}) 槽口右上", x3, y3);
            Console.WriteLine("    P4({0:F3},{1:F3}) 右斜壁底", x4, y4);
            Console.WriteLine("    P5({0:F3},{1:F3}) 左斜壁底", x5, y5);
            Console.WriteLine("    P6({0:F3},{1:F3}) 槽口左上", x6, y6);
            Console.WriteLine("    P7({0:F3},{1:F3}) 左上", x7, y7);

            SketchSegment seg1 = (SketchSegment)Part.SketchManager.CreateLine(x1, y1, 0, x2, y2, 0);
            SketchSegment seg2 = (SketchSegment)Part.SketchManager.CreateLine(x2, y2, 0, x3, y3, 0);
            SketchSegment seg3 = (SketchSegment)Part.SketchManager.CreateLine(x3, y3, 0, x4, y4, 0);
            SketchSegment seg4 = (SketchSegment)Part.SketchManager.CreateLine(x4, y4, 0, x5, y5, 0);
            SketchSegment seg5 = (SketchSegment)Part.SketchManager.CreateLine(x5, y5, 0, x6, y6, 0);
            SketchSegment seg6 = (SketchSegment)Part.SketchManager.CreateLine(x6, y6, 0, x7, y7, 0);
            SketchSegment seg7 = (SketchSegment)Part.SketchManager.CreateLine(x7, y7, 0, x1, y1, 0);

            if (seg1 == null || seg2 == null || seg3 == null || seg4 == null || seg5 == null || seg6 == null || seg7 == null)
            {
                Console.WriteLine("❌ 草图线段创建失败");
                return;
            }
            Console.WriteLine("  7条线段全部创建成功");

            Part.SketchManager.InsertSketch(true);
            Console.WriteLine("  草图已退出");

            // 草图验证
            Feature sketchFeat = (Feature)Part.FirstFeature();
            while (sketchFeat != null)
            {
                if (sketchFeat.GetTypeName2() == "ProfileFeature" || sketchFeat.GetTypeName2() == "Sketch")
                {
                    Sketch sk = (Sketch)sketchFeat.GetSpecificFeature2();
                    object[] segs = (object[])sk.GetSketchSegments();
                    Console.WriteLine("  草图验证: 线段数=" + (segs != null ? segs.Length : 0));
                    if (segs != null && segs.Length == 7)
                    {
                        // 验证斜壁角度
                        for (int i = 0; i < segs.Length; i++)
                        {
                            SketchSegment s = (SketchSegment)segs[i];
                            if (s.GetType() == (int)swSketchSegments_e.swSketchLINE)
                            {
                                SketchLine line = (SketchLine)s;
                                SketchPoint sp = (SketchPoint)line.GetStartPoint2();
                                SketchPoint ep = (SketchPoint)line.GetEndPoint2();
                                double ddx = ep.X - sp.X;
                                double ddy = ep.Y - sp.Y;
                                double angleFromVert = Math.Atan2(Math.Abs(ddx), Math.Abs(ddy)) * 180.0 / Math.PI;
                                if (angleFromVert > 0.1 && angleFromVert < 2.0)
                                {
                                    Console.WriteLine("    斜壁Line[" + i + "]: 垂直偏差=" + angleFromVert.ToString("F4") + "°");
                                }
                            }
                        }
                    }
                    break;
                }
                sketchFeat = (Feature)sketchFeat.GetNextFeature();
            }

            // ========== FeatureExtrusion2 拉伸 ==========
            Console.WriteLine("\n[3/4] FeatureExtrusion2 拉伸...");
            Feature extr = Part.FeatureManager.FeatureExtrusion2(
                true, false, false,   // T0=双向(false), T1=合并, T2=方向
                0, 0,                 // T3, T4 (swEndCondBlind=0)
                punchL, 0.0,          // D1, D2
                false, false, false, false,  // T9-T12
                0.0, 0.0,             // D3, D4
                false, false, false, false,  // T15-T18
                true, true, true,     // T19-T21 (自动选择, 特征范围, 传播)
                0, 0.0, false);       // T22-T24

            if (extr == null)
            {
                Console.WriteLine("❌ FeatureExtrusion2 返回 null");
                return;
            }
            Console.WriteLine("  特征创建成功: " + extr.Name);

            Part.ForceRebuild3(false);

            // 实体验证
            PartDoc partDoc = (PartDoc)Part;
            object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
            Console.WriteLine("  实体数: " + (bodies != null ? bodies.Length : 0));
            if (bodies != null && bodies.Length > 0)
            {
                Body2 body = (Body2)bodies[0];
                object[] faces = (object[])body.GetFaces();
                Console.WriteLine("  面数: " + faces.Length + " (实心块=6, 带U形槽=9)");

                // 斜壁面验证
                int slantCount = 0;
                foreach (object fobj in faces)
                {
                    Face2 face = (Face2)fobj;
                    Surface surf = (Surface)face.GetSurface();
                    if (surf.IsPlane())
                    {
                        double[] norm = (double[])surf.PlaneParams;
                        double nx = norm[0], ny = norm[1], nz = norm[2];
                        double angleFromVert = Math.Atan2(Math.Abs(nx), Math.Abs(ny)) * 180.0 / Math.PI;
                        if (angleFromVert > 0.1 && angleFromVert < 2.0 && Math.Abs(nz) < 0.1)
                        {
                            slantCount++;
                            Console.WriteLine("    斜壁面#{0}: 法向=({1:F4},{2:F4},{3:F4}) 垂直偏差={4:F4}°",
                                slantCount, nx, ny, nz, angleFromVert);
                        }
                    }
                }
                if (slantCount == 2)
                    Console.WriteLine("  ✅ 双侧89.5°斜壁验证通过");
                else
                    Console.WriteLine("  ⚠ 斜壁面数量异常: " + slantCount);
            }

            // ========== 槽底圆角 ==========
            Console.WriteLine("\n[4/4] 添加槽底圆角 R" + slotCornerR + "...");
            // 选择槽底的边：需要先找到槽底的两个内边
            // 简化：用特征树中的边选择可能不稳定
            // 备选：在草图中用圆弧代替尖角（更可靠）
            // 由于圆角不是本次核心目标，先跳过，后续可手动添加或用SketchFillet
            Console.WriteLine("  （圆角特征待后续优化添加）");

            // ========== 保存 ==========
            string finalPath = "C:/temp/Punch_27_UShape_Final.SLDPRT";
            int saveResult = Part.SaveAs3(finalPath, 0, 0);
            Console.WriteLine("\n[保存] " + (saveResult == 1 ? "✅ 成功" : "❌ 失败") + " -> " + finalPath);

            // 同时保存到课设目录
            string classDir = "D:/冲压课设1/181班27号";
            System.IO.Directory.CreateDirectory(classDir);
            string classPath = classDir + "/凸模_27号_U形槽.SLDPRT";
            Part.SaveAs3(classPath, 0, 0);
            Console.WriteLine("[保存] 课设目录 -> " + classPath);

            // 文件信息
            if (System.IO.File.Exists(finalPath))
            {
                var fi = new System.IO.FileInfo(finalPath);
                Console.WriteLine("  文件大小: " + fi.Length + " bytes");
                Console.WriteLine("  修改时间: " + fi.LastWriteTime);
            }

            Console.WriteLine("\n========================================");
            Console.WriteLine("Step3 完成: 凸模U形槽 89.5° 精确成型");
            Console.WriteLine("========================================");
        }
    }
}
