using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SWAutomation
{
    class Program
    {
        // 遍历实体面，返回 X 坐标最小的面（后端面）
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

        // 遍历实体面，返回 Y 坐标最大的面（顶面）
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

        // 选中面（通过 Entity.Select4）
        static void SelectFace(object faceObj)
        {
            Face2 face = (Face2)faceObj;
            Entity ent = (Entity)face;
            ent.Select4(false, null);
        }

        static void Main(string[] args)
        {
            string logPath = @"C:\Users\22374\Desktop\湛江北海\学习课程\sw\swkuskills\log.txt";
            System.IO.StreamWriter swLog = new System.IO.StreamWriter(logPath, false, System.Text.Encoding.UTF8);
            swLog.AutoFlush = true;
            Console.SetOut(swLog);
            Console.SetError(swLog);

            Console.WriteLine("=== 开始全自动构建叉形接头 ===");

            SldWorks swApp = null;
            ModelDoc2 swDoc = null;

            try
            {
                // 创建 SW 实例
                Type swType = Type.GetTypeFromProgID("SldWorks.Application");
                swApp = (SldWorks)Activator.CreateInstance(swType);
                if (swApp == null) { Console.WriteLine("✗ 无法创建 SW 实例"); swLog.Close(); return; }
                swApp.Visible = true;
                Console.WriteLine("✓ SW 实例创建成功");

                // 新建零件
                string partTemplate = swApp.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
                if (string.IsNullOrEmpty(partTemplate)) partTemplate = @"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\零件.prtdot";
                swApp.NewDocument(partTemplate, 0, 0, 0);
                swDoc = (ModelDoc2)swApp.ActiveDoc;
                if (swDoc == null) { Console.WriteLine("✗ 新建零件失败"); swLog.Close(); return; }
                Console.WriteLine("✓ 新建零件成功");

                // 选前视基准面
                bool planeOK = swDoc.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, false, 0, null, 0);
                if (!planeOK) planeOK = swDoc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0);
                if (!planeOK) { Console.WriteLine("✗ 选前视基准面失败"); swLog.Close(); return; }
                Console.WriteLine("✓ 前视基准面选中");

                // =================================================================
                // 步骤1：右侧叉部 90x50mm，拉伸 50mm
                // =================================================================
                swDoc.SketchManager.InsertSketch(true);
                swDoc.SketchManager.CreateCornerRectangle(0, 0, 0, 0.090, 0.050, 0);
                swDoc.SketchManager.InsertSketch(true);

                // FeatureExtrusion2 23参数（逐字抄 Stage2_Test.cs）
                Feature feat1 = swDoc.FeatureManager.FeatureExtrusion2(
                    false, false, false,
                    (int)swEndConditions_e.swEndCondBlind, (int)swEndConditions_e.swEndCondBlind,
                    0.050, 0.050,
                    false, false, false, false, 0.0, 0.0,
                    false, false, false, false,
                    false, false, false,
                    0, 0.0, false
                );
                int before1 = swDoc.GetFeatureCount();
                swDoc.ForceRebuild3(false);
                int after1 = swDoc.GetFeatureCount();
                if (feat1 == null && after1 <= before1) { Console.WriteLine("✗ 步骤1 失败"); swLog.Close(); return; }
                Console.WriteLine("✓ 步骤1：叉部基体 90x50x50mm 完成");

                // =================================================================
                // 步骤2：左侧柄部 70x50mm，拉伸 25mm（居中）
                // =================================================================
                // 遍历选后端面（X 最小）
                swDoc.ClearSelection2(true);
                object backFace = FindFaceByMinX(swDoc);
                if (backFace == null) { Console.WriteLine("✗ 找不到后端面"); swLog.Close(); return; }
                SelectFace(backFace);
                Console.WriteLine("✓ 后端面选中（遍历法）");

                swDoc.SketchManager.InsertSketch(true);
                // 柄部往 X 负方向延伸 70mm，Z 居中 0.0125~0.0375
                swDoc.SketchManager.CreateCornerRectangle(0, 0.050, 0.0125, -0.070, 0, 0.0375);
                swDoc.SketchManager.InsertSketch(true);

                Feature feat2 = swDoc.FeatureManager.FeatureExtrusion2(
                    false, false, false,
                    (int)swEndConditions_e.swEndCondBlind, (int)swEndConditions_e.swEndCondBlind,
                    0.025, 0.025,
                    false, false, false, false, 0.0, 0.0,
                    false, false, false, false,
                    false, false, false,
                    0, 0.0, false
                );
                int before2 = swDoc.GetFeatureCount();
                swDoc.ForceRebuild3(false);
                int after2 = swDoc.GetFeatureCount();
                if (feat2 == null && after2 <= before2) { Console.WriteLine("✗ 步骤2 失败"); swLog.Close(); return; }
                Console.WriteLine("✓ 步骤2：柄部 70x50x25mm 完成");

                // =================================================================
                // 步骤3：柄部末端 R25 半圆弧切除
                // =================================================================
                swDoc.ClearSelection2(true);
                object endFace = FindFaceByMinX(swDoc);
                if (endFace == null) { Console.WriteLine("✗ 找不到柄部端面"); swLog.Close(); return; }
                SelectFace(endFace);
                Console.WriteLine("✓ 柄部端面选中（遍历法）");

                swDoc.SketchManager.InsertSketch(true);
                // 半圆弧：圆心(0.025,0.025)，起点(0.025,0.050)，终点(0.025,0)，逆时针
                swDoc.SketchManager.CreateArc(0.025, 0.025, 0, 0.025, 0.050, 0, 0.025, 0, 0, 1);
                swDoc.SketchManager.InsertSketch(true);

                // FeatureCut4 27参数（逐字抄 Stage2_Test.cs）
                Feature cut1 = swDoc.FeatureManager.FeatureCut4(
                    false, false, false,
                    (int)swEndConditions_e.swEndCondThroughAll, (int)swEndConditions_e.swEndCondThroughAll,
                    0.0, 0.0,
                    false, false, false, false, 0.0, 0.0,
                    false, false, false, false,
                    false, false, false,
                    false, false, false,
                    0, 0.0, false, false
                );
                int before3 = swDoc.GetFeatureCount();
                swDoc.ForceRebuild3(false);
                int after3 = swDoc.GetFeatureCount();
                if (cut1 == null && after3 <= before3) { Console.WriteLine("✗ 步骤3 失败"); swLog.Close(); return; }
                Console.WriteLine("✓ 步骤3：柄部 R25 半圆弧完成");

                // =================================================================
                // 步骤4：叉部 U 形槽 75x25mm
                // =================================================================
                swDoc.ClearSelection2(true);
                object topFace = FindFaceByMaxY(swDoc);
                if (topFace == null) { Console.WriteLine("✗ 找不到顶面"); swLog.Close(); return; }
                SelectFace(topFace);
                Console.WriteLine("✓ 叉部顶面选中（遍历法）");

                swDoc.SketchManager.InsertSketch(true);
                // U 形槽：X 0.090~0.015，Z 0.0125~0.0375
                swDoc.SketchManager.CreateCornerRectangle(0.090, 0, 0.0125, 0.015, -0.050, 0.0375);
                swDoc.SketchManager.InsertSketch(true);

                Feature cut2 = swDoc.FeatureManager.FeatureCut4(
                    false, false, false,
                    (int)swEndConditions_e.swEndCondThroughAll, (int)swEndConditions_e.swEndCondThroughAll,
                    0.0, 0.0,
                    false, false, false, false, 0.0, 0.0,
                    false, false, false, false,
                    false, false, false,
                    false, false, false,
                    0, 0.0, false, false
                );
                int before4 = swDoc.GetFeatureCount();
                swDoc.ForceRebuild3(false);
                int after4 = swDoc.GetFeatureCount();
                if (cut2 == null && after4 <= before4) { Console.WriteLine("✗ 步骤4 失败"); swLog.Close(); return; }
                Console.WriteLine("✓ 步骤4：U 形槽 75x25mm 完成");

                // =================================================================
                // 强制重建
                // =================================================================
                swDoc.ForceRebuild3(false);
                Console.WriteLine("=== 全部完成！叉形接头已生成 ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("✗ 异常: {0}", ex.Message));
            }
            finally
            {
                swLog.Close();
            }
        }
    }
}
