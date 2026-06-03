// Step5_Final.cs — 凸模U形槽89.5°工程图 (A4, 三视图+等轴测+标注)
// SW 2024 Standalone C# + gb_a4.drwdot
//
// 编译同前

using System;
using System.IO;
using System.Threading;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Step5_Final
{
    static void Main()
    {
        Console.WriteLine("=== Step5: Drawing (Punch w/ 89.5 U-slot) ===\n");

        SldWorks sw = (SldWorks)Activator.CreateInstance(
            Type.GetTypeFromProgID("SldWorks.Application"));
        sw.Visible = true;
        while (sw.GetDocumentCount() > 0)
        { ModelDoc2 t = (ModelDoc2)sw.ActiveDoc; if (t != null) sw.CloseDoc(t.GetTitle()); else break; }

        // 1. Open punch part (it must be open for drawing views)
        string punchPath = @"D:\冲压课设1\181班27号\凸模_27号_U形槽.SLDPRT";
        int errors = 0, warnings = 0;
        ModelDoc2 punchDoc = (ModelDoc2)sw.OpenDoc6(punchPath, 1, 1, "", errors, warnings);
        Console.WriteLine("[1] Punch loaded: " + punchDoc.GetTitle());

        // 2. Create A4 drawing
        string drwTpl = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_a4.drwdot";
        sw.NewDocument(drwTpl, 0, 0, 0);
        Thread.Sleep(1500);
        ModelDoc2 doc = (ModelDoc2)sw.ActiveDoc;
        IDrawingDoc dDoc = (IDrawingDoc)doc;
        Console.WriteLine("[2] Drawing: " + doc.GetTitle());

        // 3. Insert views
        // CreateDrawViewFromModelView3(NameOnSheet, ViewName, X, Y, Scale)
        // A4 sheet: ~0.21 x ~0.297m (210 x 297mm)
        // View positions in meters on sheet

        Console.WriteLine("\n[3] Inserting views...");

        try
        {
            // Front view: center-left
            dDoc.CreateDrawViewFromModelView3("前视", "*前视", 0.05, 0.15, 1.0);
            Console.WriteLine("  Front view OK");
        }
        catch (Exception ex) { Console.WriteLine("  Front view fail: " + ex.Message); }

        try
        {
            // Top view: below front
            dDoc.CreateDrawViewFromModelView3("上视", "*上视", 0.05, 0.05, 1.0);
            Console.WriteLine("  Top view OK");
        }
        catch (Exception ex) { Console.WriteLine("  Top view fail: " + ex.Message); }

        try
        {
            // Right view: right of front
            dDoc.CreateDrawViewFromModelView3("右视", "*右视", 0.15, 0.15, 1.0);
            Console.WriteLine("  Right view OK");
        }
        catch (Exception ex) { Console.WriteLine("  Right view fail: " + ex.Message); }

        try
        {
            // Isometric view: top-right
            dDoc.CreateDrawViewFromModelView3("等轴测", "*等轴测", 0.15, 0.05, 1.0);
            Console.WriteLine("  Isometric view OK");
        }
        catch (Exception ex) { Console.WriteLine("  Isometric view fail: " + ex.Message); }

        // 4. Insert model annotations (dimensions)
        Console.WriteLine("\n[4] Inserting dimensions...");
        try
        {
            dDoc.InsertModelAnnotations4(
                1,       // AllViews
                2,       // Option
                true,    // ImportDims
                true,    // ImportAnnotations
                false,   // IncludeHidden
                false,   // IncludeDangling
                false,   // IncludeInstanceCounts
                false    // IncludeCustomProperties
            );
            Console.WriteLine("  InsertModelAnnotations4 OK");
        }
        catch (Exception ex) { Console.WriteLine("  Dims fail: " + ex.Message); }

        // 5. Save
        doc.EditRebuild3();
        doc.ViewZoomtofit2();
        Thread.Sleep(500);

        string savePath = @"D:\冲压课设1\181班27号\工程图_27号.SLDDRW";
        if (File.Exists(savePath)) File.Delete(savePath);
        doc.SaveAs3(savePath, 1, 2);
        if (!File.Exists(savePath) || new FileInfo(savePath).Length == 0)
            doc.SaveAs(savePath);

        long sz = File.Exists(savePath) ? new FileInfo(savePath).Length : 0;
        Console.WriteLine("\n[5] Saved: " + savePath + " (" + sz + "B)");

        // Also save die drawing
        Console.WriteLine("\n[6] Die drawing...");
        sw.CloseDoc(punchDoc.GetTitle());
        Thread.Sleep(300);

        // Open die
        string diePath = @"D:\冲压课设1\181班27号\凹模_27号.SLDPRT";
        ModelDoc2 dieDoc = (ModelDoc2)sw.OpenDoc6(diePath, 1, 1, "", errors, warnings);
        Console.WriteLine("  Die loaded: " + (dieDoc != null ? dieDoc.GetTitle() : "FAIL"));

        // Create second drawing
        sw.NewDocument(drwTpl, 0, 0, 0);
        Thread.Sleep(1500);
        doc = (ModelDoc2)sw.ActiveDoc;
        dDoc = (IDrawingDoc)doc;

        try { dDoc.CreateDrawViewFromModelView3("前视", "*前视", 0.05, 0.15, 1.0); }
        catch { }
        try { dDoc.CreateDrawViewFromModelView3("上视", "*上视", 0.05, 0.05, 1.0); }
        catch { }
        try { dDoc.CreateDrawViewFromModelView3("右视", "*右视", 0.15, 0.15, 1.0); }
        catch { }

        doc.EditRebuild3();
        string saveDie = @"D:\冲压课设1\181班27号\工程图_凹模_27号.SLDDRW";
        if (File.Exists(saveDie)) File.Delete(saveDie);
        doc.SaveAs3(saveDie, 1, 2);
        if (!File.Exists(saveDie) || new FileInfo(saveDie).Length == 0)
            doc.SaveAs(saveDie);
        Console.WriteLine("  Saved: " + saveDie + " (" + new FileInfo(saveDie).Length + "B)");

        Console.WriteLine("\n=== Step5 DONE ===");
    }
}
