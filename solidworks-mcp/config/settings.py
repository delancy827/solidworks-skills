"""
SolidWorks MCP Server — 全局配置

所有路径、超时、重试策略、API签名等集中管理。
"""
import os
import tempfile

# ─── SolidWorks 版本与 API 签名 ───
SW_VERSION = "2024"
SW_PROG_IDS = [
    "SldWorks.Application.32",
    "SldWorks.Application.31",
    "SldWorks.Application.30",
    "SldWorks.Application",
]

# FeatureExtrusion2 参数数量（SW 2024 = 23）
FEATURE_EXTRUSION2_PARAM_COUNT = 23

# FeatureFillet3 参数数量
FEATURE_FILLET3_PARAM_COUNT = 7

# ─── 模板路径候选 ───
TEMPLATE_CANDIDATES = [
    r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_part.prtdot",
    r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\ansi inch\part.prtdot",
    r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Part.prtdot",
    r"C:\ProgramData\SolidWorks\SOLIDWORKS 2023\templates\gb_part.prtdot",
    r"C:\Program Files\SolidWorks Corp\SOLIDWORKS\lang\chinese-simplified\Tutorial\part.prtdot",
    r"C:\Program Files\SolidWorks Corp\SOLIDWORKS\templates\gb_part.prtdot",
]

ASSEMBLY_TEMPLATE_CANDIDATES = [
    r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\gb_assembly.asmdot",
    r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Assembly.asmdot",
]

# ─── 截图配置 ───
SCREENSHOT_DIR = os.path.join(tempfile.gettempdir(), "sw_mcp_screenshots")

# View ID 映射（已修正：Top=3, Right=5，不是旧版 Top=5, Right=4）
VIEW_MAP = {
    "iso":    ("*等轴测", 7),
    "front":  ("*前视", 1),
    "top":    ("*上视", 3),
    "right":  ("*右视", 5),
    "back":   ("*后视", 2),
    "left":   ("*左视", 4),
    "bottom": ("*仰视", 6),
}

# 英文名称回退映射
VIEW_ENGLISH_MAP = {
    7: "*Isometric",
    1: "*Front",
    3: "*Top",
    5: "*Right",
    2: "*Back",
    4: "*Left",
    6: "*Bottom",
}

DEFAULT_VIEWS = ["iso", "front", "top", "right"]

# ─── 超时与重试 ───
CONNECT_TIMEOUT_SECONDS = 30
OPERATION_TIMEOUT_SECONDS = 60
REBUILD_WAIT_SECONDS = 0.5
SCREENSHOT_WAIT_SECONDS = 0.3
NEW_DOCUMENT_WAIT_SECONDS = 1.0

# 重试策略
MAX_RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 0.5

# ─── W-A-R 验证 ───
DEFAULT_TOLERANCE_M = 0.000001  # ±1μm
EMPTY_DOC_FEATURE_THRESHOLD = 3  # 特征数 ≤ 此值视为空文档

# ─── 熔断器 ───
CIRCUIT_BREAKER_MAX_FAILURES = 3
CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60

# ─── 反幻觉 API 白名单（SW 2024 Python COM 已验证可用）───
VERIFIED_APIS = {
    "SldWorks": [
        "ActiveDoc", "NewDocument", "NewPart", "CloseDoc",
        "GetDocumentCount", "GetDocuments", "RevisionNumber",
        "Visible", "UserControl", "GetVersion",
    ],
    "ModelDoc2": [
        "ActiveSketch", "ClearSelection2", "EditRebuild3",
        "Extension", "FeatureManager", "FirstFeature",
        "ForceRebuild3", "GetFeatureCount", "GetTitle",
        "GetPathName", "GetType", "Parameter",
        "SaveAs", "SaveAs3", "SketchManager",
        "SelectionManager", "ShowNamedView2",
        "ViewZoomtofit2", "ViewZoomToFit",
    ],
    "FeatureManager": [
        "FeatureExtrusion2", "FeatureExtrusion3",
        "FeatureFillet3", "FeatureChamfer",
        "GetLastFeature", "InsertRefPlane",
        "InsertSketch",
    ],
    "SketchManager": [
        "ActiveSketch", "CreateCircle", "CreateCircleByRadius",
        "CreateCornerRectangle", "CreateLine",
        "Create3PointArc", "InsertSketch",
    ],
    "ModelDocExtension": [
        "SelectByID2", "CreateMassProperty",
        "CreateBoundingBox",
    ],
}

# ─── Python COM 已知不可用的 API（SW 2024）───
UNAVAILABLE_APIS = {
    "FeatureCut": "Python COM 下返回 None（>12 参数 COM IDispatch 限制）",
    "FeatureCut3": "Python COM 下返回 None",
    "FeatureCut4": "Python COM 下返回 None（27 参数超限）",
    "SimpleHole": "参数不匹配",
    "SimpleHole2": "参数不匹配",
    "HoleWizard5": "类型/参数不匹配",
    "InsertCombineFeature": "类型不匹配",
    "RunMacro": "返回 False",
    "RunMacro2": "类型不匹配",
}
