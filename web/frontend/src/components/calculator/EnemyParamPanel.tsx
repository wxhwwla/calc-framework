import { useState, useEffect, useCallback } from "react";
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
  Button,
  Collapse,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import { fetchEnemyChoices, type EnemyInfo, type EnemyParams } from "../../api/search";

const DEFAULT_PARAMS: EnemyParams = {
  enemy_defense: 100,
  enemy_resistance: 0,
  ignore_resistance: 0,
  imbalance_vulnerability_coeff: 1.3,
  is_unbalanced: false,
};

interface EnemyParamPanelProps {
  onParamsChange: (params: EnemyParams) => void;
}

export default function EnemyParamPanel({ onParamsChange }: EnemyParamPanelProps) {
  const [enemies, setEnemies] = useState<EnemyInfo[]>([]);
  const [selectedEnemyId, setSelectedEnemyId] = useState("");
  const [params, setParams] = useState<EnemyParams>({ ...DEFAULT_PARAMS });
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    fetchEnemyChoices().then(setEnemies).catch(() => {});
  }, []);

  const applyEnemy = useCallback((enemyId: string) => {
    setSelectedEnemyId(enemyId);
    const enemy = enemies.find((e) => e.id === enemyId);
    if (enemy) {
      const newParams = {
        enemy_defense: enemy.enemy_defense,
        enemy_resistance: enemy.enemy_resistance,
        ignore_resistance: enemy.ignore_resistance,
        imbalance_vulnerability_coeff: enemy.imbalance_vulnerability_coeff,
        is_unbalanced: enemy.is_unbalanced,
      };
      setParams(newParams);
      onParamsChange(newParams);
    } else {
      setParams({ ...DEFAULT_PARAMS });
      onParamsChange({ ...DEFAULT_PARAMS });
    }
  }, [enemies, onParamsChange]);

  const updateParam = useCallback((key: keyof EnemyParams, value: number | boolean) => {
    setParams((prev) => {
      const next = { ...prev, [key]: value };
      return next;
    });
  }, []);

  const handleBlur = useCallback(() => {
    onParamsChange(params);
  }, [params, onParamsChange]);

  const handleReset = useCallback(() => {
    setSelectedEnemyId("");
    setParams({ ...DEFAULT_PARAMS });
    onParamsChange({ ...DEFAULT_PARAMS });
  }, [onParamsChange]);

  return (
    <Paper variant="outlined" sx={{ mb: 2 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          p: 1.5,
          cursor: "pointer",
          "&:hover": { bgcolor: "action.hover" },
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Typography variant="subtitle2">
          敌方参数
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            防御 {params.enemy_defense} | 抗性 {params.enemy_resistance}%
          </Typography>
          {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
        </Box>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ p: 2, pt: 0, display: "flex", flexDirection: "column", gap: 2 }}>
          <FormControl size="small" fullWidth>
            <InputLabel>插件敌人</InputLabel>
            <Select
              value={selectedEnemyId}
              label="插件敌人"
              onChange={(e) => applyEnemy(e.target.value)}
            >
              <MenuItem value="">
                <em>默认敌人</em>
              </MenuItem>
              {enemies
                .filter((e) => e.id !== "")
                .map((e) => (
                  <MenuItem key={e.id} value={e.id}>
                    {e.name} (防{e.enemy_defense})
                  </MenuItem>
                ))}
            </Select>
          </FormControl>

          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
            <TextField
              size="small"
              label="防御力"
              type="number"
              value={params.enemy_defense}
              onChange={(e) => updateParam("enemy_defense", parseFloat(e.target.value) || 0)}
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0, max: 99999, step: 1 } }}
            />
            <TextField
              size="small"
              label="抗性 (%)"
              type="number"
              value={params.enemy_resistance}
              onChange={(e) => updateParam("enemy_resistance", parseFloat(e.target.value) || 0)}
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: -100, max: 100, step: 1 } }}
            />
            <TextField
              size="small"
              label="无视抗性 (%)"
              type="number"
              value={params.ignore_resistance}
              onChange={(e) => updateParam("ignore_resistance", parseFloat(e.target.value) || 0)}
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: -100, max: 100, step: 1 } }}
            />
            <TextField
              size="small"
              label="失衡易伤系数"
              type="number"
              value={params.imbalance_vulnerability_coeff}
              onChange={(e) =>
                updateParam("imbalance_vulnerability_coeff", parseFloat(e.target.value) || 0)
              }
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0.1, max: 10, step: 0.05 } }}
            />
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={params.is_unbalanced}
                  onChange={(e) => {
                    updateParam("is_unbalanced", e.target.checked);
                    setTimeout(handleBlur, 0);
                  }}
                  size="small"
                />
              }
              label={<Typography variant="body2">失衡状态（启用失衡易伤乘区）</Typography>}
            />
            <Button
              size="small"
              variant="text"
              startIcon={<RestartAltIcon />}
              onClick={handleReset}
            >
              恢复默认
            </Button>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
}
