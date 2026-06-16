# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 ComputeSheet 工厂与上下文同步。

供 ``ArknightsApp`` 声明式计算页使用：创建持久化 ComputeSheet、
从干员/技能同步 DAG context、重接「计算」按钮与结果 HTML。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calc_framework.config.adapter import AdapterPackage
from calc_framework.dag.engine import DAGResult
from calc_framework.dag.service import DAGService
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import Layout, Section, load_layout_json
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QPushButton, QSlider, QSpinBox, QWidget

from games.arknights.calc.dag_adapter.loader import _get_num, _parse_potential_atk
from games.arknights.calc.inverse.stats import resolve_stats_from_segments
from utils.path_utils import get_resource_path

# DamageApp 右栏 ComputeSheet：额外加成(ATK%/伤害%) + 敌人 + 信赖/潜能（技能等级/倍率/连发仍手动）
DAMAGE_APP_SHEET_SECTION_IDS: frozenset[str] = frozenset({"enemy", "extra_bonuses"})
DAMAGE_APP_BONUS_VARS: tuple[str, ...] = (
    "user_input.攻击力百分比加成",
    "user_input.伤害加成",
)

_adapter_pkg: AdapterPackage | None = None
_adapter_layout: Layout | None = None


def ensure_arknights_adapter() -> tuple[AdapterPackage, Layout]:
    """惰性加载 DAG 适配器包与 layout.json。"""
    global _adapter_pkg, _adapter_layout
    if _adapter_pkg is None:
        adapter_dir = get_resource_path("framework/adapters/arknights")
        _adapter_pkg = AdapterPackage(str(adapter_dir))
        layout_path = adapter_dir / "ui" / "layout.json"
        _adapter_layout = load_layout_json(layout_path.read_text(encoding="utf-8"))
    assert _adapter_layout is not None
    return _adapter_pkg, _adapter_layout


def filter_layout(layout: Layout, section_ids: set[str]) -> Layout:
    """按 section id 筛选 layout（用于 DamageApp 局部 ComputeSheet）。"""
    sections = [sec for sec in layout.sections if sec.id in section_ids]
    return Layout(
        schema_version=layout.schema_version,
        name=layout.name,
        description=layout.description,
        sections=sections,
    )


def layout_for_damage_app(full_layout: Layout) -> Layout:
    """DamageApp 右栏专用 layout：额外加成 + 敌人 + 信赖/潜能（与 Web 参数组一致）。"""
    sections: list[Section] = [
        Section(
            id="extra_pct_bonus",
            title="额外加成",
            type="inputs",
            variables=list(DAMAGE_APP_BONUS_VARS),
            columns=2,
        ),
    ]
    for sec_id in ("enemy", "extra_bonuses"):
        sec = full_layout.find_section(sec_id)
        if sec is not None:
            sections.append(sec)
    return Layout(
        schema_version=full_layout.schema_version,
        name=full_layout.name,
        description=full_layout.description,
        sections=sections,
    )


