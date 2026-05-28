"""终末地适配器 — DAG 表达式自定义函数。

本模块的函数通过 ``meta.json`` 的 ``functions`` 字段自动注册到 DAG 沙箱，
可在任何 ``expr`` 节点的表达式中直接调用。

例如 DAG JSON 中的表达式节点::

    {
      "type": "expr",
      "expr": "clamp(攻击力, 0, 9999)",
      "inputs": { "攻击力": "some_node" }
    }
"""


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将 value 约束在 [min_val, max_val] 区间内。"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """线性插值: a + (b - a) * t。"""
    return a + (b - a) * t


def percent_of(value: float, total: float) -> float:
    """计算 value 占总量的比例（0-1），避免除零。"""
    if total == 0:
        return 0.0
    return value / total


def weighted_sum(values: list[float], weights: list[float]) -> float:
    """加权求和: Σ(values[i] * weights[i])。"""
    return sum(v * w for v, w in zip(values, weights))
