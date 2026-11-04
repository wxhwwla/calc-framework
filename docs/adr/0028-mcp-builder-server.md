# ADR-0028：MCP 计算器构建服务器

- 状态：已接受
- 日期：2026-11-03
- 相关：ADR-0006（CalcPack 与设计器）、ADR-0023（标准游戏包架构）

## 背景

开发者克隆本仓库后，希望让宿主 AI（Claude Code / Cursor 等）直接调用框架现有的生成器、脚手架、校验和打包能力，复刻一个与本项目类似的游戏计算器。现有构建链全部是纯 Python，但缺少一个供 AI 使用的稳定接口。

## 决策

1. 新增仓库级 MCP 服务器 `tools/calc_mcp/`，通过 stdio 启动：

   ```powershell
   pip install -r requirements-mcp.txt
   python -m tools.calc_mcp --project-dir .
   ```

2. **包名使用 `tools.calc_mcp` 而不是 `tools.mcp`**。本仓库的测试 `conftest.py` 会把 `tools/` 加入 `sys.path`，若子目录名为 `mcp`，会遮蔽官方 `mcp` SDK 的顶层包，导致 `import mcp` 解析到本仓库目录。改名后彻底消除冲突。

3. 首版只提供 **13 个确定性工具**，不调用任何 LLM：

   | 分类 | 工具 |
   |---|---|
   | 发现 | `list_templates`、`describe_schemas`、`read_guide`、`list_adapters` |
   | 文件 | `list_adapter_files`、`read_adapter_file`、`write_adapter_file` |
   | 构建 | `scaffold_adapter`、`generate_adapter` |
   | 验证 | `validate_adapter`、`smoke_test_adapter` |
   | 打包 | `export_calcpack`、`import_calcpack` |

4. 所有文件操作限制在 `--project-dir` 内：拒绝绝对路径、`..`、反斜杠、NUL 与越界符号链接；`adapter_id` 仅允许 `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`；写入默认不覆盖。

5. `tools/calc_mcp/**` 及其依赖链必须保持 **PySide6-free**，由 `tools/quality/check_pyside6_coupling.py` 的 `DECOUPLED_DIRS` 守护。为此把脚手架逻辑从 `calc_framework.dev_toolkit.adapter_creator` 迁移到 `calc_framework.config.scaffold`，原模块保留 re-export shim。

6. 输出物为 **适配器包 + `.calcpack`**；首版不生成完整 GUI 工程、搜索枚举或生存分析。

## 备选方案

- **pip 包分发**：需要把生成器/导出器拆成独立包，成本高；仓库体积仅约 10 MB，克隆成本低，暂不做。
- **HTTP/SSE 传输**：首版面向本地开发者，stdio 无鉴权面，部署最简单；远程场景后再评估。
- **MCP 内调用 LLM**：现有 `/api/generator/ai/parse` 的 JSON 提取不稳定；自然语言理解交给宿主 AI，MCP 只做确定性操作。

## 后果

- 新增依赖文件 `requirements-mcp.txt`（`mcp>=1.2,<2`），CI 的 lint/test/typecheck/pip-audit 均已接入。
- `smoke_test_adapter` 会执行适配包内的 `functions.py`，仅可用于开发者自己的本地适配包；工具描述和文档均明确提示。
- 生成器只支持 `+ - * /`、`condition`、`expr` 六种步骤；复杂公式（`unary`/`call`/子图）通过 `scaffold_adapter` 提交完整 DAG。
- `tools/` 目录达到 20 个直接子项硬顶，后续扩展需先整理目录。

## 修订 2026-11-04：三项能力增强

实测生成「无尽的拉格朗日」计算器后（见 `docs/会话接续手册.md` §4.248 缺口 ①②④），在不改变工具数量与 `.calcpack` 格式的前提下增强：

1. **`expr` 沙箱支持控制流**：新增比较 `< <= > >= == !=`、布尔 `and/or/not`（短路、返回操作数）与三元 `a if cond else b`（只求值选中分支，死分支仍做静态白名单校验）；链式比较左值只求一次。`in` / `not in` / `is` / `is not`、属性访问、lambda、容器字面量继续拒绝。护甲减免、分档公式不再必须写 `functions.py`。
2. **未绑定实体源变量自动转为可编辑输入**：`generate_adapter` 把未出现在 `data_files` 中（或对应列表为空）的 `character` / `weapon` / `equipment` / `enemy` 变量改写为 `user_input.<name>`，layout 按**原始 source** 分组（输入/角色/武器/装备/目标参数）；`computed` 不重映射；`source="input"` 别名归一为 `user_input`。UI 层零改动。
3. **`generate_adapter.data_files`**：按 `character` / `weapon` / `equipment` / `enemy` 键接收记录数组，写入 `data/characters.json` / `weapons.json` / `equipments.json` / `enemies.json`；记录须含非空 `名称`、同文件不重复、≤512 KiB（UTF-8 字节）；非空路径写入 `meta.entry_data`。仅**非空记录列表**视为绑定：绑定来源的变量保留命名空间，由 CalcPackViewer 实体下拉注入，不出现在输入区；空列表按未绑定处理并在 warnings 中提示。查看器补齐 `enemy` 映射（标签「敌人」），脚手架数据文件名由 `enemys.json` 修正为 `enemies.json` 且不再生成 `computeds.json`。

**未采纳**：`.calcpack` 携带并执行 `functions.py`——包内 Python 无签名/信任机制，等同任意代码执行；若将来需要，先单独立 ADR 定义信任边界。

**兼容性**：显式按 `enemy.*` 等命名空间传 context 的旧调用方会因变量重映射而失配；`validate_adapter` 对已绑定来源变量缺失 layout 的提示属预期噪音。

## 修订 2026-11-05：实体级联、明细面板与条件禁用

1. **`meta.entity_selectors`**：查看器可把单个实体下拉改为多级级联（如 舰船种类 → 舰船 → 武器），`generate_adapter.entity_selectors` 负责声明；末级 `field` 必须为 `名称`，其值注入 DAG 命名空间，`display_field` 仅改变显示文本。适配器数据记录无数值列表字段时查看器自动隐藏等级输入。
2. **`meta.entity_detail`**：在查看器最左列渲染当前实体字段明细；`source` 须已绑定非空 `data_files`，`sections[].columns` 限 1–3，`fields[].field` 须存在于记录中，可选 `format` 为 Python 数值格式串。`generate_adapter.entity_detail` 原样写入 meta，校验失败返回 `ENTITY_DETAIL_INVALID`。
3. **`meta.entity_input_rules`**：按实体字段值禁用无关输入（如不需要母舰时灰显母舰加成）。`disable` 只能引用 `user_input.*` 变量；实体记录缺字段或值不匹配时规则不命中，输入保持可编辑。`generate_adapter.entity_input_rules` 原样写入 meta，校验失败返回 `INPUT_RULE_INVALID`。
4. **查看器布局**：右栏增加包说明与操作提示；`entity_detail` 与禁用规则在加载及每次级联切换后重新应用。

**兼容性**：三者均为可选 meta 键，旧适配包与旧 `.calcpack` 不受影响；工具数量仍为 13，`.calcpack` 格式不变。
