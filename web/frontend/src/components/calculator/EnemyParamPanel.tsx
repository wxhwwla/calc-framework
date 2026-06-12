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
import { useTranslation } from "react-i18next";
import {
  fetchEnemyChoices,
  DEFAULT_ENEMY_PARAMS,
  ENEMY_TIERS,
  type EnemyInfo,
  type EnemyParams,
} from "../../api/search";

interface EnemyParamPanelProps {
  onParamsChange: (params: EnemyParams) => void;
}

function enemyToParams(enemy: EnemyInfo): EnemyParams {
  return {
    enemy_defense: enemy.enemy_defense,
    enemy_resistance: enemy.enemy_resistance,
    ignore_resistance: enemy.ignore_resistance,
    imbalance_vulnerability_coeff: enemy.imbalance_vulnerability_coeff,
    is_unbalanced: enemy.is_unbalanced,
    is_true_damage: enemy.is_true_damage,
    combo_stacks: enemy.combo_stacks,
    break_defense_stacks: enemy.break_defense_stacks,
    attached_effect_multiplier: enemy.attached_effect_multiplier,
    corrosion_duration_seconds: enemy.corrosion_duration_seconds,
    enemy_tier: enemy.enemy_tier,
    imbalance_efficiency_bonus: enemy.imbalance_efficiency_bonus,
  };
}

