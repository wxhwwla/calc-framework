# ADR-0011：截图识装 — YOLO 目标检测 + OCR 数据提取 + 乘区块化

**状态**：生效  
**日期**：2026-05-30  
**决策者**：维护者  
**影响范围**：`framework/`、`endfield_damage_calculator/calculation/`、`tools/`（新增识管管线）

---

## 1. 现状与痛点

当前计算器所有输入均依赖**手动填写**：

| 输入项 | 当前方式 |
|--------|---------|
| 角色/武器/装备选择 | GUI 下拉菜单手动选择 |
| 等级/潜能/信赖 | 滑块/数字框手动填写 |
| 敌方参数 | 敌方面板手动微调 |
| 技能等级 | 折叠区手动选择 |

**问题**：
- 每次配装调整需反复切换游戏↔计算器窗口，手动抄写数值
- 多件装备对比时操作繁琐
- 新手学习成本高（需理解 15 乘区含义才能填对参数）

**目标**：截一张游戏内面板图 → 自动识别角色/装备/数值 → 一键填入计算器。

---

## 2. 总体方案

```
┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌───────────┐
│ 游戏截图  │ → │ YOLO 检测 │ → │ OCR 文本提取  │ → │ 数据映射   │
│ (屏幕/文件)│   │ 区域定位   │   │ 数值识别      │   │ → 计算器   │
└──────────┘   └──────────┘   └──────────────┘   └───────────┘
```

### 2.1 YOLO 目标检测

检测游戏 UI 中的固定区域：

| 检测目标 | 说明 | 输出 |
|---------|------|------|
| 角色面板区 | 角色名、等级、信赖、能力值 | bounding box |
| 武器面板区 | 武器名、等级、词条 | bounding box |
| 装备面板区 | 各部位装备名、主/副词条 | bounding box |
| 技能面板区 | 技能等级、倍率 | bounding box |
| 乘区数值区 | 各乘区最终数值 | bounding box |

### 2.2 OCR 文本提取

对每个 bounding box 内的图像做 OCR：

| 场景 | 引擎选项 | 备注 |
|------|---------|------|
| 数字识别（等级、数值） | PaddleOCR / TrOCR | 数字准确率高 |
| 中文文本（角色名、装备名） | PaddleOCR | 需对应游戏字体训练 |
| 英文/数字混合 | TrOCR / EasyOCR | 武器词条等 |

### 2.3 数据映射

OCR 文本 → 计算器内部数据模型的映射层：

```
OCR 输出 "秋栗" → 匹配 characters.json 中 name="秋栗"
OCR 输出 "80"   → 等级=80
OCR 输出 "攻击力 1254" → weapon.base_atk=1254 (或 computed 区)
```

---

## 3. 乘区块化（Zone Blocking）

### 3.1 动机

当前 DAG 有 70 个节点、15 乘区，粒度极细。这在以下场景中反而不利：

| 场景 | 问题 |
|------|------|
| OCR 提取 | 游戏 UI 展示的是块级结果（总攻击力、总暴击伤害），而非每个子乘区 |
| 多游戏适配 | 不同游戏乘区分法不同，细粒度绑定二游 15 乘区模型 |
| 用户理解 | 大部分用户只关心"总攻击力""总伤害"，不关心中间子乘区 |

### 3.2 块化定义

基于现有 DAG 的 70 个节点和 15 乘区连乘链，划分为 **6 个逻辑块**，每块封装为 DAG `subgraph`：

#### 块 1：属性块（Stats Block）

**现有 DAG 节点**：ability_bonus 链（5 节点）+ 四维加成（4 节点）= 9 节点  
**子图**：复用已有 `ability_bonus` subgraph  
**输入**：

| 变量 | 来源 | 说明 |
|------|------|------|
| `main_flat` | computed | 主能力平值全部来源 |
| `sub_flat` | computed | 副能力平值全部来源 |
| `main_pct` | computed | 主能力百分比加成 |
| `sub_pct` | computed | 副能力百分比加成 |
| `char_attr_力量/敏捷/智识/意志` | character | 角色四维基础 |
| `comp_attr_力量/敏捷/智识/意志_bonus` | computed | 武器技能四维加成 |

**输出**：`ability_bonus`（能力值加成）、四维最终值  
**OCR 对齐**：角色面板 → 显示四维最终值

#### 块 2：攻击力块（Attack Block）

**现有 DAG 节点**：final_attack 链（6 节点）  
**子图**：复用已有 `final_attack` subgraph  
**输入**：

| 变量 | 来源 | 说明 |
|------|------|------|
| `char_base_atk` | character | 角色基础攻击力 |
| `weapon_base_atk` | weapon | 武器基础攻击力 |
| `atk_bonus` | weapon | 攻击力+%（小数） |
| `additional_atk` | weapon | 附加攻击力+（平值） |
| `equip_flat_atk` | equipment | 装备平铺攻击力 |
| `ability_bonus` | ← 块 1 输出 | 能力值加成 |

**输出**：`final_attack`（最终攻击力）  
**OCR 对齐**：角色面板 → 显示最终攻击力

