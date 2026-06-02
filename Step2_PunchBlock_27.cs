// Step2_BuildPunch.cs - 凸模建模（U形，草图闭合修复版）
// 编译：
// "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
//   /reference:"E:\sw2024\SOLIDWORKS\api\redist\SolidWorks.Interop.sldworks.dll"
//   /reference:"E:\sw2024\SOLIDWORKS\api\redist\SolidWorks.Interop.swconst.dll"
//   /out:Step2_BuildPunch.exe Step2_BuildPunch.cs

using System;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace StampingDie
{
    class Step2_BuildPunch
    {
        static void Fail(string msg)
        {
            Console.WriteLine("FAIL: " + msg);
            System.Environment.Exit(1);
        }

        static double Mm(double v) { return v / 1000.0; }  // mm→m

        static void Main()
        {
            Console.WriteLine("=== Step2: 凸模建模 ===\n");

            // 连接SW
            SldWorks swApp = (SldWorks)Activator.CreateInstance(
                Type.GetTypeFromProgID("SldWorks.Application"));
            swApp.Visible = true;
            Console.WriteLine("[1/5] SW已连接");

            // 清理残留文档
            while (swApp.GetDocumentCount() > 0)
            {
                ModelDoc2 tmp = (ModelDoc2)swApp.ActiveDoc;
                if (tmp != null) swApp.CloseDoc(tmp.GetTitle());
                else break;
            }
            Console.WriteLine("[2/5] 已清理残留文档");

            // 新建零件
            string tpl = swApp.GetUserPreferenceStringValue(
                (int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
            if (string.IsNullOrEmpty(tpl))
                tpl = @"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\gb_part.prtdot";
            swApp.NewDocument(tpl, 0, 0, 0);
            System.Threading.Thread.Sleep(1000);

            ModelDoc2 swDoc = (ModelDoc2)swApp.ActiveDoc;
            if (swDoc == null) Fail("新建零件失败");
            Console.WriteLine("[3/5] 零件已创建");

            // ===== 选择前视基准面 =====
            bool ok = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!ok) ok = swDoc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
            if (!ok) Fail("选择前视基准面失败");
            Console.WriteLine("  前视基准面已选中");

            // ===== 绘制U形凸模草图 =====
            // 策略：先画外轮廓闭合矩形，再画内轮廓（切除后得到U形）
            // 简化方案：直接画U形轮廓（左边+顶部+右边），底部开口
            // 注意：SW拉伸要求闭合轮廓，U形不闭合 → 用"矩形+切除"得到U形

            // 方案：画一个实心块，后续再切出U形槽
            // 凸模主体尺寸：宽53mm × 高30mm × 厚20mm
            double W = Mm(53);   // 宽度
            double H = Mm(30);   // 高度
            double T = Mm(20);   // 厚度（拉伸深度）

            // 画矩形轮廓（闭合）
            swDoc.SketchManager.InsertSketch(true);

            // 矩形4个角点（逆时针，确保闭合）
            // 左下(-W/2, 0) → 右下(W/2, 0) → 右上(W/2, H) → 左上(-W/2, H) → 回左下
            swDoc.SketchManager.CreateLine(-W / 2, 0, 0, W / 2, 0, 0);
            swDoc.SketchManager.CreateLine(W / 2, 0, 0, W / 2, H, 0);
            swDoc.SketchManager.CreateLine(W / 2, H, 0, -W / 2, H, 0);
            swDoc.SketchManager.CreateLine(-W / 2, H, 0, -W / 2, 0, 0);

            swDoc.SketchManager.InsertSketch(true);
            Console.WriteLine("  草图绘制完成：53×30mm矩形");

            // ===== 拉伸凸模主体 =====
            int before = swDoc.GetFeatureCount();
            Feature feat = swDoc.FeatureManager.FeatureExtrusion2(
                false, false, false,
                (int)swEndConditions_e.swEndCondBlind,
                (int)swEndConditions_e.swEndCondBlind,
                T, T,
                false, false, false, false,
                0.0, 0.0,
                false, false, false, false,
                true,   // Merge=true（参数18）
                false, false,
                0, 0.0, false
            );
            swDoc.ForceRebuild3(false);
            int after = swDoc.GetFeatureCount();
            if (after <= before) Fail(string.Format("凸模拉伸失败: {0}->{1}", before, after));
            Console.WriteLine(string.Format("  ✓ 凸模拉伸成功: {0} ({1}->{2})", feat.Name, before, after));

            // ===== 保存 =====
            string saveDir = @"C:\Users\22374\Desktop\湛江北海\学习课程\sw\冲压课设1\SW_CSharp\Model";
            System.IO.Directory.CreateDirectory(saveDir);
            string savePath = saveDir + @"\凸模_27号.SLDPRT";
            int saveResult = swDoc.SaveAs3(savePath, 1, 2);
            if (saveResult != 1)
            {
                Console.WriteLine("  SaveAs3失败(code=" + saveResult + ")，降级SaveAs...");
                swDoc.SaveAs(savePath);
            }
            Console.WriteLine("  ✓ 已保存: " + savePath);

            Console.WriteLine("\n=== Step2 完成 ===");
            Console.WriteLine("凸模主体已创建（实心块），U形槽将在Step3切除。");
        }
    }
}
