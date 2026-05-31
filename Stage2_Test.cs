using System;
using System.IO;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SWStage2
{
    class Program
    {
        static void Main(string[] args)
        {
            string logPath = @"C:\Users\22374\Desktop\湛江北海\学习课程\sw\swkuskills\log.txt";
            StreamWriter swLog = new StreamWriter(logPath, false, System.Text.Encoding.UTF8);
            swLog.AutoFlush = true;
            Console.SetOut(swLog);
            Console.SetError(swLog);

            Console.WriteLine("=== 阶段1+2：C# 强类型连接 + FeatureExtrusion2 + FeatureCut4 ===\n");

            SldWorks swApp = null;
            ModelDoc2 swDoc = null;

            try
            {
                // ===========================================
                // 步骤1：连接 SolidWorks（当前活动实例）
                // ===========================================
                Console.WriteLine("[1/7] 连接 SolidWorks...");

                try
                {
                    swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
                    swApp.Visible = true;
                    swApp.UserControl = true;   // 必须为 true，否则界面不刷新
                    Console.WriteLine("  ✓ 已连接到运行的 SolidWorks 实例");
                }
                catch (Exception ex)
                {
                    Console.WriteLine(string.Format("  ✗ 连接失败: {0}", ex.Message));
                    Console.WriteLine("  请确保 SolidWorks 已经启动（普通权限，非管理员）");
                    swLog.Close();
                    return;
                }

                // ===========================================
                // 步骤2：使用当前活动零件（不新建）
                // ===========================================
                Console.WriteLine("\n[2/7] 获取当前活动零件...");

                swDoc = (ModelDoc2)swApp.ActiveDoc;
                if (swDoc == null)
                {
                    Console.WriteLine("  ✗ 未找到活动零件！");
                    Console.WriteLine("  请先在 SolidWorks 中手动新建一个零件，然后再运行本程序。");
                    swLog.Close();
                    return;
                }

                Console.WriteLine(string.Format("  ✓ 已连接到活动零件: {0}", swDoc.GetTitle()));

                // ===========================================
                // 步骤3：选择前视基准面并创建草图（100x100mm 矩形）
                // ===========================================
                Console.WriteLine("\n[3/7] 绘制草图（100x100mm 矩形）...");

                bool selectResult = swDoc.Extension.SelectByID2(
                    "前视基准面",
                    "PLANE",
                    0, 0, 0,
                    false, 0, null, 0
                );

                if (!selectResult)
                {
                    Console.WriteLine("  ✗ 选择前视基准面失败");
                    swLog.Close();
                    return;
                }

                Console.WriteLine("  ✓ 已选择前视基准面");

                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已创建");

                swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.1, 0.1, 0);
                Console.WriteLine("  ✓ 草图绘制完成: 100x100mm 矩形");

                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已关闭");

                // ===========================================
                // 步骤4：创建拉伸特征（50mm）
                // ===========================================
                Console.WriteLine("\n[4/7] 创建拉伸特征（50mm）...");

                // FeatureExtrusion2 正确签名：23 个参数（经反射探测确认）
                // [1]Sd [2]Flip [3]Dir [4]T1 [5]T2 [6]D1 [7]D2
                // [8]Dchk1 [9]Dchk2 [10]Ddir1 [11]Ddir2 [12]Dang1 [13]Dang2
                // [14]OffsetReverse1 [15]OffsetReverse2 [16]TranslateSurface1 [17]TranslateSurface2
                // [18]Merge [19]UseFeatScope [20]UseAutoSelect [21]T0 [22]StartOffset [23]FlipStartOffset
                Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
                    false,                                    // [1]  Sd
                    false,                                    // [2]  Flip
                    false,                                    // [3]  Dir
                    (int)swEndConditions_e.swEndCondBlind,   // [4]  T1
                    (int)swEndConditions_e.swEndCondBlind,   // [5]  T2
                    0.05,                                     // [6]  D1 = 50mm
                    0.05,                                     // [7]  D2 = 50mm
                    false,                                    // [8]  Dchk1
                    false,                                    // [9]  Dchk2
                    false,                                    // [10] Ddir1
                    false,                                    // [11] Ddir2
                    0.0,                                      // [12] Dang1
                    0.0,                                      // [13] Dang2
                    false,                                    // [14] OffsetReverse1
                    false,                                    // [15] OffsetReverse2
                    false,                                    // [16] TranslateSurface1
                    false,                                    // [17] TranslateSurface2
                    false,                                    // [18] Merge
                    false,                                    // [19] UseFeatScope
                    false,                                    // [20] UseAutoSelect
                    0,                                        // [21] T0
                    0.0,                                      // [23] StartOffset
                    false                                     // [23] FlipStartOffset
                );

                if (feat == null)
                {
                    Console.WriteLine("  ⚠  FeatureExtrusion2 返回 null，验证特征树...");
                    int before = swDoc.GetFeatureCount();
                    swDoc.ForceRebuild3(false);
                    int after = swDoc.GetFeatureCount();
                    if (after > before)
                    {
                        Console.WriteLine("  ✓ 拉伸特征实际创建成功（返回值 null 是 SW API 正常行为）");
                    }
                    else
                    {
                        Console.WriteLine("  ✗ 拉伸特征创建失败");
                        swLog.Close();
                        return;
                    }
                }
                else
                {
                    Console.WriteLine(string.Format("  ✓ 拉伸特征创建成功: {0}", feat.Name));
                }

                swDoc.ForceRebuild3(false);
                Console.WriteLine("  ✓ 模型重建完成");

                // 强制激活并刷新界面
                swApp.ActivateDoc2(swDoc.GetTitle(), false, 0);
                swApp.Visible = true;

                // ===========================================
                // 阶段2：测试 FeatureCut4（27 参数）
                // ===========================================
                Console.WriteLine("\n=== 进入阶段2：FeatureCut4 27 参数测试 ===\n");

                // ===========================================
                // 步骤5：用 SelectByRay 选择顶面
                // ===========================================
                Console.WriteLine("[5/7] 选择模型顶面（SelectByRay）...");

                swDoc.ClearSelection2(true);

                // SelectByRay 签名（经反射探测确认）：
                //   (double WorldX, double WorldY, double WorldZ,
                //    double RayVecX, double RayVecY, double RayVecZ,
                //    double RayRadius, int TypeWanted, bool Append, int Mark, int Option)
                bool selectFace = swDoc.Extension.SelectByRay(
                    0, 0, 0.2,     // [1-3] 射线起点 (0,0,200mm) 方块正上方
                    0, 0, -1,        // [4-6] 射线方向 (0,0,-1) 垂直向下
                    0.1,               // [7]   射线半径 100mm（足够覆盖方块顶面）
                    1,                  // [8]   TypeWanted = 1（选面，swSelFACES）
                    false,              // [9]   Append = false（不追加选择）
                    0,                  // [10]  Mark = 0
                    0                   // [11]  Option = 0
                );

                if (!selectFace)
                {
                    Console.WriteLine("  ✗ SelectByRay 选面失败");
                    Console.WriteLine("  建议：请在 SW 中手动确认顶面是否可被选到");
                    swLog.Close();
                    return;
                }

                Console.WriteLine("  ✓ 已通过 SelectByRay 选中顶面");

                // ===========================================
                // 步骤6：在顶面上创建草图（绘制圆）
                // ===========================================
                Console.WriteLine("\n[6/7] 在顶面上创建草图（绘制圆）...");

                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已创建");

                swDoc.SketchManager.CreateCircle(0, 0, 0, 0.015, 0, 0);
                Console.WriteLine("  ✓ 草图绘制完成：直径 30mm 圆形");

                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已关闭");

                // ===========================================
                // 步骤7：执行 FeatureCut4（27 参数）
                // ===========================================
                Console.WriteLine("\n[7/7] 执行 FeatureCut4（27 参数）...");

                Feature cutFeat = swDoc.FeatureManager.FeatureCut4(
                    false,                                    // [1]  Sd
                    false,                                    // [2]  Flip
                    false,                                    // [3]  Dir
                    (int)swEndConditions_e.swEndCondThroughAll, // [4]  T1
                    (int)swEndConditions_e.swEndCondThroughAll, // [5]  T2
                    0.0,                                      // [6]  D1
                    0.0,                                      // [7]  D2
                    false,                                    // [8]  Dchk1
                    false,                                    // [9]  Dchk2
                    false,                                    // [10] Ddir1
                    false,                                    // [11] Ddir2
                    0.0,                                      // [12] Dang1
                    0.0,                                      // [13] Dang2
                    false,                                    // [14] OffsetReverse1
                    false,                                    // [15] OffsetReverse2
                    false,                                    // [16] TranslateSurface1
                    false,                                    // [17] TranslateSurface2
                    false,                                    // [18] NormalCut
                    false,                                    // [19] UseFeatScope
                    false,                                    // [20] UseAutoSelect
                    false,                                    // [21] AssemblyFeatureScope
                    false,                                    // [22] AutoSelectComponents
                    false,                                    // [23] PropagateFeatureToParts
                    0,                                        // [24] T0
                    0.0,                                      // [25] StartOffset
                    false,                                    // [26] FlipStartOffset
                    false                                     // [27] OptimizeGeometry
                );

                // ===========================================
                // 验证切除特征
                // ===========================================
                Console.WriteLine("\n  验证切除特征...");

                if (cutFeat == null)
                {
                    Console.WriteLine("  ⚠  FeatureCut4 返回 null，二次验证...");
                    int beforeCount = swDoc.GetFeatureCount();
                    swDoc.ForceRebuild3(false);
                    int afterCount = swDoc.GetFeatureCount();
                    Console.WriteLine(string.Format("  切除前特征数量: {0}", beforeCount));
                    Console.WriteLine(string.Format("  切除后特征数量: {0}", afterCount));

                    if (afterCount > beforeCount)
                    {
                        Console.WriteLine("  ✓ 切除特征实际创建成功（返回值 null 是 SW API 正常行为）");
                    }
                    else
                    {
                        Console.WriteLine("  ✗ 切除特征创建确实失败");
                        swLog.Close();
                        return;
                    }
                }
                else
                {
                    Console.WriteLine(string.Format("  ✓ 切除特征创建成功: {0}", cutFeat.Name));
                }

                swDoc.ForceRebuild3(false);
                Console.WriteLine("  ✓ 模型重建完成");

                // 强制激活文档，确保界面显示
                swApp.ActivateDoc2(swDoc.GetTitle(), false, 0);
                swApp.Visible = true;

                // ===========================================
                // 完成
                // ===========================================
                Console.WriteLine("\n=== 阶段1+2 验证成功：FeatureExtrusion2 + FeatureCut4 完全通行 ===");
                Console.WriteLine("✓ FeatureExtrusion2 23 参数完整传递成功");
                Console.WriteLine("✓ FeatureCut4 27 参数完整传递成功");
                Console.WriteLine("✓ 强类型绑定工作正常");
                Console.WriteLine("✓ 方块 + 内孔切除全套流程一次性跑完");
                Console.WriteLine("\n  请在 SolidWorks 窗口中查看结果（零件已保留，未关闭）\n");
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("\n✗ 阶段1+2 失败: {0}", ex.Message));
                Console.WriteLine(string.Format("  堆栈: {0}", ex.StackTrace));
            }
            finally
            {
                swLog.Close();
            }
        }
    }
}
