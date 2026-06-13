import { Box, Slider, Typography, Paper } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface SkillLevelPanelProps {
  charData: Record<string, unknown> | null;
  onChange: (levels: Record<string, number>) => void;
}

const SKILL_DATA_KEYS = [
  { key: "skill_1_level", i18nKey: "totalDamage.skillTypes.combatSkill", dataKey: "战技倍率" },
  { key: "skill_2_level", i18nKey: "totalDamage.skillTypes.chainSkill", dataKey: "连携技倍率" },
  { key: "skill_3_level", i18nKey: "totalDamage.skillTypes.finisher", dataKey: "终结技倍率" },
] as const;

export default function SkillLevelPanel({ charData, onChange }: SkillLevelPanelProps) {
  const { t } = useTranslation();
  const [levels, setLevels] = useState<Record<string, number>>({
    skill_1_level: 8,
    skill_2_level: 8,
    skill_3_level: 8,
  });

  useEffect(() => {
    if (!charData) return;
    const next: Record<string, number> = {};
    for (const sk of SKILL_DATA_KEYS) {
      const arr = charData[sk.dataKey];
      const hasData = Array.isArray(arr) && arr.length > 0;
      next[sk.key] = hasData ? 8 : 0;
    }
    setLevels((prev) => ({ ...prev, ...next }));
  }, [charData]);

  const handleSlider = useCallback(
    (key: string) => (_: Event, value: number | number[]) => {
      const v = value as number;
      const next = { ...levels, [key]: v };
      setLevels(next);
      onChange(next);
    },
    [levels, onChange]
  );

  const skillRows = SKILL_DATA_KEYS.filter((sk) => {
    if (!charData) return true;
    const arr = charData[sk.dataKey];
    return Array.isArray(arr) && arr.length > 0;
  });

  if (skillRows.length === 0) return null;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, color: "text.secondary" }}>
        {t("compute.skillLevel")}
      </Typography>
      {skillRows.map((sk) => (
        <Box key={sk.key} sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {t(sk.i18nKey)}: Lv.{levels[sk.key] ?? 1}
          </Typography>
          <Slider
            size="small"
            min={1}
            max={12}
            step={1}
            value={levels[sk.key] ?? 8}
            onChange={handleSlider(sk.key)}
            valueLabelDisplay="off"
          />
        </Box>
      ))}
    </Paper>
  );
}
