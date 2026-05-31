import { useState, useCallback } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  FormControlLabel,
  Checkbox,
  Collapse,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";

const PHYSICAL_TYPES = ["侵蚀", "灼烧", "冻伤", "战栗"];
const SPELL_TYPES = ["侵蚀", "灼烧"];

export interface CritAndAbnormalSettings {
  extraCritRate: number;
  extraCritDamage: number;
  includeConditionalEquipmentCrit: boolean;
  physicalAbnormalCounts: Record<string, number>;
  spellAbnormalCounts: Record<string, number>;
}

interface CritAndAbnormalPanelProps {
  onChange?: (settings: CritAndAbnormalSettings) => void;
}

function buildAbnormalKey(type: string, level: number): string {
  return `${type}:${level}`;
}

export default function CritAndAbnormalPanel({ onChange }: CritAndAbnormalPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [extraCritRate, setExtraCritRate] = useState(0);
  const [extraCritDamage, setExtraCritDamage] = useState(0);
  const [includeConditionalCrit, setIncludeConditionalCrit] = useState(false);
  const [physCounts, setPhysCounts] = useState<Record<string, number>>({});
  const [spellCounts, setSpellCounts] = useState<Record<string, number>>({});

  const notify = useCallback(
    (overrides?: Partial<CritAndAbnormalSettings>) => {
      if (!onChange) return;
      onChange({
        extraCritRate: overrides?.extraCritRate ?? extraCritRate,
        extraCritDamage: overrides?.extraCritDamage ?? extraCritDamage,
        includeConditionalEquipmentCrit: overrides?.includeConditionalEquipmentCrit ?? includeConditionalCrit,
        physicalAbnormalCounts: overrides?.physicalAbnormalCounts ?? physCounts,
        spellAbnormalCounts: overrides?.spellAbnormalCounts ?? spellCounts,
      });
    },
    [onChange, extraCritRate, extraCritDamage, includeConditionalCrit, physCounts, spellCounts],
  );

  const handlePhysCount = useCallback(
    (type: string, level: number, value: number) => {
      const key = buildAbnormalKey(type, level);
      const next = { ...physCounts, [key]: Math.max(0, value || 0) };
      setPhysCounts(next);
      notify({ physicalAbnormalCounts: next });
    },
    [physCounts, notify],
  );

  const handleSpellCount = useCallback(
    (type: string, level: number, value: number) => {
      const key = buildAbnormalKey(type, level);
      const next = { ...spellCounts, [key]: Math.max(0, value || 0) };
      setSpellCounts(next);
      notify({ spellAbnormalCounts: next });
    },
    [spellCounts, notify],
  );

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Box
        sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}
        onClick={() => setExpanded(!expanded)}
      >
        <Typography variant="subtitle2">暴击与异常</Typography>
        {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ mt: 1.5, display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="caption" color="text.secondary">暴击微调</Typography>
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              size="small"
              label="额外暴击率 (%)"
              type="number"
              value={extraCritRate}
              onChange={(e) => {
                const v = parseFloat(e.target.value) || 0;
                setExtraCritRate(v);
                notify({ extraCritRate: v });
              }}
              slotProps={{ htmlInput: { min: 0, max: 100, step: 1 } }}
              sx={{ width: 140 }}
            />
            <TextField
              size="small"
              label="额外暴伤 (%)"
              type="number"
              value={extraCritDamage}
              onChange={(e) => {
                const v = parseFloat(e.target.value) || 0;
                setExtraCritDamage(v);
                notify({ extraCritDamage: v });
              }}
              slotProps={{ htmlInput: { min: 0, max: 500, step: 5 } }}
              sx={{ width: 140 }}
            />
          </Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={includeConditionalCrit}
                onChange={(e) => {
                  setIncludeConditionalCrit(e.target.checked);
                  notify({ includeConditionalEquipmentCrit: e.target.checked });
                }}
                size="small"
              />
            }
            label={<Typography variant="body2">包含条件性装备暴击</Typography>}
          />

          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>物理异常矩阵</Typography>
          <AbnormalGrid types={PHYSICAL_TYPES} maxLevel={5} onCountChange={handlePhysCount} />

          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>法术异常矩阵</Typography>
          <AbnormalGrid types={SPELL_TYPES} maxLevel={4} onCountChange={handleSpellCount} />
        </Box>
      </Collapse>
    </Paper>
  );
}

interface AbnormalGridProps {
  types: string[];
  maxLevel: number;
  onCountChange: (type: string, level: number, value: number) => void;
}

function AbnormalGrid({ types, maxLevel, onCountChange }: AbnormalGridProps) {
  return (
    <Box sx={{ overflowX: "auto" }}>
      <Box sx={{ display: "grid", gridTemplateColumns: `120px repeat(${maxLevel}, 60px)`, gap: 0.5, alignItems: "center" }}>
        <Typography variant="caption" color="text.secondary" />
        {Array.from({ length: maxLevel }, (_, i) => (
          <Typography key={i} variant="caption" color="text.secondary" sx={{ textAlign: "center" }}>
            Lv.{i + 1}
          </Typography>
        ))}
        {types.map((type) => (
          <>
            <Typography key={`label-${type}`} variant="body2" sx={{ fontSize: "0.75rem" }}>
              {type}
            </Typography>
            {Array.from({ length: maxLevel }, (_, i) => (
              <TextField
                key={`${type}-${i}`}
                size="small"
                type="number"
                onChange={(e) => onCountChange(type, i + 1, parseInt(e.target.value) || 0)}
                slotProps={{ htmlInput: { min: 0, max: 99, step: 1, style: { textAlign: "center", fontSize: "0.75rem" } } }}
                sx={{ width: 56 }}
              />
            ))}
          </>
        ))}
      </Box>
    </Box>
  );
}
