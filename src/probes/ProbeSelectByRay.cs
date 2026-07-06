using System;
using System.Reflection;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Program
{
    static void Main()
    {
        string logPath = @"C:\Users\<user>\Desktop\湛江北海\学习课程\sw\swkuskills\log.txt";
        System.IO.StreamWriter swLog = new System.IO.StreamWriter(logPath, false, System.Text.Encoding.UTF8);
        swLog.AutoFlush = true;
        Console.SetOut(swLog);
        Console.SetError(swLog);

        Console.WriteLine("=== 阶段2：探测 SelectByRay 正确签名 ===\n");

        SldWorks swApp = null;
        ModelDoc2 swDoc = null;

        try
        {
            swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
            swApp.Visible = true;
            swApp.UserControl = false;
            Console.WriteLine("  ✓ 已连接到运行的 SolidWorks 实例");
        }
        catch (Exception ex)
        {
            Console.WriteLine(string.Format("  ✗ 连接失败: {0}", ex.Message));
            swLog.Close();
            return;
        }

        swDoc = (ModelDoc2)swApp.ActiveDoc;
        if (swDoc == null)
        {
            swApp.NewPart();
            System.Threading.Thread.Sleep(500);
            swDoc = (ModelDoc2)swApp.ActiveDoc;
        }

        // 先做一个 50mm 方块供测试
        Console.WriteLine("\n  创建 100x100x50 方块供选面测试...");
        swDoc.SketchManager.InsertSketch(true);
        // CreateCornerRectangle(x1, y1, z1, x2, y2, z2) — 6个参数
        swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.1, 0.1, 0);
        swDoc.SketchManager.InsertSketch(true);

        // FeatureExtrusion2 — 23个参数
        Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
            false, false, false,
            (int)swEndConditions_e.swEndCondBlind, (int)swEndConditions_e.swEndCondBlind,
            0.05, 0.05,
            false, false, false, false,
            0.0, 0.0,
            false, false, false, false,
            false, false,
            0, 0.0, false
        );
        swDoc.ForceRebuild3(false);
        Console.WriteLine("  ✓ 测试方块已创建\n");

        // 探测 SelectByRay 参数类型
        Console.WriteLine("  探测 IModelDocExtension.SelectByRay 参数签名...\n");
        Type extType = typeof(IModelDocExtension);
        MethodInfo mi = extType.GetMethod("SelectByRay");
        if (mi != null)
        {
            ParameterInfo[] ps = mi.GetParameters();
            Console.WriteLine(string.Format("  方法: {0}", mi.Name));
            Console.WriteLine(string.Format("  参数个数: {0}\n", ps.Length));
            for (int i = 0; i < ps.Length; i++)
            {
                Console.WriteLine(string.Format("    [{0}] {1} {2}", i + 1, ps[i].ParameterType.Name, ps[i].Name));
            }
        }
        else
        {
            Console.WriteLine("  ✗ 未找到 SelectByRay 方法");
        }

        swLog.Close();
    }
}
