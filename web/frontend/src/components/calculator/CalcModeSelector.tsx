import { FormControl, InputLabel, Select, MenuItem } from "@mui/material";

const CALC_MODES = [
  { label: "单段伤害计算", mode: "single_hit" },
  { label: "乘区快照", mode: "zone_snapshot" },
  { label: "单技能遍历(快速预览)", mode: "single_skill_search" },
  { label: "多技能遍历(快速预览)", mode: "multi_skill_search" },
];

interface CalcModeSelectorProps {
  value: string;
  onChange: (mode: string) => void;
}

export default function CalcModeSelector({ value, onChange }: CalcModeSelectorProps) {
  return (
    <FormControl fullWidth size="small">
      <InputLabel>计算模式</InputLabel>
      <Select value={value} label="计算模式" onChange={(e) => onChange(e.target.value)}>
        {CALC_MODES.map((m) => (
          <MenuItem key={m.mode} value={m.mode}>
            {m.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
