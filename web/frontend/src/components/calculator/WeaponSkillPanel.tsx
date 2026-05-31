import { Box, Slider, Typography, Paper, Chip } from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";

interface WeaponSkillPanelProps {
  weaponData: Record<string, unknown> | null;
  onChange: (values: Record<string, number>) => void;
}

interface NormalSkillSpec {
  effect: string;
  maxLevel: number;
}

interface SpecialSkillSpec {
  name: string;
  maxLevel: number;
  maxStack: number;
}

export default function WeaponSkillPanel({ weaponData, onChange }: WeaponSkillPanelProps) {
  const normalSkills = useMemo<NormalSkillSpec[]>(() => {
    if (!weaponData) return [];
    const raw = weaponData["normal_skills"];
    if (!Array.isArray(raw)) return [];
    return raw.map((item: unknown) => {
      const obj = item as Record<string, unknown>;
      const curve = obj["curve"];
      const maxLevel = Array.isArray(curve) ? curve.length : 9;
      return { effect: String(obj["effect"] ?? ""), maxLevel };
    });
  }, [weaponData]);

  const specialSkills = useMemo<SpecialSkillSpec[]>(() => {
    if (!weaponData) return [];
    const raw = weaponData["special_skills"];
    if (!Array.isArray(raw)) return [];
    return raw.map((item: unknown) => {
      const obj = item as Record<string, unknown>;
      const curve = obj["curve"];
      const maxLevel = Array.isArray(curve) ? curve.length : 9;
      return {
        name: String(obj["name"] ?? ""),
        maxLevel,
        maxStack: Math.max(1, Number(obj["max_stack"] ?? 1)),
      };
    });
  }, [weaponData]);

  const defaultValues = useMemo(() => {
    const vals: Record<string, number> = {};
    normalSkills.forEach((_, i) => {
      vals[`normal_skill_${i + 1}_level`] = 1;
    });
    specialSkills.forEach((_, i) => {
      vals[`special_skill_${i + 1}_level`] = 1;
      if (specialSkills[i].maxStack > 1) {
        vals[`special_skill_${i + 1}_stack`] = 0;
      }
    });
    return vals;
  }, [normalSkills, specialSkills]);

  const [values, setValues] = useState<Record<string, number>>({});

  useEffect(() => {
    setValues((prev) => {
      const merged = { ...defaultValues };
      for (const k of Object.keys(prev)) {
        if (k in defaultValues) merged[k] = prev[k];
      }
      return merged;
    });
  }, [defaultValues]);

  const handleChange = useCallback(
    (key: string) => (_: Event, v: number | number[]) => {
      const next = { ...values, [key]: v as number };
      setValues(next);
      onChange(next);
    },
    [values, onChange]
  );

  const hasContent = normalSkills.length > 0 || specialSkills.length > 0;
  if (!hasContent) return null;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1, color: "text.secondary" }}>
        武器技能等级
      </Typography>
      {normalSkills.map((ns, i) => (
        <Box key={`n${i}`} sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            技能{i + 1}·{ns.effect}: Lv.{values[`normal_skill_${i + 1}_level`] ?? 1}
          </Typography>
          <Slider
            size="small"
            min={1}
            max={ns.maxLevel}
            step={1}
            value={values[`normal_skill_${i + 1}_level`] ?? 1}
            onChange={handleChange(`normal_skill_${i + 1}_level`)}
            valueLabelDisplay="off"
          />
        </Box>
      ))}
      {specialSkills.map((ss, i) => (
        <Box key={`s${i}`} sx={{ mb: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              特殊·{ss.name}: Lv.{values[`special_skill_${i + 1}_level`] ?? 1}
            </Typography>
            {ss.maxStack > 1 && (
              <Chip label={`${values[`special_skill_${i + 1}_stack`] ?? 0}/${ss.maxStack}层`} size="small" variant="outlined" />
            )}
          </Box>
          <Slider
            size="small"
            min={1}
            max={ss.maxLevel}
            step={1}
            value={values[`special_skill_${i + 1}_level`] ?? 1}
            onChange={handleChange(`special_skill_${i + 1}_level`)}
            valueLabelDisplay="off"
          />
          {ss.maxStack > 1 && (
            <Box sx={{ ml: 2 }}>
              <Typography variant="caption" color="text.secondary">
                叠加层数
              </Typography>
              <Slider
                size="small"
                min={0}
                max={ss.maxStack}
                step={1}
                value={values[`special_skill_${i + 1}_stack`] ?? 0}
                onChange={handleChange(`special_skill_${i + 1}_stack`)}
                valueLabelDisplay="off"
              />
            </Box>
          )}
        </Box>
      ))}
    </Paper>
  );
}
