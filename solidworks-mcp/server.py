"""
SolidWorks MCP Server
=====================

通过 Model Context Protocol (MCP) 让 AI Agent 安全操控 SolidWorks。
基于 solidworks-skills 项目的三大铁律：
  - 铁律1: 单例连接 + 窗口生命周期管理
  - 铁律2: W-A-R 闭环断言 (Write-Assert-Read)
  - 铁律3: 反幻觉守卫 + 异常熔断

传输协议: stdio (兼容 Claude Desktop / Cursor)
目标版本: SolidWorks 2024 (FeatureExtrusion2 = 23 参数)

Usage:
    python server.py

Claude Desktop config:
    {
        "mcpServers": {
            "solidworks": {
                "command": "python",
                "args": ["path/to/solidworks-mcp/server.py"]
            }
        }
    }
"""
import sys
import os

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP

# ─── 创建 MCP Server ───
mcp = FastMCP("SolidWorks MCP Server")

# ─── 注册 Tools ───
from tools.connection_tools import register_connection_tools
from tools.modeling_tools import register_modeling_tools
from tools.verification_tools import register_verification_tools
from tools.screenshot_tools import register_screenshot_tools

register_connection_tools(mcp)
register_modeling_tools(mcp)
register_verification_tools(mcp)
register_screenshot_tools(mcp)

# ─── 注册 Resources ───
from resources.sw_resources import register_resources
register_resources(mcp)

# ─── 注册 Prompts ───
from prompts.modeling_prompts import register_prompts
register_prompts(mcp)

# ─── 启动 ───
if __name__ == "__main__":
    mcp.run(transport="stdio")
