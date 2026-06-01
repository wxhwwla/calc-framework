import { useState, useCallback, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";

export interface CritAndAbnormalSettings {
  extraCritRate: number;
  extraCritDamage: number;
  includeConditionalEquipmentCrit: boolean;
  physicalAbnormalCounts: Record<string, number>;
  spellAbnormalCounts: Record<string, number>;
}

interface MatrixRowSpec {
  label: string;
  abnormal_key: string;
  ui_levels: number[];
}

interface CritAndAbnormalPanelProps {
  onChange?: (settings: CritAndAbnormalSettings) => void;
}

export default function CritAndAbnormalPanel({ onChange }: CritAndAbnormalPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [extraCritRate, setExtraCritRate] = useState(0);
  const [extraCritDamage, setExtraCritDamage] = useState(0);
  const [includeConditionalCrit, setIncludeConditionalCrit] = useState(false);
  const [physCounts, setPhysCounts] = useState<Record<string, number>>({});
  const [spellCounts, setSpellCounts] = useState<Record<string, number>>({});
  const [physSpecs, setPhysSpecs] = useState<MatrixRowSpec[]>([]);
  const [spellSpecs, setSpellSpecs] = useState<MatrixRowSpec[]>([]);
  const [hint, setHint] = useState("");

  useEffect(() => {
    fetch("/api/manual-buff/abnormal-matrix-specs")
      .then((r) => r.json())
      .then((data) => {
        setPhysSpecs(data.physical ?? []);
        setSpellSpecs(data.spell ?? []);
        setHint(String(data.hint ?? ""));
      })
      .catch(() => {});
  }, []);

  const notify = useCallback(
    (overrides?: Partial<CritAndAbnormalSettings>) => {
      if (!onChange) return;
      onChange({
        extraCritRate: overrides?.extraCritRate ?? extraCritRate,
        extraCritDamage: overrides?.extraCritDamage ?? extraCritDamage,
        includeConditionalEquipmentCrit:
          overrides?.includeConditionalEquipmentCrit ?? includeConditionalCrit,
        physicalAbnormalCounts: overrides?.physicalAbnormalCounts ?? physCounts,
        spellAbnormalCounts: overrides?.spellAbnormalCounts ?? spellCounts,
      });
    },
    [onChange, extraCritRate, extraCritDamage, includeConditionalCrit, physCounts, spellCounts],
  );

  const setMatrixCount = useCallback(
    (
      kind: "physical" | "spell",
      key: string,
      uiLevel: number,
      value: number,
    ) => {
      const mapKey = `${key}:${uiLevel}`;
      if (kind === "physical") {
        const next = { ...physCounts, [mapKey]: Math.max(0, value || 0) };
        if (!next[mapKey]) delete next[mapKey];
        setPhysCounts(next);
        notify({ physicalAbnormalCounts: next });
      } else {
        const next = { ...spellCounts, [mapKey]: Math.max(0, value || 0) };
        if (!next[mapKey]) delete next[mapKey];
        setSpellCounts(next);
        notify({ spellAbnormalCounts: next });
      }
    },
    [physCounts, spellCounts, notify],
  );

  const renderMatrix = (title: string, specs: MatrixRowSpec[], kind: "physical" | "spell") => (
    <Box sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
        {title}
      </Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>类型</TableCell>
            {specs[0]?.ui_levels.map((lv) => (
              <TableCell key={lv} align="center">
                L{lv}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {specs.map((row) => (
            <TableRow key={row.abnormal_key}>
              <TableCell>{row.label}</TableCell>
              {row.ui_levels.map((lv) => (
                <TableCell key={lv} align="center" sx={{ p: 0.5 }}>
                  <TextField
                    size="small"
                    type="number"
                    value={(
                      (kind === "physical" ? physCounts : spellCounts)[`${row.abnormal_key}:${lv}`] ?? 0
                    ).toString()}
                    onChange={(e) =>
                      setMatrixCount(kind, row.abnormal_key, lv, parseInt(e.target.value, 10) || 0)
                    }
                    slotProps={{ htmlInput: { min: 0, style: { width: 48, textAlign: "center" } } }}
                  />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );

  return (
    <Paper variant="outlined" sx={{ mb: 2 }}>
      <Box
        sx={{ display: "flex", alignItems: "center", p: 1.5, cursor: "pointer" }}
        onClick={() => setExpanded(!expanded)}
      >
        <Typography variant="subtitle2" sx={{ flex: 1 }}>
          暴击 / 异常矩阵
        </Typography>
        {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ p: 2, pt: 0 }}>
          <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
            <TextField
              size="small"
              label="额外暴击率"
              type="number"
              value={extraCritRate}
              onChange={(e) => {
                const v = parseFloat(e.target.value) || 0;
                setExtraCritRate(v);
                notify({ extraCritRate: v });
              }}
            />
            <TextField
              size="small"
              label="额外暴击伤害"
              type="number"
              value={extraCritDamage}
              onChange={(e) => {
                const v = parseFloat(e.target.value) || 0;
                setExtraCritDamage(v);
                notify({ extraCritDamage: v });
              }}
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
            label="计入条件装备暴击"
          />
          {hint && (
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
              {hint}
            </Typography>
          )}
          {renderMatrix("物理异常", physSpecs, "physical")}
          {renderMatrix("法术异常", spellSpecs, "spell")}
          <Button
            size="small"
            onClick={() => {
              setPhysCounts({});
              setSpellCounts({});
              notify({ physicalAbnormalCounts: {}, spellAbnormalCounts: {} });
            }}
          >
            清空矩阵
          </Button>
        </Box>
      </Collapse>
    </Paper>
  );
}
