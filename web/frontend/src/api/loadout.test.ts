import { describe, expect, it } from "vitest";
import { buildSearchRequestFromLoadout, buildWebLoadoutPayload, missingFixedEquipmentDetails, type BuildLoadoutContext } from "./loadout";

function context(): BuildLoadoutContext {
  return {
    charData: { 名称: "测试角色" },
    weaponData: { 名称: "测试武器" },
    charLevel: 90,
    weaponLevel: 90,
    trustLevel: 0,
    skillLevels: {},
    weaponSkillValues: {},
    weaponScope: "当前武器",
    equipmentScope: "全部装备",
    calcMode: "zone_snapshot",
    multiSkill: {
      useManualCounts: false,
      manualCounts: {},
      damageComponentMode: "skill_and_abnormal",
      useExpectedCrit: false,
    },
    critAbnormal: {
      extraCritRate: 0,
      extraCritDamage: 0,
      includeConditionalEquipmentCrit: false,
      physicalAbnormalCounts: {},
      spellAbnormalCounts: {},
    },
    enemyParams: {} as BuildLoadoutContext["enemyParams"],
    fixedLoadout: { chest: "测试护甲", gloves: null, accessory_a: null, accessory_b: null },
    manualBuffStore: {},
    equipmentCatalog: {
      chest: [{ 名称: "测试护甲", 部位: "护甲" }],
    },
  };
}

describe("buildWebLoadoutPayload equipment details", () => {
  it("keeps affixes and effects when fixed equipment came from the slim catalog", () => {
    const ctx = {
      ...context(),
      equipmentDetails: {
        测试护甲: {
          名称: "测试护甲",
          部位: "护甲",
          属性词条: [{ 属性: "攻击力", 数值: 20 }],
          效果: ["攻击力+10%"],
          三件套效果: ["伤害+20%"],
        },
      },
    } as BuildLoadoutContext;

    const payload = buildWebLoadoutPayload(ctx);

    expect(payload?.equipment_catalog?.chest[0]).toMatchObject({
      名称: "测试护甲",
      属性词条: [{ 属性: "攻击力", 数值: 20 }],
      效果: ["攻击力+10%"],
      三件套效果: ["伤害+20%"],
    });
  });

  it("inserts fixed equipment details when the current scope excludes the item", () => {
    const detail = {
      名称: "范围外护甲",
      部位: "护甲",
      属性词条: ["攻击力16"],
      效果: [],
      三件套效果: [],
    };
    const ctx = {
      ...context(),
      fixedLoadout: { chest: "范围外护甲", gloves: null, accessory_a: null, accessory_b: null },
      equipmentCatalog: { chest: [] },
      equipmentDetails: { 范围外护甲: detail },
    } as BuildLoadoutContext;

    const payload = buildWebLoadoutPayload(ctx);

    expect(payload?.equipment_catalog?.chest).toEqual([detail]);
  });

  it("reports missing fixed details before evaluation is allowed", () => {
    const fixed = context().fixedLoadout;

    expect(missingFixedEquipmentDetails(fixed, {})).toEqual(["测试护甲"]);
    expect(
      missingFixedEquipmentDetails(fixed, {
        测试护甲: { 名称: "测试护甲", 属性词条: ["攻击力16"] },
      }),
    ).toEqual([]);
  });

  it("keeps manual buffs when converting a loadout to search", () => {
    const payload = buildWebLoadoutPayload({
      ...context(),
      manualBuffStore: { "战技:1:1": [{ effect_type: "其他伤害加成", value: 0.5 }] },
    });

    expect(buildSearchRequestFromLoadout(payload!).manual_buffs).toEqual({
      "战技:1:1": [{ effect_type: "其他伤害加成", value: 0.5 }],
    });
  });
});
