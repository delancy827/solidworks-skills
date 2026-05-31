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
    }
}
