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
        log = new StreamWriter("pin_log.txt", false, Encoding.UTF8);
        log.AutoFlush = true;
        Console.SetOut(log);
        Console.WriteLine("=== Pin Shaft - Step Cylinder Build ===");

        // 1. 连接SW（同权限级别）
        Type t = Type.GetTypeFromProgID("SldWorks.Application");
        swApp = (SldWorks)Activator.CreateInstance(t);
        swApp.Visible = true;

        // 2. 清空残留文档
        while (swApp.GetDocumentCount() > 0)
        {
            ModelDoc2 temp = (ModelDoc2)swApp.ActiveDoc;
            if (temp != null) swApp.CloseDoc(temp.GetTitle());
            else break;
        }

        // 3. 新建零件
        swDoc = (ModelDoc2)swApp.NewPart();
        if (swDoc == null) Fail("新建零件失败");
        partDoc = (PartDoc)swDoc;
        Console.WriteLine("OK: 新建零件");

        // ===================== 步骤1：头部大圆柱 Φ30×10 =====================
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.015);  // R=15mm
        swDoc.SketchManager.InsertSketch(true);

        int before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(
            true, false, false,     // [1]Sd [2]Flip [3]Dir
            0, 0,                   // [4]T1=Blind [5]T2=none
            0.010, 0.0,             // [6]D1=10mm [7]D2
            false, false, false, false,  // [8-11]Dchk/Ddir
            0.0, 0.0,               // [12-13]Dang
            false, false,           // [14-15]OffsetRev
            false, false,           // [16-17]TransSurf
            false,                  // [18]Merge（首个特征无需合并）
            false, false,           // [19-20]FeatScope/AutoSel
            0, 0.0, false);         // [21-23]T0/StartOffset/FlipStart
        VerifyFeature(before, "Step1-头部Φ30×10");
        VerifyBodies(1, "Step1");

        // ===================== 步骤2：杆身小圆柱 Φ18×50 (Merge=true) =====================
        SelectPlane("前视基准面", "Front Plane");
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.009);  // R=9mm
        swDoc.SketchManager.InsertSketch(true);

        before = swDoc.GetFeatureCount();
        swDoc.FeatureManager.FeatureExtrusion2(
            true, false, false,
            0, 0,
            0.050, 0.0,             // D1=50mm杆身长度
            false, false, false, false,
            0.0, 0.0,
            false, false,
            false, false,
            true,                   // [18]Merge=true ← 与头部融为一体！
            false, false,
            0, 0.0, false);
        VerifyFeature(before, "Step2-杆身Φ18×50");
        VerifyBodies(1, "Step2");

        Console.WriteLine("=== ALL DONE - 阶梯销轴生成完成 ===");
        log.Close();
    }

    static void SelectPlane(string cn, string en)
    {
        bool ok = swDoc.Extension.SelectByID2(cn, "PLANE", 0, 0, 0, false, 0, null, 0);
        if (!ok) ok = swDoc.Extension.SelectByID2(en, "PLANE", 0, 0, 0, false, 0, null, 0);
        if (!ok) Fail("选基准面失败: " + cn + "/" + en);
    }

    // 特征数验证
    static void VerifyFeature(int before, string name)
    {
        swDoc.ForceRebuild3(false);
        int after = swDoc.GetFeatureCount();
        if (after <= before)
            Fail(name + " 失败: 特征数未增长 " + before + "->" + after);
        Console.WriteLine("OK " + name + " 特征:" + before + "->" + after);
    }

    // 实体计数硬验证（防假通关）
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
        if (swDoc != null) swApp.CloseDoc(swDoc.GetTitle());
        log.Close();
        throw new Exception(msg);
    }
}
