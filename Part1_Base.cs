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
    static string sldprt = "";

    static void Main()
    {
        log = new StreamWriter(Path.Combine(outDir, "Part1_log.txt"), false, Encoding.UTF8);
        log.AutoFlush = true;
        Console.SetOut(log);
        Console.WriteLine("=== Part1 底座支架 ===");

        Type t = Type.GetTypeFromProgID("SldWorks.Application");
        swApp = (SldWorks)Activator.CreateInstance(t);
        swApp.Visible = true;

        while (swApp.GetDocumentCount() > 0) {
            ModelDoc2 temp = (ModelDoc2)swApp.ActiveDoc;
            if (temp != null) swApp.CloseDoc(temp.GetTitle());
            else break;
        }

        swDoc = (ModelDoc2)swApp.NewPart();
        if (swDoc == null) Fail("新建零件失败");
        partDoc = (PartDoc)swDoc;
        Console.WriteLine("OK: 新建零件");

        // ==================== Step1: Φ150圆盘基体 ====================
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.075);
        swDoc.SketchManager.InsertSketch(true);

        int before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(
            true, false, false, 0, 0, 0.020, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, 0, 0.0, false);
        VerifyFeature(before, "Part1_Step1");
        VerifyBodies(1, "Part1_Step1");
        TakeScreenshot("Part1_Step1.jpg");

        // ==================== Step2: 凸台+双耳+Φ18孔 ====================
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);

        // 凸台基座矩形: X[-0.025,0.025], Y[0,0.035]
        swDoc.SketchManager.CreateCornerRectangle(-0.025, 0, 0, 0.025, 0.035, 0);

        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(
            true, false, false, 0, 0, 0.020, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, true,   // Merge=true
            false, false, 0, 0.0, false);
        VerifyFeature(before, "Part1_Step2a-凸台");

        // 2b: 切除中间槽 → 形成双耳
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        // 槽: X[-0.012,0.012], Y[0.020,0.035] 切除中间留两侧耳朵
        swDoc.SketchManager.CreateCornerRectangle(-0.012, 0.020, 0, 0.012, 0.035, 0);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureCut4(
            false, false, false, 1, 1, 0.0, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, false, false, false,
            0, 0.0, false, false);
        VerifyFeature(before, "Part1_Step2b-切槽");

        // 2c: 双侧Φ18孔
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0.017, 0.0275, 0, 0.009);
        swDoc.SketchManager.CreateCircleByRadius(-0.017, 0.0275, 0, 0.009);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureCut4(
            false, false, false, 1, 1, 0.0, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, false, false, false,
            0, 0.0, false, false);
        VerifyFeature(before, "Part1_Step2c-Φ18孔");
        VerifyBodies(1, "Part1_Step2");

        // 保存零件
        sldprt = Path.Combine(outDir, "零件1.SLDPRT");
        swDoc.SaveAs3(sldprt, 0, 0);
        Console.WriteLine("SAVED: " + sldprt);
        TakeScreenshot("Part1_Step2.jpg");

        Console.WriteLine("=== Part1 ALL DONE ===");
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
            swDoc.ViewZoomtofit();
            System.Threading.Thread.Sleep(300);
            swDoc.ForceRebuild3(false);
            string path = Path.Combine(outDir, filename);
            // SW SaveAs3 通过扩展名自动识别JPG格式
            int errs = 0, warns = 0;
            swDoc.Extension.SaveAs(path, (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, ref errs, ref warns);
            Console.WriteLine("Screenshot: OK " + filename + (errs>0?" (warns:"+errs+")":""));
        } catch (Exception ex) {
            Console.WriteLine("Screenshot error: " + ex.Message);
        }
    }

    static void Fail(string msg) {
        Console.WriteLine("FAIL: " + msg);
        if (swDoc != null) swApp.CloseDoc(swDoc.GetTitle());
        log.Close();
        throw new Exception(msg);
    }
}
