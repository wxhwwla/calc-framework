"""FPS 适配器 — DAG 表达式自定义函数。"""


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def le(a: float, b: float) -> float:
    """小于等于比较，返回 1.0 或 0.0。"""
    return 1.0 if a <= b else 0.0


def ge(a: float, b: float) -> float:
    """大于等于比较，返回 1.0 或 0.0。"""
    return 1.0 if a >= b else 0.0