#### 块 3：暴击块（Crit Block）

**现有 DAG 节点**：crit_zone call（3 节点）  
**子图**：复用已有 `crit_zone` subgraph  
**输入**：

| 变量 | 说明 |
|------|------|
| `crit_rate` | 暴击率（小数） |
| `crit_damage` | 暴击伤害（小数） |

**输出**：`crit_zone`（暴击区乘数 = 1 + 暴击率×(暴击伤害-1)）  
**OCR 对齐**：角色面板 → 暴击率/暴击伤害

#### 块 4：基础伤害块（Base Damage Block）

**现有 DAG 节点**：`zone_base` + `zone_crit` + `z1`（3 节点）  
**子图**：新建 subgraph `base_damage_block`  
**输入**：

| 变量 | 来源 | 说明 |
|------|------|------|
| `final_attack` | ← 块 2 输出 | 最终攻击力 |
| `skill_mult` | computed | 技能倍率 |
| `crit_zone` | ← 块 3 输出 | 暴击区乘数 |

**内部计算**：
```
base_damage = final_attack × skill_mult          [基础伤害区]
damage_after_crit = base_damage × crit_zone      [×暴击区]
```

**输出**：`damage_after_crit`（暴击后伤害）  
**OCR 对齐**：无直接对应（计算中间值）

#### 块 5：增益/减益块（Buff & Debuff Block）

**现有 DAG 节点**：z2–z8（7 个乘区 + 7 个 BinaryNode = 14 节点）  
**子图**：新建 subgraph `buff_debuff_block`  
**输入**：

| 变量 | 类型 | 说明 |
|------|------|------|
| `damage_after_crit` | ← 块 4 输出 | 暴击后伤害 |
| `zone_dmg_bonus` | 加法增益 | 伤害加成区 = 1+类型+技能+失衡+其他 |
| `zone_amp` | 加法增益 | 增幅区 = 1+Σ增幅值 |
| `zone_fragile` | 加法增益 | 脆弱区 = 1+Σ脆弱值 |
| `zone_vuln` | 加法增益 | 易伤区 = 1+Σ易伤值 |
| `zone_dmg_reduc` | 乘法减益 | 伤害减免区 = ∏(1-减免值) |
| `zone_weak` | 乘法减益 | 虚弱区 = ∏(1-虚弱值) |
| `zone_shelter` | 乘法减益 | 庇护区 = 1-max(庇护值) |

**内部计算**（7 个乘区连乘）：
```
增益系数 = zone_dmg_bonus × zone_amp × zone_fragile × zone_vuln
减益系数 = zone_dmg_reduc × zone_weak × zone_shelter
damage_after_buff = damage_after_crit × 增益系数 × 减益系数
```

**输出**：`damage_after_buff`（增益减益后伤害）  
**OCR 对齐**：部分可见（BUFF 栏位）

#### 块 6：环境乘区块（Environment Block）

**现有 DAG 节点**：z9–final_damage（6 个乘区 + 6 个 BinaryNode = 12 节点）  
**子图**：新建 subgraph `environment_block`  
**输入**：

| 变量 | 类型 | 说明 |
|------|------|------|
| `damage_after_buff` | ← 块 5 输出 | 增益减益后伤害 |
| `enemy_defense` | 敌方参数 | 敌方防御值 |
| `zone_imbal` | 环境机制 | 失衡易伤区 |
| `zone_res` | 敌方参数 | 抗性区 |
| `zone_ncr` | 环境机制 | 非主控减伤区 |
| `zone_combo` | 环境机制 | 连击增伤区 |
| `zone_special` | 环境机制 | 特殊乘区 |

**内部计算**（调用 `defense_reduction` subgraph + 5 个乘区连乘）：
```
def_mult = 100 / (enemy_defense + 100)           [防御区]
damage = damage_after_buff × def_mult × zone_imbal × zone_res × zone_ncr × zone_combo × zone_special
```

**输出**：`final_damage`（最终伤害）  
**OCR 对齐**：敌方面板 → 防御/抗性

#### 块划分总览

| 块 | 名称 | DAG 节点数 | 子图 | 输入来源 | 输出去向 |
|----|------|-----------|------|---------|---------|
| 1 | 属性块 | 9 | 复用已有 | character/computed | → 块 2 |
| 2 | 攻击力块 | 6 | 复用已有 | character/weapon/equipment + 块 1 | → 块 4 |
| 3 | 暴击块 | 3 | 复用已有 | character | → 块 4 |
| 4 | 基础伤害块 | 3 | **新建** | 块 2 + 块 3 + computed | → 块 5 |
| 5 | 增益/减益块 | 14 | **新建** | 块 4 + 7 个 computed 乘区 | → 块 6 |
| 6 | 环境乘区块 | 12 | **新建** | 块 5 + enemy + 5 个 computed | → 最终伤害 |

**总节点数**：9+6+3+3+14+12 = **47**（vs 原 70 扁平节点，节省 23 个中间 BinaryNode）

### 3.3 与 DAG subgraph 的关系

