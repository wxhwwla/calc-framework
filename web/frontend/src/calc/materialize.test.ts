import { describe, it, expect } from "vitest";
import { materializeCharacterEntity, materializeWeaponEntity, sampleEntityAtLevel } from "./materialize";

describe("materializeCharacterEntity", () => {
  it("从成长参数物化角色属性", () => {
    const entity = materializeCharacterEntity({
      name: "测试角色",
      最大等级: 90,
      成长参数: {
        基础攻击力: { base: 100, growth: 5, divisor: 1 },
        基础生命值: { base: 1000, growth: 50, divisor: 1 },
        基础防御力: { base: 50, growth: 3, divisor: 1 },
      },
      战技倍率: { base: 100, growth: 10, divisor: 1 },
      连携技倍率: { base: 50, growth: 5, divisor: 1 },
    } as Record<string, unknown>);
    expect(entity["基础攻击力"]).toBeDefined();
    expect((entity["基础攻击力"] as number[])).toHaveLength(90);
    expect((entity["基础攻击力"] as number[])[0]).toBe(100);
    expect((entity["基础攻击力"] as number[])[89]).toBe(100 + 5 * 89);
    expect((entity["基础生命值"] as number[])).toHaveLength(90);
    expect((entity["基础防御力"] as number[])).toHaveLength(90);
  });

  it("战技倍率物化为 12 级", () => {
    const entity = materializeCharacterEntity({
      name: "技能测试",
      最大等级: 90,
      成长参数: {
        基础攻击力: { base: 100, growth: 1, divisor: 1 },
        战技倍率: { base: 150, growth: 10, divisor: 1 },
      },
    } as Record<string, unknown>);
    expect((entity["战技倍率"] as number[])).toHaveLength(12);
    expect((entity["战技倍率"] as number[])[0]).toBe(150);
    expect((entity["战技倍率"] as number[])[11]).toBe(150 + 10 * 11);
  });

  it("连携技/终结技倍率物化为 9 级", () => {
    const entity = materializeCharacterEntity({
      name: "技能测试",
      最大等级: 90,
      成长参数: {
        基础攻击力: { base: 100, growth: 1, divisor: 1 },
        连携技倍率: { base: 200, growth: 20, divisor: 1 },
        终结技倍率: { base: 300, growth: 30, divisor: 1 },
      },
    } as Record<string, unknown>);
    expect((entity["连携技倍率"] as number[])).toHaveLength(9);
    expect((entity["终结技倍率"] as number[])).toHaveLength(9);
  });

  it("无成长参数时原样返回", () => {
    const input = { name: "旧角色" };
    const entity = materializeCharacterEntity(input as Record<string, unknown>);
    expect(entity["name"]).toBe("旧角色");
  });
});

describe("materializeWeaponEntity", () => {
  it("从成长参数物化武器属性", () => {
    const entity = materializeWeaponEntity({
      name: "测试武器",
      最大等级: 90,
      成长参数: {
        基础攻击力: { base: 200, growth: 10, divisor: 1 },
      },
    } as Record<string, unknown>);
    expect((entity["基础攻击力"] as number[])).toHaveLength(90);
    expect((entity["基础攻击力"] as number[])[0]).toBe(200);
    expect((entity["基础攻击力"] as number[])[89]).toBe(200 + 10 * 89);
  });
});

describe("sampleEntityAtLevel", () => {
  it("从物化实体中取指定等级的值（character）", () => {
    const entity = materializeCharacterEntity({
      name: "采样测试",
      最大等级: 90,
      成长参数: {
        基础攻击力: { base: 100, growth: 10, divisor: 1 },
      },
    } as Record<string, unknown>);
    const sampled = sampleEntityAtLevel(entity, "character", 1);
    expect(sampled["基础攻击力"]).toBe(100);
    const sampled5 = sampleEntityAtLevel(entity, "character", 5);
    expect(sampled5["基础攻击力"]).toBe(140);
    const sampled90 = sampleEntityAtLevel(entity, "character", 90);
    expect(sampled90["基础攻击力"]).toBe(990);
  });

  it("从物化实体中取指定等级的值（weapon）", () => {
    const entity = materializeWeaponEntity({
      name: "采样武器",
      最大等级: 90,
      成长参数: {
        基础攻击力: { base: 200, growth: 10, divisor: 1 },
      },
    } as Record<string, unknown>);
    const sampled = sampleEntityAtLevel(entity, "weapon", 1);
    expect(sampled["基础攻击力"]).toBe(200);
  });
});
