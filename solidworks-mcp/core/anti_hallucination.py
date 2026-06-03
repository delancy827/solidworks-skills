"""
反幻觉守卫 + 异常熔断器 — 铁律3的工程化实现

1. API 探测：不确定的 API 必须 dir() 实机探测后才能使用
2. 参数签名白名单：已知可用/不可用的 API 注册表
3. 熔断器：连续失败 N 次后自动拒绝执行
4. 禁止静默捕获：所有异常必须完整报告
"""
import time
import logging

from config.settings import (
    VERIFIED_APIS,
    UNAVAILABLE_APIS,
    CIRCUIT_BREAKER_MAX_FAILURES,
    CIRCUIT_BREAKER_COOLDOWN_SECONDS,
)

logger = logging.getLogger("solidworks-mcp")


class AntiHallucinationError(Exception):
    """反幻觉错误 — 使用了未经验证的 API"""
    pass


class CircuitBreaker:
    """
    异常熔断器。
    连续失败 N 次后自动触发熔断，拒绝执行直到冷却期结束。
    """

    def __init__(self,
                 max_failures: int = CIRCUIT_BREAKER_MAX_FAILURES,
                 cooldown: int = CIRCUIT_BREAKER_COOLDOWN_SECONDS):
        self.max_failures = max_failures
        self.cooldown = cooldown
        self.failure_count = 0
        self._tripped = False
        self._trip_time = None
        self._last_error = None

    @property
    def is_tripped(self) -> bool:
        if not self._tripped:
            return False
        if time.time() - self._trip_time > self.cooldown:
            self.reset()
            return False
        return True

    def record_failure(self, error: Exception):
        self.failure_count += 1
        self._last_error = str(error)
        logger.warning(f"熔断器记录失败 #{self.failure_count}: {error}")

        if self.failure_count >= self.max_failures:
            self._tripped = True
            self._trip_time = time.time()
            logger.critical(
                f"熔断器触发！连续失败 {self.failure_count} 次。"
                f"冷却期 {self.cooldown}s。最后错误: {self._last_error}"
            )

    def record_success(self):
        self.reset()

    def reset(self):
        self.failure_count = 0
        self._tripped = False
        self._trip_time = None
        self._last_error = None

    def get_status(self) -> dict:
        return {
            "tripped": self.is_tripped,
            "failure_count": self.failure_count,
            "max_failures": self.max_failures,
            "cooldown_seconds": self.cooldown,
            "last_error": self._last_error,
        }


class AntiHallucinationGuard:
    """
    反幻觉守卫。

    核心职责：
    1. 在调用 SW API 前验证其是否在白名单中
    2. 对不在白名单中的 API，用 dir() 实机探测
    3. 对已知不可用的 API，直接拒绝并提示替代方案
    """

    def __init__(self):
        self.breaker = CircuitBreaker()
        self._probe_cache = {}  # {(object_type, method_name): bool}

    def assert_api_exists(self, obj, method_name: str) -> None:
        """
        断言对象上存在指定方法/属性。
        铁律3.1: 任何不确定的 API，必须先实机探测。
        """
        obj_type = type(obj).__name__

        # 检查已知不可用 API
        if method_name in UNAVAILABLE_APIS:
            reason = UNAVAILABLE_APIS[method_name]
            raise AntiHallucinationError(
                f"API '{method_name}' 在 Python COM (SW 2024) 下不可用: {reason}。\n"
                f"请使用替代方案（如 FeatureExtrusion2 代替 FeatureCut）。"
            )

        # 检查白名单
        for category, apis in VERIFIED_APIS.items():
            if method_name in apis:
                return  # 白名单中，允许使用

        # 不在白名单也不在黑名单 → 实机探测
        cache_key = (obj_type, method_name)
        if cache_key in self._probe_cache:
            if not self._probe_cache[cache_key]:
                raise AntiHallucinationError(
                    f"API '{method_name}' 在 {obj_type} 上不存在（缓存结果）。"
                )
            return

        # dir() 探测
        exists = hasattr(obj, method_name)
        self._probe_cache[cache_key] = exists

        if not exists:
            available = self.probe_object(obj, method_name)
            raise AntiHallucinationError(
                f"API '{method_name}' 在 {obj_type} 上不存在。\n"
                f"包含 '{method_name}' 的可用方法: {available}"
            )

    def probe_object(self, obj, keyword: str = "") -> list:
        """
        探测对象上的可用方法/属性。
        铁律3.1 的实机探测实现。
        """
        try:
            all_members = dir(obj)
            if keyword:
                keyword_lower = keyword.lower()
                return [m for m in all_members if keyword_lower in m.lower()]
            return sorted(all_members)
        except Exception as e:
            return [f"ERROR: {e}"]

    def get_api_status(self, method_name: str) -> dict:
        """查询 API 的已知状态"""
        if method_name in UNAVAILABLE_APIS:
            return {
                "name": method_name,
                "status": "unavailable",
                "reason": UNAVAILABLE_APIS[method_name],
            }

        for category, apis in VERIFIED_APIS.items():
            if method_name in apis:
                return {
                    "name": method_name,
                    "status": "verified",
                    "category": category,
                }

        return {
            "name": method_name,
            "status": "unknown",
            "message": "未在白名单或黑名单中，需要实机 dir() 探测",
        }
