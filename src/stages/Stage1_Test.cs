using System;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SWStage1
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== 阶段1：C# 强类型连接与基础拉伸测试 ===\n");

            SldWorks swApp = null;
            ModelDoc2 swDoc = null;

            try
            {
                // ============================================
                // 步骤1：连接SolidWorks
                // ============================================
                Console.WriteLine("[1/4] 连接SolidWorks...");

                try
                {
                    swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
                    swApp.Visible = true;
                    swApp.UserControl = false;
                    Console.WriteLine("  ✓ 已连接到运行的SolidWorks实例");
                }
                catch (Exception ex)
                {
                    Console.WriteLine(string.Format("  ✗ 连接失败: {0}", ex.Message));
                    Console.WriteLine("  请确保SolidWorks已经启动");
                    return;
                }

                // ============================================
                // 步骤2：新建零件
                // ============================================
                Console.WriteLine("\n[2/4] 新建零件...");

                swApp.NewPart();
                System.Threading.Thread.Sleep(1000);

                swDoc = (ModelDoc2)swApp.ActiveDoc;
                if (swDoc == null)
                {
                    Console.WriteLine("  ✗ 新建零件失败");
                    return;
                }

                Console.WriteLine(string.Format("  ✓ 零件已创建: {0}", swDoc.GetTitle()));

                // ============================================
                // 步骤3：选择前视基准面并创建草图
                // ============================================
                Console.WriteLine("\n[3/4] 绘制草图（100x100mm矩形）...");

                // 选择前视基准面（中文版）
                bool selectResult = swDoc.Extension.SelectByID2(
                    "前视基准面",
                    "PLANE",
                    0, 0, 0,
                    false, 0, null, 0
                );

                if (!selectResult)
                {
                    Console.WriteLine("  ✗ 选择前视基准面失败");
                    return;
                }

                Console.WriteLine("  ✓ 已选择前视基准面");

                // 创建草图
                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已创建");

                // 绘制100x100mm矩形（中心在原点）
                // CreateCornerRectangle 参数：(x1, y1, z1, x2, y2, z2)
                swDoc.SketchManager.CreateCornerRectangle(
                    -0.05, 0.05, 0,   // 左上角 (-50mm, 50mm)
                    0.05, -0.05, 0     // 右下角 (50mm, -50mm)
                );

                Console.WriteLine("  ✓ 草图绘制完成: 100x100mm矩形");

                // 关闭草图
                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已关闭");

                // ============================================
                // 步骤4：创建拉伸特征 (50mm)
                // ============================================
                Console.WriteLine("\n[4/4] 创建拉伸特征（50mm）...");

                Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
                    false,                              // [1] Sd: 是否双向拉伸
                    false,                              // [2] Flip: 是否翻转方向
                    false,                              // [3] Dir: 是否使用方向2
                    (int)swEndConditions_e.swEndCondBlind,   // [4] T1: 终止条件1
                    (int)swEndConditions_e.swEndCondBlind,   // [5] T2: 终止条件2
                    0.05,                               // [6] D1: 深度1 (50mm)
                    0.05,                               // [7] D2: 深度2
                    false,                              // [8] Dchk1
                    false,                              // [9] Dchk2
                    false,                              // [10] Ddir1
                    false,                              // [11] Ddir2
                    0.0,                                // [12] Dang1
                    0.0,                                // [13] Dang2
                    false,                              // [14] OffsetReverse1
                    false,                              // [15] OffsetReverse2
                    false,                              // [16] TranslateSurface1
                    false,                              // [17] TranslateSurface2
                    false,                              // [18] Merge
                    false,                              // [19] UseFeatScope
                    false,                              // [20] UseAutoSelect
                    0,                                  // [21] T0: 起始条件
                    0.0,                                // [22] StartOffset
                    false                               // [23] FlipStartOffset
                );

                if (feat == null)
                {
                    Console.WriteLine("  ✗ 拉伸特征创建失败（返回null）");

                    // 尝试通过特征数量验证
                    int beforeCount = swDoc.GetFeatureCount();
                    Console.WriteLine(string.Format("  特征数量: {0}", beforeCount));

                    // 强制重建
                    swDoc.ForceRebuild3(false);

                    int afterCount = swDoc.GetFeatureCount();
                    Console.WriteLine(string.Format("  重建后特征数量: {0}", afterCount));

                    if (afterCount > beforeCount)
                    {
                        Console.WriteLine("  ⚠ 特征实际创建成功（返回值null是SW API的正常行为）");
                    }
                    else
                    {
                        Console.WriteLine("  ✗ 特征创建确实失败");
                        return;
                    }
                }
                else
                {
                    Console.WriteLine(string.Format("  ✓ 拉伸特征创建成功: {0}", feat.Name));
                }

                // 强制重建模型
                swDoc.ForceRebuild3(false);
                Console.WriteLine("  ✓ 模型重建完成");

                // 停顿3秒供截图
                Console.WriteLine("\n  ⏸  停顿3秒供截图...");
                System.Threading.Thread.Sleep(3000);

                Console.WriteLine("\n=== 阶段1验证成功：C# 强类型基础拉伸完全通行 ===");
                Console.WriteLine("✓ FeatureExtrusion2 23参数完整传递成功");
                Console.WriteLine("✓ 强类型绑定工作正常");
                Console.WriteLine("✓ 准备进入阶段2：探测FeatureCut4\n");

                // 阶段2：测试 FeatureCut4（27参数）
                TestFeatureCut4(swApp, swDoc);
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("\n✗ 阶段1失败: {0}", ex.Message));
                Console.WriteLine(string.Format("  堆栈: {0}", ex.StackTrace));

                // 保存错误日志
                string logPath = "stage1_error.log";
                System.IO.File.WriteAllText(logPath, string.Format("[{0}] Stage 1 Error:\n{1}\n{2}", DateTime.Now, ex.Message, ex.StackTrace));
                Console.WriteLine(string.Format("\n错误日志已保存到: {0}", logPath));
            }
            finally
            {
                // 清理资源
                if (swApp != null)
                {
                    swApp.CloseAllDocuments(true);
                    Console.WriteLine("\n  ✓ 所有文档已关闭");
                }
            }
        }

        // ============================================
        // 阶段2：测试 FeatureCut4（27个参数）
        // ============================================
        static void TestFeatureCut4(SldWorks swApp, ModelDoc2 swDoc)
        {
            Console.WriteLine("\n=== 阶段2：FeatureCut4 27参数测试 ===\n");

            try
            {
                // ============================================
                // 步骤1：选择模型的顶面（面<1>）
                // ============================================
                Console.WriteLine("[1/4] 选择模型顶面...");

                bool selectFace = swDoc.Extension.SelectByID2(
                    "面<1>",
                    "FACE",
                    0, 0, 0,
                    false, 0, null, 0
                );

                if (!selectFace)
                {
                    Console.WriteLine("  ✗ 选择顶面失败");
                    Console.WriteLine("  提示：请确保模型已生成，且面<1>存在");
                    return;
                }

                Console.WriteLine("  ✓ 已选择顶面（面<1>）");

                // ============================================
                // 步骤2：创建新草图（在顶面上）
                // ============================================
                Console.WriteLine("\n[2/4] 在顶面上创建草图...");

                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已创建");

                // 绘制圆形（直径 30mm，中心在原点）
                // CreateCircle 参数：(x1, y1, z1, x2, y2, z2)
                swDoc.SketchManager.CreateCircle(
                    0, 0, 0,   // 圆心
                    0.015, 0, 0   // 圆周上一点（半径 15mm）
                );

                Console.WriteLine("  ✓ 草图绘制完成：直径 30mm 圆形");

                // 关闭草图
                swDoc.SketchManager.InsertSketch(true);
                Console.WriteLine("  ✓ 草图已关闭");

                // ============================================
                // 步骤3：执行 FeatureCut4（27个参数）
                // ============================================
                Console.WriteLine("\n[3/4] 执行 FeatureCut4（27参数）...");

                Feature cutFeat = swDoc.FeatureManager.FeatureCut4(
                    false,                                    // [1]  Sd: 是否双向切除
                    false,                                    // [2]  Flip: 是否翻转方向
                    false,                                    // [3]  Dir: 是否使用方向2
                    (int)swEndConditions_e.swEndCondThroughAll, // [4]  T1: 终止条件1（完全贯穿）
                    (int)swEndConditions_e.swEndCondThroughAll, // [5]  T2: 终止条件2
                    0.0,                                      // [6]  D1: 深度1
                    0.0,                                      // [7]  D2: 深度2
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
                    0,                                        // [24] T0: 起始条件
                    0.0,                                      // [25] StartOffset
                    false,                                    // [26] FlipStartOffset
                    false                                     // [27] OptimizeGeometry
                );

                // ============================================
                // 步骤4：验证切除特征是否创建成功
                // ============================================
                Console.WriteLine("\n[4/4] 验证切除特征...");

                if (cutFeat == null)
                {
                    Console.WriteLine("  ⚠ FeatureCut4 返回 null，开始二次验证...");

                    // 二次验证：通过特征数量判断
                    int beforeCount = swDoc.GetFeatureCount();
                    Console.WriteLine(string.Format("  切除前特征数量: {0}", beforeCount));

                    // 强制重建
                    swDoc.ForceRebuild3(false);

                    int afterCount = swDoc.GetFeatureCount();
                    Console.WriteLine(string.Format("  切除后特征数量: {0}", afterCount));

                    if (afterCount > beforeCount)
                    {
                        Console.WriteLine("  ✓ 切除特征实际创建成功（返回值null是SW API的正常行为）");
                    }
                    else
                    {
                        Console.WriteLine("  ✗ 切除特征创建确实失败");
                        Console.WriteLine("  建议：检查草图是否合法，或是否需要切换终止条件");
                        return;
                    }
                }
                else
                {
                    Console.WriteLine(string.Format("  ✓ 切除特征创建成功: {0}", cutFeat.Name));
                }

                // 强制重建模型
                swDoc.ForceRebuild3(false);
                Console.WriteLine("  ✓ 模型重建完成");

                // 停顿3秒供截图
                Console.WriteLine("\n  ⏸  停顿3秒供截图...");
                System.Threading.Thread.Sleep(3000);

                Console.WriteLine("\n=== 阶段2验证成功：FeatureCut4 27参数完全通行 ===");
                Console.WriteLine("✓ 顶面选择成功");
                Console.WriteLine("✓ 草图绘制成功");
                Console.WriteLine("✓ FeatureCut4 27参数传递成功");
                Console.WriteLine("✓ 切除特征创建成功\n");
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("\n✗ 阶段2失败: {0}", ex.Message));
                Console.WriteLine(string.Format("  堆栈: {0}", ex.StackTrace));
            }
        }
    }
}