# layout.json 中 user_input 变量定义（与终末地 endfield_actions 模式一致）
ARKNIGHTS_USER_VARS: dict[str, Any] = {
    "user_input.技能倍率": {
        "source": "user_input",
        "type": "float",
        "default": 1.0,
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
    },
    "user_input.技能等级": {
        "source": "user_input",
        "type": "int",
        "default": 7,
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "user_input.敌人防御": {
        "source": "user_input",
        "type": "float",
        "default": 200.0,
        "min": 0,
        "max": 10000,
        "step": 10,
    },
    "user_input.敌人法术抗性": {
        "source": "user_input",
        "type": "float",
        "default": 50.0,
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "user_input.攻击力百分比加成": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": -100,
        "max": 200,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
    "user_input.伤害加成": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": -100,
        "max": 200,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
    "user_input.物理穿透": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 3000,
        "step": 10,
    },
    "user_input.法术穿透": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 1.0,
        "step": 0.01,
    },
    "user_input.信赖攻击": {
        "source": "user_input",
        "type": "float",
        "default": 0,
        "min": 0,
        "max": 500,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
    "user_input.潜能攻击": {
        "source": "user_input",
        "type": "float",
        "default": 0,
        "min": 0,
        "max": 500,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
}

ARKNIGHTS_USER_CONTEXT_OVERRIDES: dict[str, tuple[str, list[str]]] = {
    "user_input.技能倍率": ("computed.技能倍率", ["override"]),
    "user_input.技能等级": ("computed.技能等级", ["override"]),
    "user_input.敌人防御": ("enemy.防御", ["override"]),
    "user_input.敌人法术抗性": ("enemy.法术抗性", ["override"]),
    "user_input.攻击力百分比加成": ("computed.攻击力百分比加成", ["override"]),
    "user_input.伤害加成": ("computed.伤害加成", ["override"]),
    "user_input.物理穿透": ("computed.物理穿透", ["override"]),
    "user_input.法术穿透": ("computed.法术穿透", ["override"]),
    "user_input.信赖攻击": ("character.信赖攻击", ["override"]),
    "user_input.潜能攻击": ("character.潜能攻击", ["override"]),
}


def combo_index_to_skill_index(combo_index: int) -> int:
    """技能下拉索引 → ``get_parsed_skill_info`` 的 skill_index（0=普攻时为 -1）。"""
    return combo_index - 1 if combo_index > 0 else -1


def create_arknights_compute_sheet(
    dag_service: DAGService,
    layout: Layout,
    *,
    parent: QWidget | None = None,
) -> ComputeSheet:
    """创建带明日方舟 user_input 映射的 ComputeSheet。"""
    variables = dict(dag_service.dag.variables)
    variables.update(ARKNIGHTS_USER_VARS)
    return ComputeSheet(
        dag_service,
        layout,
        variables,
        base_context={},
        user_context_overrides=ARKNIGHTS_USER_CONTEXT_OVERRIDES,
        parent=parent,
    )


def set_user_input_value(sheet: ComputeSheet, path: str, value: Any) -> None:
    """将 user_input 控件设为指定值（干员切换时同步信赖/潜能等）。"""
    entry = sheet._input_widgets.get(path)
    if entry is None:
        return
    widget, spec = entry
    if isinstance(widget, QDoubleSpinBox):
        widget.setValue(float(value))
    elif isinstance(widget, QSpinBox):
        widget.setValue(int(value))
    elif isinstance(widget, QSlider):
        if spec.step < 1:
            widget.setValue(int(float(value) * 100))
        else:
            widget.setValue(int(value))
    elif isinstance(widget, QCheckBox):
        widget.setChecked(bool(value))
    elif isinstance(widget, QComboBox):
        idx = widget.findText(str(value))
        if idx >= 0:
            widget.setCurrentIndex(idx)


def populate_operator_context(
    sheet: ComputeSheet,
    operator: dict[str, Any],
    *,
    skill_multiplier: float,
    skill_level: int,
) -> None:
    """从干员数据与当前技能写入 DAG context，并同步 sheet 输入控件。"""
    base_stats = operator.get("基础属性", {})
    trust_bonus = operator.get("信赖加成", {})
    seg_stats = resolve_stats_from_segments(operator, elite=2, level=None)
    base_atk = float(seg_stats["atk"]) if "atk" in seg_stats else _get_num(base_stats, "atk")
    trust_atk = _get_num(trust_bonus, "攻击", 0.0)
    pot_atk = _parse_potential_atk(operator.get("潜能", []))

    sheet.set("character.攻击力", base_atk)
    sheet.set("character.信赖攻击", trust_atk)
    sheet.set("character.潜能攻击", pot_atk)
    sheet.set("computed.技能倍率", skill_multiplier)
    sheet.set("computed.技能等级", skill_level)

    set_user_input_value(sheet, "user_input.技能倍率", skill_multiplier)
    set_user_input_value(sheet, "user_input.技能等级", skill_level)
    set_user_input_value(sheet, "user_input.信赖攻击", trust_atk)
    set_user_input_value(sheet, "user_input.潜能攻击", pot_atk)


def merge_atk_percent_bonus(user_pct: float, atk_buff_hint: float) -> float:
    """合并用户 ATK% 与技能解析 buff，与 Web ``handleCompute`` 一致（百分点制）。"""
    return user_pct + atk_buff_hint * 100.0


def read_compute_params_from_sheet(sheet: ComputeSheet) -> dict[str, float]:
    """从 ComputeSheet 读取全部 DAG 计算参数（与 Web computeParams 字段对齐）。"""
    raw = sheet.read_user_inputs()
    return {
        "atk_percent_bonus": float(raw.get("user_input.攻击力百分比加成", 0.0)),
        "dmg_bonus": float(raw.get("user_input.伤害加成", 0.0)),
        "enemy_def": float(raw.get("user_input.敌人防御", 200.0)),
        "enemy_res": float(raw.get("user_input.敌人法术抗性", 50.0)),
        "def_penetration": float(raw.get("user_input.物理穿透", 0.0)),
        "res_penetration": float(raw.get("user_input.法术穿透", 0.0)),
        "trust_atk": float(raw.get("user_input.信赖攻击", 0.0)),
        "pot_atk": float(raw.get("user_input.潜能攻击", 0.0)),
    }


def read_enemy_bonus_params(sheet: ComputeSheet) -> dict[str, float]:
    """从 ComputeSheet 读取敌人参数与信赖/潜能覆盖值（兼容旧调用）。"""
    p = read_compute_params_from_sheet(sheet)
    return {
        "enemy_def": p["enemy_def"],
        "enemy_res": p["enemy_res"],
        "def_penetration": p["def_penetration"],
        "res_penetration": p["res_penetration"],
        "trust_atk": p["trust_atk"],
        "pot_atk": p["pot_atk"],
    }


def hide_sheet_eval_button(sheet: ComputeSheet) -> None:
    """隐藏 ComputeSheet 内置「计算」按钮（DamageApp 使用外部「开始计算」）。"""
    for btn in sheet.widget.findChildren(QPushButton):
        if btn.text() == "计算":
            btn.hide()
            return


def wire_compute_button(sheet: ComputeSheet, callback: Callable[[], None]) -> None:
    """将 ComputeSheet 内置「计算」按钮重接到自定义求值流程。"""
    for btn in sheet.widget.findChildren(QPushButton):
        if btn.text() == "计算":
            try:
                btn.clicked.disconnect(sheet.evaluate)
            except RuntimeError:
                pass
            btn.clicked.connect(callback)
            return


def build_result_html(result: DAGResult | Any) -> str:
    """将 DAG 输出格式化为简要 HTML 表格。"""
    outputs = result.outputs if hasattr(result, "outputs") else {}
    lines = ['<hr><table style="width:100%;border-collapse:collapse;">']
    lines.append(
        '<tr style="background:#2B6CB6;color:white;">'
        '<td colspan="2" style="padding:6px 10px;font-weight:bold;font-size:15px;">'
        "计算结果</td></tr>"
    )
    for name in ("最终攻击力", "物理伤害", "法术伤害", "真伤伤害"):
        val = outputs.get(name)
        if val is not None:
            lines.append(
                f'<tr><td style="padding:3px 10px;">{name}</td>'
                f'<td style="padding:3px 10px;text-align:right;font-weight:bold;">'
                f"{float(val):.2f}</td></tr>"
            )
    lines.append("</table>")
    return "\n".join(lines)


def mount_compute_sheet(
    container: QWidget,
    sheet: ComputeSheet,
    *,
    extra_widgets: list[QWidget] | None = None,
) -> None:
    """将 ComputeSheet 挂载到右侧容器（仅首次或替换布局时使用）。"""
    from PySide6.QtWidgets import QVBoxLayout

    old_layout = container.layout()
    if old_layout is not None:
        while old_layout.count():
            item = old_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        old_layout.deleteLater()

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(sheet.widget, stretch=1)
    for w in extra_widgets or []:
        layout.addWidget(w)
    container.setLayout(layout)
