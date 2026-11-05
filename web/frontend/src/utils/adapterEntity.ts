/** 适配器实体选择与 context 构建 — 与 Python 端 entity_cascade / entity_meta 对齐。 */

export type EntityRecord = Record<string, unknown>;
export type EntitySelections = (string | null)[];
export type EntityValue = number | boolean | string;

export interface EntityStep {
  field: string;
  label?: string;
  display_field?: string;
}

export interface EntitySelector {
  source: string;
  data_file: string;
  steps: EntityStep[];
}

export interface EntityInputRule {
  source: string;
  field: string;
  equals: EntityValue;
  disable: string[];
  reason?: string;
}

export interface EntityDetailField {
  field: string;
  label?: string;
  format?: string;
}

export interface EntityDetailSection {
  title?: string;
  columns?: number;
  fields: EntityDetailField[];
}

export interface EntityDetailMeta {
  source: string;
  title?: string;
  sections: EntityDetailSection[];
}

function text(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

/** 实体明细字段格式化 — 与 Python `format_detail_value` 对齐。 */
export function formatDetailValue(value: unknown, format?: string): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) {
    return value.map((item) => formatDetailValue(item, format)).join("、");
  }
  if (typeof value === "boolean") return value ? "是" : "否";
  if (typeof value === "number") {
    const spec = (format || "").trim();
    const percent = /^\.(\d+)%$/.exec(spec);
    if (percent) return `${(value * 100).toFixed(Number(percent[1]))}%`;
    const fixed = /^\.(\d+)f$/.exec(spec);
    if (fixed) return value.toFixed(Number(fixed[1]));
    if (Number.isInteger(value)) return String(value);
    return String(Number(value.toFixed(2)));
  }
  const result = String(value);
  return result.trim() ? result : "—";
}

/** 读取记录中某一步骤的候选值；列表字段展开，空值过滤。 */
export function fieldValues(record: EntityRecord, field: string): string[] {
  const value = record[field];
  if (Array.isArray(value)) {
    return value.map(text).filter((item) => item.length > 0);
  }
  const single = text(value);
  return single ? [single] : [];
}

/** 按已选步骤过滤记录；遇到第一个未选择（null）的步骤即停止。 */
export function matchingRecords(
  records: readonly EntityRecord[],
  steps: readonly EntityStep[],
  selections: readonly (string | null)[],
): EntityRecord[] {
  let matched = records.slice();
  for (let index = 0; index < steps.length; index += 1) {
    const selection = index < selections.length ? selections[index] : null;
    if (selection === null) break;
    const field = text(steps[index].field);
    if (!field) continue;
    matched = matched.filter((record) => fieldValues(record, field).includes(selection));
  }
  return matched;
}

/** 计算第 index 级下拉候选值，按记录顺序去重。 */
export function stepOptions(
  records: readonly EntityRecord[],
  steps: readonly EntityStep[],
  selections: readonly (string | null)[],
  index: number,
): string[] {
  if (index < 0 || index >= steps.length) return [];
  const field = text(steps[index].field);
  if (!field) return [];

  const options: string[] = [];
  const seen = new Set<string>();
  for (const record of matchingRecords(records, steps.slice(0, index), selections.slice(0, index))) {
    for (const value of fieldValues(record, field)) {
      if (!seen.has(value)) {
        seen.add(value);
        options.push(value);
      }
    }
  }
  return options;
}

/** 候选值到显示文案的映射（display_field 存在时使用它）。 */
export function optionDisplays(
  records: readonly EntityRecord[],
  steps: readonly EntityStep[],
  selections: readonly (string | null)[],
  index: number,
): Record<string, string> {
  const options = stepOptions(records, steps, selections, index);
  if (options.length === 0) return {};

  const displayField = text(steps[index].display_field);
  const displays: Record<string, string> = {};
  for (const option of options) displays[option] = option;
  if (!displayField) return displays;

  const remaining = new Set(options);
  for (const record of matchingRecords(records, steps.slice(0, index), selections.slice(0, index))) {
    const display = text(record[displayField]);
    if (!display) continue;
    for (const value of fieldValues(record, text(steps[index].field))) {
      if (remaining.has(value)) {
        displays[value] = display;
        remaining.delete(value);
      }
    }
    if (remaining.size === 0) break;
  }
  return displays;
}

/** 默认选中每一级第一项（与桌面查看器一致）。 */
export function initialSelections(
  records: readonly EntityRecord[],
  steps: readonly EntityStep[],
): EntitySelections {
  const selections: EntitySelections = [];
  for (let index = 0; index < steps.length; index += 1) {
    const options = stepOptions(records, steps, selections, index);
    selections.push(options[0] ?? null);
  }
  return selections;
}

function valueEquals(value: unknown, expected: EntityValue): boolean {
  if (Array.isArray(value)) return value.some((item) => valueEquals(item, expected));
  if (typeof value === "boolean" || typeof expected === "boolean") return value === expected;
  if (typeof value === "number" && typeof expected === "number") return value === expected;
  return text(value) === text(expected);
}

/** 规则是否命中记录；字段缺失视为未知，不命中。 */
export function ruleMatches(rule: EntityInputRule, record: EntityRecord): boolean {
  const field = text(rule.field);
  if (!field || !(field in record)) return false;
  return valueEquals(record[field], rule.equals);
}

/** 汇总某来源下应禁用的 user_input 路径及原因；同一路径保留第一条原因。 */
export function computeDisabledPaths(
  rules: readonly EntityInputRule[],
  record: EntityRecord,
  source: string,
): Record<string, string> {
  const disabled: Record<string, string> = {};
  for (const rule of rules) {
    if (rule.source !== source || !ruleMatches(rule, record)) continue;
    for (const path of rule.disable) {
      if (!(path in disabled)) disabled[path] = rule.reason ?? "";
    }
  }
  return disabled;
}

/**
 * 构建求值 context：实体数值标量进入来源命名空间，用户输入按
 * `user_input.<key>` 进入 `user_input` 命名空间。
 */
export function buildEntityContext(
  record: EntityRecord,
  source: string,
  userInputs: Record<string, EntityValue>,
): Record<string, Record<string, EntityValue>> {
  const entityFields: Record<string, EntityValue> = {};
  for (const [key, value] of Object.entries(record)) {
    if (typeof value === "number" && Number.isFinite(value)) {
      entityFields[key] = value;
    }
  }

  const context: Record<string, Record<string, EntityValue>> = {
    [source]: entityFields,
    user_input: {},
  };

  for (const [path, value] of Object.entries(userInputs)) {
    const dot = path.indexOf(".");
    if (dot <= 0 || dot === path.length - 1) continue;
    const namespace = path.slice(0, dot);
    const key = path.slice(dot + 1);
    (context[namespace] ??= {})[key] = value;
  }

  return context;
}
