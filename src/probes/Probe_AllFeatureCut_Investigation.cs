using System;
using System.Reflection;
using SolidWorks.Interop.sldworks;

namespace SWProbe
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== 探测切除相关API参数数量 ===\n");

            try
            {
                Type fmType = typeof(IFeatureManager);

                string[] methodsToProbe = { "FeatureCut", "FeatureCut2", "FeatureCut3", "FeatureCut4", "FeatureExtrusion", "FeatureExtrusion2", "FeatureExtrusion3" };

                foreach (string mname in methodsToProbe)
                {
                    MethodInfo mi = fmType.GetMethod(mname);
                    if (mi == null)
                    {
                        Console.WriteLine("[缺失] " + mname);
                    }
                    else
                    {
                        ParameterInfo[] pars = mi.GetParameters();
                        Console.WriteLine("[找到] " + mname + " → " + pars.Length + " 个参数");
                        // 只打印前5个参数名称，避免刷屏
                        for (int i = 0; i < Math.Min(5, pars.Length); i++)
                        {
                            Console.WriteLine("    [" + (i+1) + "] " + pars[i].ParameterType.Name + " " + pars[i].Name);
                        }
                        if (pars.Length > 5)
                            Console.WriteLine("    ... 共 " + pars.Length + " 个");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("错误: " + ex.Message);
            }

            Console.WriteLine("\n按任意键退出...");
            Console.ReadKey();
        }
    }
}