框架 DAG 引擎的 `call` 节点 + `subgraphs` 区已经提供了等价机制：

```json
{
  "nodes": [
    {"id": "attack_block", "type": "call", "subgraph_id": "attack_block_sub", "inputs": {...}},
    {"id": "crit_block",   "type": "call", "subgraph_id": "crit_block_sub",   "inputs": {...}},
    {"id": "final_damage", "type": "call", "subgraph_id": "final_damage_sub", "inputs": {...}}
  ],
  "subgraphs": {
    "attack_block_sub": { ... },
    "crit_block_sub": { ... },
    "final_damage_sub": { ... }
  }
}
```

**区别**：当前 subgraph 在求值前被 `expand_subgraphs()` 递归展开为扁平 DAG，展开后无块边界。块化是在语义层面保留块边界，便于：
- 块级缓存（块输入不变 → 跳过块内求值）
- 块级替换（不同游戏可替换"攻击力块"的实现）
- 块级 OCR（截图只识别到块级结果时，跳过块内计算，直接注入块输出）

### 3.4 深层嵌套

乘区块可以嵌套，但必须控制深度：

```
最终伤害块
├── 攻击力块（第1层）
│   ├── 基础攻击块（第2层）
│   └── 百分比加成块（第2层）
├── 暴击块（第1层）
└── 减伤块（第1层）
    ├── 防御减伤块（第2层）
    └── 抗性减伤块（第2层）
```

**约束规则**：

| 规则 | 值 |
|------|-----|
| 最大嵌套深度 | 3 层（含根） |
| 每块最大子节点数 | ≤ 15 |
| 块间禁止循环引用 | 拓扑排序检测 |
| 块接口 | 必须声明 inputs / outputs |

---

## 4. 与现有框架的关系

### 4.1 已有基础设施

| 现有组件 | 与本方案的关系 |
|---------|--------------|
| DAG 引擎 + subgraph | 块化可直接复用 `call` + `subgraph` 机制 |
| `DataContext` | OCR 提取的数据可直接构建 DataContext |
| `ComputeSheet` | 块级 UI 渲染（每块一个 Section） |
| `AdapterPackage` | 不同游戏的识管配置可作为适配包的一部分 |
| `EndfieldContextLoader` | 可扩展为接受 OCR 输入 + 手动输入混合 |

### 4.2 需要新增

| 模块 | 说明 |
|------|------|
| `tools/ocr/` 管线 | YOLO 模型 + OCR 引擎的封装管线 |
| 区块定义配置 | 各游戏的乘区块划分 JSON（block 拓扑） |
| 混合输入适配器 | OCR 自动填充 + 用户手动微调的 merging 逻辑 |
| 块级缓存 | 块输入不变时，跳过块内 DAG 求值 |

---

## 5. 落地路线

### Phase 1：区块定义 + 块级 DAG（当前对话）

| 任务 | 说明 |
|------|------|
| 1.1 | 定义终末地 15 乘区的块划分（5~6 块） |
| 1.2 | 在现有 DAG config 上验证块拓扑 |
| 1.3 | 实现块级求值（跳过未变块） |
| 1.4 | 块级缓存机制 |

### Phase 2：YOLO 检测模型

| 任务 | 说明 |
|------|------|
| 2.1 | 采集终末地 UI 截图数据集（角色/武器/装备/乘区面板） |
| 2.2 | 标注 bounding box → 训练 YOLO 检测模型 |
| 2.3 | 模型导出 + 推理封装（`tools/ocr/detector.py`） |

### Phase 3：OCR 识别

| 任务 | 说明 |
|------|------|
| 3.1 | 选定 OCR 引擎（PaddleOCR 优先） |
| 3.2 | 数字/文本识别管线（`tools/ocr/recognizer.py`） |
| 3.3 | 专有名词字典（角色名/武器名/词条名）提升准确率 |

### Phase 4：数据映射与 GUI 集成

| 任务 | 说明 |
|------|------|
| 4.1 | OCR 输出 → 计算器输入映射层 |
| 4.2 | GUI「截图识装」按钮 + 截图选择对话框 |
| 4.3 | 自动填充后的人工确认/微调交互 |
| 4.4 | 多游戏适配（按适配包切换识管配置） |

---

## 6. 开放问题

| 问题 | 现状 | 待决策 |
|------|------|--------|
| OCR 引擎选择 | PaddleOCR 优先 | 需实测终末地字体准确率 |
| YOLO 模型大小 | YOLOv8n（轻量）vs YOLOv8m | 取决于用户设备性能容忍度 |
| 是否需要 GPU | OCR 推理 CPU 可跑 | YOLO 训练需 GPU，推理可 CPU |
| 数据集来源 | 人工截图 + 数据增强 | 需确定最低标注量（预估 200~500 张） |
| 块粒度 | 5~6 块 v.s. 更粗（3 块）或更细（10 块） | 需 UI 原型验证 |
| 块级缓存的失效粒度 | 块级 vs 整图 | DAG 已有整图缓存，块级需新增 |
