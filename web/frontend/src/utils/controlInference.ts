/** 控件推断 — 根据 DAG variables 声明推断对应的 UI 控件类型。

Python 版：framework/src/calc_framework/ui/controls.py
TypeScript 移植版，与 Python 版保持逻辑一致。
*/

export interface ControlSpec {
  label: string;
  widget: "slider" | "spinbox" | "switch" | "dropdown" | "none" | "text";
  default: number | boolean | string;
  minVal: number | null;
  maxVal: number | null;
  step: number;
  options: string[];
  description: string;
}

export interface DagVariable {
  type: string;
  source: string;
  description?: string;
  default?: number | boolean | string | null;
  min?: number | null;
  max?: number | null;
  options?: string[];
  ui_control?: {
    widget?: string;
    step?: number;
    options?: string[];
  };
}

/**
 * 根据变量路径和变量声明推断控件规格。
 * 与 Python infer_control() 保持逻辑一致。
 */
export function inferControl(path: string, variable: DagVariable): ControlSpec {
  const uiOverride = variable.ui_control || {};
  const source = variable.source || "";
  const varType = variable.type || "float";

  const label = path;
  const description = variable.description || "";

  // 非 user_input 来源不渲染控件
  if (source !== "user_input") {
    return { label, widget: "none", default: 0, minVal: null, maxVal: null, step: 0.01, options: [], description };
  }

  const widget = uiOverride.widget;
  let step = uiOverride.step;
  const options = uiOverride.options;

  const rawDefault = variable.default;
  let defaultValue: number | boolean | string = 0;
  if (rawDefault === null || rawDefault === undefined) {
    defaultValue = varType === "float" || varType === "int" ? 0 : "";
  } else {
    defaultValue = rawDefault as number | boolean | string;
  }

  const minVal = variable.min ?? null;
  const maxVal = variable.max ?? null;

  let resolvedWidget: ControlSpec["widget"];

  if (widget) {
    resolvedWidget = widget as ControlSpec["widget"];
  } else if (varType === "bool") {
    resolvedWidget = "switch";
  } else if (varType === "str") {
    resolvedWidget = "dropdown";
  } else if ((minVal !== null && maxVal !== null) || widget === "slider") {
    resolvedWidget = "slider";
  } else {
    resolvedWidget = "spinbox";
  }

  if (step === undefined || step === null) {
    step = varType === "int" ? 1 : 0.01;
  }

  const resolvedOptions = options || (varType === "str" ? variable.options || [] : []);

  return {
    label,
    widget: resolvedWidget,
    default: defaultValue,
    minVal,
    maxVal,
    step,
    options: resolvedOptions,
    description,
  };
}

/**
 * 从 DAG variables 中筛选出 user_input 类型的变量。
 */
export function getUserInputVariables(variables: Record<string, DagVariable>): Record<string, DagVariable> {
  const result: Record<string, DagVariable> = {};
  for (const [path, varDef] of Object.entries(variables)) {
    if (varDef.source === "user_input") {
      result[path] = varDef;
    }
  }
  return result;
}

/**
 * 从 DAG variables 中筛选出 character/weapon/enemy/computed 类型的变量。
 */
export function getEntityVariables(variables: Record<string, DagVariable>): Record<string, DagVariable> {
  const result: Record<string, DagVariable> = {};
  for (const [path, varDef] of Object.entries(variables)) {
    const src = varDef.source || "";
    if (src !== "user_input") {
      result[path] = varDef;
    }
  }
  return result;
}
