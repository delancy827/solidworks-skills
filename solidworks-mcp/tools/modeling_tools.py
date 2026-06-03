"""
MCP Tools: 建模操作 (12个工具)

sw_select_plane, sw_create_sketch, sw_draw_line, sw_draw_circle,
sw_draw_rectangle, sw_draw_arc, sw_close_sketch, sw_extrude,
sw_extrude_cut, sw_fillet, sw_chamfer, sw_rebuild_model

所有坐标单位为米（SW内部单位）。
"""
from core.sw_connection import get_connection_manager
from core.sw_operations import SWOperations
from core.war_validator import WARValidator
from core.anti_hallucination import AntiHallucinationGuard


def register_modeling_tools(mcp):
    """注册所有建模操作工具到 MCP Server"""

    conn = get_connection_manager()
    guard = AntiHallucinationGuard()
    war = WARValidator(conn)
    ops = SWOperations(conn, war, guard)

    @mcp.tool()
    def sw_select_plane(plane_name: str) -> dict:
        """Select a reference plane for sketching.
        Accepts: Chinese name (前视基准面), English (Front Plane),
        or shorthand (front, top, right).
        Falls back to feature tree traversal if SelectByID2 fails.
        """
        return ops.select_plane(plane_name)

    @mcp.tool()
    def sw_create_sketch(plane_name: str = "front") -> dict:
        """Create a 2D sketch on the specified plane.
        Automatically selects the plane first.
        """
        return ops.create_sketch(plane_name)

    @mcp.tool()
    def sw_draw_line(x1: float, y1: float, x2: float, y2: float) -> dict:
        """Draw a line in the active sketch.
        All coordinates in METERS (SW internal unit).
        Example: 50mm = 0.050
        """
        return ops.draw_line(x1, y1, x2, y2)

    @mcp.tool()
    def sw_draw_circle(cx: float, cy: float, radius: float) -> dict:
        """Draw a circle in the active sketch.
        cx, cy: center coordinates in meters.
        radius: circle radius in meters.
        """
        return ops.draw_circle(cx, cy, radius)

    @mcp.tool()
    def sw_draw_rectangle(x1: float, y1: float, x2: float, y2: float) -> dict:
        """Draw a rectangle in the active sketch (corner rectangle).
        x1, y1: first corner in meters.
        x2, y2: opposite corner in meters.
        """
        return ops.draw_rectangle(x1, y1, x2, y2)

    @mcp.tool()
    def sw_draw_arc(x1: float, y1: float, x2: float, y2: float,
                    x3: float, y3: float) -> dict:
        """Draw a 3-point arc in the active sketch.
        x1,y1: start point; x2,y2: end point; x3,y3: midpoint.
        All in meters.
        """
        return ops.draw_arc(x1, y1, x2, y2, x3, y3)

    @mcp.tool()
    def sw_close_sketch() -> dict:
        """Close the active sketch and return to 3D mode."""
        return ops.close_sketch()

    @mcp.tool()
    def sw_extrude(depth: float, flip: bool = False,
                   merge: bool = False) -> dict:
        """Extrude the active sketch to create a solid feature.
        Uses FeatureExtrusion2 with 23 parameters (SW 2024).
        Includes W-A-R (Write-Assert-Read) verification.

        depth: Extrusion depth in METERS. Example: 50mm = 0.050
        flip: Reverse extrusion direction.
        merge: Merge with existing body.
        """
        return ops.extrude(depth, flip, merge)

    @mcp.tool()
    def sw_extrude_cut(depth: float, through_all: bool = False,
                       flip: bool = False) -> dict:
        """Extrude cut (removes material).
        Uses FeatureExtrusion2 with Dir=True (FeatureCut unavailable in Python COM).
        Includes W-A-R verification.

        depth: Cut depth in meters (ignored if through_all=True).
        through_all: Cut through entire model.
        flip: Reverse cut direction.
        """
        return ops.extrude_cut(depth, through_all, flip)

    @mcp.tool()
    def sw_fillet(radius: float) -> dict:
        """Add fillet to pre-selected edges.
        IMPORTANT: You must select edges FIRST using sw_select_plane or direct selection.
        radius: Fillet radius in meters. Example: 5mm = 0.005
        """
        return ops.fillet(radius)

    @mcp.tool()
    def sw_chamfer(distance: float, angle: float = 0.785398) -> dict:
        """Add chamfer to pre-selected edges.
        distance: Chamfer distance in meters.
        angle: Chamfer angle in radians (default: 45° = 0.785398).
        """
        return ops.chamfer(distance, angle)

    @mcp.tool()
    def sw_rebuild_model() -> dict:
        """Force rebuild the model (EditRebuild3 / ForceRebuild3).
        Returns rebuild status, feature count, and body count.
        """
        return ops.rebuild_model()
