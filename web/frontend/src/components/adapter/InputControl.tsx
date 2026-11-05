import {
  Box,
  FormControl,
  FormControlLabel,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import type { ControlSpec } from "../../utils/controlInference";

interface InputControlProps {
  spec: ControlSpec;
  value: number | boolean | string;
  onChange: (value: number | boolean | string) => void;
  /** 由 entity_input_rules 判定无关时禁用控件。 */
  disabled?: boolean;
}

/** 单个 user_input 控件 — 支持后缀单位与禁用态。 */
export default function InputControl({ spec, value, onChange, disabled = false }: InputControlProps) {
  const numValue = typeof value === "number" ? value : typeof spec.default === "number" ? spec.default : 0;
  const boolValue = typeof value === "boolean" ? value : Boolean(spec.default);

  switch (spec.widget) {
    case "spinbox":
    case "text":
      return (
        <TextField
          type="number"
          size="small"
          fullWidth
          value={numValue}
          disabled={disabled}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            const parsed = parseFloat(e.target.value);
            onChange(Number.isNaN(parsed) ? 0 : parsed);
          }}
          inputProps={{
            step: spec.step,
            min: spec.minVal ?? undefined,
            max: spec.maxVal ?? undefined,
          }}
          InputProps={
            spec.suffix
              ? { endAdornment: <InputAdornment position="end">{spec.suffix}</InputAdornment> }
              : undefined
          }
        />
      );

    case "slider":
      return (
        <Box sx={{ px: 1 }}>
          <Slider
            value={numValue}
            min={spec.minVal ?? 0}
            max={spec.maxVal ?? 100}
            step={spec.step}
            disabled={disabled}
            onChange={(_e, v) => onChange(v as number)}
            valueLabelDisplay="auto"
          />
        </Box>
      );

    case "switch":
      return (
        <FormControlLabel
          disabled={disabled}
          control={
            <Switch checked={boolValue} onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.checked)} />
          }
          label={spec.description || spec.label.split(".").pop() || ""}
        />
      );

    case "dropdown":
      return (
        <FormControl fullWidth size="small" disabled={disabled}>
          <InputLabel>{spec.description || spec.label}</InputLabel>
          <Select
            value={String(value)}
            label={spec.description || spec.label}
            onChange={(e: SelectChangeEvent) => onChange(e.target.value)}
          >
            {spec.options.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      );

    default:
      return (
        <Typography variant="body2" color="text.secondary">
          {String(value)}
        </Typography>
      );
  }
}
