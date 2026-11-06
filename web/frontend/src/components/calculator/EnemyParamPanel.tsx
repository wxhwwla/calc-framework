import { useState, useEffect, useCallback, useRef } from "react";
import {
  Box,
  Typography,
  Paper,
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Collapse,
} from "@mui/material";
import NumberField from "../common/NumberField";
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

const ENEMY_TIER_I18N: Record<string, string> = {
  普通: "enemyTiers.normal",
  进阶: "enemyTiers.advanced",
  精英: "enemyTiers.elite",
  头目: "enemyTiers.boss",
  领袖: "enemyTiers.leader",
};

export default function EnemyParamPanel({ onParamsChange }: EnemyParamPanelProps) {
  const { t } = useTranslation();
  const [enemies, setEnemies] = useState<EnemyInfo[]>([]);
  const [selectedEnemyId, setSelectedEnemyId] = useState("");
  const [params, setParams] = useState<EnemyParams>({ ...DEFAULT_ENEMY_PARAMS });
  const [expanded, setExpanded] = useState(false);
  // 失焦时 NumberField 会先提交夹紧后的数值，再调用 onBlur；
  // 用 ref 保存最新值，避免闭包里的旧 params 覆盖刚输入的结果。
  const paramsRef = useRef<EnemyParams>({ ...DEFAULT_ENEMY_PARAMS });

  useEffect(() => {
    fetchEnemyChoices().then(setEnemies).catch(() => {});
  }, []);

  const applyParams = useCallback((next: EnemyParams) => {
    paramsRef.current = next;
    setParams(next);
  }, []);

  const applyEnemy = useCallback(
    (enemyId: string) => {
      setSelectedEnemyId(enemyId);
      const enemy = enemies.find((e) => e.id === enemyId);
      const next = enemy ? enemyToParams(enemy) : { ...DEFAULT_ENEMY_PARAMS };
      applyParams(next);
      onParamsChange(next);
    },
    [applyParams, enemies, onParamsChange],
  );

  const updateParam = useCallback(<K extends keyof EnemyParams>(key: K, value: EnemyParams[K]) => {
    const next = { ...paramsRef.current, [key]: value };
    applyParams(next);
  }, [applyParams]);

  const handleBlur = useCallback(() => {
    onParamsChange(paramsRef.current);
  }, [onParamsChange]);

  const handleReset = useCallback(() => {
    setSelectedEnemyId("");
    applyParams({ ...DEFAULT_ENEMY_PARAMS });
    onParamsChange({ ...DEFAULT_ENEMY_PARAMS });
  }, [applyParams, onParamsChange]);

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
            <NumberField
              fullWidth
              label={t("enemy.defense")}
              value={params.enemy_defense}
              onChange={(v) => updateParam("enemy_defense", v)}
              onBlur={handleBlur}
              min={0}
              max={99999}
              integer
            />
            <NumberField
              fullWidth
              label={t("enemy.resistance")}
              value={params.enemy_resistance}
              onChange={(v) => updateParam("enemy_resistance", v)}
              onBlur={handleBlur}
              min={-100}
              max={100}
              integer
            />
            <NumberField
              fullWidth
              label={t("enemy.ignoreResistance")}
              value={params.ignore_resistance}
              onChange={(v) => updateParam("ignore_resistance", v)}
              onBlur={handleBlur}
              min={-100}
              max={100}
              integer
            />
            <NumberField
              fullWidth
              label={t("enemy.imbalanceCoeff")}
              value={params.imbalance_vulnerability_coeff}
              onChange={(v) => updateParam("imbalance_vulnerability_coeff", v)}
              onBlur={handleBlur}
              min={0.1}
              max={10}
            />
            <NumberField
              fullWidth
              label={t("enemy.comboStacks")}
              value={params.combo_stacks}
              onChange={(v) => updateParam("combo_stacks", v)}
              onBlur={handleBlur}
              min={0}
              max={4}
              integer
            />
            <NumberField
              fullWidth
              label={t("enemy.breakDefenseStacks")}
              value={params.break_defense_stacks}
              onChange={(v) => updateParam("break_defense_stacks", v)}
              onBlur={handleBlur}
              min={0}
              max={4}
              integer
            />
            <NumberField
              fullWidth
              label={t("enemy.attachedEffectMultiplier")}
              value={params.attached_effect_multiplier}
              onChange={(v) => updateParam("attached_effect_multiplier", v)}
              onBlur={handleBlur}
              min={0}
              max={10}
            />
            <NumberField
              fullWidth
              label={t("enemy.corrosionDuration")}
              value={params.corrosion_duration_seconds}
              onChange={(v) => updateParam("corrosion_duration_seconds", v)}
              onBlur={handleBlur}
              min={0}
              max={15}
            />
            <FormControl size="small" fullWidth>
              <InputLabel>{t("enemy.tier")}</InputLabel>
              <Select
                value={params.enemy_tier}
                label={t("enemy.tier")}
                onChange={(e) => {
                  updateParam("enemy_tier", e.target.value);
                  setTimeout(handleBlur, 0);
                }}
              >
                {ENEMY_TIERS.map((tier) => (
                  <MenuItem key={tier} value={tier}>
                    {ENEMY_TIER_I18N[tier] ? t(ENEMY_TIER_I18N[tier]) : tier}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <NumberField
              fullWidth
              label={t("enemy.imbalanceEfficiency")}
              value={params.imbalance_efficiency_bonus}
              onChange={(v) => updateParam("imbalance_efficiency_bonus", v)}
              onBlur={handleBlur}
              min={0}
              max={2}
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
              label={<Typography variant="body2">{t("enemy.imbalanced")}</Typography>}
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
              label={<Typography variant="body2">{t("enemy.trueDamage")}</Typography>}
            />
            <Box sx={{ flex: 1 }} />
            <Button size="small" variant="text" startIcon={<RestartAltIcon />} onClick={handleReset}>
              {t("enemy.resetDefault")}
            </Button>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
}
