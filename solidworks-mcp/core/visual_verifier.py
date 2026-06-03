"""
多角度截图验证器 — 解决 AI 幻觉问题

基于 visual_qa_capture.py 重构，修正了 View ID 映射：
- 旧版(错误): Top=5, Right=4
- 新版(正确): Top=3, Right=5

工作流:
1. ShowNamedView2 切换视角（中文失败回退英文）
2. ViewZoomtofit2 缩放适配
3. SaveAs3 保存 BMP
4. 读取 → base64 编码 → 返回 MCP Image 对象
"""
import os
import base64
import time

from config.settings import (
    VIEW_MAP,
    VIEW_ENGLISH_MAP,
    DEFAULT_VIEWS,
    SCREENSHOT_DIR,
    SCREENSHOT_WAIT_SECONDS,
)
from core.sw_connection import safe_call


class VisualVerifier:
    """多角度截图验证器"""

    def __init__(self, connection_manager):
        self.conn = connection_manager
        self._ensure_dir(SCREENSHOT_DIR)

    def capture_views(self, doc, views: list = None,
                      output_dir: str = None) -> list:
        """
        截取多视图并返回图片信息列表。

        Args:
            doc: SW ModelDoc2 对象
            views: 视图列表，如 ["iso", "front", "top", "right"]
            output_dir: 截图保存目录

        Returns:
            [{"view": "iso", "path": "...", "base64": "...", "mime": "image/bmp"}, ...]
        """
        if views is None:
            views = list(DEFAULT_VIEWS)
        if output_dir is None:
            output_dir = SCREENSHOT_DIR
        self._ensure_dir(output_dir)

        results = []
        for view_key in views:
            view_info = VIEW_MAP.get(view_key)
            if view_info is None:
                results.append({
                    "view": view_key,
                    "success": False,
                    "error": f"未知视图: {view_key}",
                })
                continue

            view_name, view_id = view_info
            bmp_path = os.path.join(output_dir, f"verify_{view_key}.bmp")

            try:
                # 1. 切换视图
                self._switch_view(doc, view_name, view_id)

                # 2. 缩放适配
                self._zoom_to_fit(doc)

                # 3. 等待渲染
                time.sleep(SCREENSHOT_WAIT_SECONDS)

                # 4. 保存截图
                success = self._save_screenshot(doc, bmp_path)

                if success and os.path.exists(bmp_path):
                    # 5. 读取并 base64 编码
                    with open(bmp_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode("ascii")
                    file_size = os.path.getsize(bmp_path)
                    results.append({
                        "view": view_key,
                        "path": bmp_path,
                        "base64": img_data,
                        "mime": "image/bmp",
                        "size_bytes": file_size,
                        "success": True,
                    })
                else:
                    results.append({
                        "view": view_key,
                        "path": bmp_path,
                        "success": False,
                        "error": "截图保存失败",
                    })
            except Exception as e:
                results.append({
                    "view": view_key,
                    "path": bmp_path,
                    "success": False,
                    "error": str(e),
                })

        # 恢复等轴测视图
        try:
            iso_name, iso_id = VIEW_MAP["iso"]
            self._switch_view(doc, iso_name, iso_id)
            self._zoom_to_fit(doc)
        except Exception:
            pass

        return results

    def capture_single_view(self, doc, view_key: str = "iso",
                            output_dir: str = None) -> dict:
        """截取单视图"""
        results = self.capture_views(doc, [view_key], output_dir)
        return results[0] if results else {"success": False, "error": "截图失败"}

    def capture_and_verify(self, doc, expected_description: str = "",
                           war_validator=None) -> dict:
        """
        综合验证：截图 + 特征树 + 实体数 + 包围盒。
        一次调用获取全部验证信息，供 AI 自我判断。
        """
        # 1. 截图
        screenshots = self.capture_views(doc, DEFAULT_VIEWS)

        # 2. 特征树
        feature_tree = self._get_feature_tree(doc)

        # 3. 实体数
        body_count = self._get_body_count(doc)

        # 4. 包围盒
        bounding_box = self._get_bounding_box(doc)

        # 5. 重建验证
        rebuild_ok = False
        try:
            result = doc.EditRebuild3
            rebuild_ok = result is True or result is None or result == 0
        except Exception:
            try:
                doc.ForceRebuild3(False)
                rebuild_ok = True
            except Exception:
                pass

        # 6. 特征数
        feature_count = safe_call(doc, "GetFeatureCount", 0)
        if callable(feature_count):
            feature_count = 0

        return {
            "screenshots": screenshots,
            "expected": expected_description,
            "feature_tree": feature_tree,
            "feature_count": feature_count,
            "body_count": body_count,
            "bounding_box": bounding_box,
            "rebuild_ok": rebuild_ok,
            "screenshot_count": sum(1 for s in screenshots if s.get("success")),
        }

    # ─── 内部方法 ───

    def _switch_view(self, doc, view_name: str, view_id: int) -> bool:
        """切换视图，中文失败则回退英文"""
        # 尝试中文名
        try:
            doc.ShowNamedView2(view_name, view_id)
            return True
        except Exception:
            pass

        # 回退英文名
        eng_name = VIEW_ENGLISH_MAP.get(view_id, "*Isometric")
        try:
            doc.ShowNamedView2(eng_name, view_id)
            return True
        except Exception:
            pass

        return False

    def _zoom_to_fit(self, doc) -> None:
        """缩放适配，多版本 API 回退"""
        for method in ["ViewZoomtofit2", "ViewZoomToFit", "ViewZoomtofit"]:
            try:
                getattr(doc, method)()
                return
            except Exception:
                continue

    def _save_screenshot(self, doc, save_path: str) -> bool:
        """保存截图，多方法回退"""
        # 方法1: SaveAs3
        try:
            result = doc.SaveAs3(save_path, 0, 2)
            if os.path.exists(save_path):
                return True
        except Exception:
            pass

        # 方法2: SaveAs
        try:
            doc.SaveAs(save_path)
            if os.path.exists(save_path):
                return True
        except Exception:
            pass

        # 方法3: SaveAs2
        try:
            doc.SaveAs2(save_path, 0)
            if os.path.exists(save_path):
                return True
        except Exception:
            pass

        return False

    def _get_feature_tree(self, doc) -> list:
        """遍历特征树"""
        features = []
        try:
            feat = doc.FirstFeature
            if feat is None:
                feat = doc.FirstFeature()
            count = 0
            while feat is not None and count < 200:
                name = safe_call(feat, "Name", "")
                type_name = ""
                try:
                    tn = feat.GetTypeName2
                    type_name = tn() if callable(tn) else tn
                except Exception:
                    pass
                features.append({"name": name, "type": type_name})
                feat = feat.GetNextFeature()
                count += 1
        except Exception:
            pass
        return features

    def _get_body_count(self, doc) -> int:
        try:
            bodies = doc.GetBodies2(0, False)
            return len(bodies) if bodies else 0
        except Exception:
            return -1

    def _get_bounding_box(self, doc) -> dict:
        try:
            bbox = doc.Extension.CreateBoundingBox()
            if bbox:
                pts = bbox.GetExtremePoints()
                if pts and len(pts) >= 6:
                    return {
                        "x_mm": round((pts[3] - pts[0]) * 1000, 2),
                        "y_mm": round((pts[4] - pts[1]) * 1000, 2),
                        "z_mm": round((pts[5] - pts[2]) * 1000, 2),
                    }
        except Exception:
            pass
        return {}

    @staticmethod
    def _ensure_dir(path: str):
        if path and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
