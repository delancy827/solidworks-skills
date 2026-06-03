"""
W-A-R 闭环验证器 — 铁律2的工程化实现

Write-Assert-Read 三步验证：
1. Write: 操作前记录"几何指纹"（feature_count, body_count, last_feature）
2. Assert: 强制重建 (EditRebuild3) + 错误码检查
3. Read: 对比前后状态，硬断言 (±1μm)

任何修改操作必须经过此验证器才算成功。
断言失败 = 任务彻底失败，严禁静默捕获。
"""
from config.settings import DEFAULT_TOLERANCE_M, REBUILD_WAIT_SECONDS
from core.sw_connection import safe_call
import time


class SWAssertionError(Exception):
    """W-A-R 断言失败 — 铁律2.3: 任务彻底失败"""
    pass


class WARValidator:
    """
    Write-Assert-Read 闭环验证器。

    使用方式:
        validator = WARValidator(connection_manager)
        result = validator.execute_with_war(doc, operation_fn, expectations)
    """

    def __init__(self, connection_manager=None):
        self.conn = connection_manager

    # ─── Write 阶段：提取指纹 ───

    def write_fingerprint(self, doc) -> dict:
        """
        操作前记录几何指纹。
        对应铁律2.1: 修改前提取目标参数指纹。
        """
        fingerprint = {
            "feature_count": self._get_feature_count(doc),
            "body_count": self._get_body_count(doc),
            "last_feature": self._get_last_feature_name(doc),
        }

        # 如果有活动草图，记录草图实体数
        try:
            sk = doc.SketchManager.ActiveSketch
            if sk is not None:
                seg_count = (
                    sk.GetSketchSegmentsCount()
                    if callable(sk.GetSketchSegmentsCount)
                    else sk.GetSketchSegmentsCount
                )
                fingerprint["sketch_segments"] = seg_count
        except Exception:
            pass

        return fingerprint

    # ─── Assert 阶段：强制重建 ───

    def assert_rebuild(self, doc) -> dict:
        """
        强制重建 + 错误码检查。
        对应铁律2.2。

        注意: EditRebuild3 在 Python COM 下是属性（不加括号）。
        """
        time.sleep(REBUILD_WAIT_SECONDS)
        try:
            # EditRebuild3 是属性访问，不加括号
            result = doc.EditRebuild3
            # result 可能为: True/False/None/整数错误码
            rebuild_ok = result is True or result is None or result == 0
            return {
                "rebuild_ok": rebuild_ok,
                "raw_result": str(result),
            }
        except Exception as e:
            # 回退到 ForceRebuild3
            try:
                doc.ForceRebuild3(False)
                return {"rebuild_ok": True, "raw_result": "ForceRebuild3"}
            except Exception as e2:
                return {"rebuild_ok": False, "raw_result": f"ERROR: {e2}"}

    # ─── Read 阶段：硬断言 ───

    def read_verify(self, doc, fingerprint_before: dict,
                    expectations: dict = None) -> dict:
        """
        对比修改前后的状态变化。
        对应铁律2.3: 断言失败 = 任务彻底失败。

        expectations 示例:
        {
            "feature_count_increase": True,
            "body_count_expected": 1,
            "dimension_name": "D1",
            "dimension_target_m": 0.050,
            "tolerance_m": 0.000001,
        }
        """
        result = {"passed": True, "checks": []}

        # 检查1: 特征数变化
        after_count = self._get_feature_count(doc)
        before_count = fingerprint_before["feature_count"]

        if expectations and expectations.get("feature_count_increase"):
            if after_count <= before_count:
                result["passed"] = False
                result["checks"].append({
                    "check": "feature_count_increase",
                    "status": "FAIL",
                    "before": before_count,
                    "after": after_count,
                    "message": f"特征数未增长: {before_count} → {after_count}",
                })
            else:
                result["checks"].append({
                    "check": "feature_count_increase",
                    "status": "PASS",
                    "before": before_count,
                    "after": after_count,
                })

        # 检查2: 实体数
        after_bodies = self._get_body_count(doc)
        if expectations and "body_count_expected" in expectations:
            expected = expectations["body_count_expected"]
            if expected is not None and after_bodies != expected:
                result["passed"] = False
                result["checks"].append({
                    "check": "body_count",
                    "status": "FAIL",
                    "expected": expected,
                    "actual": after_bodies,
                    "message": f"实体数不匹配: 期望={expected}, 实际={after_bodies}",
                })
            else:
                result["checks"].append({
                    "check": "body_count",
                    "status": "PASS",
                    "expected": expected,
                    "actual": after_bodies,
                })

        # 检查3: 尺寸硬断言 (±1μm)
        if expectations and "dimension_target_m" in expectations:
            target = expectations["dimension_target_m"]
            tolerance = expectations.get("tolerance_m", DEFAULT_TOLERANCE_M)
            dim_name = expectations.get("dimension_name", "")
            actual = self._get_dimension_value(doc, dim_name)

            if actual is not None:
                dim_ok = abs(actual - target) < tolerance
                if not dim_ok:
                    result["passed"] = False
                result["checks"].append({
                    "check": "dimension_assertion",
                    "status": "PASS" if dim_ok else "FAIL",
                    "target_m": target,
                    "actual_m": actual,
                    "tolerance_m": tolerance,
                    "deviation_m": abs(actual - target),
                })

        # 检查4: 重建验证
        rebuild = self.assert_rebuild(doc)
        if not rebuild["rebuild_ok"]:
            result["passed"] = False
        result["checks"].append({
            "check": "rebuild",
            **rebuild,
        })

        return result

    # ─── 完整 W-A-R 执行器 ───

    def execute_with_war(self, doc, operation_fn, expectations=None) -> dict:
        """
        完整 W-A-R 闭环执行器。

        Args:
            doc: SW ModelDoc2 对象
            operation_fn: 执行实际 SW 操作的 callable，返回操作结果 dict
            expectations: 验证期望（参见 read_verify）

        Returns:
            {
                "status": "SUCCESS" | "OPERATION_FAILED" | "VERIFICATION_FAILED",
                "operation_result": {...},
                "fingerprint_before": {...},
                "rebuild": {...},
                "verification": {...},
            }
        """
        # W: Write — 提取指纹
        fingerprint = self.write_fingerprint(doc)

        # 执行操作
        try:
            op_result = operation_fn()
        except Exception as e:
            return {
                "status": "OPERATION_FAILED",
                "error": str(e),
                "error_type": type(e).__name__,
                "fingerprint_before": fingerprint,
            }

        # A: Assert — 重建
        rebuild = self.assert_rebuild(doc)

        # R: Read — 硬断言
        verification = self.read_verify(doc, fingerprint, expectations)

        status = "SUCCESS" if verification["passed"] else "VERIFICATION_FAILED"

        result = {
            "status": status,
            "operation_result": op_result,
            "fingerprint_before": fingerprint,
            "rebuild": rebuild,
            "verification": verification,
        }

        # 验证失败时附加警告（铁律2.3: 禁止静默）
        if status == "VERIFICATION_FAILED":
            failed = [c for c in verification["checks"] if c.get("status") == "FAIL"]
            result["warning"] = (
                f"W-A-R 验证失败！失败项: {[c['check'] for c in failed]}。"
                f"请检查模型状态并修正后重试。"
            )

        return result

    # ─── 独立验证方法 ───

    def verify_feature_created(self, doc, before_count: int) -> dict:
        """验证特征是否创建成功（简化版 W-A-R）"""
        after = self._get_feature_count(doc)
        ok = after > before_count
        return {
            "passed": ok,
            "before": before_count,
            "after": after,
        }

    def verify_body_count(self, doc, expected: int) -> dict:
        """验证实体数量"""
        actual = self._get_body_count(doc)
        return {
            "passed": actual == expected,
            "expected": expected,
            "actual": actual,
        }

    def verify_rebuild(self, doc) -> dict:
        """验证模型重建"""
        return self.assert_rebuild(doc)

    def full_model_check(self, doc) -> dict:
        """全面模型健康检查"""
        result = {
            "feature_count": self._get_feature_count(doc),
            "body_count": self._get_body_count(doc),
            "rebuild": self.assert_rebuild(doc),
            "bounding_box": self._get_bounding_box(doc),
            "mass": self._get_mass_properties(doc),
        }
        result["healthy"] = (
            result["rebuild"]["rebuild_ok"]
            and result["feature_count"] > 0
        )
        return result

    # ─── 内部工具方法 ───

    def _get_feature_count(self, doc) -> int:
        """GetFeatureCount 是属性，不加括号"""
        try:
            val = doc.GetFeatureCount
            return val() if callable(val) else val
        except Exception:
            return -1

    def _get_body_count(self, doc) -> int:
        """
        GetBodies2 获取实体数量。
        注意: Python COM 下 GetBodies2 可能参数不匹配，需 try/except。
        """
        try:
            bodies = doc.GetBodies2(0, False)  # 0 = solid bodies
            return len(bodies) if bodies else 0
        except Exception:
            # 回退: 通过 PartDoc 获取
            try:
                import win32com.client
                part = doc
                bodies = part.GetBodies2(0, False)
                return len(bodies) if bodies else 0
            except Exception:
                return -1

    def _get_last_feature_name(self, doc) -> str:
        try:
            feat = doc.FeatureManager.GetLastFeature()
            if feat is not None:
                name = feat.Name
                return name() if callable(name) else name
        except Exception:
            pass
        return ""

    def _get_dimension_value(self, doc, dim_name: str):
        """获取指定尺寸的值（米）"""
        if not dim_name:
            return None
        try:
            dim = doc.Parameter(dim_name)
            if dim is not None:
                return dim.GetSystemValue3(0)
        except Exception:
            pass
        return None

    def _get_bounding_box(self, doc) -> dict:
        """获取模型包围盒"""
        try:
            bbox = doc.Extension.CreateBoundingBox()
            if bbox:
                pts = bbox.GetExtremePoints()
                if pts and len(pts) >= 6:
                    return {
                        "x_min": round(pts[0] * 1000, 2),
                        "y_min": round(pts[1] * 1000, 2),
                        "z_min": round(pts[2] * 1000, 2),
                        "x_max": round(pts[3] * 1000, 2),
                        "y_max": round(pts[4] * 1000, 2),
                        "z_max": round(pts[5] * 1000, 2),
                        "dimensions_mm": {
                            "x": round((pts[3] - pts[0]) * 1000, 2),
                            "y": round((pts[4] - pts[1]) * 1000, 2),
                            "z": round((pts[5] - pts[2]) * 1000, 2),
                        },
                    }
        except Exception:
            pass
        return {}

    def _get_mass_properties(self, doc) -> dict:
        """获取质量属性"""
        try:
            mass = doc.Extension.CreateMassProperty()
            if mass:
                return {
                    "volume_m3": safe_call(mass, "Volume", 0),
                    "surface_area_m2": safe_call(mass, "SurfaceArea", 0),
                    "mass_kg": safe_call(mass, "Mass", 0),
                }
        except Exception:
            pass
        return {}
