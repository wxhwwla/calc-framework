import { Box, Typography, Slider, FormControl, InputLabel, Select, MenuItem, Paper } from "@mui/material";

interface SearchSettings {
  topN: number;
  workers: number;
  damageComponent: string;
}

interface SearchSettingsPanelProps {
  settings: SearchSettings;
  onChange: (settings: SearchSettings) => void;
}

export default function SearchSettingsPanel({ settings, onChange }: SearchSettingsPanelProps) {
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, color: "text.secondary" }}>
        搜索设置
      </Typography>

      <Box sx={{ mb: 1.5 }}>
        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
          前 {settings.topN} 条结果
        </Typography>
        <Slider
          size="small"
          min={1}
          max={50}
          step={1}
          value={settings.topN}
          onChange={(_, v) => onChange({ ...settings, topN: v as number })}
          valueLabelDisplay="auto"
        />
      </Box>

      <Box sx={{ mb: 1.5 }}>
        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
          并行线程: {settings.workers}
        </Typography>
        <Slider
          size="small"
          min={1}
          max={16}
          step={1}
          value={settings.workers}
          onChange={(_, v) => onChange({ ...settings, workers: v as number })}
          valueLabelDisplay="auto"
        />
      </Box>

      <FormControl fullWidth size="small">
        <InputLabel>伤害口径</InputLabel>
        <Select
          value={settings.damageComponent}
          label="伤害口径"
          onChange={(e) => onChange({ ...settings, damageComponent: e.target.value })}
        >
          <MenuItem value="skill_and_abnormal">技能+异常</MenuItem>
          <MenuItem value="skill_only">仅技能</MenuItem>
          <MenuItem value="abnormal_only">仅异常</MenuItem>
        </Select>
      </FormControl>
    </Paper>
  );
}

export type { SearchSettings };
