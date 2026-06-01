using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SWAutomation
{
    class Program
    {
        static object FindFaceByMinX(ModelDoc2 swDoc)
        {
            PartDoc partDoc = (PartDoc)swDoc;
            object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
            if (bodies == null || bodies.Length == 0) return null;
            Body2 body = (Body2)bodies[0];
            object[] faces = (object[])body.GetFaces();
            if (faces == null || faces.Length == 0) return null;
            Face2 bestFace = null;
            double minX = double.MaxValue;
            foreach (Face2 face in faces)
            {
                double[] box = (double[])face.GetBox();
                if (box[0] < minX) { minX = box[0]; bestFace = face; }
            }
            return bestFace;
        }
        static object FindFaceByMaxY(ModelDoc2 swDoc)
        {
            PartDoc partDoc = (PartDoc)swDoc;
            object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, false);
            if (bodies == null || bodies.Length == 0) return null;
            Body2 body = (Body2)bodies[0];
            object[] faces = (object[])body.GetFaces();
            if (faces == null || faces.Length == 0) return null;
            Face2 bestFace = null;
            double maxY = double.MinValue;
            foreach (Face2 face in faces)
            {
                double[] box = (double[])face.GetBox();
                if (box[4] > maxY) { maxY = box[4]; bestFace = face; }
            }
            return bestFace;
        }
        static void SelectFace(object faceObj)
        {
            Face2 face = (Face2)faceObj;
            Entity ent = (Entity)face;
            ent.Select4(false, null);
        }
        static void Main(string[] args)
        {
            string logPath = @".\log.txt";
            System.IO.StreamWriter swLog = new System.IO.StreamWriter(logPath, false, System.Text.Encoding.UTF8);
            swLog.AutoFlush = true;
            Console.SetOut(swLog);
            Console.SetError(swLog);
            Console.WriteLine("=== 叉形接头(闭合轮廓版) ===");
            SldWorks swApp = null;
            ModelDoc2 swDoc = null;
            try
            {
                Type swType = Type.GetTypeFromProgID("SldWorks.Application");
                swApp = (SldWorks)Activator.CreateInstance(swType);
                if (swApp == null) { Console.WriteLine("FAIL: SW实例"); swLog.Close(); return; }
                swApp.Visible = true;
                Console.WriteLine("OK: SW实例创建");
                string partTemplate = swApp.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
                if (string.IsNullOrEmpty(partTemplate)) partTemplate = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\零件.prtdot";
                swApp.NewDocument(partTemplate, 0, 0, 0);
                swDoc = (ModelDoc2)swApp.ActiveDoc;
                if (swDoc == null) { Console.WriteLine("FAIL: 新建零件"); swLog.Close(); return; }
                Console.WriteLine("OK: 新建零件");

                // 选前视基准面
                bool po = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
                if (!po) po = swDoc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
                if (!po) { Console.WriteLine("FAIL: 基准面"); swLog.Close(); return; }
                Console.WriteLine("OK: 基准面选中");

                // =============================================================
                // 步骤1: 叉部 90x50mm 双向拉伸50mm
                // =============================================================
                swDoc.SketchManager.InsertSketch(true);
                swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.090, 0.050, 0);
                swDoc.SketchManager.InsertSketch(true);
                Feature f1 = swDoc.FeatureManager.FeatureExtrusion2(
                    false, false, false, 0, 0, 0.050, 0.050, false, false, false, false, 0.0, 0.0,
                    false, false, false, false, false, false, false, 0, 0.0, false);
                swDoc.ForceRebuild3(false);
                if (f1 == null && swDoc.GetFeatureCount() <= 0) { Console.WriteLine("FAIL: 步骤1"); swLog.Close(); return; }
                Console.WriteLine("OK: 步骤1 叉部基体");

                // =============================================================
                // 步骤2: 柄部 70x50mm 拉伸25mm
                // =============================================================
                swDoc.ClearSelection2(true);
                object bf = FindFaceByMinX(swDoc);
                SelectFace(bf);
                swDoc.SketchManager.InsertSketch(true);
                swDoc.SketchManager.CreateCornerRectangle(0, 0.050, 0.0125, -0.070, 0, 0.0375);
                swDoc.SketchManager.InsertSketch(true);
                Feature f2 = swDoc.FeatureManager.FeatureExtrusion2(
                    false, false, false, 0, 0, 0.025, 0.025, false, false, false, false, 0.0, 0.0,
                    false, false, false, false, false, false, false, 0, 0.0, false);
                swDoc.ForceRebuild3(false);
                if (f2 == null && swDoc.GetFeatureCount() <= 0) { Console.WriteLine("FAIL: 步骤2"); swLog.Close(); return; }
                Console.WriteLine("OK: 步骤2 柄部");

                // =============================================================
                // 步骤3: 柄部末端 R25 圆头 + Φ18 通孔
                // 在端面上画闭合轮廓: 圆弧+3条直线=切除端部两角, 再加Φ18圆
                // 端面草图坐标: X=模型Y, Y=模型Z
                // 圆弧圆心(Y=-0.045, Z=0.025), R=0.025
                // 闭合轮廓: 弧(顶→底)+顶线(到左角)+右线(左角向下)+底线(回到弧底)
                // =============================================================
                swDoc.ClearSelection2(true);
                object ef = FindFaceByMinX(swDoc);
                SelectFace(ef);
                swDoc.SketchManager.InsertSketch(true);
                // 圆弧: 圆心(-0.045,0.025), 起点(-0.045,0.050), 终点(-0.045,0), CCW(1)
                swDoc.SketchManager.CreateArc(-0.045, 0.025, 0, -0.045, 0.050, 0, -0.045, 0, 0, 1);
                // 顶线: 弧起点 → 左上角
                swDoc.SketchManager.CreateLine(-0.045, 0.050, 0, -0.070, 0.050, 0);
                // 右边线: 左上角 → 左下角（沿手柄左端边界）
                swDoc.SketchManager.CreateLine(-0.070, 0.050, 0, -0.070, 0, 0);
                // 底线: 左下角 → 弧终点
                swDoc.SketchManager.CreateLine(-0.070, 0, 0, -0.045, 0, 0);
                // Φ18 通孔: 圆心(-0.045, 0.025), R=0.009
                swDoc.SketchManager.CreateCircleByRadius(-0.045, 0.025, 0, 0.009);
                swDoc.SketchManager.InsertSketch(true);

                Feature c1 = swDoc.FeatureManager.FeatureCut4(
                    false, false, false, 4, 4, 0.0, 0.0, false, false, false, false, 0.0, 0.0,
                    false, false, false, false, false, false, false, false, false, false, 0, 0.0, false, false);
                swDoc.ForceRebuild3(false);
                if (c1 == null && swDoc.GetFeatureCount() <= 0) { Console.WriteLine("FAIL: 步骤3"); swLog.Close(); return; }
                Console.WriteLine("OK: 步骤3 R25圆头+Φ18通孔");

                // =============================================================
                // 步骤4: U形槽 75x25mm
                // 顶面草图: X=模型X, Y=模型Z
                // =============================================================
                swDoc.ClearSelection2(true);
                object tf = FindFaceByMaxY(swDoc);
                SelectFace(tf);
                swDoc.SketchManager.InsertSketch(true);
                swDoc.SketchManager.CreateCornerRectangle(0.015, 0.0125, 0, 0.090, 0.0375, 0);
                swDoc.SketchManager.InsertSketch(true);
                Feature c2 = swDoc.FeatureManager.FeatureCut4(
                    false, false, false, 4, 4, 0.0, 0.0, false, false, false, false, 0.0, 0.0,
                    false, false, false, false, false, false, false, false, false, false, 0, 0.0, false, false);
                swDoc.ForceRebuild3(false);
                if (c2 == null && swDoc.GetFeatureCount() <= 0) { Console.WriteLine("FAIL: 步骤4(U形槽)"); swLog.Close(); return; }
                Console.WriteLine("OK: 步骤4 U形槽");

                // =============================================================
                // 步骤5: 双侧 Φ18 通孔
                // =============================================================
                swDoc.ClearSelection2(true);
                po = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
                if (!po) { Console.WriteLine("FAIL: 基准面(步骤5)"); swLog.Close(); return; }
                swDoc.SketchManager.InsertSketch(true);
                swDoc.SketchManager.CreateCircleByRadius(0.045, 0.025, 0, 0.009);
                swDoc.SketchManager.CreateCircleByRadius(0.078, 0.025, 0, 0.009);
                swDoc.SketchManager.InsertSketch(true);
                Feature c3 = swDoc.FeatureManager.FeatureCut4(
                    false, false, false, 4, 4, 0.0, 0.0, false, false, false, false, 0.0, 0.0,
                    false, false, false, false, false, false, false, false, false, false, 0, 0.0, false, false);
                swDoc.ForceRebuild3(false);
                if (c3 == null && swDoc.GetFeatureCount() <= 0) { Console.WriteLine("FAIL: 步骤5(通孔)"); swLog.Close(); return; }
                Console.WriteLine("OK: 步骤5 双侧Φ18通孔");

                swDoc.ForceRebuild3(false);
                Console.WriteLine("=== 全部完成！ ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("异常: {0}", ex.Message));
            }
            finally { swLog.Close(); }
        }
    }
}
