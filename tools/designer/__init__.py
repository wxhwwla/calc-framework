"""开发者工具 — 生成 .calcpack 配置包的独立 GUI。

入口：``python -m tools.designer``

功能：
- 数据录入（四层标准 schema，调用 ``tools.data_pipeline``）
- 布局编辑（QGraphicsView 画布 + 网格吸附 + 碰撞检测）
- 主题编辑（字体/色板）
- 导出 .calcpack（ZIP 包）
"""
