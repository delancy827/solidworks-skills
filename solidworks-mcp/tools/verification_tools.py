"""
MCP Tools: 验证查询 (6个工具)

sw_get_feature_tree, sw_get_body_count, sw_get_bounding_box,
sw_get_mass_properties, sw_verify_model, sw_probe_api
"""
from core.sw_connection import get_connection_manager, safe_call
from core.sw_operations import SWOperations
from core.war_validator import WARValidator
from core.anti_hallucination import AntiHallucinationGuard


def register_verification_tools(mcp):
    """注册所有验证查询工具到 MCP Server"""

    conn = get_connection_manager()
    war = WARValidator(conn)
    ops = SWOperations(conn, war)
    guard = AntiHallucinationGuard()

    @mcp.tool()
    def sw_get_feature_tree() -> dict:
        """Get the complete feature tree of the current document.
        Returns list of features with name and type.
        """
        doc = conn.get_active_doc()
        features = ops.get_feature_tree(doc)
        return {
            "features": features,
            "feature_count": len(features),
        }

    @mcp.tool()
    def sw_get_body_count() -> dict:
        """Get the number of solid and surface bodies in the model.
        Uses GetBodies2 for hard verification.
        """
        doc = conn.get_active_doc()
        solid = war._get_body_count(doc)

        # 尝试获取曲面体数量
        surface_count = 0
        try:
            bodies = doc.GetBodies2(1, False)  # 1 = surface bodies
            surface_count = len(bodies) if bodies else 0
        except Exception:
            pass

        return {
            "solid_bodies": solid,
            "surface_bodies": surface_count,
        }

    @mcp.tool()
    def sw_get_bounding_box() -> dict:
        """Get the model's bounding box dimensions in millimeters."""
        doc = conn.get_active_doc()
        bbox = ops.get_bounding_box(doc)
        return bbox if bbox else {"error": "无法获取包围盒（可能是空模型）"}

    @mcp.tool()
    def sw_get_mass_properties() -> dict:
        """Get mass properties: volume, surface area, mass.
        Note: Material must be assigned for accurate mass calculation.
        """
        doc = conn.get_active_doc()
        mass = ops.get_mass_properties(doc)
        return mass if mass else {"error": "无法获取质量属性"}

    @mcp.tool()
    def sw_verify_model() -> dict:
        """Comprehensive model health check.
        Performs: rebuild, feature count, body count, bounding box, mass.
        Returns overall health status and all metrics.
        """
        doc = conn.get_active_doc()
        result = war.full_model_check(doc)
        result["doc_title"] = safe_call(doc, "GetTitle", "unknown")
        return result

    @mcp.tool()
    def sw_probe_api(object_path: str, keyword: str = "") -> dict:
        """Probe available methods/attributes on a SolidWorks COM object.
        Uses dir() reflection to discover APIs (Iron Rule 3: Anti-Hallucination).

        object_path: Dot-separated path like 'doc.SketchManager' or 'doc.FeatureManager'.
        keyword: Filter results by keyword (case-insensitive).
        """
        doc = conn.get_active_doc()

        # 解析对象路径
        obj_map = {
            "doc": doc,
            "doc.SketchManager": doc.SketchManager,
            "doc.FeatureManager": doc.FeatureManager,
            "doc.Extension": doc.Extension,
            "doc.SelectionManager": doc.SelectionManager,
        }

        # 尝试获取 sw app
        if conn.sw is not None:
            obj_map["sw"] = conn.sw
            obj_map["sw_app"] = conn.sw

        obj = obj_map.get(object_path)
        if obj is None:
            return {
                "error": f"未知对象路径: {object_path}",
                "available": list(obj_map.keys()),
            }

        members = guard.probe_object(obj, keyword)
        return {
            "object": object_path,
            "keyword": keyword or "(all)",
            "count": len(members),
            "members": members,
        }
