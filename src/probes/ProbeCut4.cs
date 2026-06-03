using System;
using System.Reflection;
using SolidWorks.Interop.sldworks;

namespace SWProbe2
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== 探测 FeatureCut4 签名 ===\n");

            try
            {
                Type fmType = typeof(IFeatureManager);
                MethodInfo mi = fmType.GetMethod("FeatureCut4");

                if (mi == null)
                {
                    Console.WriteLine("未找到 FeatureCut4 方法");
                    // 尝试找类似方法
                    foreach (MethodInfo m in fmType.GetMethods())
                    {
                        if (m.Name.Contains("Cut"))
                            Console.WriteLine("  找到: " + m.Name);
                    }
                    return;
                }

                ParameterInfo[] pars = mi.GetParameters();
                Console.WriteLine("方法名: " + mi.Name);
                Console.WriteLine("参数数量: " + pars.Length);
                Console.WriteLine("\n参数列表:");
                for (int i = 0; i < pars.Length; i++)
                {
                    Console.WriteLine(string.Format("  [{0}] {1} {2}", i + 1, pars[i].ParameterType.Name, pars[i].Name));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("错误: " + ex.Message);
            }
        }
    }
}
