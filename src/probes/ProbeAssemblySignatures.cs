using System;
using System.Reflection;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace ProbeAssembly
{
    class Program
    {
        static void Main()
        {
            SldWorks swApp = (SldWorks)Activator.CreateInstance(
                Type.GetTypeFromProgID("SldWorks.Application"));
            swApp.Visible = true;
            Console.WriteLine("SW v" + swApp.RevisionNumber());

            // New assembly
            swApp.NewDocument(
                @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_assembly.asmdot",
                0, 0, 0);
            System.Threading.Thread.Sleep(1000);
            ModelDoc2 doc = (ModelDoc2)swApp.ActiveDoc;
            Console.WriteLine("Doc type: " + doc.GetType());

            // Check IAssemblyDoc (the COM interface, not the CoClass)
            Console.WriteLine("\n=== typeof(IAssemblyDoc) methods ===");
            Type iassyType = typeof(IAssemblyDoc);
            int count = 0;
            foreach (MethodInfo mi in iassyType.GetMethods())
            {
                if (mi.Name.Contains("Add"))
                {
                    ParameterInfo[] p = mi.GetParameters();
                    Console.Write("  " + mi.Name + "(" + p.Length + "): ");
                    for (int i = 0; i < p.Length; i++)
                        Console.Write(p[i].ParameterType.Name + " ");
                    Console.WriteLine();
                    count++;
                }
            }
            if (count == 0)
            {
                Console.WriteLine("  No 'Add' methods found on AssemblyDoc type!");
                Console.WriteLine("  Total methods on AssemblyDoc: " + iassyType.GetMethods().Length);
                // List first 15 unconditionally
                Console.WriteLine("  First 15 methods:");
                foreach (MethodInfo mi in iassyType.GetMethods())
                {
                    if (count++ > 18) break;
                    Console.WriteLine("    " + mi.Name);
                }
            }

            swApp.CloseDoc(doc.GetTitle());
        }
    }
}
