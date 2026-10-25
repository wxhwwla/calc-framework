/** skillParser 安全剥离回归测试 */

import { describe, expect, it } from "vitest";
import { parseSkill, type ArknightsSkill } from "./skillParser";

describe("skillParser stripHtmlTags fallback", () => {
  it("剥离嵌套 HTML 标签", () => {
    const skill: ArknightsSkill = {
      name: "测试",
      sp_type: "AUTO",
      trigger: "AUTO",
      levels: [
        {
          description: "<<<script><script>alert(1)</script>>>攻击力100%的物理伤害",
          sp_cost: 0,
          init_sp: 0,
          duration: "0",
        },
      ],
    };
    const parsed = parseSkill(skill, 1);
    expect(parsed.description).not.toMatch(/<[^>]+>/);
    expect(parsed.description).not.toMatch(/<!--|<script/i);
    expect(parsed.description).toContain("攻击力");
  });

  it("未闭合注释不残留注入点", () => {
    const skill: ArknightsSkill = {
      name: "注释",
      sp_type: "AUTO",
      trigger: "AUTO",
      levels: [
        {
          description: "<!-- 未闭合攻击力120%的物理伤害",
          sp_cost: 0,
          init_sp: 0,
          duration: "0",
        },
      ],
    };
    const parsed = parseSkill(skill, 1);
    expect(parsed.description).not.toMatch(/<!--/);
  });
});
