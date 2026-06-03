"""
MCP Tools: 连接管理与文档管理 (7个工具)

sw_connect, sw_disconnect, sw_get_status,
sw_new_part, sw_open_document, sw_save_document, sw_close_document
"""
from core.sw_connection import get_connection_manager, SWConnectionError
from core.memory_monitor import MemoryMonitor


def register_connection_tools(mcp):
    """注册所有连接管理工具到 MCP Server"""

    conn = get_connection_manager()
    monitor = MemoryMonitor(conn)

    @mcp.tool()
    def sw_connect(sw_version: str = "32") -> dict:
        """Connect to SolidWorks (singleton pattern).
        Uses GetActiveObject first, then falls back to Dispatch.
        Sets UserControl=True to prevent GC collection.
        """
        try:
            return conn.connect(sw_version)
        except SWConnectionError as e:
            return {"status": "error", "error": str(e)}

    @mcp.tool()
    def sw_disconnect() -> dict:
        """Disconnect from SolidWorks and close all managed documents."""
        return conn.disconnect()

    @mcp.tool()
    def sw_get_status() -> dict:
        """Get SolidWorks connection status, version, active document,
        open document count, and memory usage."""
        status = conn.get_status()
        # 附加内存监控
        mem = monitor.snapshot()
        status["memory"] = mem
        # 检查内存泄漏
        leak = monitor.check_leak()
        if leak.get("warning"):
            status["memory_warning"] = leak["warning"]
        return status

    @mcp.tool()
    def sw_new_part(template_path: str = "") -> dict:
        """Create a new part document.
        Reuses existing empty document if available (prevents window proliferation).
        template_path: Full path to .prtdot template (empty = auto-detect).
        """
        try:
            return conn.new_document(template_path)
        except (SWConnectionError, FileNotFoundError) as e:
            return {"status": "error", "error": str(e)}

    @mcp.tool()
    def sw_open_document(file_path: str) -> dict:
        """Open an existing SolidWorks document (.sldprt, .sldasm, .slddrw)."""
        try:
            return conn.open_document(file_path)
        except (SWConnectionError, FileNotFoundError) as e:
            return {"status": "error", "error": str(e)}

    @mcp.tool()
    def sw_save_document(file_path: str) -> dict:
        """Save the current document to the specified path."""
        try:
            return conn.save_document(file_path)
        except (SWConnectionError, Exception) as e:
            return {"saved": False, "error": str(e)}

    @mcp.tool()
    def sw_close_document(doc_title: str = "") -> dict:
        """Close a document. Empty string = close current active document."""
        return conn.close_document(doc_title)
