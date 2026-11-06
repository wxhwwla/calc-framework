import { useCallback, useState } from "react";
import type { SxProps, Theme } from "@mui/material";
import { InputAdornment, TextField } from "@mui/material";
import {
  clampNumber,
  formatNumberDraft,
  parseNumericDraft,
  sanitizeNumericDraft,
} from "../../utils/numericDraft";

interface NumberFieldProps {
  value: number;
  onChange: (value: number) => void;
  /** 失焦时调用（在数值归一之后），用于触发重算等动作。 */
  onBlur?: () => void;
  min?: number | null;
  max?: number | null;
  /** 只接受整数；非整数中间态不向上提交。 */
  integer?: boolean;
  disabled?: boolean;
  size?: "small" | "medium";
  fullWidth?: boolean;
  /** 输入框右侧单位，例如 %。 */
  suffix?: string;
  /** 浮动标签；不传则由父组件自行渲染标题。 */
  label?: string;
  placeholder?: string;
  ariaLabel?: string;
  /** 聚焦时全选当前值，便于手机上直接输入新值。 */
  selectOnFocus?: boolean;
  /** 透传键盘事件，供「回车即计算」等快捷操作使用。 */
  onKeyDown?: React.KeyboardEventHandler<HTMLInputElement>;
  sx?: SxProps<Theme>;
}

/**
 * 移动端友好的数值输入框。
 *
 * 与直接使用 `<TextField type="number">` 不同，这里维护「输入草稿」：
 * 用户可以把输入框清空、输入 `.`/`-` 等中间态，不会被父组件立刻重置为 0；
 * 失焦时按 min/max 归一，并把最终数值写回父组件。
 */
export default function NumberField({
  value,
  onChange,
  onBlur,
  min = null,
  max = null,
  integer = false,
  disabled = false,
  size = "small",
  fullWidth = false,
  suffix,
  label,
  placeholder,
  ariaLabel,
  selectOnFocus = true,
  onKeyDown,
  sx,
}: NumberFieldProps) {
  const [draft, setDraft] = useState<string | null>(null);
  const display = draft ?? formatNumberDraft(value);

  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const sanitized = sanitizeNumericDraft(event.target.value);
      setDraft(sanitized);
      const parsed = parseNumericDraft(sanitized);
      if (parsed === null) return;
      if (integer && !Number.isInteger(parsed)) return;
      onChange(parsed);
    },
    [integer, onChange],
  );

  const handleBlur = useCallback(
    (event: React.FocusEvent<HTMLInputElement>) => {
      const parsed = parseNumericDraft(event.target.value);
      let final = clampNumber(parsed, min, max, value);
      if (integer) final = Math.round(final);
      setDraft(null);
      if (final !== value) onChange(final);
      onBlur?.();
    },
    [integer, max, min, onBlur, onChange, value],
  );

  return (
    <TextField
      type="text"
      size={size}
      fullWidth={fullWidth}
      value={display}
      disabled={disabled}
      label={label}
      placeholder={placeholder}
      onChange={handleChange}
      onBlur={handleBlur}
      onKeyDown={onKeyDown}
      onFocus={(event: React.FocusEvent<HTMLInputElement>) => {
        if (selectOnFocus) event.target.select();
      }}
      autoComplete="off"
      slotProps={{
        htmlInput: {
          inputMode: integer ? "numeric" : "decimal",
          "aria-label": ariaLabel ?? label,
          enterKeyHint: "done",
        },
      }}
      InputProps={
        suffix
          ? { endAdornment: <InputAdornment position="end">{suffix}</InputAdornment> }
          : undefined
      }
      sx={sx}
    />
  );
}
