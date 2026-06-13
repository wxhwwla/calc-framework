import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, color: "text.secondary" }}>
        {t("searchSettings.title")}
      </Typography>

      <Box sx={{ mb: 1.5 }}>
        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
          {t("searchSettings.topResults", { n: settings.topN })}
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
          {t("searchSettings.parallelWorkers", { n: settings.workers })}
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
        <InputLabel>{t("searchSettings.damageScope")}</InputLabel>
        <Select
          value={settings.damageComponent}
          label={t("searchSettings.damageScope")}
          onChange={(e) => onChange({ ...settings, damageComponent: e.target.value })}
        >
          <MenuItem value="skill_and_abnormal">{t("multiSkill.skillAndAbnormal")}</MenuItem>
          <MenuItem value="skill_only">{t("multiSkill.skillOnly")}</MenuItem>
          <MenuItem value="abnormal_only">{t("multiSkill.abnormalOnly")}</MenuItem>
        </Select>
      </FormControl>
    </Paper>
  );
}

export type { SearchSettings };
