"""
MCP Resources: SolidWorks 状态与参考信息

sw://status         — SW 连接状态、版本、活动文档、内存
sw://feature-tree   — 当前文档完整特征树
sw://model-info     — 模型信息（包围盒、质量、实体数、特征数）
sw://api-reference  — 已验证的 SW 2024 API 速查表
"""
import json

from core.sw_connection import get_connection_manager, safe_call
from core.sw_operations import SWOperations
from core.war_validator import WARValidator
from config.settings import VERIFIED_APIS, UNAVAILABLE_APIS


def register_resources(mcp):
    """注册 MCP Resources"""

    conn = get_connection_manager()
    war = WARValidator(conn)
    ops = SWOperations(conn, war)

    @mcp.resource("sw://status")
    def sw_status() -> str:
        """SolidWorks connection status, version, active document, memory usage."""
        return json.dumps(conn.get_status(), indent=2, default=str)

    @mcp.resource("sw://feature-tree")
    def sw_feature_tree() -> str:
        """Complete feature tree of the current document (name + type)."""
        try:
            doc = conn.get_active_doc()
            features = ops.get_feature_tree(doc)
            return json.dumps({
                "doc_title": safe_call(doc, "GetTitle", "unknown"),
                "feature_count": len(features),
                "features": features,
            }, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("sw://model-info")
    def sw_model_info() -> str:
        """Model information: bounding box, mass, body count, feature count."""
        try:
            doc = conn.get_active_doc()
            return json.dumps(war.full_model_check(doc), indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("sw://api-reference")
    def sw_api_reference() -> str:
        """Verified SW 2024 API reference table (from solidworks-skills project)."""
        lines = ["# SolidWorks 2024 Python COM API 速查表\n"]

        lines.append("## 已验证可用的 API\n")
        for category, apis in VERIFIED_APIS.items():
            lines.append(f"### {category}")
            for api in apis:
                lines.append(f"  - {api}")
            lines.append("")

        lines.append("## 已知不可用的 API（Python COM 限制）\n")
        for api, reason in UNAVAILABLE_APIS.items():
            lines.append(f"  - {api}: {reason}")
        lines.append("")

        lines.append("## 关键签名\n")
        lines.append("- FeatureExtrusion2: 23 参数 (SW 2024)")
        lines.append("- FeatureFillet3: 7 参数")
        lines.append("- SelectByID2: 9 参数, 第8参数必须 VARIANT(VT_DISPATCH, None)")
        lines.append("- GetTitle/GetFeatureCount: 属性（不加括号）")
        lines.append("- EditRebuild3: 属性（不加括号）")
        lines.append("- 单位: 全部为米 (meters)")

        return "\n".join(lines)
