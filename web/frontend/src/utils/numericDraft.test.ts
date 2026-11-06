import { describe, expect, it } from "vitest";
import {
  clampNumber,
  formatNumberDraft,
  parseNumericDraft,
  sanitizeNumericDraft,
} from "./numericDraft";

describe("sanitizeNumericDraft", () => {
  it("保留合法数字与小数", () => {
    expect(sanitizeNumericDraft("12.5")).toBe("12.5");
    expect(sanitizeNumericDraft("0.5")).toBe("0.5");
    expect(sanitizeNumericDraft("-3.25")).toBe("-3.25");
  });

  it("允许输入过程中的中间态", () => {
    expect(sanitizeNumericDraft("")).toBe("");
    expect(sanitizeNumericDraft("-")).toBe("-");
    expect(sanitizeNumericDraft(".")).toBe(".");
    expect(sanitizeNumericDraft("1.")).toBe("1.");
    expect(sanitizeNumericDraft(".5")).toBe(".5");
  });

  it("把全角数字与句号转为半角（中文输入法）", () => {
    expect(sanitizeNumericDraft("１２．５")).toBe("12.5");
    expect(sanitizeNumericDraft("０。５")).toBe("0.5");
    expect(sanitizeNumericDraft("－７")).toBe("-7");
  });

  it("去掉单位、空格等无关字符", () => {
    expect(sanitizeNumericDraft(" 12.5% ")).toBe("12.5");
    expect(sanitizeNumericDraft("abc")).toBe("");
    expect(sanitizeNumericDraft("1 000")).toBe("1000");
  });

  it("最多保留一个小数点与一个前导负号", () => {
    expect(sanitizeNumericDraft("1.2.3")).toBe("1.23");
    expect(sanitizeNumericDraft("--5")).toBe("-5");
    expect(sanitizeNumericDraft("5-2")).toBe("52");
  });

  it("去除多余前导零，同时保留 0.x", () => {
    expect(sanitizeNumericDraft("025")).toBe("25");
    expect(sanitizeNumericDraft("00.5")).toBe("0.5");
    expect(sanitizeNumericDraft("-00.5")).toBe("-0.5");
    expect(sanitizeNumericDraft("0")).toBe("0");
  });
});

describe("parseNumericDraft", () => {
  it("解析完整数字", () => {
    expect(parseNumericDraft("12.5")).toBe(12.5);
    expect(parseNumericDraft("1.")).toBe(1);
    expect(parseNumericDraft(".5")).toBe(0.5);
    expect(parseNumericDraft("-0.5")).toBe(-0.5);
    expect(parseNumericDraft("025")).toBe(25);
  });

  it("中间态返回 null，避免把空输入当成 0", () => {
    expect(parseNumericDraft("")).toBeNull();
    expect(parseNumericDraft("-")).toBeNull();
    expect(parseNumericDraft(".")).toBeNull();
    expect(parseNumericDraft("abc")).toBeNull();
  });
});

describe("clampNumber", () => {
  it("按上下限夹紧", () => {
    expect(clampNumber(150, 0, 100, 0)).toBe(100);
    expect(clampNumber(-5, 0, null, 0)).toBe(0);
    expect(clampNumber(50, null, 100, 0)).toBe(50);
  });

  it("无效值回退到 fallback", () => {
    expect(clampNumber(null, 1, 90, 8)).toBe(8);
  });
});

describe("formatNumberDraft", () => {
  it("输出稳定文本", () => {
    expect(formatNumberDraft(25)).toBe("25");
    expect(formatNumberDraft(0.5)).toBe("0.5");
    expect(formatNumberDraft(-3.25)).toBe("-3.25");
  });

  it("消除浮点误差噪音", () => {
    expect(formatNumberDraft(0.30000000000000004)).toBe("0.3");
    expect(formatNumberDraft(1.0000000000000002)).toBe("1");
  });

  it("非有限数字返回空串", () => {
    expect(formatNumberDraft(Number.NaN)).toBe("");
    expect(formatNumberDraft(Number.POSITIVE_INFINITY)).toBe("");
  });
});
