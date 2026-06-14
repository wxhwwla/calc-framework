import { useState, useCallback, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useTranslation } from "react-i18next";
import { fetchSurvivalEstimate, type SurvivalEstimateResult } from "../../api/survival";
import { ENEMY_TIERS, type EnemyParams } from "../../api/search";

interface SurvivalEstimateDialogProps {
  open: boolean;
  onClose: () => void;
  charData: Record<string, unknown> | null;
  weaponData: Record<string, unknown> | null;
  charLevel: number;
  weaponLevel: number;
  trustLevel: number;
  enemyParams: EnemyParams;
  selectedEnemyId?: string;
}

const TIER_I18N_MAP: Record<string, string> = {
  普通: "enemyTiers.normal",
  进阶: "enemyTiers.advanced",
  精英: "enemyTiers.elite",
  头目: "enemyTiers.boss",
  领袖: "enemyTiers.leader",
};

export default function SurvivalEstimateDialog({
  open,
  onClose,
  charData,
  weaponData,
  charLevel,
  weaponLevel,
  trustLevel,
  enemyParams,
  selectedEnemyId = "",
}: SurvivalEstimateDialogProps) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SurvivalEstimateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [enemyTier, setEnemyTier] = useState(enemyParams.enemy_tier ?? "普通");
  const [imbGainBase, setImbGainBase] = useState(10);
  const [imbGainEff, setImbGainEff] = useState(enemyParams.imbalance_efficiency_bonus ?? 0);
  const [enemyMaxHp, setEnemyMaxHp] = useState(6605);
  const [hotResist, setHotResist] = useState(0);
  const [spStart, setSpStart] = useState(0);
  const [spSeconds, setSpSeconds] = useState(5);
  const [ultStart, setUltStart] = useState(0);
  const [lifeStealRate, setLifeStealRate] = useState(0.1);
  const [baseHealFlat, setBaseHealFlat] = useState(201.6);
  const [statPerPoint, setStatPerPoint] = useState(0.47);
  const [healEfficiency, setHealEfficiency] = useState(0.2);
  const [independentHealBonus, setIndependentHealBonus] = useState(0.3);

  useEffect(() => {
    if (open) {
      setEnemyTier(enemyParams.enemy_tier ?? "普通");
      setImbGainEff(enemyParams.imbalance_efficiency_bonus ?? 0);
    }
  }, [open, enemyParams.enemy_tier, enemyParams.imbalance_efficiency_bonus]);

  const runEstimate = useCallback(async () => {
    if (!charData || !weaponData) {
      setError(t("survivalEstimate.selectCharWeaponFirst"));
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSurvivalEstimate({
        char_data: charData,
        weapon_data: weaponData,
        char_level: charLevel,
        weapon_level: weaponLevel,
        trust_level: trustLevel,
        enemy_tier: enemyTier,
        imbalance_efficiency_bonus: imbGainEff,
        enemy_max_hp: enemyMaxHp,
        enemy_id: selectedEnemyId,
        imbalance_gain_base: imbGainBase,
        hot_resistance_percent: hotResist,
        sp_start: spStart,
        sp_seconds: spSeconds,
        ult_start: ultStart,
        life_steal_rate: lifeStealRate,
        base_heal_flat: baseHealFlat,
        stat_per_point: statPerPoint,
        heal_efficiency: healEfficiency,
        independent_heal_bonus: independentHealBonus,
      });
      setResult(data);
    } catch (e) {
      setError(String(e));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [
    t,
    charData,
    weaponData,
    charLevel,
    weaponLevel,
    trustLevel,
    enemyTier,
    imbGainEff,
    enemyMaxHp,
    selectedEnemyId,
    imbGainBase,
    hotResist,
    spStart,
    spSeconds,
    ultStart,
    lifeStealRate,
    baseHealFlat,
    statPerPoint,
    healEfficiency,
    independentHealBonus,
  ]);

  useEffect(() => {
    if (open && charData && weaponData) {
      runEstimate();
    }
  }, [open, charData, weaponData, runEstimate]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t("survivalEstimate.title")}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2, mb: 2 }}>
          <FormControl size="small" fullWidth>
            <InputLabel>{t("survivalEstimate.enemyTier")}</InputLabel>
            <Select
              value={enemyTier}
              label={t("survivalEstimate.enemyTier")}
              onChange={(e) => setEnemyTier(e.target.value)}
              onClose={runEstimate}
            >
              {ENEMY_TIERS.map((tier) => (
                <MenuItem key={tier} value={tier}>
                  {TIER_I18N_MAP[tier] ? t(TIER_I18N_MAP[tier]) : tier}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            fullWidth
            type="number"
            label={t("survivalEstimate.singleImbGain")}
            value={imbGainBase}
            onChange={(e) => setImbGainBase(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
          <TextField
            size="small"
            fullWidth
            type="number"
            label={t("survivalEstimate.imbEfficiency")}
            value={imbGainEff}
            onChange={(e) => setImbGainEff(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
          <TextField
            size="small"
            fullWidth
            type="number"
            label={t("survivalEstimate.enemyMaxHp")}
            value={enemyMaxHp}
            onChange={(e) => setEnemyMaxHp(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
          <TextField
            size="small"
            fullWidth
            type="number"
            label={t("survivalEstimate.hotResist")}
            value={hotResist}
            onChange={(e) => setHotResist(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
        </Box>

        <Accordion disableGutters sx={{ mb: 1 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2">{t("survivalEstimate.spUltimate")}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.startSp")}
                value={spStart}
                onChange={(e) => setSpStart(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.naturalRegenDuration")}
                value={spSeconds}
                onChange={(e) => setSpSeconds(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.startUltCharge")}
                value={ultStart}
                onChange={(e) => setUltStart(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.lifeStealRate")}
                value={lifeStealRate}
                onChange={(e) => setLifeStealRate(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
                slotProps={{ htmlInput: { min: 0, max: 1, step: 0.01 } }}
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        <Accordion disableGutters sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2">{t("survivalEstimate.healingThreeZones")}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.baseHeal")}
                value={baseHealFlat}
                onChange={(e) => setBaseHealFlat(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.perWillBonus")}
                value={statPerPoint}
                onChange={(e) => setStatPerPoint(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.healEfficiency")}
                value={healEfficiency}
                onChange={(e) => setHealEfficiency(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label={t("survivalEstimate.independentHeal")}
                value={independentHealBonus}
                onChange={(e) => setIndependentHealBonus(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
            <CircularProgress size={28} />
          </Box>
        )}
        {error && (
          <Typography color="error" variant="body2">
            {error}
          </Typography>
        )}
        {result && !loading && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <Typography variant="body2">
              {t("survivalEstimate.executeDamage")}: <strong>{result.execute_damage.toLocaleString()}</strong>（×
              {result.execute_multiplier.toFixed(2)}）| 恢复技力 {result.execute_sp_restore}
            </Typography>
            <Typography variant="body2">
              {t("survivalEstimate.imbalance")}: {t("survivalEstimate.imbalanceCap", { cap: result.imbalance_cap, dur: result.imbalance_duration_sec })} | {t("survivalEstimate.effectiveAccum")}{" "}
              {result.imbalance_gain_effective}（{result.imbalance_gain_percent.toFixed(1)}%）
            </Typography>
            <Typography variant="body2">
              {t("survivalEstimate.fastBreakPenalty")}: ×{result.fast_break_multiplier.toFixed(2)} | {t("survivalEstimate.burn")}{" "}
              {result.burn_tick_per_sec.toLocaleString()}/s
            </Typography>
            <Typography variant="body2">
              {t("survivalEstimate.sp")}: {result.sp_after_regen.toFixed(1)}（{result.sp_regen_per_sec}/s）| {t("survivalEstimate.ultCharge")}{" "}
              {result.ultimate_charge_after.toFixed(1)}
            </Typography>
            <Typography variant="body2">
              {t("survivalEstimate.healing")}: {result.healing_amount.toLocaleString()} | {t("survivalEstimate.lifeSteal")}{" "}
              {result.life_steal_heal.toLocaleString()} | {t("survivalEstimate.charHp")} {result.character_max_hp.toLocaleString()}
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={runEstimate} disabled={loading}>
          {t("common.refresh")}
        </Button>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
