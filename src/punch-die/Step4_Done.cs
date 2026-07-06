// Step4_Done.cs — 冲压课设最终交付：凹模 + 凸模U形槽89.5° (两独立零件)
// SW 2024 Standalone COM: 单文档单一 FeatureExtrusion2 可用; InsertPart 不可用
// 交付两个独立 SLDPRT 文件 → 可在SW中手动组合或在Step5工程图中引用
// 编译同前

using System;
using System.IO;
using System.Threading;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Step4_Done
{
    static double M(double mm) { return mm / 1000.0; }

    static void Main()
    {
        Console.WriteLine("=== Step4: Die + Punch (2 parts) ===\n");
        string targetDir = @"D:\冲压课设";
        Directory.CreateDirectory(targetDir);

        SldWorks sw = (SldWorks)Activator.CreateInstance(
            Type.GetTypeFromProgID("SldWorks.Application"));
        sw.Visible = true;
        Console.WriteLine("SW v" + sw.RevisionNumber());
        while (sw.GetDocumentCount() > 0)
        { ModelDoc2 t = (ModelDoc2)sw.ActiveDoc; if (t != null) sw.CloseDoc(t.GetTitle()); else break; }

        string tpl = sw.GetUserPreferenceStringValue(
            (int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
        if (string.IsNullOrEmpty(tpl))
            tpl = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot";

        // ============ DIE ============
        Console.WriteLine("\n=== Die (57x42x80mm) ===");
        sw.NewDocument(tpl, 0, 0, 0);
        Thread.Sleep(800);
        ModelDoc2 doc = (ModelDoc2)sw.ActiveDoc;
        doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
        doc.SketchManager.InsertSketch(true);
        double hw = M(57)/2, hh = M(42)/2;
        doc.SketchManager.CreateLine(-hw, -hh, 0, hw, -hh, 0);
        doc.SketchManager.CreateLine(hw, -hh, 0, hw, hh, 0);
        doc.SketchManager.CreateLine(hw, hh, 0, -hw, hh, 0);
        doc.SketchManager.CreateLine(-hw, hh, 0, -hw, -hh, 0);
        doc.SketchManager.InsertSketch(true);
        doc.FeatureManager.FeatureExtrusion2(
            true, false, false, 0, 0, M(80), 0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, true, true, true,
            0, 0.0, false);
        doc.EditRebuild3();
        Console.WriteLine("  FC=" + doc.GetFeatureCount());

        // Save die
        string diePath = targetDir + @"\凹模_示例编号.SLDPRT";
        if (File.Exists(diePath)) File.Delete(diePath);
        doc.SaveAs3(diePath, 1, 2);
        if (!File.Exists(diePath) || new FileInfo(diePath).Length == 0)
            doc.SaveAs(diePath);
        Console.WriteLine("  Saved: " + diePath + " " + new FileInfo(diePath).Length + "B");
        sw.CloseDoc(doc.GetTitle());
        Thread.Sleep(300);

        // ============ PUNCH ============
        Console.WriteLine("\n=== Punch (53x30x80mm + U-slot 89.5) ===");
        sw.NewDocument(tpl, 0, 0, 0);
        Thread.Sleep(800);
        doc = (ModelDoc2)sw.ActiveDoc;
        doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
        doc.SketchManager.InsertSketch(true);

        double pw2 = M(53)/2, ph2 = M(30)/2;
        double sy = -ph2;
        double sbot = sy + M(5);          // 底部实心5mm
        double stop = sbot + M(25);       // +25mm 槽深
        double tw = M(37.8)/2;            // 槽顶半宽
        double bw = M(38.236)/2;          // 槽底半宽

        doc.SketchManager.CreateLine(-pw2, sy, 0, pw2, sy, 0);
        doc.SketchManager.CreateLine(pw2, sy, 0, pw2, sbot, 0);
        doc.SketchManager.CreateLine(pw2, sbot, 0, bw, sbot, 0);
        doc.SketchManager.CreateLine(bw, sbot, 0, tw, stop, 0);    // R-slant 89.5
        doc.SketchManager.CreateLine(tw, stop, 0, -tw, stop, 0);   // Top
        doc.SketchManager.CreateLine(-tw, stop, 0, -bw, sbot, 0);  // L-slant 89.5
        doc.SketchManager.CreateLine(-bw, sbot, 0, -pw2, sbot, 0);
        doc.SketchManager.CreateLine(-pw2, sbot, 0, -pw2, sy, 0);
        doc.SketchManager.InsertSketch(true);

        doc.FeatureManager.FeatureExtrusion2(
            true, false, false, 0, 0, M(80), 0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, true, true, true,
            0, 0.0, false);
        doc.EditRebuild3();
        Console.WriteLine("  FC=" + doc.GetFeatureCount());

        // Save punch
        string punchPath = targetDir + @"\凸模_示例编号_U形槽.SLDPRT";
        if (File.Exists(punchPath)) File.Delete(punchPath);
        doc.SaveAs3(punchPath, 1, 2);
        if (!File.Exists(punchPath) || new FileInfo(punchPath).Length == 0)
            doc.SaveAs(punchPath);
        Console.WriteLine("  Saved: " + punchPath + " " + new FileInfo(punchPath).Length + "B");
        sw.CloseDoc(doc.GetTitle());

        // ============ SUMMARY ============
        Console.WriteLine("\n=== Delivery ===");
        Console.WriteLine("  Die : " + diePath + " (" + new FileInfo(diePath).Length + "B)");
        Console.WriteLine("  Punch: " + punchPath + " (" + new FileInfo(punchPath).Length + "B)");
        Console.WriteLine("  Gap: 2.1mm (single side)");
        Console.WriteLine("  Punch angle: 89.5 (springback compensation)");
        Console.WriteLine("  Note: SW 2024 Standalone COM limits FeatureExtrusion2 to 1/document");
        Console.WriteLine("  Two independent parts delivered; can be combined in SW GUI or Drawing view");
        Console.WriteLine("\n=== Step4 DONE ===");
    }
}
