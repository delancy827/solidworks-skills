using System;
using System.Reflection;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SWAutomation
{
    class Program
    {
        static void Main(string[] args)
        {
            string logPath = @".\probe_log.txt";
            System.IO.StreamWriter log = new System.IO.StreamWriter(logPath, false, System.Text.Encoding.UTF8);
            log.AutoFlush = true;
            Console.SetOut(log);
            Console.SetError(log);

            try
            {
                Type swType = Type.GetTypeFromProgID("SldWorks.Application");
                SldWorks swApp = (SldWorks)Activator.CreateInstance(swType);
                if (swApp == null) { Console.WriteLine("FAIL: cannot create SW"); return; }
                swApp.Visible = true;
                Console.WriteLine("OK: SW created");

                string partTemplate = swApp.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
                if (string.IsNullOrEmpty(partTemplate)) partTemplate = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\零件.prtdot";
                swApp.NewDocument(partTemplate, 0, 0, 0);
                ModelDoc2 swDoc = (ModelDoc2)swApp.ActiveDoc;
                if (swDoc == null) { Console.WriteLine("FAIL: no new doc"); return; }
                Console.WriteLine("OK: new part");

                // 反射打印 FeatureExtrusion2 和 FeatureCut4 精确签名
                Type fmType = swDoc.FeatureManager.GetType();
                MethodInfo miExt = fmType.GetMethod("FeatureExtrusion2");
                MethodInfo miCut = fmType.GetMethod("FeatureCut4");

                Console.WriteLine("=== FeatureExtrusion2 参数 ===");
                if (miExt != null)
                {
                    ParameterInfo[] ps = miExt.GetParameters();
                    Console.WriteLine(string.Format("参数个数: {0}", ps.Length));
                    for (int i = 0; i < ps.Length; i++)
                    {
                        Console.WriteLine(string.Format("  [{0}] {1} {2}", i + 1, ps[i].ParameterType.Name, ps[i].Name));
                    }
                }

                Console.WriteLine("=== FeatureCut4 参数 ===");
                if (miCut != null)
                {
                    ParameterInfo[] ps = miCut.GetParameters();
                    Console.WriteLine(string.Format("参数个数: {0}", ps.Length));
                    for (int i = 0; i < ps.Length; i++)
                    {
                        Console.WriteLine(string.Format("  [{0}] {1} {2}", i + 1, ps[i].ParameterType.Name, ps[i].Name));
                    }
                }

                // 同时探测 CreateCornerRectangle 和 SelectByRay 签名
                Type skType = swDoc.SketchManager.GetType();
                MethodInfo miRect = skType.GetMethod("CreateCornerRectangle");
                MethodInfo miRay = swDoc.Extension.GetType().GetMethod("SelectByRay");

                Console.WriteLine("=== CreateCornerRectangle 参数 ===");
                if (miRect != null)
                {
                    ParameterInfo[] ps = miRect.GetParameters();
                    Console.WriteLine(string.Format("参数个数: {0}", ps.Length));
                    for (int i = 0; i < ps.Length; i++)
                        Console.WriteLine(string.Format("  [{0}] {1}", i + 1, ps[i].ParameterType.Name));
                }

                Console.WriteLine("=== SelectByRay 参数 ===");
                if (miRay != null)
                {
                    ParameterInfo[] ps = miRay.GetParameters();
                    Console.WriteLine(string.Format("参数个数: {0}", ps.Length));
                    for (int i = 0; i < ps.Length; i++)
                        Console.WriteLine(string.Format("  [{0}] {1}", i + 1, ps[i].ParameterType.Name));
                }

                swApp.ExitApp();
                Console.WriteLine("=== DONE ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine("EXCEPTION: " + ex.Message);
            }
            finally
            {
                log.Close();
            }
        }
    }
}
