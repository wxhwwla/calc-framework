# wiki_scout — 模块化 Wiki 数据采集

所有 provider 共用 `Fetcher`（标准库 `urllib`、SHA1 磁盘缓存、限速与重试），
`fetch` 只负责抓原始响应，`parse` 只做离线解析，因此：

- 测试可以用离线夹具直接验证 `parse`，不发网络请求；
- 抓取一次后可反复调整解析逻辑（`python -m tools.wiki_scout parse <provider>`）。

## 命令（在 `[根]` 执行）

```powershell
python -m tools.wiki_scout list
python -m tools.wiki_scout run all
python -m tools.wiki_scout run warfarin --limit 5
python -m tools.wiki_scout run wjdlglr
python -m tools.wiki_scout fetch wjdlglr --refresh
python -m tools.wiki_scout parse wjdlglr
```

产物：`tools/wiki_scout/output/<provider>/raw.json`（原始响应）与
`<provider>.json`（标准化数据），目录已被 `.gitignore` 忽略。

单个条目抓取失败不会中断整体运行：失败条目记录在原始数据的 `errors` 中，
解析结果的 `抓取失败` 字段会原样带出，便于下次单独补抓。华法琳 API 偶发
SSL 握手超时属正常现象，重跑同一命令即可凭缓存续抓缺失条目。

## 新增数据源（3 步）

1. 在 `providers/` 下新建模块，继承 `BaseProvider` 并注册：

```python
@register_provider
class ExampleProvider(BaseProvider):
    name = "example"
    description = "示例 Wiki — 角色/武器"

    def fetch(self, fetcher, *, limit=None, refresh=False) -> dict:
        return {"pages": [...]}  # 只抓数据，不解析

    def parse(self, raw: dict) -> dict:
        return {"游戏": "...", "角色": [...]}  # 纯函数，离线可测
```

2. 在 `providers/__init__.py` 导入该类（触发注册）。
3. 在 `tools/tests/` 放离线夹具并添加 `test_wiki_scout_<name>.py`：
   `python -m pytest tools/tests -q -k wiki_scout`。

## 字段口径

### warfarin（明日方舟：终末地）

- 来源：`https://api.warfarin.wiki/v1/cn/`（`operators` / `weapons` / `gear`）。
- 干员：1–90 级 力量/敏捷/智识/意志/基础攻击力/基础防御力；
  战技/连携技/终结技倍率（`atk_scale*` ×100）与段伤害类型。
- 武器：基础攻击力曲线（1–最大等级）、普通技能/特殊技能成长。
- 装备：基础属性与属性词条。
- 列表响应包裹在 `data` 字段；`_as_list` 负责展开。

### wjdlglr（无尽的拉格朗日）

- 来源：`Category:舰船` 页面 wikitext（类型/稀有度/所属/站位/指挥值）
  + `MediaWiki:EnhTreeData1..8.js`（官方全量配置，`window.__ETW_DATA`）。
- 舰船：`ship.base.hp` 血量、`resist` 物理护甲、`resist_energy` 能量护甲、
  `shield` 护盾值。
- 武器：`atk` 单发伤害；攻击次数 = `at`（工作次数）× `rep`（弹药数）；
  `cd` 冷却、`dur` 持续时间、`lock` 锁定、`iv` 攻击间隔，单位毫秒；
  `hits` → `[{优先级, 目标, 命中率}]`。
- **`fa` = 去程、`fb` = 回程**（Wiki 渲染器标注相反，已用 AT021 /
  维塔斯A021 / BR050 页面数据交叉验证）。
- 少数页面没有 `data-ship` 组件，解析时退化为「页面标题 == 配置名称」精确匹配；
  仍无法匹配的页面写入 `未匹配页面`，不会静默丢弃。

## 测试

```powershell
python -m pytest tools/tests -q -k wiki_scout
```

正式验证仍以 `act` 在 Docker 中运行的 CI 为准（见 `docs/操作指令集.md`）。
