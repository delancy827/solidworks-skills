"""
SolidWorks COM 单例连接管理器 — 铁律1的工程化实现

所有 MCP Tools 必须通过此类获取 SW 对象，禁止自行 Dispatch。
- 单例模式：__new__ 保证全局唯一
- ProgID 回退链：GetActiveObject → Dispatch(.32) → Dispatch(.31) → Dispatch("")
- 文档复用：先检查 ActiveDoc，只有明确要求新建时才 NewDocument
- 闭环清理：managed_docs 跟踪，cleanup_all() 一键关闭
- pythoncom.CoInitialize() / CoUninitialize() 配对
"""
import os
import threading
import time

import pythoncom
import win32com.client

from config.settings import (
    SW_PROG_IDS,
    TEMPLATE_CANDIDATES,
    ASSEMBLY_TEMPLATE_CANDIDATES,
    EMPTY_DOC_FEATURE_THRESHOLD,
    NEW_DOCUMENT_WAIT_SECONDS,
)


def safe_call(obj, attr, default=None):
    """
    安全访问 COM 属性/方法。
    SW 中 GetTitle、GetFeatureCount 等是属性而非方法，
    直接调用不加括号，此函数兼容两种访问方式。
    （来自 sw_connect_info.py 的经验）
    """
    try:
        val = getattr(obj, attr)
        if callable(val):
            return val()
        return val
    except Exception:
        return default


class SWConnectionError(Exception):
    """SW 连接相关错误"""
    pass


