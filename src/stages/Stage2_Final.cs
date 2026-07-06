using System;
using System.IO;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Program
{
    static void Main()
    {
        string logPath = @"C:\Users\<user>\Desktop\湛江北海\学习课程\sw\swkuskills\stage2_final.log";
        StreamWriter log = new StreamWriter(logPath, false, System.Text.Encoding.UTF8);
        log.AutoFlush = true;
        Console.SetOut(log);
        Console.SetError(log);

        Console.WriteLine("=== Stage2 最终版：操作活动零件 ===\n");

        SldWorks swApp = null;
        ModelDoc2 swDoc = null;

        try
        {
            // 步骤1：连接 SolidWorks（多个 ProgID 尝试）
            Console.WriteLine("[1/4] 连接 SolidWorks...");
            string[] progIds = new string[] {
                "SldWorks.Application.31",
                "SldWorks.Application",
                "SldWorks.Application.32"
            };

            foreach (string pid in progIds)
            {
                try
                {
                    swApp = (SldWorks)Marshal.GetActiveObject(pid);
                    swApp.Visible = true;
                    swApp.UserControl = true;
                    Console.WriteLine(string.Format("  ✓ 已连接: {0}", pid));
                    break;
                }
                catch { }
            }

            if (swApp == null)
            {
                Console.WriteLine("  ✗ 连接失败：请确保 SW 已启动（权限需一致）");
                log.Close();
                return;
            }

            // 步骤2：获取活动零件（不新建！）
            Console.WriteLine("\n[2/4] 获取活动零件...");
            swDoc = (ModelDoc2)swApp.ActiveDoc;
            if (swDoc == null)
            {
                Console.WriteLine("  ✗ 没有活动零件！");
                Console.WriteLine("  请先在 SW 中手动新建一个零件，然后再运行本程序。");
                log.Close();
                return;
            }
            Console.WriteLine(string.Format("  ✓ 活动零件: {0}", swDoc.GetTitle()));

            // 强制激活并显示
            swApp.ActivateDoc2(swDoc.GetTitle(), false, 0);
            swApp.Visible = true;

            // 步骤3：在前视基准面上画 100x100mm 矩形，拉伸 50mm
            Console.WriteLine("\n[3/4] 绘制草图并拉伸...");
            bool sel = swDoc.Extension.SelectByID2(
                "前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!sel)
            {
                Console.WriteLine("  ✗ 选择前视基准面失败");
                log.Close();
                return;
            }
            Console.WriteLine("  ✓ 已选择前视基准面");

            swDoc.SketchManager.InsertSketch(true);
            swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.1, 0.1, 0);
            swDoc.SketchManager.InsertSketch(true);
            Console.WriteLine("  ✓ 草图完成（100x100mm）");

            // FeatureExtrusion2 — 23 个参数（逐行核对）
            Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
                false,                                        // [1]  Sd
                false,                                        // [2]  Flip
                false,                                        // [3]  Dir
                (int)swEndConditions_e.swEndCondBlind,        // [4]  T1
                (int)swEndConditions_e.swEndCondBlind,        // [5]  T2
                0.05,                                         // [6]  D1
                0.05,                                         // [7]  D2
                false,                                        // [8]  Dchk1
                false,                                        // [9]  Dchk2
                false,                                        // [10] Ddir1
                false,                                        // [11] Ddir2
                0.0,                                          // [12] Dang1
                0.0,                                          // [13] Dang2
                false,                                        // [14] OffsetReverse1
                false,                                        // [15] OffsetReverse2
                false,                                        // [16] TranslateSurface1
                false,                                        // [17] TranslateSurface2
                false,                                        // [18] Merge
                false,                                        // [19] UseFeatScope
                false,                                        // [20] UseAutoSelect
                0,                                              // [21] T0
                0.0,                                           // [22] StartOffset
                false                                           // [23] FlipStartOffset
            );
            swDoc.ForceRebuild3(false);
            Console.WriteLine("  ✓ 拉伸完成（50mm）");

            // 强制激活文档
            swApp.ActivateDoc2(swDoc.GetTitle(), false, 0);
            swApp.Visible = true;

            // 步骤4：用 SelectByRay 选顶面，画圆，切除
            Console.WriteLine("\n[4/4] 选顶面 → 画圆 → 切除...");
            swDoc.ClearSelection2(true);

            bool selFace = swDoc.Extension.SelectByRay(
                0, 0, 0.2,     // [1-3] 射线起点 (0,0,200mm)
                0, 0, -1,        // [4-6] 射线方向 (0,0,-1)
                0.1,               // [7]   RayRadius = 100mm
                1,                  // [8]   TypeWanted = 1（面）
                false,              // [9]   Append
                0,                  // [10]  Mark
                0                   // [11]  Option
            );
            if (!selFace)
            {
                Console.WriteLine("  ✗ SelectByRay 选面失败");
                log.Close();
                return;
            }
            Console.WriteLine("  ✓ 已选中顶面");

            swDoc.SketchManager.InsertSketch(true);
            swDoc.SketchManager.CreateCircle(0, 0, 0, 0.015, 0, 0);
            swDoc.SketchManager.InsertSketch(true);
            Console.WriteLine("  ✓ 圆草图完成（直径 30mm）");

            // FeatureCut4 — 27 个参数（逐行核对）
            Feature cutFeat = swDoc.FeatureManager.FeatureCut4(
                false,                                        // [1]  Sd
                false,                                        // [2]  Flip
                false,                                        // [3]  Dir
                (int)swEndConditions_e.swEndCondThroughAll,  // [4]  T1
                (int)swEndConditions_e.swEndCondThroughAll,  // [5]  T2
                0.0,                                          // [6]  D1
                0.0,                                          // [7]  D2
                false,                                        // [8]  Dchk1
                false,                                        // [9]  Dchk2
                false,                                        // [10] Ddir1
                false,                                        // [11] Ddir2
                0.0,                                          // [12] Dang1
                0.0,                                          // [13] Dang2
                false,                                        // [14] OffsetReverse1
                false,                                        // [15] OffsetReverse2
                false,                                        // [16] TranslateSurface1
                false,                                        // [17] TranslateSurface2
                false,                                        // [18] NormalCut
                false,                                        // [19] UseFeatScope
                false,                                        // [20] UseAutoSelect
                false,                                        // [21] AssemblyFeatureScope
                false,                                        // [22] AutoSelectComponents
                false,                                        // [23] PropagateFeatureToParts
                0,                                              // [24] T0
                0.0,                                           // [25] StartOffset
                false,                                        // [26] FlipStartOffset
                false                                           // [27] OptimizeGeometry
            );
            swDoc.ForceRebuild3(false);
            Console.WriteLine("  ✓ 切除完成（完全贯穿）");

            // 最终激活，确保界面显示
            swApp.ActivateDoc2(swDoc.GetTitle(), false, 0);
            swApp.Visible = true;

            Console.WriteLine("\n=== ✅ 全部完成 ===");
            Console.WriteLine("请在 SolidWorks 窗口中查看结果（零件已保留）。\n");
            Console.WriteLine("按 Enter 键退出（SW 保持打开）...");
        }
        catch (Exception ex)
        {
            Console.WriteLine(string.Format("\n✗ 错误: {0}", ex.Message));
            Console.WriteLine(string.Format("  堆栈: {0}", ex.StackTrace));
        }
        finally
        {
            log.Close();
        }

        Console.ReadLine();
    }
}
