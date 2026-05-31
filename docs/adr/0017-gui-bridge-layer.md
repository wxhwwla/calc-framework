# ADR-0017：GUI 桥接层 — 消除三角依赖

## 状态

已批准

## 背景

`games/endfield/gui_design/`（GUI 层）存在三角依赖：

```
calc_framework (框架)
    ↙ 直接导入         ↘ 通过适配器导入
 GUI 层 ───────────────→ calc_engine.endfield (游戏计算引擎)
```

GUI 同时依赖 `calc_framework.*` 和 `calc_engine.endfield.*`。如果框架 API 变化，GUI 需同时适配两端。

当前直接依赖清单：

| 框架模块 | GUI 使用者 |
|---------|-----------|
| `calc_framework.logging.setup_logging` | `main.py` |
| `calc_framework.logging.get_logger` | `qt_app.py`, `ocr/__init__.py` |
| `calc_framework.config.adapter.AdapterPackage` | `qt_app.py` |
| `calc_framework.ui.compute_sheet.ComputeSheet` | `qt_app.py`, `qt_app_confirm_mixin.py` |
| `calc_framework.ui.layout.load_layout_json` | `qt_app.py` |

## 决策

在 `games/endfield/` 创建桥接模块 `framework_bridge.py`，集中代理所有框架依赖。GUI 层只从桥接模块导入，不再直接引用 `calc_framework`。

## 影响范围

| 文件 | 改动 |
|------|------|
| 新增 `games/endfield/framework_bridge.py` | 代理 logging / adapter / layout / compute_sheet |
| 修改 `games/endfield/main.py` | logging 导入 → 桥接 |
| 修改 `games/endfield/gui_design/shell/qt_app.py` | 4 处导入 → 桥接 |
| 修改 `games/endfield/gui_design/shell/qt_app_confirm_mixin.py` | ComputeSheet 导入 → 桥接 |
| 修改 `games/endfield/gui_design/controls/ocr/__init__.py` | get_logger 导入 → 桥接 |

## 实施步骤

### 1. 创建桥接层
```python
# games/endfield/framework_bridge.py
from calc_framework.logging import get_logger, setup_logging
from calc_framework.config.adapter import AdapterPackage
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json
```

### 2. GUI 层导入替换
所有 `from calc_framework.xxx import yyy` → `from games.endfield.framework_bridge import yyy`

### 3. 测试验证
`pytest calc_engine/endfield/tests/` + `pytest framework/tests/` 全部通过

## 风险

| 风险 | 级别 | 缓解 |
|------|------|------|
| 循环导入（桥接层导入 GUI） | 低 | 桥接层只向框架方向导入 |
| 框架 API 变化通知不足 | 低 | 桥接层是唯一的框架依赖点 |

## 替代方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| A：不改变 | 零工作 | 三角依赖持续存在 |
| B：桥接层（选定） | 单一依赖点，低成本 | 多一层导入 |
| C：calc_engine 代理所有框架依赖 | 更彻底的解耦 | 侵入性高，框架 UI 组件不适合放在引擎中 |
