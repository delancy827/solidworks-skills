using System;
using System.IO;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class Program
{
    static StreamWriter log;
    static SldWorks swApp;
    static ModelDoc2 swDoc;
    static PartDoc partDoc;

    static void Main()
    {
        log = new StreamWriter("log.txt", false, Encoding.UTF8);
        log.AutoFlush = true;
        Console.SetOut(log);
        Console.WriteLine("=== Clevis Joint - Offset Plane Build ===");

        Type t = Type.GetTypeFromProgID("SldWorks.Application");
        swApp = (SldWorks)Activator.CreateInstance(t);
        swApp.Visible = true;

        while (swApp.GetDocumentCount() > 0)
        {
            ModelDoc2 temp = (ModelDoc2)swApp.ActiveDoc;
            if (temp != null) swApp.CloseDoc(temp.GetTitle());
            else break;
        }

        swDoc = (ModelDoc2)swApp.NewPart();
        if (swDoc == null) Fail("新建零件失败");
        partDoc = (PartDoc)swDoc;
        Console.WriteLine("OK: 新建零件");

        // ===================== 步骤1：叉部大基体 =====================
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.090, 0.050, 0);
        swDoc.SketchManager.InsertSketch(true);

        int before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(
            true, false, false, 0, 0, 0.050, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, 0, 0.0, false);
        VerifyFeature(before, "Step1-基体拉伸");
        VerifyBodies(1, "Step1");

        // ===================== 步骤2：创建偏移基准面 + 扁柄草图 =====================
        // 创建距前视基准面0.0125的平行基准面（Z=0.0125）
        SelectPlane("前视基准面", "Front Plane");
        Feature offsetPlaneFeat = (Feature)swDoc.FeatureManager.InsertRefPlane(
            8, 0.0125, 0, 0, 0, 0);
        if (offsetPlaneFeat == null) Fail("创建偏移基准面失败");
        string planeName = offsetPlaneFeat.Name;
        Console.WriteLine("OK: 偏移基准面 " + planeName);

        // 在偏移基准面上画草图
        bool ok = swDoc.Extension.SelectByID2(planeName, "PLANE", 0, 0, 0, false, 0, null, 0);
        if (!ok) Fail("选偏移基准面失败: " + planeName);
        swDoc.SketchManager.InsertSketch(true);

        // 分段闭合轮廓：底边→右边→顶边→左侧R25圆弧
        swDoc.SketchManager.CreateLine(-0.045, 0, 0, 0, 0, 0);           // 底边
        swDoc.SketchManager.CreateLine(0, 0, 0, 0, 0.050, 0);            // 右边
        swDoc.SketchManager.CreateLine(0, 0.050, 0, -0.045, 0.050, 0);   // 顶边
        // 用三点圆弧：起点(-0.045,0)，终点(-0.045,0.050)，中点(-0.070,0.025)
        swDoc.SketchManager.Create3PointArc(-0.045, 0, 0, -0.045, 0.050, 0, -0.070, 0.025, 0);
        // 同心孔 Φ18
        swDoc.SketchManager.CreateCircleByRadius(-0.045, 0.025, 0, 0.009);

        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(
            true, false, false, 0, 0, 0.025, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, true,   // [18]Merge=true
            false, false, 0, 0.0, false);
        VerifyFeature(before, "Step2-扁柄拉伸");
        VerifyBodies(1, "Step2");

        // ===================== 步骤3：U形槽 =====================
        SelectPlane("上视基准面", "Top Plane");
        swDoc.SketchManager.InsertSketch(true);
        // 上视基准面草图Y正方向对应模型Z负方向，故取负坐标
        swDoc.SketchManager.CreateCornerRectangle(0.015, -0.0125, 0, 0.090, -0.0375, 0);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureCut4(
            false, false, false,    // Sd=false,Flip=false,Dir
            1, 1,
            0.0, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, false, false, false,
            0, 0.0, false, false);
        VerifyFeature(before, "Step3-U形槽");
        VerifyBodies(1, "Step3");

        // ===================== 步骤4：双侧同轴通孔 =====================
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0.075, 0.025, 0, 0.009);
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureCut4(
            false, false, false,
            1, 1,
            0.0, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, false, false, false,
            0, 0.0, false, false);
        VerifyFeature(before, "Step4-通孔");
        VerifyBodies(1, "Step4");

        Console.WriteLine("=== ALL DONE ===");
        log.Close();
    }

    static void SelectPlane(string cn, string en)
    {
        bool ok = swDoc.Extension.SelectByID2(cn, "PLANE", 0, 0, 0, false, 0, null, 0);
        if (!ok) ok = swDoc.Extension.SelectByID2(en, "PLANE", 0, 0, 0, false, 0, null, 0);
        if (!ok) Fail("选基准面失败: " + cn + "/" + en);
    }

    static void VerifyFeature(int before, string name)
    {
        swDoc.ForceRebuild3(false);
        int after = swDoc.GetFeatureCount();
        if (after <= before)
            Fail(name + " 失败: 特征数未增长 " + before + "->" + after);
        Console.WriteLine("OK " + name + " 特征:" + before + "->" + after);
    }

    static void VerifyBodies(int expected, string name)
    {
        object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
        int count = (bodies == null) ? 0 : bodies.Length;
        if (count != expected)
            Fail(name + " 实体数量错误: 期望" + expected + " 实际" + count);
        Console.WriteLine("OK " + name + " 实体数:" + count);
    }

    static void Fail(string msg)
    {
        Console.WriteLine("FAIL: " + msg);
        try { if (swDoc != null) swApp.CloseDoc(swDoc.GetTitle()); } catch { }
        try { log.Close(); } catch { }
        throw new Exception(msg);
    }
}