class SWConnectionManager:
    """
    单例连接管理器 — 全局唯一 SW 连接点。

    使用方式:
        conn = SWConnectionManager()  # 永远返回同一实例
        conn.connect()
        doc = conn.get_active_doc()
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._initialized = False
            cls._instance = inst
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.sw = None               # SldWorks.Application COM 对象
        self.managed_docs = {}        # {doc_title: doc_object}
        self.operation_lock = threading.Lock()
        self._com_initialized = False

    # ─── 连接 ───

    def connect(self, sw_version: str = "32") -> dict:
        """
        连接 SolidWorks（单例回退链）。
        优先级: GetActiveObject → Dispatch(.32) → .31 → .30 → ""
        铁律1.1: 必须 GetActiveObject 优先，严禁盲目 Dispatch。
        """
        # 检查已有连接是否存活
        if self.sw is not None:
            try:
                _ = self.sw.Visible
                return {
                    "status": "already_connected",
                    "version": self._get_version(),
                    "visible": True,
                    "document_count": self.sw.GetDocumentCount()
                    if hasattr(self.sw, "GetDocumentCount")
                    else self.sw.GetDocumentCount,
                }
            except Exception:
                self.sw = None  # 旧连接已死

        # COM 初始化（必须在当前线程）
        if not self._com_initialized:
            try:
                pythoncom.CoInitialize()
            except Exception:
                pass
            self._com_initialized = True

        # 优先级1: GetActiveObject（复用已运行实例）
        try:
            self.sw = win32com.client.GetActiveObject("SldWorks.Application")
        except Exception:
            pass

        # 优先级2: 版本化 Dispatch 回退链
        if self.sw is None:
            prog_ids = list(SW_PROG_IDS)
            # 把用户指定的版本放最前
            user_prog = f"SldWorks.Application.{sw_version}"
            if user_prog not in prog_ids:
                prog_ids.insert(0, user_prog)
            for prog_id in prog_ids:
                try:
                    self.sw = win32com.client.Dispatch(prog_id)
                    break
                except Exception:
                    continue

        if self.sw is None:
            raise SWConnectionError(
                "无法连接 SolidWorks。请确认 SW 已安装并可运行。\n"
                f"尝试的 ProgID: {SW_PROG_IDS}"
            )

        # 铁律1核心：必须设置
        self.sw.Visible = True
        self.sw.UserControl = True

        return {
            "status": "connected",
            "version": self._get_version(),
            "visible": True,
            "document_count": self._safe_doc_count(),
        }

    def disconnect(self) -> dict:
        """断开连接，关闭所有托管文档"""
        closed = []
        if self.sw is not None:
            for title in list(self.managed_docs.keys()):
                try:
                    self.sw.CloseDoc(title)
                    closed.append(title)
                except Exception:
                    pass
            self.managed_docs.clear()

        if self._com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
            self._com_initialized = False

        self.sw = None
        return {"status": "disconnected", "closed_docs": closed}

    # ─── 文档管理 ───

    def get_active_doc(self):
        """
        获取当前活动文档（复用，禁止盲目新建）。
        铁律1.2: 必须先检查 sw.ActiveDoc。
        """
        if self.sw is None:
            raise SWConnectionError("SW 未连接，请先调用 sw_connect")
        doc = self.sw.ActiveDoc
        if doc is None:
            raise SWConnectionError(
                "没有打开的文档，请先调用 sw_new_part 新建或 sw_open_document 打开"
            )
        self._register_doc(doc)
        return doc

    def new_document(self, template_path: str = "") -> dict:
        """
        新建零件文档。
        铁律1.2: 如果已有空文档（特征数 ≤ 3），优先复用。
        """
        if self.sw is None:
            raise SWConnectionError("SW 未连接")

        # 反盲目：检查是否可复用现有空文档
        existing = self.sw.ActiveDoc
        if existing is not None:
            try:
                feat_count = (
                    existing.GetFeatureCount
                    if not callable(existing.GetFeatureCount)
                    else existing.GetFeatureCount()
                )
                if feat_count <= EMPTY_DOC_FEATURE_THRESHOLD:
                    title = safe_call(existing, "GetTitle", "unknown")
                    self._register_doc(existing)
                    return {
                        "status": "reused_existing",
                        "doc_title": title,
                        "doc_type": safe_call(existing, "GetType", 0),
                        "feature_count": feat_count,
                        "warning": "复用了已有的空文档。如需全新文档请先关闭现有文档。",
                    }
            except Exception:
                pass

        # 确定模板路径
        if not template_path:
            template_path = self._find_template(TEMPLATE_CANDIDATES)

        before_count = self._safe_doc_count()
        self.sw.NewDocument(template_path, 0, 0, 0)
        time.sleep(NEW_DOCUMENT_WAIT_SECONDS)

        doc = self.sw.ActiveDoc
        if doc is None:
            raise SWConnectionError("NewDocument 后 ActiveDoc 为 None，新建零件失败")

        self._register_doc(doc)
        return {
            "status": "created",
            "doc_title": safe_call(doc, "GetTitle", "unknown"),
            "doc_type": safe_call(doc, "GetType", 0),
            "feature_count": safe_call(doc, "GetFeatureCount", 0),
        }

    def open_document(self, file_path: str) -> dict:
        """打开现有文档"""
        if self.sw is None:
            raise SWConnectionError("SW 未连接")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        errors = 0
        warnings = 0
        # doc_type: 1=part, 2=assembly, 3=drawing
        ext = os.path.splitext(file_path)[1].lower()
        doc_type_map = {".sldprt": 1, ".sldasm": 2, ".slddrw": 3}
        doc_type = doc_type_map.get(ext, 1)

        doc = self.sw.OpenDoc6(file_path, doc_type, 1, "", errors, warnings)
        if doc is None:
            raise SWConnectionError(
                f"打开文档失败: {file_path} (errors={errors}, warnings={warnings})"
            )

        self._register_doc(doc)
        return {
            "status": "opened",
            "doc_title": safe_call(doc, "GetTitle", "unknown"),
            "doc_type": safe_call(doc, "GetType", 0),
            "feature_count": safe_call(doc, "GetFeatureCount", 0),
        }

    def save_document(self, file_path: str) -> dict:
        """保存当前文档"""
        doc = self.get_active_doc()
        try:
            result = doc.SaveAs3(file_path, 1, 2)
            saved = result == 0
        except Exception:
            try:
                doc.SaveAs(file_path)
                saved = os.path.exists(file_path)
            except Exception as e:
                raise SWConnectionError(f"保存失败: {e}")

        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        return {
            "saved": saved,
            "path": file_path,
            "file_size_bytes": file_size,
        }

    def close_document(self, doc_title: str = "") -> dict:
        """关闭文档（空字符串 = 关闭当前活动文档）"""
        if self.sw is None:
            return {"status": "not_connected"}

        if not doc_title:
            doc = self.sw.ActiveDoc
            if doc is None:
                return {"status": "no_document"}
            doc_title = safe_call(doc, "GetTitle", "")

        try:
            self.sw.CloseDoc(doc_title)
        except Exception as e:
            return {"status": "error", "error": str(e), "title": doc_title}
        finally:
            self.managed_docs.pop(doc_title, None)

        return {"status": "closed", "title": doc_title}

    # ─── 状态查询 ───

    def get_status(self) -> dict:
        """获取 SW 连接和资源状态"""
        if self.sw is None:
            return {"connected": False}

        try:
            version = self._get_version()
            doc_count = self._safe_doc_count()
            active_title = None
            doc = self.sw.ActiveDoc
            if doc is not None:
                active_title = safe_call(doc, "GetTitle", "unknown")

            return {
                "connected": True,
                "version": version,
                "active_doc": active_title,
                "open_docs": doc_count,
                "managed_docs": list(self.managed_docs.keys()),
                "memory_mb": self._get_memory_mb(),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def cleanup_all(self) -> dict:
        """紧急清理 — 关闭所有托管文档"""
        closed = []
        for title in list(self.managed_docs.keys()):
            try:
                self.sw.CloseDoc(title)
                closed.append(title)
            except Exception:
                pass
        self.managed_docs.clear()
        return {"closed": closed, "count": len(closed)}

    # ─── 内部方法 ───

    def _register_doc(self, doc):
        """注册托管文档"""
        if doc is not None:
            title = safe_call(doc, "GetTitle", None)
            if title:
                self.managed_docs[title] = doc

    def _find_template(self, candidates: list) -> str:
        """动态模板检测 — 遍历候选路径，返回第一个存在的"""
        for c in candidates:
            if os.path.exists(c):
                return c
        # 回退：返回第一个候选（让 SW 自己报错）
        return candidates[0] if candidates else ""

    def _safe_doc_count(self) -> int:
        """安全获取文档计数"""
        if self.sw is None:
            return 0
        try:
            val = self.sw.GetDocumentCount
            if callable(val):
                return val()
            return val
        except Exception:
            return -1

    def _get_version(self) -> str:
        """获取 SW 版本号"""
        if self.sw is None:
            return "unknown"
        return safe_call(self.sw, "RevisionNumber", "unknown")

    def _get_memory_mb(self) -> float:
        """获取 SW 进程内存占用 (MB)"""
        try:
            import psutil
            for proc in psutil.process_iter(["name", "memory_info"]):
                if "SLDWORKS" in proc.info.get("name", "").upper():
                    mem = proc.info["memory_info"]
                    return round(mem.rss / (1024 * 1024), 1)
        except Exception:
            pass
        return -1.0


# 全局获取单例
def get_connection_manager() -> SWConnectionManager:
    return SWConnectionManager()
