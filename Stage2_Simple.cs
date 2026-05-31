using System;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Program
{
    static void Main()
    {
        string logPath = @"C:\Users\22374\Desktop\湛江北海\学习课程\sw\swkuskills\log.txt";
        System.IO.StreamWriter swLog = new System.IO.StreamWriter(logPath, false, System.Text.Encoding.UTF8);
        swLog.AutoFlush = true;
        Console.SetOut(swLog);
        Console.SetError(swLog);

        Console.WriteLine("=== Stage2 最简版：启动新SW实例 ===\n");

        SldWorks swApp = null;
        ModelDoc2 swDoc = null;

        try
        {
            // 用 Activator 启动新 SW 实例（避免权限/实例混乱）
            Console.WriteLine("[1/4] 启动 SolidWorks 新实例...");
            Type swType = Type.GetTypeFromProgID("SldWorks.Application");
            if (swType == null)
            {
                Console.WriteLine("  ✗ 未找到 SolidWorks ProgID");
                swLog.Close();
                return;
            }
            swApp = (SldWorks)Activator.CreateInstance(swType);
            swApp.Visible = true;
            swApp.UserControl = true;
            Console.WriteLine("  ✓ SolidWorks 已启动（新实例）\n");

            // 新建零件
            Console.WriteLine("[2/4] 新建零件...");
            swApp.NewPart();
            System.Threading.Thread.Sleep(1000);
            swDoc = (ModelDoc2)swApp.ActiveDoc;
            if (swDoc == null)
            {
                Console.WriteLine("  ✗ 新建零件失败");
                swLog.Close();
                return;
            }
            Console.WriteLine(string.Format("  ✓ 零件已创建: {0}\n", swDoc.GetTitle()));

            // 选择前视基准面，画 100x100mm 矩形，拉伸 50mm
            Console.WriteLine("[3/4] 绘制草图并拉伸...");
            bool sel = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!sel)
            {
                Console.WriteLine("  ✗ 选择前视基准面失败");
                swLog.Close();
                return;
            }
            swDoc.SketchManager.InsertSketch(true);
            swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.1, 0.1, 0);
            swDoc.SketchManager.InsertSketch(true);
            Console.WriteLine("  ✓ 草图绘制完成");

            // FeatureExtrusion2 — 23个参数（逐行书写，方便核对）
            Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
                false,                                          // [1]  Sd
                false,                                          // [2]  Flip
                false,                                          // [3]  Dir
                (int)swEndConditions_e.swEndCondBlind,           // [4]  T1
                (int)swEndConditions_e.swEndCondBlind,           // [5]  T2
                0.05,                                           // [6]  D1
                0.05,                                           // [7]  D2
                false,                                          // [8]  Dchk1
                false,                                          // [9]  Dchk2
                false,                                          // [10] Ddir1
                false,                                          // [11] Ddir2
                0.0,                                            // [12] Dang1
                0.0,                                            // [13] Dang2
                false,                                          // [14] OffsetReverse1
                false,                                          // [15] OffsetReverse2
                false,                                          // [16] TranslateSurface1
                false,                                          // [17] TranslateSurface2
                false,                                          // [18] Merge
                false,                                          // [19] UseFeatScope
                false,                                          // [20] UseAutoSelect
                0,                                              // [21] T0
                0.0,                                            // [22] StartOffset
                false                                           // [23] FlipStartOffset
            );
            swDoc.ForceRebuild3(false);
            Console.WriteLine("  ✓ 拉伸特征创建成功");
            Console.WriteLine(string.Format("  ✓ 零件名: {0}\n", swDoc.GetTitle()));

            // 用 SelectByRay 选顶面，画圆，切除
            Console.WriteLine("[4/4] SelectByRay 选顶面 → 画圆 → 切除...");
            swDoc.ClearSelection2(true);
            bool selFace = swDoc.Extension.SelectByRay(
                0, 0, 0.2,    // [1-3] 射线起点 (0,0,200mm)
                0, 0, -1,       // [4-6] 射线方向 (0,0,-1)
                0.1,             // [7]   RayRadius = 100mm
                1,               // [8]   TypeWanted = 1（面）
                false,           // [9]   Append
                0,               // [10]  Mark
                0                // [11]  Option
            );
            if (!selFace)
            {
                Console.WriteLine("  ✗ SelectByRay 选面失败");
                swLog.Close();
                return;
            }
            Console.WriteLine("  ✓ 顶面已选中");

            swDoc.SketchManager.InsertSketch(true);
            swDoc.SketchManager.CreateCircle(0, 0, 0, 0.015, 0, 0);
            swDoc.SketchManager.InsertSketch(true);
            Console.WriteLine("  ✓ 圆草图绘制完成");

            Feature cutFeat = swDoc.FeatureManager.FeatureCut4(
                false, false, false,
                (int)swEndConditions_e.swEndCondThroughAll,
                (int)swEndConditions_e.swEndCondThroughAll,
                0.0, 0.0,
                false, false, false, false,
                0.0, 0.0,
                false, false, false, false,
                false, false,
                false, false, false,
                0, 0.0, false, false
            );
            swDoc.ForceRebuild3(false);
            Console.WriteLine("  ✓ 切除特征创建成功\n");

            Console.WriteLine("=== ✅ 全部完成 ===");
            Console.WriteLine("请在弹出的 SolidWorks 窗口中查看带孔方块。\n");
            Console.WriteLine("按 Enter 键退出（SW 窗口会保持打开）...");
        }
        catch (Exception ex)
        {
            Console.WriteLine(string.Format("\n✗ 错误: {0}", ex.Message));
            Console.WriteLine(string.Format("  堆栈: {0}", ex.StackTrace));
        }
        finally
        {
            swLog.Close();
        }

        // 等待用户按 Enter，保持 SW 窗口打开
        Console.ReadLine();
    }
}
