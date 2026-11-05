/** 输出值格式化 — 与 Python 端 `f"{value:{format}}"` 约定保持一致。 */

/**
 * 按 DAG 输出的 format 字段格式化数值。
 *
 * 支持 `.N%`（乘 100 加百分号）与 `.Nf`（固定小数位）；格式为空或无法
 * 识别时回退到 `.4f`，与桌面查看器未声明格式时的默认值一致。
 *
 * @param value 输出数值；缺失或 NaN 时返回占位符 `--`。
 * @param format DAG outputs 中的格式字符串，如 `.2%`、`.2f`。
 */
export function formatOutputValue(value: number | null | undefined, format?: string): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  const spec = (format || "").trim();
  const percent = /^\.(\d+)%$/.exec(spec);
  if (percent) {
    return `${(value * 100).toFixed(Number(percent[1]))}%`;
  }

  const fixed = /^\.(\d+)f$/.exec(spec);
  if (fixed) {
    return value.toFixed(Number(fixed[1]));
  }

  return value.toFixed(4);
}
