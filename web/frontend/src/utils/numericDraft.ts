/** 数值输入草稿 — 支持清空、小数中间态与中文输入法全角字符。

受控 `type="number"` 输入框在移动端有两个问题：
1. 清空后会被父组件立刻重置为 0，无法重新输入；
2. 部分输入法数字键盘没有小数点，且全角数字无法解析。

这里把「用户正在输入的原始文本」与「解析后的数值」分开：
草稿允许空串、`-`、`.`、`1.` 等中间态，解析失败时返回 null，
父组件只在拿到有效数值时更新状态。
*/

const FULL_WIDTH_MAP: Record<string, string> = {
  "０": "0",
  "１": "1",
  "２": "2",
  "３": "3",
  "４": "4",
  "５": "5",
  "６": "6",
  "７": "7",
  "８": "8",
  "９": "9",
  "．": ".",
  "。": ".",
  "－": "-",
  "−": "-",
  "﹣": "-",
};

/**
 * 清洗输入草稿：保留一个可选前导负号、一个可选小数点与数字。
 *
 * 全角数字/句号/负号转为半角；单位、空格等字符直接丢弃；
 * 多余的小数点与负号丢弃；整数部分允许多余前导零但会被去掉。
 */
export function sanitizeNumericDraft(raw: string): string {
  let body = "";
  let hasDot = false;
  let hasSign = false;

  for (const char of raw) {
    const normalized = FULL_WIDTH_MAP[char] ?? char;
    if (normalized >= "0" && normalized <= "9") {
      body += normalized;
    } else if (normalized === "-" && !hasSign && body.length === 0) {
      body = "-";
      hasSign = true;
    } else if (normalized === "." && !hasDot) {
      body += ".";
      hasDot = true;
    }
  }

  const sign = body.startsWith("-") ? "-" : "";
  let digits = sign ? body.slice(1) : body;
  const dotIndex = digits.indexOf(".");
  if (dotIndex === -1) {
    digits = digits.replace(/^0+(?=\d)/, "");
  } else {
    const integerPart = digits.slice(0, dotIndex).replace(/^0+(?=\d)/, "");
    digits = `${integerPart}.${digits.slice(dotIndex + 1)}`;
  }
  return `${sign}${digits}`;
}

/**
 * 解析草稿为数值；空串、单独的负号/小数点等中间态返回 null。
 */
export function parseNumericDraft(draft: string): number | null {
  const sanitized = sanitizeNumericDraft(draft);
  if (!/\d/.test(sanitized)) return null;
  const value = Number.parseFloat(sanitized);
  return Number.isFinite(value) ? value : null;
}

/**
 * 按上下限夹紧数值；无效值回退到 fallback。
 */
export function clampNumber(
  value: number | null,
  min: number | null | undefined,
  max: number | null | undefined,
  fallback: number,
): number {
  if (value === null || !Number.isFinite(value)) return fallback;
  let result = value;
  if (min !== null && min !== undefined) result = Math.max(result, min);
  if (max !== null && max !== undefined) result = Math.min(result, max);
  return result;
}

/**
 * 把数值格式化为输入框显示文本；非有限数字返回空串。
 *
 * 先按 6 位小数取整再转字符串，避免滑块产生的 `0.30000000000000004`
 * 之类的浮点噪音出现在输入框里。
 */
export function formatNumberDraft(value: number): string {
  if (!Number.isFinite(value)) return "";
  return String(Math.round(value * 1e6) / 1e6);
}
