import { describe, it, expect } from "vitest";
import {
  buildEntityContext,
  computeDisabledPaths,
  fieldValues,
  formatDetailValue,
  initialSelections,
  matchingRecords,
  optionDisplays,
  ruleMatches,
  stepOptions,
} from "./adapterEntity";
import type { EntityInputRule, EntityStep } from "./adapterEntity";

const STEPS: EntityStep[] = [
  { field: "舰船分类", label: "舰船种类" },
  { field: "舰船", label: "舰船" },
  { field: "名称", label: "武器", display_field: "武器标签" },
];

const RECORDS: Record<string, unknown>[] = [
  {
    舰船分类: ["战机", "护卫舰"],
    舰船: "A",
    名称: "W1",
    武器标签: "W1 标签",
    base_damage: 10,
    needs_mothership: 0,
    is_energy: 1,
    friendly: 0,
  },
  {
    舰船分类: "战机",
    舰船: "A",
    名称: "W2",
    武器标签: "W2 标签",
    base_damage: 20,
    needs_mothership: 1,
    is_energy: 0,
    friendly: 1,
  },
  {
    舰船分类: "驱逐舰",
    舰船: "B",
    名称: "W3",
    武器标签: "W3 标签",
    base_damage: 30,
  },
];

const RULES: EntityInputRule[] = [
  { source: "weapon", field: "needs_mothership", equals: 0, disable: ["user_input.mothership_flight_bonus"], reason: "该舰船不需要母舰" },
  { source: "weapon", field: "is_energy", equals: 1, disable: ["user_input.physical_armor"], reason: "能量武器使用能量护甲" },
  { source: "weapon", field: "is_energy", equals: 0, disable: ["user_input.energy_armor"], reason: "实弹/辅助武器使用物理护甲" },
  { source: "weapon", field: "friendly", equals: 1, disable: ["user_input.target_evasion"], reason: "维修/驻防/增益类武器固定 100% 命中" },
];

describe("fieldValues", () => {
  it("列表字段展开为多个值", () => {
    expect(fieldValues(RECORDS[0], "舰船分类")).toEqual(["战机", "护卫舰"]);
  });

  it("标量字段返回单元素数组", () => {
    expect(fieldValues(RECORDS[1], "舰船分类")).toEqual(["战机"]);
  });

  it("缺失或空值返回空数组", () => {
    expect(fieldValues(RECORDS[2], "不存在")).toEqual([]);
    expect(fieldValues({ 舰船分类: "" }, "舰船分类")).toEqual([]);
    expect(fieldValues({ 舰船分类: null }, "舰船分类")).toEqual([]);
  });
});

describe("级联选择", () => {
  it("第一级按记录顺序去重并展开列表字段", () => {
    expect(stepOptions(RECORDS, STEPS, [null, null, null], 0)).toEqual(["战机", "护卫舰", "驱逐舰"]);
  });

  it("后续级只显示上级过滤后的候选", () => {
    expect(stepOptions(RECORDS, STEPS, ["战机", null, null], 1)).toEqual(["A"]);
    expect(stepOptions(RECORDS, STEPS, ["驱逐舰", null, null], 1)).toEqual(["B"]);
    expect(stepOptions(RECORDS, STEPS, ["战机", "A", null], 2)).toEqual(["W1", "W2"]);
  });

  it("matchingRecords 只保留全部已选条件匹配的记录", () => {
    expect(matchingRecords(RECORDS, STEPS, ["护卫舰", "A", "W1"])).toEqual([RECORDS[0]]);
    expect(matchingRecords(RECORDS, STEPS, ["战机", null, null])).toHaveLength(2);
    expect(matchingRecords(RECORDS, STEPS, [null, null, null])).toHaveLength(3);
  });

  it("optionDisplays 使用 display_field 生成显示文案", () => {
    expect(optionDisplays(RECORDS, STEPS, ["战机", null, null], 2)).toEqual({
      W1: "W1 标签",
      W2: "W2 标签",
    });
  });

  it("未配置 display_field 时显示值本身", () => {
    expect(optionDisplays(RECORDS, STEPS, [null, null, null], 0)).toEqual({
      战机: "战机",
      护卫舰: "护卫舰",
      驱逐舰: "驱逐舰",
    });
  });

  it("initialSelections 默认选中每一级第一项", () => {
    expect(initialSelections(RECORDS, STEPS)).toEqual(["战机", "A", "W1"]);
  });

  it("空数据返回全空选择", () => {
    expect(initialSelections([], STEPS)).toEqual([null, null, null]);
  });
});

