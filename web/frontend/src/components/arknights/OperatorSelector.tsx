import {
  Autocomplete,
  TextField,
  Box,
  Typography,
  Chip,
  Slider,
} from "@mui/material";

interface OperatorSelectorProps {
  operators: string[];
  selectedOperator: string | null;
  onSelect: (name: string) => void;
  skillLevel: number;
  onSkillLevelChange: (level: number) => void;
  skillMultiplier: number;
  onSkillMultiplierChange: (mult: number) => void;
}

export default function OperatorSelector({
  operators,
  selectedOperator,
  onSelect,
  skillLevel,
  onSkillLevelChange,
  skillMultiplier,
  onSkillMultiplierChange,
}: OperatorSelectorProps) {
  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom color="text.secondary">
        选择干员
      </Typography>
      <Autocomplete
        options={operators}
        value={selectedOperator ?? null}
        onChange={(_e, v) => { if (v) onSelect(v); }}
        renderInput={(params) => (
          <TextField {...params} size="small" placeholder="搜索干员..." />
        )}
        sx={{ mb: 2 }}
      />

      {selectedOperator && (
        <>
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            技能等级（1-7 = 技能等级, 8-10 = 专精1-3）
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
              Lv.{skillLevel}
            </Typography>
            <Slider
              size="small"
              min={1}
              max={10}
              step={1}
              value={skillLevel}
              onChange={(_e, v) => onSkillLevelChange(v as number)}
              valueLabelDisplay="auto"
              marks={[
                { value: 1, label: "1" },
                { value: 7, label: "7" },
                { value: 8, label: "专1" },
                { value: 10, label: "专3" },
              ]}
              sx={{ flex: 1 }}
            />
          </Box>

          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 2 }}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((lv) => (
              <Chip
                key={lv}
                label={lv <= 7 ? `Lv.${lv}` : `专${lv - 7}`}
                size="small"
                variant={skillLevel === lv ? "filled" : "outlined"}
                color={skillLevel === lv ? "primary" : "default"}
                onClick={() => onSkillLevelChange(lv)}
                sx={{ height: 24, cursor: "pointer" }}
              />
            ))}
          </Box>

          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            技能倍率
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
              {skillMultiplier.toFixed(1)}x
            </Typography>
            <Slider
              size="small"
              min={0.1}
              max={5.0}
              step={0.1}
              value={skillMultiplier}
              onChange={(_e, v) => onSkillMultiplierChange(v as number)}
              valueLabelDisplay="auto"
              marks={[
                { value: 1.0, label: "1.0" },
                { value: 2.0, label: "2.0" },
                { value: 3.0, label: "3.0" },
              ]}
              sx={{ flex: 1 }}
            />
          </Box>
        </>
      )}
    </Box>
  );
}
