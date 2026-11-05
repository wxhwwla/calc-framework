import { describe, expect, it } from "vitest";
import type { DagVariable } from "./controlInference";
import { defaultInputValues } from "./controlInference";

describe("defaultInputValues", () => {
  it("只收集 user_input 变量并取其推断默认值", () => {
    const variables: Record<string, DagVariable> = {
      "user_input.fleet_count": { type: "int", source: "user_input", default: 2 },
      "user_input.friendly": { type: "bool", source: "user_input", default: false },
      "user_input.mode": {
        type: "str",
        source: "user_input",
        default: "alpha",
        options: ["alpha", "beta"],
      },
      "weapon.attack": { type: "float", source: "weapon", default: 100 },
    };

    expect(defaultInputValues(variables)).toEqual({
      "user_input.fleet_count": 2,
      "user_input.friendly": false,
      "user_input.mode": "alpha",
    });
  });

  it("缺失默认值时数值类型归 0、字符串类型归空串", () => {
    const variables: Record<string, DagVariable> = {
      "user_input.ratio": { type: "float", source: "user_input", default: null },
      "user_input.label": { type: "str", source: "user_input" },
    };

    expect(defaultInputValues(variables)).toEqual({
      "user_input.ratio": 0,
      "user_input.label": "",
    });
  });
});
