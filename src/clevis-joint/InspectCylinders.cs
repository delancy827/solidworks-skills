using System;
using System.IO;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

class InspectCylinders
{
    static void Main()
    {
        string dir = @"C:\Users\<user>\Desktop\湛江北海\学习课程\sw\冲压作业";
        SldWorks sw;
        try { sw = (SldWorks)Marshal.GetActiveObject("SldWorks.Application"); }
        catch
        {
            Type t = Type.GetTypeFromProgID("SldWorks.Application");
            sw = (SldWorks)Activator.CreateInstance(t);
        }
        sw.Visible = true;

        foreach (string name in new[] { "零件1.SLDPRT", "零件2.SLDPRT", "零件3.SLDPRT" })
        {
            string path = Path.Combine(dir, name);
            int errors = 0, warnings = 0;
            ModelDoc2 doc = (ModelDoc2)sw.OpenDoc6(path, (int)swDocumentTypes_e.swDocPART,
                (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref errors, ref warnings);
            if (doc == null)
            {
                Console.WriteLine("OPEN FAIL " + path + " errors=" + errors);
                continue;
            }

            Console.WriteLine("== " + name + " ==");
            PartDoc part = (PartDoc)doc;
            object[] bodies = (object[])part.GetBodies2((int)swBodyType_e.swSolidBody, true);
            if (bodies != null)
            {
                foreach (Body2 body in bodies)
                {
                    object[] faces = (object[])body.GetFaces();
                    if (faces == null) continue;
                    foreach (Face2 face in faces)
                    {
                        Surface surf = (Surface)face.GetSurface();
                        if (surf == null || !surf.IsCylinder()) continue;
                        double[] p = (double[])surf.CylinderParams;
                        Console.WriteLine(String.Format(
                            "cyl r={0:F4} base=({1:F4},{2:F4},{3:F4}) axis=({4:F4},{5:F4},{6:F4})",
                            p[6], p[0], p[1], p[2], p[3], p[4], p[5]));
                    }
                }
            }

            sw.CloseDoc(doc.GetTitle());
        }
    }
}