export default function EnemyParamPanel({ onParamsChange }: EnemyParamPanelProps) {
  const { t } = useTranslation();
  const [enemies, setEnemies] = useState<EnemyInfo[]>([]);
  const [selectedEnemyId, setSelectedEnemyId] = useState("");
  const [params, setParams] = useState<EnemyParams>({ ...DEFAULT_ENEMY_PARAMS });
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    fetchEnemyChoices().then(setEnemies).catch(() => {});
  }, []);

  const applyEnemy = useCallback(
    (enemyId: string) => {
      setSelectedEnemyId(enemyId);
      const enemy = enemies.find((e) => e.id === enemyId);
      if (enemy) {
        const newParams = enemyToParams(enemy);
        setParams(newParams);
        onParamsChange(newParams);
      } else {
        setParams({ ...DEFAULT_ENEMY_PARAMS });
        onParamsChange({ ...DEFAULT_ENEMY_PARAMS });
      }
    },
    [enemies, onParamsChange],
  );

  const updateParam = useCallback(<K extends keyof EnemyParams>(key: K, value: EnemyParams[K]) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleBlur = useCallback(() => {
    onParamsChange(params);
  }, [params, onParamsChange]);

  const handleReset = useCallback(() => {
    setSelectedEnemyId("");
    setParams({ ...DEFAULT_ENEMY_PARAMS });
    onParamsChange({ ...DEFAULT_ENEMY_PARAMS });
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
        <Typography variant="subtitle2">{t("enemy.title")}</Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {t("enemy.defense")} {params.enemy_defense} | {t("enemy.resistance")} {params.enemy_resistance}%
            {params.is_true_damage ? ` | ${t("compute.trueDmg")}` : ""}
          </Typography>
          {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
        </Box>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ p: 2, pt: 0, display: "flex", flexDirection: "column", gap: 2 }}>
          <FormControl size="small" fullWidth>
            <InputLabel>{t("compute.pluginEnemy")}</InputLabel>
            <Select
              value={selectedEnemyId}
              label={t("compute.pluginEnemy")}
              onChange={(e) => applyEnemy(e.target.value)}
            >
              <MenuItem value="">
                <em>{t("compute.defaultEnemy")}</em>
              </MenuItem>
              {enemies
                .filter((e) => e.id !== "")
                .map((e) => (
                  <MenuItem key={e.id} value={e.id}>
                    {e.name}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>

          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" }, gap: 2 }}>
            <TextField
              size="small"
              fullWidth
              label={t("enemy.defense")}
              type="number"
              value={params.enemy_defense}
              onChange={(e) => updateParam("enemy_defense", parseFloat(e.target.value) || 0)}
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0, max: 99999, step: 1 } }}
            />
            <TextField
              size="small"
              fullWidth
              label={t("enemy.resistance")}
              type="number"
              value={params.enemy_resistance}
              onChange={(e) => updateParam("enemy_resistance", parseFloat(e.target.value) || 0)}
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: -100, max: 100, step: 1 } }}
            />
            <TextField
              size="small"
              fullWidth
              label={t("enemy.ignoreResistance")}
              type="number"
              value={params.ignore_resistance}
              onChange={(e) => updateParam("ignore_resistance", parseFloat(e.target.value) || 0)}
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: -100, max: 100, step: 1 } }}
            />
            <TextField
              size="small"
              fullWidth
              label={t("enemy.imbalanceCoeff")}
              type="number"
              value={params.imbalance_vulnerability_coeff}
              onChange={(e) =>
                updateParam("imbalance_vulnerability_coeff", parseFloat(e.target.value) || 0)
              }
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0.1, max: 10, step: 0.05 } }}
            />
            <TextField
              size="small"
              fullWidth
              label="连击层数 (0–4)"
              type="number"
              value={params.combo_stacks}
              onChange={(e) =>
                updateParam("combo_stacks", Math.max(0, Math.min(4, parseInt(e.target.value, 10) || 0)))
              }
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0, max: 4, step: 1 } }}
            />
            <TextField
              size="small"
              fullWidth
              label="破防层数 (0–4)"
              type="number"
              value={params.break_defense_stacks}
              onChange={(e) =>
                updateParam(
                  "break_defense_stacks",
                  Math.max(0, Math.min(4, parseInt(e.target.value, 10) || 0)),
                )
              }
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0, max: 4, step: 1 } }}
            />
            <TextField
              size="small"
              fullWidth
              label="附带效果倍率"
              type="number"
              value={params.attached_effect_multiplier}
              onChange={(e) =>
                updateParam("attached_effect_multiplier", parseFloat(e.target.value) || 0)
              }
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0, max: 10, step: 0.05 } }}
            />
            <TextField
              size="small"
              fullWidth
              label="腐蚀计时 (秒)"
              type="number"
              value={params.corrosion_duration_seconds}
              onChange={(e) =>
                updateParam("corrosion_duration_seconds", parseFloat(e.target.value) || 0)
              }
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0, max: 15, step: 0.1 } }}
            />
            <FormControl size="small" fullWidth>
              <InputLabel>敌人等阶</InputLabel>
              <Select
                value={params.enemy_tier}
                label="敌人等阶"
                onChange={(e) => {
                  updateParam("enemy_tier", e.target.value);
                  setTimeout(handleBlur, 0);
                }}
              >
                {ENEMY_TIERS.map((tier) => (
                  <MenuItem key={tier} value={tier}>
                    {tier}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              size="small"
              fullWidth
              label="失衡效率加成"
              type="number"
              value={params.imbalance_efficiency_bonus}
              onChange={(e) =>
                updateParam("imbalance_efficiency_bonus", parseFloat(e.target.value) || 0)
              }
              onBlur={handleBlur}
              slotProps={{ htmlInput: { min: 0, max: 2, step: 0.01 } }}
            />
          </Box>

          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, alignItems: "center" }}>
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
              label={<Typography variant="body2">失衡状态</Typography>}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={params.is_true_damage}
                  onChange={(e) => {
                    updateParam("is_true_damage", e.target.checked);
                    setTimeout(handleBlur, 0);
                  }}
                  size="small"
                />
              }
              label={<Typography variant="body2">真实伤害</Typography>}
            />
            <Box sx={{ flex: 1 }} />
            <Button size="small" variant="text" startIcon={<RestartAltIcon />} onClick={handleReset}>
              恢复默认
            </Button>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
}
