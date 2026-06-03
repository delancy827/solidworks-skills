"""
SolidWorks 建模操作封装

每个操作都内嵌 W-A-R 验证，通过 AntiHallucinationGuard 守卫。
- FeatureExtrusion2: 23参数签名 (SW 2024)
- SelectByID2: 第8参数必须 VARIANT(VT_DISPATCH, None) 包装
- FeatureCut 不可用 → 用 FeatureExtrusion2 反向拉伸代替
"""
import pythoncom
import win32com.client

from config.settings import REBUILD_WAIT_SECONDS
from core.sw_connection import safe_call
from core.war_validator import WARValidator
from core.anti_hallucination import AntiHallucinationGuard

import time


# 中英文基准面映射
PLANE_NAMES = {
    "front":  ["前视基准面", "Front Plane"],
    "top":    ["上视基准面", "Top Plane"],
    "right":  ["右视基准面", "Right Plane"],
    "back":   ["后视基准面", "Back Plane"],
    "left":   ["左视基准面", "Left Plane"],
    "bottom": ["仰视基准面", "Bottom Plane"],
}


class SWOperations:
    """
    SW 建模操作封装。

    所有操作通过此类的实例方法执行，自动集成 W-A-R 验证和反幻觉守卫。
    """

    def __init__(self, connection_manager, war_validator=None, guard=None):
        self.conn = connection_manager
        self.war = war_validator or WARValidator(connection_manager)
        self.guard = guard or AntiHallucinationGuard()

    # ─── 基准面与草图 ───

    def select_plane(self, plane_name: str) -> dict:
        """
        选择基准面。
        支持中文名、英文名、简写（front/top/right）。
        SelectByID2 第8参数必须 VARIANT(VT_DISPATCH, None)。
        失败时回退到遍历特征树。
        """
        doc = self.conn.get_active_doc()
        doc.ClearSelection2(True)

        # 构建候选名称列表
        candidates = self._resolve_plane_name(plane_name)

        # 尝试 SelectByID2
        for name in candidates:
            for ctx in [
                win32com.client.VARIANT(pythoncom.VT_DISPATCH, None),
                None,
            ]:
                try:
                    ok = doc.Extension.SelectByID2(
                        name, "PLANE", 0, 0, 0, False, 0, ctx, 0
                    )
                    if ok:
                        return {"selected": True, "plane_name": name, "method": "SelectByID2"}
                except Exception:
                    continue

        # 回退：遍历特征树
        for name in candidates:
            try:
                feat = doc.FirstFeature
                if feat is None:
                    feat = doc.FirstFeature()
                while feat is not None:
                    fname = safe_call(feat, "Name", "")
                    if fname == name:
                        feat.Select2(False, 0)
                        return {"selected": True, "plane_name": name, "method": "traversal"}
                    feat = feat.GetNextFeature()
            except Exception:
                continue

        # 列出可用特征（调试用）
        available = self._list_features(doc, max_count=20)
        return {
            "selected": False,
            "plane_name": plane_name,
            "tried": candidates,
            "available_features": available,
        }

    def create_sketch(self, plane_name: str = "front") -> dict:
        """在指定基准面上创建草图"""
        # 先选择基准面
        sel_result = self.select_plane(plane_name)
        if not sel_result.get("selected"):
            return {"sketch_active": False, "error": f"无法选择基准面: {plane_name}"}

        doc = self.conn.get_active_doc()
        doc.SketchManager.InsertSketch(True)

        # 验证草图激活
        sk = doc.SketchManager.ActiveSketch
        if sk is None:
            return {"sketch_active": False, "error": "InsertSketch 后 ActiveSketch 为 None"}

        sk_name = safe_call(sk, "Name", "unknown")
        return {"sketch_active": True, "plane_name": sel_result["plane_name"], "sketch_name": sk_name}

    def close_sketch(self) -> dict:
        """关闭当前草图"""
        doc = self.conn.get_active_doc()

        # 记录草图实体数
        seg_count = 0
        try:
            sk = doc.SketchManager.ActiveSketch
            if sk is not None:
                seg_count = sk.GetSketchSegmentsCount()
                if callable(seg_count):
                    seg_count = seg_count()
        except Exception:
            pass

        doc.SketchManager.InsertSketch(True)

        # 验证草图已关闭
        active = doc.SketchManager.ActiveSketch
        return {
            "sketch_closed": active is None,
            "entity_count": seg_count,
        }

    # ─── 草图绘制 ───

    def draw_line(self, x1: float, y1: float, x2: float, y2: float) -> dict:
        """绘制直线（单位: 米）"""
        doc = self.conn.get_active_doc()
        doc.SketchManager.CreateLine(x1, y1, 0, x2, y2, 0)
        return {"entity_type": "line", "start": [x1, y1], "end": [x2, y2]}

    def draw_circle(self, cx: float, cy: float, radius: float) -> dict:
        """绘制圆（单位: 米）"""
        doc = self.conn.get_active_doc()
        doc.SketchManager.CreateCircle(cx, cy, 0, cx + radius, cy, 0)
        return {"entity_type": "circle", "center": [cx, cy], "radius": radius}

    def draw_rectangle(self, x1: float, y1: float, x2: float, y2: float) -> dict:
        """绘制矩形（单位: 米）"""
        doc = self.conn.get_active_doc()
        doc.SketchManager.CreateCornerRectangle(x1, y1, 0, x2, y2, 0)
        return {"entity_type": "rectangle", "corners": [[x1, y1], [x2, y2]]}

    def draw_arc(self, x1: float, y1: float, x2: float, y2: float,
                 x3: float, y3: float) -> dict:
        """绘制三点圆弧（单位: 米）"""
        doc = self.conn.get_active_doc()
        doc.SketchManager.Create3PointArc(x1, y1, 0, x2, y2, 0, x3, y3, 0)
        return {"entity_type": "arc", "start": [x1, y1], "end": [x2, y2], "mid": [x3, y3]}

    # ─── 特征操作（内嵌 W-A-R）───

    def extrude(self, depth: float, flip: bool = False,
                merge: bool = False, expected_bodies: int = None) -> dict:
        """
        拉伸凸台/基体（FeatureExtrusion2 23参数签名, SW 2024）。
        内嵌完整 W-A-R 验证。

        Args:
            depth: 拉伸深度（米）
            flip: 是否反向
            merge: 是否合并到已有实体
            expected_bodies: 期望实体数（None=不检查）
        """
        doc = self.conn.get_active_doc()

        # 反幻觉：确认 API 存在
        self.guard.assert_api_exists(doc.FeatureManager, "FeatureExtrusion2")

        def do_extrude():
            # 先关闭草图
            doc.SketchManager.InsertSketch(True)

            feat = doc.FeatureManager.FeatureExtrusion2(
                False, flip, False,     # Sd, Flip, Dir
                0, 0,                   # T1, T2 (0=Blind)
                depth, 0,               # D1, D2 (米)
                False, False,           # Dchk1, Dchk2
                False, False,           # Ddir1, Ddir2
                0, 0,                   # Dang1, Dang2
                False, False,           # Ofr, Ofc
                False, False,           # Tf1, Tf2
                merge,                  # Merge
                True, True,             # UseFeatScope, UseAutoSelect
                0, False, False         # StartOffset, IsAutoStartOffset, FlipStartOffset
            )
            return {
                "feature_returned": feat is not None,
                "feature_name": safe_call(feat, "Name", "") if feat else "",
            }

        expectations = {"feature_count_increase": True}
        if expected_bodies is not None:
            expectations["body_count_expected"] = expected_bodies

        return self.war.execute_with_war(doc, do_extrude, expectations)

    def extrude_cut(self, depth: float, through_all: bool = False,
                    flip: bool = False) -> dict:
        """
        拉伸切除。
        使用 FeatureExtrusion2 反向拉伸（FeatureCut 在 Python COM 下不可用）。
        Dir=True 表示切除方向。
        """
        doc = self.conn.get_active_doc()

        def do_cut():
            doc.SketchManager.InsertSketch(True)

            # 通过深度或完全贯穿实现切除
            cut_depth = depth
            if through_all:
                cut_depth = 1.0  # 1米，足够贯穿

            feat = doc.FeatureManager.FeatureExtrusion2(
                False, flip, True,      # Sd, Flip, Dir=True(切除方向)
                0, 0,                   # T1, T2
                cut_depth, 0,           # D1, D2
                False, False,           # Dchk1, Dchk2
                False, False,           # Ddir1, Ddir2
                0, 0,                   # Dang1, Dang2
                False, False,           # Ofr, Ofc
                False, False,           # Tf1, Tf2
                True, True, True,       # Merge, UseFeatScope, UseAutoSelect
                0, False, False         # StartOffset 系列
            )
            return {
                "feature_returned": feat is not None,
                "method": "FeatureExtrusion2 (Dir=True for cut)",
            }

        expectations = {"feature_count_increase": True}
        return self.war.execute_with_war(doc, do_cut, expectations)

    def fillet(self, radius: float) -> dict:
        """
        添加圆角（FeatureFillet3，需先预选边）。
        7参数签名: (Options, Radius, FeatureOptions, ...).
        """
        doc = self.conn.get_active_doc()
        self.guard.assert_api_exists(doc.FeatureManager, "FeatureFillet3")

        before_count = safe_call(doc, "GetFeatureCount", 0)
        if callable(before_count):
            before_count = 0

        feat = doc.FeatureManager.FeatureFillet3(
            122,        # Options (swFeatureFilletPropagate + swFeatureFilletAttachEdges)
            radius,     # 半径 (米)
            0, 0,       # FeatureOptions, ConicRho
            0, 0, 0     # OverflowType, Rho, ...
        )

        after_count = safe_call(doc, "GetFeatureCount", 0)
        if callable(after_count):
            after_count = 0

        # 重建验证
        rebuild = self.war.assert_rebuild(doc)

        return {
            "feature_returned": feat is not None,
            "feature_count_before": before_count,
            "feature_count_after": after_count,
            "rebuild_ok": rebuild.get("rebuild_ok", False),
            "status": "SUCCESS" if after_count > before_count else "POSSIBLE_FAILURE",
        }

    def chamfer(self, distance: float, angle: float = 0.785398) -> dict:
        """添加倒角"""
        doc = self.conn.get_active_doc()

        before_count = safe_call(doc, "GetFeatureCount", 0)
        if callable(before_count):
            before_count = 0

        feat = doc.FeatureManager.FeatureChamfer(
            1, distance, distance, angle, 0, 0, 0
        )

        after_count = safe_call(doc, "GetFeatureCount", 0)
        if callable(after_count):
            after_count = 0

        rebuild = self.war.assert_rebuild(doc)
        return {
            "feature_returned": feat is not None,
            "feature_count_before": before_count,
            "feature_count_after": after_count,
            "rebuild_ok": rebuild.get("rebuild_ok", False),
        }

    def rebuild_model(self) -> dict:
        """强制重建模型"""
        doc = self.conn.get_active_doc()
        rebuild = self.war.assert_rebuild(doc)
        feature_count = safe_call(doc, "GetFeatureCount", 0)
        if callable(feature_count):
            feature_count = 0
        body_count = self.war._get_body_count(doc)
        return {
            **rebuild,
            "feature_count": feature_count,
            "body_count": body_count,
        }

    # ─── 查询方法 ───

    def get_feature_tree(self, doc=None) -> list:
        """获取完整特征树"""
        if doc is None:
            doc = self.conn.get_active_doc()
        features = []
        try:
            feat = doc.FirstFeature
            if feat is None:
                feat = doc.FirstFeature()
            count = 0
            while feat is not None and count < 500:
                name = safe_call(feat, "Name", "")
                type_name = ""
                try:
                    tn = feat.GetTypeName2
                    type_name = tn() if callable(tn) else tn
                except Exception:
                    pass
                features.append({"name": name, "type": type_name})
                feat = feat.GetNextFeature()
                count += 1
        except Exception:
            pass
        return features

    def get_bounding_box(self, doc=None) -> dict:
        if doc is None:
            doc = self.conn.get_active_doc()
        return self.war._get_bounding_box(doc)

    def get_mass_properties(self, doc=None) -> dict:
        if doc is None:
            doc = self.conn.get_active_doc()
        return self.war._get_mass_properties(doc)

    # ─── 内部方法 ───

    def _resolve_plane_name(self, plane_name: str) -> list:
        """将 plane_name 解析为候选名称列表"""
        candidates = []
        lower = plane_name.lower().strip()

        # 简写映射
        if lower in PLANE_NAMES:
            candidates.extend(PLANE_NAMES[lower])
        else:
            # 直接使用输入
            candidates.append(plane_name)
            # 中英文互换
            if "基准面" in plane_name:
                en = plane_name.replace("基准面", "Plane")
                candidates.append(en)
            elif "Plane" in plane_name:
                cn_map = {
                    "Front Plane": "前视基准面",
                    "Top Plane": "上视基准面",
                    "Right Plane": "右视基准面",
                    "Back Plane": "后视基准面",
                    "Left Plane": "左视基准面",
                    "Bottom Plane": "仰视基准面",
                }
                if plane_name in cn_map:
                    candidates.append(cn_map[plane_name])

        return candidates

    def _list_features(self, doc, max_count: int = 20) -> list:
        """列出前 N 个特征（调试用）"""
        features = []
        try:
            feat = doc.FirstFeature
            if feat is None:
                feat = doc.FirstFeature()
            count = 0
            while feat is not None and count < max_count:
                name = safe_call(feat, "Name", "")
                features.append(name)
                feat = feat.GetNextFeature()
                count += 1
        except Exception:
            pass
        return features
