using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class VerticalClevisSupport
{
    const double BaseDia = 0.150;
    const double BaseHeight = 0.030;
    const double UprightWidth = 0.070;
    const double UprightHeightAboveBase = 0.120;
    const double EarPackDepth = 0.060;
    const double SlotWidth = 0.025;
    const double SlotBottomAboveBase = 0.020;
    const double HoleDia = 0.018;

    static readonly double EarThickness = (EarPackDepth - SlotWidth) / 2.0;
    static readonly double UprightRadius = UprightWidth / 2.0;
    static readonly double HoleCenterY = BaseHeight + UprightHeightAboveBase - UprightRadius;

    static SldWorks swApp;
    static ModelDoc2 swDoc;
    static PartDoc partDoc;
    static string createdDocTitle;
    static string outputDir;
    static string outputPath;
    static bool keepOpen;
    static bool captureViews;
    static bool forceWithManyDocs;

    enum StandardPlane
    {
        Front = 0,
        Top = 1,
        Right = 2
    }

    [STAThread]
    static int Main(string[] args)
    {
        ParseArgs(args);
        outputDir = Path.Combine(
            System.Environment.GetFolderPath(System.Environment.SpecialFolder.DesktopDirectory),
            "vertical_clevis_support_output");
        Directory.CreateDirectory(outputDir);
        outputPath = Path.Combine(outputDir, "vertical_clevis_support.SLDPRT");

        try
        {
            Connect();
            NewPart();

            BuildBase();
            BuildSlotBottomBridge();
            BuildForkEarsWithThroughHoles();

            VerifyBodies(1, "finished part");
            SavePart(outputPath);
            if (captureViews) CaptureViews();
            AssertVolume();

            Log("DONE part=" + outputPath);
            return 0;
        }
        catch (Exception ex)
        {
            Log("FAIL " + ex.GetType().Name + ": " + ex.Message);
            Log(ex.StackTrace ?? "");
            return 1;
        }
        finally
        {
            CloseOwnedDoc();
        }
    }

    static void ParseArgs(string[] args)
    {
        foreach (string arg in args)
        {
            if (arg == "--keep-open") keepOpen = true;
            else if (arg == "--capture") captureViews = true;
            else if (arg == "--force-with-many-docs") forceWithManyDocs = true;
        }
    }

    static void Connect()
    {
        string[] progIds = {
            "SldWorks.Application.32",
            "SldWorks.Application.31",
            "SldWorks.Application"
        };

        foreach (string pid in progIds)
        {
            try
            {
                swApp = (SldWorks)Marshal.GetActiveObject(pid);
                Log("connected active " + pid);
                break;
            }
            catch
            {
            }
        }

        if (swApp == null)
        {
            Process[] running = Process.GetProcessesByName("SLDWORKS");
            if (running.Length > 0)
            {
                Fail("SLDWORKS.exe is running but is not available through COM. Refusing to start a second instance; close or restart SolidWorks first.");
            }

            Type t = Type.GetTypeFromProgID("SldWorks.Application");
            if (t == null) Fail("SolidWorks COM ProgID is not registered.");
            swApp = (SldWorks)Activator.CreateInstance(t);
            Log("started SolidWorks");
        }

        if (swApp == null) Fail("cannot connect SolidWorks");
        swApp.Visible = true;
        swApp.UserControl = true;

        int openDocs = SafeDocumentCount();
        if (openDocs > 5 && !forceWithManyDocs)
        {
            Fail("SolidWorks already has " + openDocs + " documents open. Close generated test parts or rerun with --force-with-many-docs.");
        }
    }

    static int SafeDocumentCount()
    {
        try { return swApp.GetDocumentCount(); }
        catch { return 0; }
    }

    static void NewPart()
    {
        string template = "";
        try
        {
            template = swApp.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
        }
        catch
        {
        }

        if (String.IsNullOrWhiteSpace(template) || !File.Exists(template))
        {
            template = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot";
        }
        if (!File.Exists(template))
        {
            template = @"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_part.prtdot";
        }
        if (!File.Exists(template)) Fail("part template not found");

        swDoc = (ModelDoc2)swApp.NewDocument(template, 0, 0, 0);
        if (swDoc == null) swDoc = (ModelDoc2)swApp.ActiveDoc;
        if (swDoc == null) Fail("new part failed");

        partDoc = (PartDoc)swDoc;
        createdDocTitle = swDoc.GetTitle();
        try { swDoc.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swSketchAutomaticRelations, false); }
        catch { }
        Log("new part " + createdDocTitle);
    }

    static void BuildBase()
    {
        Log("[1] base cylinder dia=150 height=30");
        SelectStandardPlane(StandardPlane.Top);
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCircleByRadius(0, 0, 0, BaseDia / 2.0);
        swDoc.SketchManager.InsertSketch(true);
        ExtrudeBoss(BaseHeight, false, false, "base cylinder", (int)swStartConditions_e.swStartSketchPlane, 0, false);
        VerifyBodies(1, "base");
    }

    static void BuildSlotBottomBridge()
    {
        Log("[2] full-width/full-depth bridge below slot bottom");
        double x = UprightWidth / 2.0;
        double y0 = BaseHeight;
        double y1 = BaseHeight + SlotBottomAboveBase;

        SelectStandardPlane(StandardPlane.Front);
        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateCornerRectangle(-x, y0, 0, x, y1, 0);
        swDoc.SketchManager.InsertSketch(true);
        ExtrudeBossMidPlane(EarPackDepth, true, "slot-bottom bridge");

        VerifyBodies(1, "bridge");
    }

    static void BuildForkEarsWithThroughHoles()
    {
        Log("[3] two separated fork ears; central slot=25, each ear=17.5");
        double slotHalf = SlotWidth / 2.0;
        double earCenterOffset = slotHalf + EarThickness / 2.0;

        BuildEarOnMidPlane(-earCenterOffset, "rear ear");
        BuildEarOnMidPlane(earCenterOffset, "front ear");

        VerifyBodies(1, "fork ears");
    }

    static void BuildEarOnMidPlane(double offset, string label)
    {
        Feature plane = CreateFrontOffsetPlane(offset, label + " center plane");
        swDoc.ClearSelection2(true);
        if (!plane.Select2(false, 0)) Fail("cannot select " + label + " plane");
        DrawEarProfileWithHole();
        ExtrudeBossMidPlane(EarThickness, true, label + " with through hole");
    }

    static Feature CreateFrontOffsetPlane(double offset, string label)
    {
        SelectStandardPlane(StandardPlane.Front);
        int before = swDoc.GetFeatureCount();
        Feature plane = (Feature)swDoc.FeatureManager.InsertRefPlane(
            (int)swRefPlaneReferenceConstraints_e.swRefPlaneReferenceConstraint_Distance,
            offset, 0, 0, 0, 0);
        swDoc.ForceRebuild3(false);
        if (plane == null || swDoc.GetFeatureCount() <= before) Fail("offset plane failed: " + label);
        plane.Name = label;
        return plane;
    }

    static void DrawEarProfileWithHole()
    {
        double x = UprightWidth / 2.0;
        double y0 = BaseHeight + SlotBottomAboveBase;
        double yc = HoleCenterY;
        double yt = BaseHeight + UprightHeightAboveBase;

        swDoc.SketchManager.InsertSketch(true);
        swDoc.SketchManager.CreateLine(-x, y0, 0, -x, yc, 0);
        swDoc.SketchManager.Create3PointArc(-x, yc, 0, x, yc, 0, 0, yt, 0);
        swDoc.SketchManager.CreateLine(x, yc, 0, x, y0, 0);
        swDoc.SketchManager.CreateLine(x, y0, 0, -x, y0, 0);
        swDoc.SketchManager.CreateCircleByRadius(0, yc, 0, HoleDia / 2.0);
        swDoc.SketchManager.InsertSketch(true);
    }

    static void ExtrudeBoss(double depth, bool merge, bool flip, string label, int startCondition, double startOffset, bool flipStartOffset)
    {
        int before = swDoc.GetFeatureCount();
        Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
            true, flip, false,
            (int)swEndConditions_e.swEndCondBlind,
            (int)swEndConditions_e.swEndCondBlind,
            depth, 0.0,
            false, false,
            false, false,
            0.0, 0.0,
            false, false,
            false, false,
            merge,
            true, true,
            startCondition,
            startOffset,
            flipStartOffset);

        swDoc.ForceRebuild3(false);
        int after = swDoc.GetFeatureCount();
        if (feat == null && after <= before) Fail(label + " returned null and no feature was added");
        if (after <= before) Fail(label + " feature count did not increase " + before + "->" + after);
        Log("OK " + label + " " + before + "->" + after);
    }

    static void ExtrudeBossMidPlane(double depth, bool merge, string label)
    {
        int before = swDoc.GetFeatureCount();
        Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
            true, false, false,
            (int)swEndConditions_e.swEndCondMidPlane,
            (int)swEndConditions_e.swEndCondBlind,
            depth, 0.0,
            false, false,
            false, false,
            0.0, 0.0,
            false, false,
            false, false,
            merge,
            true, true,
            (int)swStartConditions_e.swStartSketchPlane,
            0,
            false);

        swDoc.ForceRebuild3(false);
        int after = swDoc.GetFeatureCount();
        if (feat == null && after <= before) Fail(label + " returned null and no feature was added");
        if (after <= before) Fail(label + " feature count did not increase " + before + "->" + after);
        Log("OK " + label + " " + before + "->" + after);
    }

    static void VerifyBodies(int expected, string label)
    {
        object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
        int count = bodies == null ? 0 : bodies.Length;
        if (count != expected) Fail(label + " body count " + count + " expected " + expected);
        Log("OK " + label + " body count=" + count);
        if (count == 1) LogBodyBox(bodies[0], label);
        LogVolume(label);
    }

    static void LogBodyBox(object bodyObject, string label)
    {
        try
        {
            Body2 body = (Body2)bodyObject;
            object boxObject = body.GetBodyBox();
            double[] box = (double[])boxObject;
            if (box == null || box.Length < 6) return;
            Log(String.Format(
                "{0} bbox x=[{1:F4},{2:F4}] y=[{3:F4},{4:F4}] z=[{5:F4},{6:F4}]",
                label,
                box[0], box[3],
                box[1], box[4],
                box[2], box[5]));
        }
        catch
        {
        }
    }

    static void AssertVolume()
    {
        double baseVolume = Math.PI * Math.Pow(BaseDia / 2.0, 2) * BaseHeight;
        double bridgeVolume = UprightWidth * EarPackDepth * SlotBottomAboveBase;
        double earOuterArea = UprightWidth * (HoleCenterY - BaseHeight - SlotBottomAboveBase)
            + 0.5 * Math.PI * Math.Pow(UprightRadius, 2);
        double holeArea = Math.PI * Math.Pow(HoleDia / 2.0, 2);
        double earsVolume = 2.0 * EarThickness * (earOuterArea - holeArea);
        double expected = baseVolume + bridgeVolume + earsVolume;

        MassProperty mp = (MassProperty)swDoc.Extension.CreateMassProperty();
        double actual = mp.Volume;
        double relErr = Math.Abs(actual - expected) / expected;

        Log(String.Format("volume expected={0:F9} actual={1:F9} rel_err={2:P3}", expected, actual, relErr));
        if (relErr > 0.008)
        {
            Fail("volume assertion failed; the middle slot or pin holes are probably not modeled correctly");
        }
    }

    static void LogVolume(string label)
    {
        try
        {
            MassProperty mp = (MassProperty)swDoc.Extension.CreateMassProperty();
            Log(String.Format("{0} volume={1:F9}", label, mp.Volume));
        }
        catch
        {
        }
    }

    static void SavePart(string path)
    {
        try
        {
            if (File.Exists(path)) File.Delete(path);
        }
        catch
        {
        }

        try { swDoc.SaveAs3(path, (int)swSaveAsVersion_e.swSaveAsCurrentVersion, (int)swSaveAsOptions_e.swSaveAsOptions_Silent); }
        catch { }

        if (!File.Exists(path))
        {
            try { swDoc.SaveAs(path); }
            catch { }
        }
        if (!File.Exists(path)) Fail("save failed " + path);
        Log("saved " + path);
    }

    static void CaptureViews()
    {
        string dir = Path.Combine(outputDir, "views");
        Directory.CreateDirectory(dir);
        CaptureView("*Front", 1, Path.Combine(dir, "front.jpg"));
        CaptureView("*Right", 4, Path.Combine(dir, "right.jpg"));
        CaptureView("*Isometric", 7, Path.Combine(dir, "iso.jpg"));
    }

    static void CaptureView(string name, int id, string path)
    {
        try { if (File.Exists(path)) File.Delete(path); } catch { }
        try { swDoc.ShowNamedView2(name, id); } catch { }
        try { swDoc.ViewZoomtofit2(); } catch { }
        try { swDoc.SaveAs(path); } catch { }
        if (File.Exists(path)) Log("capture " + path);
    }

    static void SelectStandardPlane(StandardPlane plane)
    {
        swDoc.ClearSelection2(true);
        string[] names = plane == StandardPlane.Front
            ? new[] { "Front Plane", "前视基准面" }
            : plane == StandardPlane.Top
                ? new[] { "Top Plane", "上视基准面" }
                : new[] { "Right Plane", "右视基准面" };

        foreach (string name in names)
        {
            bool ok = swDoc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, false, 0, null, 0);
            if (ok)
            {
                Log("selected " + plane + " plane by name: " + name);
                return;
            }
        }

        Feature feat = (Feature)swDoc.FirstFeature();
        int index = 0;
        while (feat != null)
        {
            string type = "";
            try { type = feat.GetTypeName2(); } catch { }
            if (type == "RefPlane")
            {
                if (index == (int)plane)
                {
                    swDoc.ClearSelection2(true);
                    if (feat.Select2(false, 0))
                    {
                        Log("selected " + plane + " plane by fallback index " + index + ": " + feat.Name);
                        return;
                    }
                }
                index++;
            }
            feat = (Feature)feat.GetNextFeature();
        }

        Fail("cannot select standard plane " + plane);
    }

    static void CloseOwnedDoc()
    {
        if (keepOpen || swApp == null || String.IsNullOrEmpty(createdDocTitle)) return;
        try
        {
            swApp.CloseDoc(createdDocTitle);
            Log("closed generated document " + createdDocTitle);
        }
        catch
        {
        }
    }

    static void Log(string message)
    {
        Console.WriteLine(message);
    }

    static void Fail(string message)
    {
        throw new Exception(message);
    }
}
