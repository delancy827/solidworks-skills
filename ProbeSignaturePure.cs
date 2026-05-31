using System;
using System.Reflection;
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

        Console.WriteLine("=== 探测 SelectByRay 签名（纯反射，无需 SW 运行）===\n");

        // 方法1：通过已加载的类型反射
        Type extType = typeof(IModelDocExtension);
        MethodInfo mi = extType.GetMethod("SelectByRay");
        if (mi != null)
        {
            ParameterInfo[] ps = mi.GetParameters();
            Console.WriteLine(string.Format("  方法: {0}", mi.Name));
            Console.WriteLine(string.Format("  参数个数: {0}\n", ps.Length));
            for (int i = 0; i < ps.Length; i++)
            {
                Console.WriteLine(string.Format(
                    "    [{0}] {1} {2}",
                    i + 1,
                    ps[i].ParameterType.FullName,
                    ps[i].Name
                ));
            }
        }
        else
        {
            Console.WriteLine("  ✗ 未找到 SelectByRay 方法");
        }

        // 方法2：探测 FeatureExtrusion2 签名（确认23个参数）
        Console.WriteLine("\n=== 探测 FeatureExtrusion2 签名 ===\n");
        MethodInfo mi2 = typeof(IFeatureManager).GetMethod("FeatureExtrusion2");
        if (mi2 != null)
        {
            ParameterInfo[] ps2 = mi2.GetParameters();
            Console.WriteLine(string.Format("  方法: {0}", mi2.Name));
            Console.WriteLine(string.Format("  参数个数: {0}\n", ps2.Length));
            for (int i = 0; i < ps2.Length; i++)
            {
                Console.WriteLine(string.Format(
                    "    [{0}] {1} {2}",
                    i + 1,
                    ps2[i].ParameterType.FullName,
                    ps2[i].Name
                ));
            }
        }

        // 方法3：探测 FeatureCut4 签名（确认27个参数）
        Console.WriteLine("\n=== 探测 FeatureCut4 签名 ===\n");
        MethodInfo mi3 = typeof(IFeatureManager).GetMethod("FeatureCut4");
        if (mi3 != null)
        {
            ParameterInfo[] ps3 = mi3.GetParameters();
            Console.WriteLine(string.Format("  方法: {0}", mi3.Name));
            Console.WriteLine(string.Format("  参数个数: {0}\n", ps3.Length));
            for (int i = 0; i < ps3.Length; i++)
            {
                Console.WriteLine(string.Format(
                    "    [{0}] {1} {2}",
                    i + 1,
                    ps3[i].ParameterType.FullName,
                    ps3[i].Name
                ));
            }
        }

        Console.WriteLine("\n=== 探测完成 ===");
        swLog.Close();
    }
}
