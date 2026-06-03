"""
MCP Tools: 截图验证 (2个工具)

sw_capture_screenshots: 多视图截图，返回截图路径和元数据
sw_capture_and_verify: 截图 + 特征树 + 实体数 + 包围盒的综合验证

核心机制:
- ShowNamedView2 切换视角（中英文回退）
- ViewZoomtofit2 缩放适配
- SaveAs3 保存 BMP
- 返回截图文件路径供 AI 通过 Read 工具查看
"""
from config.settings import DEFAULT_VIEWS
from core.sw_connection import get_connection_manager, safe_call
from core.visual_verifier import VisualVerifier
from core.war_validator import WARValidator


def register_screenshot_tools(mcp):
    """注册截图验证工具到 MCP Server"""

    conn = get_connection_manager()
    verifier = VisualVerifier(conn)
    war = WARValidator(conn)

    @mcp.tool()
    def sw_capture_screenshots(
        views: list[str] = None,
    ) -> dict:
        """Capture multi-view screenshots of the current 3D model.
        Screenshots are saved as BMP files. The AI can use the Read tool
        to view the image files at the returned paths.
        Default views: iso (isometric), front, top, right.

        Available views: iso, front, top, right, back, left, bottom.
        """
        if views is None:
            views = list(DEFAULT_VIEWS)

        doc = conn.get_active_doc()
        screenshots = verifier.capture_views(doc, views)

        captured = []
        failed = []
        for s in screenshots:
            if s.get("success") and s.get("path"):
                captured.append({
                    "view": s["view"],
                    "path": s["path"],
                    "size_bytes": s.get("size_bytes", 0),
                    "mime": s.get("mime", "image/bmp"),
                })
            else:
                failed.append({
                    "view": s["view"],
                    "error": s.get("error", "未知错误"),
                })

        return {
            "screenshot_count": len(captured),
            "screenshots": captured,
            "failed": failed,
            "message": (
                f"Captured {len(captured)} screenshots. "
                f"Use the Read tool with the file paths to view images."
            ),
        }

    @mcp.tool()
    def sw_capture_and_verify(
        expected_description: str = "",
    ) -> dict:
        """Comprehensive verification: screenshots + feature tree + body count + bounding box.
        Returns all information needed for AI self-verification in a single call.

        The AI should compare the screenshots (via file paths) and metrics
        against expected_description to determine if the model is correct.

        expected_description: What the model should look like (e.g., "80x90x55mm rectangular block").
        """
        doc = conn.get_active_doc()

        result = verifier.capture_and_verify(doc, expected_description, war)

        # 整理截图信息
        image_list = []
        for s in result.get("screenshots", []):
            if s.get("success") and s.get("path"):
                image_list.append({
                    "view": s["view"],
                    "path": s["path"],
                    "size_bytes": s.get("size_bytes", 0),
                })

        return {
            "expected": expected_description,
            "screenshots": image_list,
            "screenshot_count": result.get("screenshot_count", 0),
            "feature_tree": result.get("feature_tree", []),
            "feature_count": result.get("feature_count", 0),
            "body_count": result.get("body_count", -1),
            "bounding_box": result.get("bounding_box", {}),
            "rebuild_ok": result.get("rebuild_ok", False),
            "verification_prompt": (
                f"Expected: {expected_description}\n"
                f"Feature count: {result.get('feature_count', 0)}\n"
                f"Body count: {result.get('body_count', -1)}\n"
                f"Bounding box: {result.get('bounding_box', {})}\n"
                f"Rebuild OK: {result.get('rebuild_ok', False)}\n"
                f"Please use the Read tool to view the screenshot files and verify the model matches the expected description."
            ),
        }
