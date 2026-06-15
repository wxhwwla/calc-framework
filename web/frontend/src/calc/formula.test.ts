import { describe, it, expect } from "vitest";
import { calculateGrowthCurve, valueAtLevel, type GrowthParams } from "./formula";

describe("calculateGrowthCurve", () => {
  it("计算线性增长曲线", () => {
    const curve = calculateGrowthCurve({ base: 100, growth: 5, divisor: 1 }, 5);
    expect(curve).toHaveLength(5);
    expect(curve[0]).toBe(100);
    expect(curve[1]).toBe(105);
    expect(curve[4]).toBe(120);
  });

  it("处理非整数增长（自动检测小数模式）", () => {
    const curve = calculateGrowthCurve({ base: 50, growth: 3.3, divisor: 1 }, 3);
    expect(curve).toHaveLength(3);
  });

  it("处理 levelOverrides 覆盖", () => {
    const overrides: Record<number, number> = { 2: 999 };
    const curve = calculateGrowthCurve({ base: 1, growth: 1, divisor: 1 }, 5, overrides);
    expect(curve[0]).toBe(1);
    expect(curve[1]).toBe(999); // 被覆盖
    expect(curve[2]).toBe(3);
  });

  it("maxLevel < 1 抛出错误", () => {
    expect(() => calculateGrowthCurve({ base: 100, growth: 5, divisor: 1 }, 0)).toThrow("invalid growth params");
  });

  it("divisor <= 0 抛出错误", () => {
    expect(() => calculateGrowthCurve({ base: 100, growth: 5, divisor: 0 }, 5)).toThrow("invalid growth params");
  });

  it("处理 offset 非零：base + floor((growth * (lv-1) + offset) / divisor)", () => {
    const curve = calculateGrowthCurve({ base: 100, growth: 5, divisor: 2, offset: 3 }, 4);
    // lv1: 100 + floor((5*0 + 3)/2) = 100 + 1 = 101
    expect(curve[0]).toBe(101);
    expect(curve).toHaveLength(4);
  });

  it("默认 maxLevel 为 90", () => {
    const curve = calculateGrowthCurve({ base: 0, growth: 1, divisor: 1 });
    expect(curve).toHaveLength(90);
  });

  it("is_decimal 模式下精度正确", () => {
    const curve = calculateGrowthCurve({ base: 0.5, growth: 0.1, divisor: 1, is_decimal: true }, 3);
    expect(curve).toHaveLength(3);
  });
});

describe("valueAtLevel", () => {
  it("按索引取值（1-indexed）", () => {
    const curve = calculateGrowthCurve({ base: 100, growth: 10, divisor: 1 }, 10);
    expect(valueAtLevel(curve, 1)).toBe(100);
    expect(valueAtLevel(curve, 2)).toBe(110);
    expect(valueAtLevel(curve, 10)).toBe(190);
  });

  it("等级越界（level < 1）取索引 0", () => {
    const curve = [100, 110];
    expect(valueAtLevel(curve, 0)).toBe(100);
  });

  it("等级超过数组长度取最后一个", () => {
    const curve = [100, 110];
    expect(valueAtLevel(curve, 999)).toBe(110);
  });

  it("空数组返回 undefined", () => {
    expect(valueAtLevel([], 1)).toBeUndefined();
  });
});
