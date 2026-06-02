import { useState, useMemo, useCallback } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";

const SKILL_TYPES = ["战技", "连携技", "终结技"] as const;
const SKILL_FIELDS = ["战技倍率", "连携技倍率", "终结技倍率"] as const;

export interface SegmentSpec {
  key: string;
  label: string;
  skillType: string;
  segmentIndex: number;
  multiplierPercent: number;
  damageType: string;
}

export interface MultiSkillSettings {
  useManualCounts: boolean;
  manualCounts: Record<string, number>;
  damageComponentMode: string;
  useExpectedCrit: boolean;
}

interface MultiSkillPanelProps {
  charData: Record<string, unknown> | null;
  skillLevels?: [number, number, number];
  onChange?: (settings: MultiSkillSettings) => void;
}

function extractSegmentSpecs(
  charData: Record<string, unknown>,
  skillLevels: [number, number, number],
): SegmentSpec[] {
  const specs: SegmentSpec[] = [];

  for (let s = 0; s < SKILL_TYPES.length; s++) {
    const skillType = SKILL_TYPES[s];
    const fieldName = SKILL_FIELDS[s];
    const skillLevel = skillLevels[s];
    if (skillLevel <= 0) continue;

    const segments = charData[fieldName];
    if (!Array.isArray(segments) || segments.length === 0) continue;

    for (let segIdx = 0; segIdx < segments.length; segIdx++) {
      const seg = segments[segIdx];
      if (!Array.isArray(seg) || seg.length === 0) continue;

      const levelIdx = Math.min(skillLevel - 1, seg.length - 1);
      const raw = seg[levelIdx];
      if (raw == null || raw === 0) continue;

      const key = `${skillType}:${segIdx + 1}`;
      const multiplierPct = (Number(raw) / 100) * 100;
      const damageType = extractDamageType(charData, s, segIdx);

      specs.push({
        key,
        label: `${skillType} 第${segIdx + 1}段 (${Math.round(multiplierPct)}%) · ${damageType}`,
        skillType,
        segmentIndex: segIdx + 1,
        multiplierPercent: multiplierPct,
        damageType,
      });
    }
  }

  return specs;
}

const DAMAGE_TYPE_FIELDS = ["战技段伤害类型", "连携技段伤害类型", "终结技段伤害类型"] as const;

function extractDamageType(
  charData: Record<string, unknown>,
  skillIdx: number,
  segIdx: number,
): string {
  const field = charData[DAMAGE_TYPE_FIELDS[skillIdx]];
  if (Array.isArray(field)) {
    const val = field[segIdx];
    if (typeof val === "string") return val;
  }
  return "物理";
}

export default function MultiSkillPanel({
  charData,
  skillLevels = [0, 0, 0],
  onChange,
}: MultiSkillPanelProps) {
  const [useManual, setUseManual] = useState(false);
  const [damageComponentMode, setDamageComponentMode] = useState("skill_and_abnormal");
  const [counts, setCounts] = useState<Record<string, number>>({});

  const segmentSpecs = useMemo(() => {
    if (!charData) return [];
    return extractSegmentSpecs(charData, skillLevels);
  }, [charData, skillLevels]);

  const notifyChange = useCallback(
    (overrides?: Partial<MultiSkillSettings>) => {
      if (!onChange) return;
      onChange({
        useManualCounts: overrides?.useManualCounts ?? useManual,
        manualCounts: overrides?.manualCounts ?? counts,
        damageComponentMode: overrides?.damageComponentMode ?? damageComponentMode,
        useExpectedCrit: false,
      });
    },
    [onChange, useManual, counts, damageComponentMode],
  );

  const handleToggleManual = useCallback(
    (checked: boolean) => {
      setUseManual(checked);
      if (checked && segmentSpecs.length > 0) {
        const initial: Record<string, number> = {};
        segmentSpecs.forEach((spec) => {
          initial[spec.key] = 0;
        });
        setCounts(initial);
        notifyChange({ useManualCounts: checked, manualCounts: initial });
      } else {
        notifyChange({ useManualCounts: checked });
      }
    },
    [segmentSpecs, notifyChange],
  );

  const handleCountChange = useCallback(
    (key: string, value: number) => {
      const next = { ...counts, [key]: Math.max(0, value || 0) };
      setCounts(next);
      notifyChange({ manualCounts: next });
    },
    [counts, notifyChange],
  );

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        多技能次数
      </Typography>

      <FormControlLabel
        control={
          <Checkbox
            checked={useManual}
            onChange={(e) => handleToggleManual(e.target.checked)}
            size="small"
          />
        }
        label={<Typography variant="body2">使用手动次数</Typography>}
      />

      {useManual && (
        <Box sx={{ mt: 1, display: "flex", flexDirection: "column", gap: 1.5 }}>
          {segmentSpecs.length === 0 && (
            <Typography variant="caption" color="text.secondary">
              请先选择角色并设置技能等级
            </Typography>
          )}

          {segmentSpecs.map((spec) => (
            <Box
              key={spec.key}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              <Typography
                variant="body2"
                sx={{ minWidth: { xs: 140, sm: 200 }, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
              >
                {spec.label}
              </Typography>
              <TextField
                size="small"
                type="number"
                value={counts[spec.key] ?? 0}
                onChange={(e) => handleCountChange(spec.key, parseInt(e.target.value) || 0)}
                slotProps={{ htmlInput: { min: 0, max: 99, step: 1 } }}
                sx={{ width: 80 }}
              />
              <Typography variant="caption" color="text.secondary">
                次
              </Typography>
            </Box>
          ))}
        </Box>
      )}

      <Box sx={{ mt: 2, display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>伤害口径</InputLabel>
          <Select
            value={damageComponentMode}
            label="伤害口径"
            onChange={(e) => {
              setDamageComponentMode(e.target.value);
              notifyChange({ damageComponentMode: e.target.value });
            }}
          >
            <MenuItem value="skill_and_abnormal">技能+异常</MenuItem>
            <MenuItem value="skill_only">仅技能</MenuItem>
            <MenuItem value="abnormal_only">仅异常</MenuItem>
          </Select>
        </FormControl>
      </Box>
    </Paper>
  );
}
