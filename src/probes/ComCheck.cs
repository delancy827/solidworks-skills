using System;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Program
{
    static void Main()
    {
        string logPath = System.IO.Path.Combine(
            System.Environment.GetFolderPath(System.Environment.SpecialFolder.Desktop),
            "com_status.log");
        System.IO.StreamWriter log = new System.IO.StreamWriter(logPath, false, System.Text.Encoding.UTF8);
        log.AutoFlush = true;
        Console.SetOut(log);
        Console.SetError(log);

        Console.WriteLine("=== COM 连接状态探测 ===\n");

        string[] progIds = new string[] {
            "SldWorks.Application",
            "SldWorks.Application.31",
            "SldWorks.Application.32"
        };

        foreach (string pid in progIds)
        {
            Console.WriteLine(string.Format("[探测] ProgID: {0}", pid));
            try
            {
                SldWorks sw = (SldWorks)Marshal.GetActiveObject(pid);
                sw.Visible = true;
                Console.WriteLine("  ✓ 连接成功");
                Console.WriteLine(string.Format("  版本: {0}", sw.GetVersion()));
                Console.WriteLine(string.Format("  Revision: {0}", sw.RevisionNumber()));

                ModelDoc2 doc = (ModelDoc2)sw.ActiveDoc;
                if (doc == null)
                {
                    Console.WriteLine("  活动文档: (无)");
                }
                else
                {
                    Console.WriteLine(string.Format("  活动文档: {0}", doc.GetTitle()));
                    Console.WriteLine(string.Format("  文档路径: {0}", doc.GetPathName()));
                    Console.WriteLine(string.Format("  特征数量: {0}", doc.GetFeatureCount()));
                }
                Console.WriteLine("");
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("  ✗ 连接失败: {0}\n", ex.Message));
            }
        }

        Console.WriteLine("=== 探测完成 ===");
        Console.WriteLine("请查看：你的 SW 界面里有没有变化（比如变得可见）？");
        log.Close();
    }
}
