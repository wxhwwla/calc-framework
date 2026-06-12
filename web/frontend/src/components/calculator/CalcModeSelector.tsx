import { useMemo } from "react";
import { FormControl, InputLabel, Select, MenuItem } from "@mui/material";
import { useTranslation } from "react-i18next";

interface CalcModeSelectorProps {
  value: string;
  onChange: (mode: string) => void;
}

export default function CalcModeSelector({ value, onChange }: CalcModeSelectorProps) {
  const { t } = useTranslation();
  const calcModes = useMemo(() => [
    { label: t("compute.singleHit"), mode: "single_hit" },
    { label: t("compute.zoneSnapshot"), mode: "zone_snapshot" },
    { label: t("compute.singleSkillPreview"), mode: "single_skill_search" },
    { label: t("compute.multiSkillPreview"), mode: "multi_skill_search" },
  ], [t]);

  return (
    <FormControl fullWidth size="small">
      <InputLabel>{t("compute.calcMode")}</InputLabel>
      <Select value={value} label={t("compute.calcMode")} onChange={(e) => onChange(e.target.value)}>
        {calcModes.map((m) => (
          <MenuItem key={m.mode} value={m.mode}>
            {m.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
