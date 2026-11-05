import { describe, it, expect } from "vitest";
import { formatOutputValue } from "./outputFormat";

describe("formatOutputValue", () => {
  it("百分比格式 .2% 乘以 100 后保留两位小数", () => {
    expect(formatOutputValue(0.912345, ".2%")).toBe("91.23%");
  });

  it("百分比格式支持任意小数位", () => {
    expect(formatOutputValue(0.912345, ".1%")).toBe("91.2%");
    expect(formatOutputValue(0.912345, ".0%")).toBe("91%");
  });

  it("固定小数位格式 .Nf", () => {
    expect(formatOutputValue(123.456, ".2f")).toBe("123.46");
    expect(formatOutputValue(123.456, ".0f")).toBe("123");
  });

  it("负值百分比保持符号", () => {
    expect(formatOutputValue(-0.05, ".2%")).toBe("-5.00%");
  });

  it("空格式回退到 .4f（与桌面临界默认一致）", () => {
    expect(formatOutputValue(1234.56784, "")).toBe("1234.5678");
    expect(formatOutputValue(1234.56784)).toBe("1234.5678");
  });

  it("无法识别的格式回退到 .4f", () => {
    expect(formatOutputValue(1.23456, "abc")).toBe("1.2346");
  });

  it("undefined / null / NaN 显示占位符", () => {
    expect(formatOutputValue(undefined, ".2%")).toBe("--");
    expect(formatOutputValue(null, ".2%")).toBe("--");
    expect(formatOutputValue(Number.NaN, ".2%")).toBe("--");
  });

  it("整数值按格式输出", () => {
    expect(formatOutputValue(1000, ".2f")).toBe("1000.00");
    expect(formatOutputValue(1, ".2%")).toBe("100.00%");
  });
});
