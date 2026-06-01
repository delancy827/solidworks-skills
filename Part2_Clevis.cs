using System;
using System.IO;
using System.Text;
using System.Threading;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Program
{
    static StreamWriter log;
    static SldWorks swApp;
    static ModelDoc2 swDoc;
    static PartDoc partDoc;
    static string outDir = @"C:\Users\22374\Desktop\湛江北海\学习课程\sw\冲压作业";

    static void Main()
    {
        log = new StreamWriter(Path.Combine(outDir, "Part2_log.txt"), false, Encoding.UTF8);
        log.AutoFlush = true; Console.SetOut(log);
        Console.WriteLine("=== Part2 双叉接头 ===");

        Type t = Type.GetTypeFromProgID("SldWorks.Application");
        swApp = (SldWorks)Activator.CreateInstance(t);
        swApp.Visible = true;

        while (swApp.GetDocumentCount() > 0) {
            ModelDoc2 temp = (ModelDoc2)swApp.ActiveDoc;
            if (temp != null) swApp.CloseDoc(temp.GetTitle());
            else break;
        }

        swDoc = (ModelDoc2)swApp.NewPart();
        partDoc = (PartDoc)swDoc;
        Console.WriteLine("OK: 新建零件");

        // === Step1: 叉部基体 90x50x50 ===
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.090, 0.050, 0);
        swDoc.SketchManager.InsertSketch(true);

        int before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(true, false, false, 0, 0, 0.050, 0.0,
            false,false,false,false, 0.0,0.0, false,false,false,false, false,
            false,false, 0,0.0,false);
        VerifyFeature(before, "Part2_Step1");
        VerifyBodies(1, "Part2_Step1");
        TakeScreenshot("Part2_Step1.jpg");

        // === Step2: 偏移基准面 + 扁柄(R25圆头+Φ18孔) ===
        SelectPlane("前视基准面", "Front Plane");
        Feature planeFeat = (Feature)swDoc.FeatureManager.InsertRefPlane(8, 0.0125, 0,0,0,0);
        string pn = planeFeat.Name;
        Console.WriteLine("OK 偏移面: " + pn);
        swDoc.Extension.SelectByID2(pn, "PLANE", 0,0,0, false, 0, null, 0);
        swDoc.SketchManager.InsertSketch(true);

        swDoc.SketchManager.CreateLine(-0.045, 0, 0, 0, 0, 0);
        swDoc.SketchManager.CreateLine(0, 0, 0, 0, 0.050, 0);
        swDoc.SketchManager.CreateLine(0, 0.050, 0, -0.045, 0.050, 0);
        swDoc.SketchManager.Create3PointArc(-0.045, 0, 0, -0.045, 0.050, 0, -0.070, 0.025, 0);
        swDoc.SketchManager.CreateCircleByRadius(-0.045, 0.025, 0, 0.009);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(true, false, false, 0, 0, 0.025, 0.0,
            false,false,false,false, 0.0,0.0, false,false,false,false, true,
            false,false, 0,0.0,false);
        VerifyFeature(before, "Part2_Step2");
        VerifyBodies(1, "Part2_Step2");
        TakeScreenshot("Part2_Step2.jpg");

        // === Step3: U形槽 ===
        SelectPlane("上视基准面", "Top Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCornerRectangle(0.015, -0.0125, 0, 0.090, -0.0375, 0);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureCut4(false, false, false, 1, 1, 0.0,0.0,
            false,false,false,false, 0.0,0.0, false,false,false,false, false,
            false,false,false,false,false, 0,0.0,false,false);
        VerifyFeature(before, "Part2_Step3");
        VerifyBodies(1, "Part2_Step3");
        TakeScreenshot("Part2_Step3.jpg");

        // === Step4: 叉耳Φ18通孔 ===
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0.075, 0.025, 0, 0.009);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureCut4(false, false, false, 1, 1, 0.0,0.0,
            false,false,false,false, 0.0,0.0, false,false,false,false, false,
            false,false,false,false,false, 0,0.0,false,false);
        VerifyFeature(before, "Part2_Step4");
        VerifyBodies(1, "Part2_Step4");
        TakeScreenshot("Part2_Step4.jpg");

        string sldprt = Path.Combine(outDir, "零件2.SLDPRT");
        swDoc.SaveAs3(sldprt, 0, 0);
        Console.WriteLine("SAVED: " + sldprt);
        Console.WriteLine("=== Part2 ALL DONE ===");
        log.Close();
    }

    static void SelectPlane(string cn, string en) {
        bool ok = swDoc.Extension.SelectByID2(cn, "PLANE", 0,0,0, false, 0, null, 0);
        if (!ok) ok = swDoc.Extension.SelectByID2(en, "PLANE", 0,0,0, false, 0, null, 0);
        if (!ok) Fail("选基准面失败: " + cn);
    }
    static void VerifyFeature(int before, string name) {
        swDoc.ForceRebuild3(false);
        int after = swDoc.GetFeatureCount();
        if (after <= before) Fail(name + " 失败: " + before + "->" + after);
        Console.WriteLine("OK " + name + " 特征:" + before + "->" + after);
    }
    static void VerifyBodies(int expected, string name) {
        object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
        int count = (bodies == null) ? 0 : bodies.Length;
        if (count != expected) Fail(name + " 实体:" + expected + "!=" + count);
        Console.WriteLine("OK " + name + " 实体数:" + count);
    }
    static void TakeScreenshot(string filename) {
        try {
            swDoc.ViewZoomtofit(); Thread.Sleep(300);
            swDoc.ForceRebuild3(false);
            int errs = 0, warns = 0;
            swDoc.Extension.SaveAs(Path.Combine(outDir, filename),
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, ref errs, ref warns);
            Console.WriteLine("Screenshot: OK " + filename);
        } catch (Exception ex) { Console.WriteLine("Screenshot error: " + ex.Message); }
    }
    static void Fail(string msg) {
        Console.WriteLine("FAIL: " + msg);
        if (swDoc != null) swApp.CloseDoc(swDoc.GetTitle());
        log.Close(); throw new Exception(msg);
    }
}