describe("ruleMatches / computeDisabledPaths", () => {
  it("数值相等命中", () => {
    expect(ruleMatches(RULES[0], RECORDS[0])).toBe(true);
    expect(ruleMatches(RULES[0], RECORDS[1])).toBe(false);
  });

  it("字段缺失视为未知，不命中", () => {
    expect(ruleMatches(RULES[0], RECORDS[2])).toBe(false);
  });

  it("字符串比较忽略首尾空白", () => {
    const rule: EntityInputRule = { source: "weapon", field: "标志", equals: "是", disable: ["user_input.x"] };
    expect(ruleMatches(rule, { 标志: " 是 " })).toBe(true);
  });

  it("列表字段任一元素命中即可", () => {
    const rule: EntityInputRule = { source: "weapon", field: "舰船分类", equals: "护卫舰", disable: ["user_input.x"] };
    expect(ruleMatches(rule, RECORDS[0])).toBe(true);
  });

  it("按来源与命中规则汇总禁用路径及原因", () => {
    expect(computeDisabledPaths(RULES, RECORDS[0], "weapon")).toEqual({
      "user_input.mothership_flight_bonus": "该舰船不需要母舰",
      "user_input.physical_armor": "能量武器使用能量护甲",
    });
    expect(computeDisabledPaths(RULES, RECORDS[1], "weapon")).toEqual({
      "user_input.energy_armor": "实弹/辅助武器使用物理护甲",
      "user_input.target_evasion": "维修/驻防/增益类武器固定 100% 命中",
    });
  });

  it("来源不匹配的规则被忽略", () => {
    expect(computeDisabledPaths(RULES, RECORDS[0], "character")).toEqual({});
  });

  it("同一路径多条规则时保留第一条原因", () => {
    const rules: EntityInputRule[] = [
      { source: "weapon", field: "needs_mothership", equals: 0, disable: ["user_input.x"], reason: "原因 A" },
      { source: "weapon", field: "is_energy", equals: 1, disable: ["user_input.x"], reason: "原因 B" },
    ];
    expect(computeDisabledPaths(rules, RECORDS[0], "weapon")).toEqual({ "user_input.x": "原因 A" });
  });
});

describe("formatDetailValue", () => {
  it("空值显示占位符", () => {
    expect(formatDetailValue(null)).toBe("—");
    expect(formatDetailValue(undefined)).toBe("—");
    expect(formatDetailValue("   ")).toBe("—");
  });

  it("布尔值显示是/否", () => {
    expect(formatDetailValue(true)).toBe("是");
    expect(formatDetailValue(false)).toBe("否");
  });

  it("列表用顿号连接", () => {
    expect(formatDetailValue(["战机", "护卫舰"])).toBe("战机、护卫舰");
    expect(formatDetailValue([1, 2])).toBe("1、2");
  });

  it("整数不带小数点，浮点最多两位并去掉尾零", () => {
    expect(formatDetailValue(10)).toBe("10");
    expect(formatDetailValue(10.5)).toBe("10.5");
    expect(formatDetailValue(10.25)).toBe("10.25");
    expect(formatDetailValue(10.256)).toBe("10.26");
  });

  it("支持显式格式", () => {
    expect(formatDetailValue(10, ".2f")).toBe("10.00");
    expect(formatDetailValue(0.1234, ".2%")).toBe("12.34%");
  });
});

describe("buildEntityContext", () => {
  it("实体数值字段进入来源命名空间，用户输入进入 user_input", () => {
    const context = buildEntityContext(RECORDS[0], "weapon", {
      "user_input.fleet_count": 3,
      "user_input.target_evasion": 0.1,
    });

    expect(context).toEqual({
      weapon: {
        base_damage: 10,
        needs_mothership: 0,
        is_energy: 1,
        friendly: 0,
      },
      user_input: {
        fleet_count: 3,
        target_evasion: 0.1,
      },
    });
  });

  it("忽略字符串、列表等非数值字段", () => {
    const context = buildEntityContext(RECORDS[0], "weapon", {});
    expect(context.weapon).not.toHaveProperty("名称");
    expect(context.weapon).not.toHaveProperty("舰船分类");
    expect(context.weapon).not.toHaveProperty("武器标签");
  });

  it("同一路径重复出现时用户输入不被实体字段覆盖", () => {
    const record = { ...RECORDS[0], fleet_count: 99 };
    const context = buildEntityContext(record, "weapon", { "user_input.fleet_count": 3 });
    expect(context.user_input.fleet_count).toBe(3);
    expect(context.weapon.fleet_count).toBe(99);
  });

  it("无点号的输入路径被忽略", () => {
    const context = buildEntityContext(RECORDS[0], "weapon", { fleet_count: 3 });
    expect(context.user_input).toEqual({});
  });
});
