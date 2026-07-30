# Web / 桌面功能对称清单

> **目的**：明确哪些不对称是"有意为之"（技术限制），哪些是"待补的"（应补齐）。
> **最后更新**：2026-07-30（账本纠偏：统计表与正文状态对齐）

---

## 核心计算功能

| 功能 | 桌面 (PySide6) | Web (React+FastAPI) | 对称？ | 备注 |
|------|:---:|:---:|:---:|------|
| 终末地伤害计算 | ✅ | ✅ | ✅ | 完全对齐 |
| 明日方舟计算 | ✅ | ✅ | ✅ | 完全对齐 |
| 15 乘区 DAG 求值 | ✅ | ✅ | ✅ | 同一引擎 |
| 角色/武器/装备选择 | ✅ | ✅ | ✅ | |
| 技能等级调整 | ✅ | ✅ | ✅ | |
| 敌方参数面板 | ✅ | ✅ | ✅ | |
| 暴击/异常微调 | ✅ | ✅ | ✅ | |
| 伤害可视化（图表） | ✅ matplotlib | ✅ ECharts | ✅ | 不同库，同效果 |
| 搜索最优配装 | ✅ | ✅ SSE 流式 | ✅ | Web 体验更好 |

---

## 数据相关功能

| 功能 | 桌面 (PySide6) | Web (React+FastAPI) | 对称？ | 备注 |
|------|:---:|:---:|:---:|------|
| 数据浏览 | ✅ DataEditorPanel | ✅ ProfileDataBrowser | ✅ | Web 有搜索/分页，更优 |
| 数据 CRUD | ❌ 仅整体保存 | ✅ 行级 CRUD | ⚠️ 不对称 | Web 更强 |
| 数据验证 (schema check) | ✅ | ✅ POST /api/data/validate | ✅ | |
| DAG 验证（选中角色→跑 DAG） | ✅ | ✅ DagVerifyDialog | ✅ | |
| 公式反推 (inverse) | ✅ | ✅ InverseTab | ✅ | |
| JSON 导入 | ✅ 文件选择器 | 🟡 FileReader 可选增强 | 🟡 可选 | 非阻塞 |
| 数据 details 面板 | ✅ 键值对+技能树 | ✅ 展开行 | ✅ | |

---

## DAG 编辑器

| 功能 | 桌面 (PySide6) | Web (React+FastAPI) | 对称？ | 备注 |
|------|:---:|:---:|:---:|------|
| 可视化 DAG 编辑 | ✅ QGraphicsView | ✅ ReactFlow | ✅ | |
| 拖拽节点 | ✅ | ✅ | ✅ | |
| 连线编辑 | ✅ | ✅ | ✅ | |
| 复合节点/子图 | ✅ | ✅ call 节点 + 参数绑定 | ✅ | |
| 网格吸附 | ✅ | ❌ | 🟢 低优 / 有意 | 体验差异可接受 |
| 节点属性面板 | ✅ | ✅ | ✅ | |

---

## 配置包设计器 (CalcPack)

| 功能 | 桌面 (PySide6) | Web (React+FastAPI) | 对称？ | 备注 |
|------|:---:|:---:|:---:|------|
| 数据录入 | ✅ DataEditorPanel | ✅ PackDataTab | ✅ | |
| 布局编辑 | ✅ LayoutCanvasPanel | ✅ PackLayoutTab | ✅ | |
| 主题编辑 | ✅ ThemePanel | ✅ ThemeExportTab | ✅ | |
| 导出 .calcpack | ✅ exporter.py | ✅ POST /api/pack/export | ✅ | |
| 资产图片打包 | ✅ 解析 layout→收集图片 | ✅ POST /api/pack/export (asset_files) | ✅ | 2026-06-14 补上 |
| 三页签数据共享 | ✅ 信号/槽 | ✅ 自动加载 | ✅ | |

---

## 扩展功能

| 功能 | 桌面 (PySide6) | Web (React+FastAPI) | 对称？ | 备注 |
|------|:---:|:---:|:---:|------|
| OCR 截图导入 | ✅ 完整管线 | ❌ | ⚠️ 有意 | 浏览器限制，不补 |
| 插件管理器 | ✅ | ✅ PluginManagerDialog + /api/plugins | ✅ | 2026-06-14 补上 |
| Calc Hub 市场 | ❌ | ✅ MarketplacePage | ⚠️ 有意 | 天然 Web |
| AI 生成器 | ❌ | ✅ GeneratorPage | ⚠️ 有意 | 天然 Web |
| 数据贡献表单 | ❌ | ✅ DataContributePage | ⚠️ 有意 | 天然 Web |
| 批量对比 | ✅ BatchCompareDialog | ✅ BatchCompareDialog | ✅ | 两端均已完整 |
| 生存估计 | ✅ SurvivalEstimateDialog | ✅ SurvivalEstimateDialog | ✅ | 两端均已完整 |
| PWA 离线支持 | ❌ | ✅ | ⚠️ 有意 | 天然 Web |

---

## 工程化

| 功能 | 桌面 (PySide6) | Web (React+FastAPI) | 对称？ | 备注 |
|------|:---:|:---:|:---:|------|
| i18n 多语言 | 🟡 UI 控件字面量已 `tr()` | ✅ ~500 键 | 🟡 | Desktop 对话框等次要文案可继续 |
| 多主题 | ✅ 3 主题 | ❌ | 🟢 低优 / 有意 | |
| 自动更新 | ✅ | ❌ 不适用 | ⚠️ 有意 | |
| Docker 部署 | ❌ | ✅ | ⚠️ 有意 | |

---

## 统计

| 分类 | 总数 | 已对齐 | 有意不对称 | 开放/可选 |
|------|:---:|:---:|:---:|:---:|
| 核心计算 | 9 | 9 | 0 | 0 |
| 数据相关 | 7 | 5 | 0 | 2（Web 更强 CRUD 算优势；JSON 导入可选） |
| DAG 编辑器 | 6 | 5 | 1（网格吸附） | 0 |
| 配置包设计器 | 6 | 6 | 0 | 0 |
| 扩展功能 | 8 | 3 | 5 | 0 |
| 工程化 | 5 | 0 | 3 | 2（Desktop i18n / Web 多主题） |
| **合计** | **41** | **28** | **9** | **4** |

> 说明：核心玩家路径（计算/搜索/打包）已对称；剩余主要是 Desktop i18n 收尾与有意平台差异（OCR/Hub/PWA 等）。

---

## 待补项优先级

| 优先级 | 功能 | 工作量 | 状态 |
|:------:|------|:------:|:----:|
| 🔴 P0 | 桌面 i18n 硬编码收尾 | 持续 | 🟡 开放 |
| 🟡 P1 | Web 端批量对比组件 | — | ✅ 已有 |
| 🟡 P1 | Web 端数据验证 API（schema check） | — | ✅ |
| 🟡 P2 | Web 端复合节点/子图编辑 | — | ✅ |
| 🟢 P3 | Web 端资产图片打包 | — | ✅ |
| 🟢 P3 | Web 端数据详情面板 | — | ✅ |
| 🟢 P3 | Web 端生存估计 UI | — | ✅ |
| 🟢 P3 | Web 端插件管理器 | — | ✅ |
