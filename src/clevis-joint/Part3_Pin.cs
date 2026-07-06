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
    static string outDir = @"C:\Users\<user>\Desktop\湛江北海\学习课程\sw\冲压作业";

    static void Main()
    {
        log = new StreamWriter(Path.Combine(outDir, "Part3_log.txt"), false, Encoding.UTF8);
        log.AutoFlush = true; Console.SetOut(log);
        Console.WriteLine("=== Part3 阶梯销轴 ===");

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

        // === Step1: Φ30头部圆柱 ===
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.015);
        swDoc.SketchManager.InsertSketch(true);

        int before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(true, false, false, 0, 0, 0.010, 0.0,
            false,false,false,false, 0.0,0.0, false,false,false,false, false,
            false,false, 0,0.0,false);
        VerifyFeature(before, "Part3_Step1");
        VerifyBodies(1, "Part3_Step1");
        TakeScreenshot("Part3_Step1.jpg");

        // === Step2: Φ18杆身圆柱 (Merge=true) ===
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.009);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(true, false, false, 0, 0, 0.050, 0.0,
            false,false,false,false, 0.0,0.0, false,false,false,false, true,
            false,false, 0,0.0,false);
        VerifyFeature(before, "Part3_Step2");
        VerifyBodies(1, "Part3_Step2");
        TakeScreenshot("Part3_Step2.jpg");

        string sldprt = Path.Combine(outDir, "零件3.SLDPRT");
        swDoc.SaveAs3(sldprt, 0, 0);
        Console.WriteLine("SAVED: " + sldprt);
        Console.WriteLine("=== Part3 ALL DONE ===");
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
        try { if (swDoc != null) swApp.CloseDoc(swDoc.GetTitle()); } catch { }
        try { log.Close(); } catch { } throw new Exception(msg);
    }
}
