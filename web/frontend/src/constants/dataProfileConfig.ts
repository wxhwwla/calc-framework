/** Web 数据录入字段定义（对齐 tools/designer/data_editor/profiles.py） */

export type FieldType = "text" | "number" | "select";

export interface FieldDef {
  key: string;
  label: string;
  type: FieldType;
  options?: string[];
}

export interface EntityConfig {
  key: string;
  label: string;
  fields: FieldDef[];
  columns: string[];
}

export interface ProfileConfig {
  id: string;
  label: string;
  entities: EntityConfig[];
}

export const DATA_PROFILES: ProfileConfig[] = [
  {
    id: "endfield",
    label: "终末地",
    entities: [
      {
        key: "characters",
        label: "角色",
        columns: ["名称", "类型", "星级", "主能力", "副能力"],
        fields: [
          { key: "名称", label: "名称", type: "text" },
          { key: "类型", label: "类型", type: "select", options: ["物理", "能量", "电磁", "热熔", "异裂"] },
          { key: "星级", label: "星级", type: "number" },
          { key: "武器", label: "武器", type: "text" },
          { key: "主能力", label: "主能力", type: "select", options: ["力量", "敏捷", "智识", "意志"] },
          { key: "副能力", label: "副能力", type: "select", options: ["力量", "敏捷", "智识", "意志"] },
          { key: "力量", label: "力量", type: "number" },
          { key: "敏捷", label: "敏捷", type: "number" },
          { key: "智识", label: "智识", type: "number" },
          { key: "意志", label: "意志", type: "number" },
          { key: "信赖", label: "信赖", type: "number" },
        ],
      },
      {
        key: "weapons",
        label: "武器",
        columns: ["名称", "类型", "星级"],
        fields: [
          { key: "名称", label: "名称", type: "text" },
          { key: "类型", label: "类型", type: "select", options: ["尖兵", "刀锋", "重装", "射手", "术士", "医疗", "支援"] },
          { key: "星级", label: "星级", type: "number" },
        ],
      },
      {
        key: "equipments",
        label: "装备",
        columns: ["名称", "部位", "稀有度"],
        fields: [
          { key: "名称", label: "名称", type: "text" },
          { key: "部位", label: "部位", type: "select", options: ["胸甲", "护手", "饰品"] },
          { key: "稀有度", label: "稀有度", type: "text" },
          { key: "所属套组", label: "套组", type: "text" },
        ],
      },
    ],
  },
  {
    id: "arknights",
    label: "明日方舟",
    entities: [
      {
        key: "operators",
        label: "干员",
        columns: ["名称", "职业", "星级", "分支"],
        fields: [
          { key: "名称", label: "名称", type: "text" },
          { key: "职业", label: "职业", type: "text" },
          { key: "星级", label: "星级", type: "number" },
          { key: "分支", label: "分支", type: "text" },
        ],
      },
    ],
  },
];

export function getProfile(profileId: string): ProfileConfig | undefined {
  return DATA_PROFILES.find((p) => p.id === profileId);
}

export function getEntity(profileId: string, entityKey: string): EntityConfig | undefined {
  return getProfile(profileId)?.entities.find((e) => e.key === entityKey);
}
