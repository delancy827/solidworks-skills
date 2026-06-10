using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class CourseProjectAssembly
{
    // TODO: Update WorkDir to your working directory before running.
    static readonly string WorkDir = @"C:\temp\sw_course";
    static readonly string ShotDir = Path.Combine(WorkDir, "建模过程截图");
    static readonly string Part1Source = @"C:\temp\sw_course\vertical_clevis_support.SLDPRT";
    static readonly string Part1Path = Path.Combine(WorkDir, "零件1.SLDPRT");
    static readonly string Part2Path = Path.Combine(WorkDir, "零件2.SLDPRT");
    static readonly string Part3Path = Path.Combine(WorkDir, "零件3.SLDPRT");
    static readonly string AssemblyPath = Path.Combine(WorkDir, "课程设计装配体.SLDASM");

    static SldWorks swApp;
    static ModelDoc2 activeDoc;

    [STAThread]
    static int Main()
    {
        try
        {
            Directory.CreateDirectory(WorkDir);
            Directory.CreateDirectory(ShotDir);
            CopyPart1();
            Connect();

            CapturePart(Part1Path, "01_零件1_圆底双耳支座.jpg", "*Isometric", 7);
            CapturePart(Part2Path, "02_零件2_叉形连杆.jpg", "*Isometric", 7);
            CapturePart(Part3Path, "03_零件3_销轴.jpg", "*Isometric", 7);
            BuildAssembly();

            Log("DONE " + AssemblyPath);
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
            try
            {
                if (activeDoc != null && swApp != null) swApp.CloseDoc(activeDoc.GetTitle());
            }
            catch { }
        }
    }

    static void CopyPart1()
    {
        if (!File.Exists(Part1Source)) Fail("source part1 not found: " + Part1Source);
        File.Copy(Part1Source, Part1Path, true);
        Log("copied part1 to " + Part1Path);
    }

    static void Connect()
    {
        try
        {
            swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application");
            Log("connected active SolidWorks");
        }
        catch
        {
            if (Process.GetProcessesByName("SLDWORKS").Length > 0)
            {
                Fail("SLDWORKS is running but COM is unavailable; restart SolidWorks and rerun.");
            }
            Type t = Type.GetTypeFromProgID("SldWorks.Application");
            if (t == null) Fail("SolidWorks COM ProgID is not registered.");
            swApp = (SldWorks)Activator.CreateInstance(t);
            Log("started SolidWorks");
        }

        swApp.Visible = true;
        swApp.UserControl = true;
    }

    static void CapturePart(string path, string fileName, string viewName, int viewId)
    {
        if (!File.Exists(path)) Fail("part not found: " + path);
        int errors = 0, warnings = 0;
        ModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(
            path,
            (int)swDocumentTypes_e.swDocPART,
            (int)swOpenDocOptions_e.swOpenDocOptions_Silent,
            "",
            ref errors,
            ref warnings);
        if (doc == null) Fail("cannot open part: " + path + " errors=" + errors);
        activeDoc = doc;
        CaptureCurrentDoc(fileName, viewName, viewId);
        swApp.CloseDoc(doc.GetTitle());
        activeDoc = null;
    }

    static void BuildAssembly()
    {
        string template = GetAssemblyTemplate();
        ModelDoc2 asmModel = (ModelDoc2)swApp.NewDocument(template, 0, 0, 0);
        if (asmModel == null) asmModel = (ModelDoc2)swApp.ActiveDoc;
        if (asmModel == null) Fail("new assembly failed");
        activeDoc = asmModel;

        AssemblyDoc asm = (AssemblyDoc)asmModel;
        SaveDoc(asmModel, AssemblyPath);

        Component2 support = AddComponent(asm, Part1Path, 0.0, 0.0, 0.0, "support");
        TryFixComponent(asmModel, support);
        LogBox("support", support);
        double[] supportHoleCenter = TransformPoint(support, 0.0, 0.115, 0.0);
        Log(String.Format("support actual hole center=({0:F4},{1:F4},{2:F4})",
            supportHoleCenter[0], supportHoleCenter[1], supportHoleCenter[2]));
        CaptureCurrentDoc("04_装配_插入圆底双耳支座.jpg", "*Isometric", 7);

        Component2 link = AddComponent(asm, Part2Path, 0.0, 0.0, 0.0, "clevis link");
        SetLinkTransform(link, 135.0, supportHoleCenter);
        asmModel.ForceRebuild3(false);
        LogBox("link", link);
        LogAssemblyCenters(support, link, null);
        CaptureCurrentDoc("05_装配_连杆绕销轴成135度.jpg", "*Isometric", 7);

        Component2 pin = AddComponent(asm, Part3Path, 0.0, 0.0, 0.0, "pin");
        SetPinTransform(pin, supportHoleCenter);
        asmModel.ForceRebuild3(false);
        LogBox("pin", pin);
        LogAssemblyCenters(support, link, pin);
        double[] forkHoleCenter = TransformPoint(link, 0.075, 0.025, 0.025);
        Log(String.Format("link fork actual hole center=({0:F4},{1:F4},{2:F4})",
            forkHoleCenter[0], forkHoleCenter[1], forkHoleCenter[2]));

        Component2 secondLink = AddComponent(asm, Part2Path, 0.0, 0.0, 0.0, "second clevis link");
        SetLinkTransform(secondLink, 180.0, forkHoleCenter);
        asmModel.ForceRebuild3(false);
        LogBox("second link", secondLink);

        Component2 headPin = AddComponent(asm, Part3Path, 0.0, 0.0, 0.0, "link-to-link pin");
        SetPinTransform(headPin, forkHoleCenter);
        asmModel.ForceRebuild3(false);
        LogBox("link-to-link pin", headPin);
        CaptureCurrentDoc("06_装配_插入销轴.jpg", "*Isometric", 7);
        CaptureCurrentDoc("07_装配_视图A.jpg", "*Top", 5);
        CaptureCurrentDoc("08_装配_视图B.jpg", "*Front", 1);

        SaveDoc(asmModel, AssemblyPath);
        swApp.CloseDoc(asmModel.GetTitle());
        activeDoc = null;
    }

    static Component2 AddComponent(AssemblyDoc asm, string path, double x, double y, double z, string label)
    {
        EnsurePartLoaded(path);
        ActivateAssembly();
        Component2 comp = asm.AddComponent5(path, 0, "", false, "", x, y, z);
        if (comp == null) Fail("cannot add " + label + ": " + path);
        Log("added " + label + ": " + comp.Name2);
        return comp;
    }

    static void EnsurePartLoaded(string path)
    {
        int errors = 0, warnings = 0;
        ModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(
            path,
            (int)swDocumentTypes_e.swDocPART,
            (int)swOpenDocOptions_e.swOpenDocOptions_Silent,
            "",
            ref errors,
            ref warnings);
        if (doc == null) Fail("cannot load component part: " + path + " errors=" + errors);
    }

    static void ActivateAssembly()
    {
        if (activeDoc == null) Fail("assembly document is not active");
        int errors = 0;
        swApp.ActivateDoc3(activeDoc.GetTitle(), false, (int)swRebuildOnActivation_e.swUserDecision, ref errors);
        if (errors != 0) Log("assembly activation warning/errors=" + errors);
    }

    static void TryFixComponent(ModelDoc2 asmModel, Component2 comp)
    {
        try
        {
            asmModel.ClearSelection2(true);
            comp.Select4(false, null, false);
            ((AssemblyDoc)asmModel).FixComponent();
            asmModel.ClearSelection2(true);
        }
        catch { }
    }

    static void SetLinkTransform(Component2 comp, double angleDeg, double[] target)
    {
        // Part2 left round hole center from its construction sketch.
        double localHoleX = -0.045;
        double localHoleY = 0.025;
        double localHoleZ = 0.025;
        double targetX = target[0];
        double targetY = target[1];
        double targetZ = target[2];

        double angle = angleDeg * Math.PI / 180.0;
        double c = Math.Cos(angle);
        double s = Math.Sin(angle);
        double rotatedX = localHoleX * c - localHoleY * s;
        double rotatedY = localHoleX * s + localHoleY * c;
        double tx = targetX - rotatedX;
        double ty = targetY - rotatedY;
        double tz = targetZ - localHoleZ;
        comp.Transform2 = CreateZTransform(angleDeg, tx, ty, tz);
        Log(String.Format("link transform angle={0} tx={1:F4} ty={2:F4} tz={3:F4}", angleDeg, tx, ty, tz));
    }

    static void SetPinTransform(Component2 comp, double[] target)
    {
        // Pin axis follows the support pin-hole axis. The 50 mm shaft is centered
        // through the ear pack as far as the supplied part length allows.
        comp.Transform2 = CreateZTransform(0.0, target[0], target[1], target[2] - 0.025);
        Log("pin transform centered on support hole");
    }

    static void LogBox(string label, Component2 comp)
    {
        try
        {
            double[] box = (double[])comp.GetBox(false, false);
            Log(String.Format(
                "{0} box x[{1:F4},{2:F4}] y[{3:F4},{4:F4}] z[{5:F4},{6:F4}]",
                label, box[0], box[3], box[1], box[4], box[2], box[5]));
        }
        catch (Exception ex)
        {
            Log(label + " box unavailable: " + ex.Message);
        }
    }

    static void LogAssemblyCenters(Component2 support, Component2 link, Component2 pin)
    {
        double[] supportCenter = TransformPoint(support, 0.0, 0.115, 0.0);
        double[] linkCenter = TransformPoint(link, -0.045, 0.025, 0.025);
        Log(String.Format(
            "center check support=({0:F4},{1:F4},{2:F4}) link=({3:F4},{4:F4},{5:F4}) delta={6:F6}",
            supportCenter[0], supportCenter[1], supportCenter[2],
            linkCenter[0], linkCenter[1], linkCenter[2],
            Distance(supportCenter, linkCenter)));
        if (pin != null)
        {
            double[] pinCenter = TransformPoint(pin, 0.0, 0.0, 0.025);
            Log(String.Format(
                "center check pin=({0:F4},{1:F4},{2:F4}) delta={3:F6}",
                pinCenter[0], pinCenter[1], pinCenter[2],
                Distance(supportCenter, pinCenter)));
        }
    }

    static double[] TransformPoint(Component2 comp, double x, double y, double z)
    {
        MathPoint pt = (MathPoint)((MathUtility)swApp.GetMathUtility()).CreatePoint(new double[] { x, y, z });
        MathTransform tr = comp.Transform2;
        MathPoint outPt = (MathPoint)pt.MultiplyTransform(tr);
        return (double[])outPt.ArrayData;
    }

    static double Distance(double[] a, double[] b)
    {
        double dx = a[0] - b[0];
        double dy = a[1] - b[1];
        double dz = a[2] - b[2];
        return Math.Sqrt(dx * dx + dy * dy + dz * dz);
    }

    static MathTransform CreateZTransform(double angleDeg, double tx, double ty, double tz)
    {
        double a = angleDeg * Math.PI / 180.0;
        double c = Math.Cos(a);
        double s = Math.Sin(a);
        double[] data = new double[]
        {
            c, s, 0.0,
            -s, c, 0.0,
            0.0, 0.0, 1.0,
            tx, ty, tz,
            1.0, 0.0, 0.0, 0.0
        };
        MathUtility mu = (MathUtility)swApp.GetMathUtility();
        return (MathTransform)mu.CreateTransform(data);
    }

    static void CaptureCurrentDoc(string fileName, string viewName, int viewId)
    {
        ModelDoc2 doc = (ModelDoc2)swApp.ActiveDoc;
        if (doc == null) Fail("no active doc for capture " + fileName);
        try { doc.ClearSelection2(true); } catch { }
        try { doc.ShowNamedView2(viewName, viewId); } catch { }
        try { doc.ViewZoomtofit2(); } catch { }
        Thread.Sleep(500);
        string path = Path.Combine(ShotDir, fileName);
        try { if (File.Exists(path)) File.Delete(path); } catch { }
        int errors = 0, warnings = 0;
        bool ok = doc.Extension.SaveAs(
            path,
            (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
            (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
            null,
            ref errors,
            ref warnings);
        if (!ok || !File.Exists(path)) Fail("capture failed " + fileName + " errors=" + errors);
        Log("capture " + path);
    }

    static void SaveDoc(ModelDoc2 doc, string path)
    {
        try { if (File.Exists(path)) File.Delete(path); } catch { }
        int result = doc.SaveAs3(path, (int)swSaveAsVersion_e.swSaveAsCurrentVersion, (int)swSaveAsOptions_e.swSaveAsOptions_Silent);
        if (!File.Exists(path))
        {
            try { doc.SaveAs(path); } catch { }
        }
        if (!File.Exists(path)) Fail("save failed " + path + " result=" + result);
        Log("saved " + path);
    }

    static string GetAssemblyTemplate()
    {
        string[] candidates = new string[]
        {
            @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_assembly.asmdot",
            @"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_assembly.asmdot",
            @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Assembly.asmdot",
            @"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\Assembly.asmdot"
        };
        foreach (string candidate in candidates)
        {
            if (File.Exists(candidate)) return candidate;
        }
        try
        {
            string value = swApp.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplateAssembly);
            if (!String.IsNullOrWhiteSpace(value) && File.Exists(value)) return value;
        }
        catch { }
        Fail("assembly template not found");
        return "";
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
