"""
内存与窗口监控器

监控 SolidWorks 进程的内存使用和打开文档数量，
用于检测内存泄漏和窗口泛滥问题。
"""

class MemoryMonitor:
    """SW 进程内存与窗口监控"""

    def __init__(self, connection_manager):
        self.conn = connection_manager
        self._history = []  # [(timestamp, rss_mb, doc_count), ...]

    def snapshot(self) -> dict:
        """获取当前内存快照"""
        info = self._get_process_info()
        self._history.append(info)
        return info

    def check_leak(self, threshold_mb: float = 500.0) -> dict:
        """
        检查内存泄漏。
        如果最近一次快照超过阈值，发出警告。
        """
        if not self._history:
            self.snapshot()

        latest = self._history[-1]
        rss = latest.get("rss_mb", 0)

        warning = None
        if rss > threshold_mb:
            warning = (
                f"SW 进程内存占用 {rss:.0f}MB 超过阈值 {threshold_mb:.0f}MB，"
                f"建议关闭不需要的文档释放内存。"
            )

        return {
            "rss_mb": rss,
            "threshold_mb": threshold_mb,
            "warning": warning,
            "doc_count": latest.get("doc_count", 0),
            "managed_count": latest.get("managed_count", 0),
        }

    def get_history_summary(self) -> dict:
        """获取历史快照摘要"""
        if not self._history:
            return {"snapshots": 0}

        rss_values = [h.get("rss_mb", 0) for h in self._history]
        return {
            "snapshots": len(self._history),
            "rss_min_mb": round(min(rss_values), 1),
            "rss_max_mb": round(max(rss_values), 1),
            "rss_current_mb": round(rss_values[-1], 1),
            "trend": "increasing" if len(rss_values) >= 3 and rss_values[-1] > rss_values[0] * 1.1 else "stable",
        }

    def _get_process_info(self) -> dict:
        """获取 SW 进程信息"""
        import time

        result = {
            "timestamp": time.time(),
            "rss_mb": 0,
            "vms_mb": 0,
            "doc_count": 0,
            "managed_count": len(self.conn.managed_docs),
        }

        # 获取文档计数
        if self.conn.sw is not None:
            try:
                val = self.conn.sw.GetDocumentCount
                result["doc_count"] = val() if callable(val) else val
            except Exception:
                pass

        # 获取进程内存
        try:
            import psutil
            for proc in psutil.process_iter(["name", "memory_info"]):
                if "SLDWORKS" in proc.info.get("name", "").upper():
                    mem = proc.info["memory_info"]
                    result["rss_mb"] = round(mem.rss / (1024 * 1024), 1)
                    result["vms_mb"] = round(mem.vms / (1024 * 1024), 1)
                    break
        except Exception:
            pass

        return result
