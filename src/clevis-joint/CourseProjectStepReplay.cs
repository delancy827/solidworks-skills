using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class CourseProjectStepReplay
{
    static readonly string WorkDir = @"C:\Users\22374\Desktop\湛江北海\学习课程\sw\冲压作业";
    static readonly string ShotDir = Path.Combine(WorkDir, "建模过程截图");
    static SldWorks swApp;
    static ModelDoc2 doc;
    static PartDoc part;

    enum Plane { Front = 0, Top = 1, Right = 2 }

    [STAThread]
    static int Main()
    {
        try
        {
            Directory.CreateDirectory(ShotDir);
            Connect();
            ReplayPart1();
            ReplayPart2();
            ReplayPart3();
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine("FAIL " + ex.GetType().Name + ": " + ex.Message);
            Console.WriteLine(ex.StackTrace);
            return 1;
        }
        finally
        {
            try { if (doc != null) swApp.CloseDoc(doc.GetTitle()); } catch { }
        }
    }

    static void Connect()
    {
        try { swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application"); }
        catch
        {
            if (Process.GetProcessesByName("SLDWORKS").Length > 0)
                throw new Exception("SLDWORKS is running but COM is unavailable.");
            Type t = Type.GetTypeFromProgID("SldWorks.Application");
            swApp = (SldWorks)Activator.CreateInstance(t);
        }
        swApp.Visible = true;
        swApp.UserControl = true;
    }

    static void NewPart()
    {
        string template = "";
        try { template = swApp.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplatePart); } catch { }
        if (String.IsNullOrWhiteSpace(template) || !File.Exists(template))
            template = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot";
        doc = (ModelDoc2)swApp.NewDocument(template, 0, 0, 0);
        if (doc == null) doc = (ModelDoc2)swApp.ActiveDoc;
        if (doc == null) throw new Exception("new part failed");
        part = (PartDoc)doc;
    }

    static void ReplayPart1()
    {
        NewPart();
        SelectPlane(Plane.Top);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.075);
        doc.SketchManager.InsertSketch(true);
        Boss(0.030, false, false, (int)swStartConditions_e.swStartSketchPlane);
        Capture("01-1_零件1_拉伸圆形底座.jpg", "*Isometric", 7);

        SelectPlane(Plane.Front);
        doc.SketchManager.InsertSketch(true);
        double x = 0.035, y0 = 0.030, yc = 0.115, yt = 0.150;
        doc.SketchManager.CreateLine(-x, y0, 0, -x, yc, 0);
        doc.SketchManager.Create3PointArc(-x, yc, 0, x, yc, 0, 0, yt, 0);
        doc.SketchManager.CreateLine(x, yc, 0, x, y0, 0);
        doc.SketchManager.CreateLine(x, y0, 0, -x, y0, 0);
        doc.SketchManager.CreateCircleByRadius(0, yc, 0, 0.009);
        doc.SketchManager.InsertSketch(true);
        Boss(0.060, true, false, (int)swStartConditions_e.swStartSketchPlane, true);
        Capture("01-2_零件1_建立双耳外形和孔.jpg", "*Isometric", 7);

        SelectPlane(Plane.Front);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateCornerRectangle(-0.035, 0.050, 0, 0.035, 0.150, 0);
        doc.SketchManager.InsertSketch(true);
        CutMid(0.025);
        Capture("01-3_零件1_切除中间25mm槽.jpg", "*Isometric", 7);

        swApp.CloseDoc(doc.GetTitle());
        doc = null;
    }

    static void ReplayPart2()
    {
        NewPart();
        SelectPlane(Plane.Front);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.090, 0.050, 0);
        doc.SketchManager.InsertSketch(true);
        Boss(0.050, false, false, (int)swStartConditions_e.swStartSketchPlane);
        Capture("02-1_零件2_拉伸叉形基础块.jpg", "*Isometric", 7);

        SelectPlane(Plane.Front);
        Feature plane = (Feature)doc.FeatureManager.InsertRefPlane(8, 0.0125, 0, 0, 0, 0);
        doc.Extension.SelectByID2(plane.Name, "PLANE", 0, 0, 0, false, 0, null, 0);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateLine(-0.045, 0, 0, 0, 0, 0);
        doc.SketchManager.CreateLine(0, 0, 0, 0, 0.050, 0);
        doc.SketchManager.CreateLine(0, 0.050, 0, -0.045, 0.050, 0);
        doc.SketchManager.Create3PointArc(-0.045, 0, 0, -0.045, 0.050, 0, -0.070, 0.025, 0);
        doc.SketchManager.CreateCircleByRadius(-0.045, 0.025, 0, 0.009);
        doc.SketchManager.InsertSketch(true);
        Boss(0.025, true, false, (int)swStartConditions_e.swStartSketchPlane);
        Capture("02-2_零件2_建立单耳铰接端.jpg", "*Isometric", 7);

        SelectPlane(Plane.Top);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateCornerRectangle(0.015, -0.0125, 0, 0.090, -0.0375, 0);
        doc.SketchManager.InsertSketch(true);
        CutThrough();
        Capture("02-3_零件2_切除叉口.jpg", "*Isometric", 7);

        SelectPlane(Plane.Front);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateCircleByRadius(0.075, 0.025, 0, 0.009);
        doc.SketchManager.InsertSketch(true);
        CutThrough();
        Capture("02-4_零件2_加工叉耳孔.jpg", "*Isometric", 7);

        swApp.CloseDoc(doc.GetTitle());
        doc = null;
    }

    static void ReplayPart3()
    {
        NewPart();
        SelectPlane(Plane.Front);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.015);
        doc.SketchManager.InsertSketch(true);
        Boss(0.010, false, false, (int)swStartConditions_e.swStartSketchPlane);
        Capture("03-1_零件3_拉伸销轴头部.jpg", "*Isometric", 7);

        SelectPlane(Plane.Front);
        doc.SketchManager.InsertSketch(true);
        doc.SketchManager.CreateCircleByRadius(0, 0, 0, 0.009);
        doc.SketchManager.InsertSketch(true);
        Boss(0.050, true, false, (int)swStartConditions_e.swStartSketchPlane);
        Capture("03-2_零件3_拉伸18mm轴身.jpg", "*Isometric", 7);

        swApp.CloseDoc(doc.GetTitle());
        doc = null;
    }

    static void Boss(double depth, bool merge, bool flip, int start)
    {
        Boss(depth, merge, flip, start, false);
    }

    static void Boss(double depth, bool merge, bool flip, int start, bool midPlane)
    {
        doc.FeatureManager.FeatureExtrusion2(
            true, flip, false,
            midPlane ? (int)swEndConditions_e.swEndCondMidPlane : (int)swEndConditions_e.swEndCondBlind,
            (int)swEndConditions_e.swEndCondBlind,
            depth, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false,
            merge, true, true, start, 0.0, false);
        doc.ForceRebuild3(false);
    }

    static void CutThrough()
    {
        doc.FeatureManager.FeatureCut4(false, false, false, 1, 1, 0.0, 0.0,
            false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, false, false, false,
            0, 0.0, false, false);
        doc.ForceRebuild3(false);
    }

    static void CutMid(double depth)
    {
        doc.FeatureManager.FeatureCut4(false, false, false,
            (int)swEndConditions_e.swEndCondMidPlane, (int)swEndConditions_e.swEndCondBlind,
            depth, 0.0, false, false, false, false, 0.0, 0.0,
            false, false, false, false, false,
            false, false, false, false, false,
            (int)swStartConditions_e.swStartSketchPlane, 0.0, false, false);
        doc.ForceRebuild3(false);
    }

    static void SelectPlane(Plane plane)
    {
        doc.ClearSelection2(true);
        string[] names = plane == Plane.Front
            ? new[] { "Front Plane", "前视基准面" }
            : plane == Plane.Top ? new[] { "Top Plane", "上视基准面" } : new[] { "Right Plane", "右视基准面" };
        foreach (string name in names)
            if (doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, false, 0, null, 0)) return;
        Feature feat = (Feature)doc.FirstFeature();
        int index = 0;
        while (feat != null)
        {
            if (feat.GetTypeName2() == "RefPlane")
            {
                if (index == (int)plane && feat.Select2(false, 0)) return;
                index++;
            }
            feat = (Feature)feat.GetNextFeature();
        }
        throw new Exception("cannot select plane " + plane);
    }

    static void Capture(string fileName, string view, int id)
    {
        doc.ClearSelection2(true);
        try { doc.ShowNamedView2(view, id); } catch { }
        try { doc.ViewZoomtofit2(); } catch { }
        Thread.Sleep(350);
        string path = Path.Combine(ShotDir, fileName);
        try { if (File.Exists(path)) File.Delete(path); } catch { }
        int errors = 0, warnings = 0;
        bool ok = doc.Extension.SaveAs(path,
            (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
            (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
            null, ref errors, ref warnings);
        if (!ok || !File.Exists(path)) throw new Exception("capture failed " + fileName + " errors=" + errors);
        Console.WriteLine("capture " + path);
    }
}
