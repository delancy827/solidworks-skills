using System;
using System.Reflection;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class ProbeDrawing
{
    static void Main()
    {
        SldWorks sw = (SldWorks)Activator.CreateInstance(
            Type.GetTypeFromProgID("SldWorks.Application"));
        sw.Visible = true;

        while (sw.GetDocumentCount() > 0)
        { ModelDoc2 t = (ModelDoc2)sw.ActiveDoc; if (t != null) sw.CloseDoc(t.GetTitle()); else break; }

        string drwTpl = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_a4.drwdot";
        sw.NewDocument(drwTpl, 0, 0, 0);
        System.Threading.Thread.Sleep(1000);
        ModelDoc2 doc = (ModelDoc2)sw.ActiveDoc;

        Console.WriteLine("=== DrawingDoc methods (view/create/draw/insert) ===");
        int count = 0;
        foreach (MethodInfo mi in typeof(IDrawingDoc).GetMethods())
        {
            if (mi.Name.Contains("Create") || mi.Name.Contains("View") ||
                mi.Name.Contains("Draw") || mi.Name.Contains("Insert") ||
                mi.Name.Contains("Sheet") || mi.Name.Contains("Model") ||
                mi.Name.Contains("Annotation") || mi.Name.Contains("Dimension") ||
                mi.Name.Contains("get_") || mi.Name.Contains("Auto") ||
                mi.Name.Contains("Activate") || mi.Name.Contains("Setup"))
            {
                count++;
                if (count > 80) break;
                ParameterInfo[] p = mi.GetParameters();
                Console.Write("  " + mi.Name + "(" + p.Length + "): ");
                for (int i = 0; i < Math.Min(5, p.Length); i++)
                    Console.Write(p[i].ParameterType.Name + " ");
                Console.WriteLine();
            }
        }
        Console.WriteLine("Total matched: " + count);
        Console.WriteLine("Total IDrawingDoc methods: " + typeof(IDrawingDoc).GetMethods().Length);
    }
}
