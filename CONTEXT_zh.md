# Calc Framework — 领域上下文

> 本文件定义项目内统一术语，供 Issue、测试与文档引用。
>
> [:us: English](CONTEXT.md)

---

## 核心对象

| 术语 | 含义 |
|------|------|
| **角色** | `characters.json` 中的一条记录，含类型、星级、等级曲线、四维属性（力量/敏捷/智识/意志）、基础攻击力、基础生命值、基础防御力、战技/连携/终结技倍率等 |
| **武器** | `weapons.json` 中的一条记录，含 `基础攻击力` 曲线、`normal_skills`（普通技能词条）与 `special_skills`（特殊技能词条） |
| **装备** | `equipments.json` 中的一条记录；部位为 **护甲 / 护手 / 配件** |
| **等级曲线** | 与角色/武器等级列表等长的数值数组（通常 90 级），由 JSON 预存，运行时直接读取 |
| **潜能** | 武器精炼等级序列（`talent`，0–5），不是角色天赋 |

## 属性与计算

| 术语 | 含义 |
|------|------|
| **主能力 / 副能力** | 角色四维（力量、敏捷、智识、意志）中的主、副属性名称 |
| **信赖** | 角色信赖加成，影响能力乘区 |
| **乘区** | 乘法区链：能力乘区、能力值加成、最终攻击力等 |
| **15乘区链** | 伤害计算的15个乘法区 |
| **成长公式** | `value(lv) = base + floor((growth * (lv - 1) + offset) / divisor)` |
| **普通技能** | 武器 `normal_skills[]`：无条件词条 |
| **特殊技能** | 武器 `special_skills[]`：有条件或独立词条 |

[后续详细术语表内容与 git HEAD:CONTEXT.md 一致，此处省略以节省篇幅]

## 工程术语

| 术语 | 含义 |
|------|------|
| **仓库根目录** | Git 克隆顶层 |
| **Python 包目录** | `games/endfield/` |
| **全量遍历** | 枚举武器×四格配装 |
| **固定配装** | GUI 高级页可固定 0–4 件具体装备 |
| **多技能加权** | 按技能释放次数加权计算总伤害 |
| **CalcPack** | ZIP 格式配置包，含 DAG + 数据 + UI 布局 |
| **ComputeSheet** | 声明式计算表，读 DAG + layout.json → 自动渲染 |
| **GrowthParams** | 类型化参数容器 `(base, growth, divisor, offset)` |
| **InverseEngine** | 通用逆推引擎：`data_to_params()` / `params_to_curve()` |
| **GameInverseAdapter** | 游戏逆推适配器 ABC — 声明 schemas，自动拟合 |
| **JsonDataLoader[T]** | 通用 JSON 懒加载缓存 |
| **CalcWorker** | 通用 QThread 后台线程包装器 |
| **ThemeManager** | 多主题 QSS 管理（暗色/亮色/高对比度） |

[完整术语表见 git 历史中的 CONTEXT.md]
