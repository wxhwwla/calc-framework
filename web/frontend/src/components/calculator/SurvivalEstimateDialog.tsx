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
      setError("请先选择角色与武器");
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
      <DialogTitle>处决 / 治疗 / 失衡估算</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2, mb: 2 }}>
          <FormControl size="small" fullWidth>
            <InputLabel>敌人等阶</InputLabel>
            <Select
              value={enemyTier}
              label="敌人等阶"
              onChange={(e) => setEnemyTier(e.target.value)}
              onClose={runEstimate}
            >
              {ENEMY_TIERS.map((t) => (
                <MenuItem key={t} value={t}>
                  {t}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            fullWidth
            type="number"
            label="单次失衡值"
            value={imbGainBase}
            onChange={(e) => setImbGainBase(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
          <TextField
            size="small"
            fullWidth
            type="number"
            label="失衡效率加成"
            value={imbGainEff}
            onChange={(e) => setImbGainEff(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
          <TextField
            size="small"
            fullWidth
            type="number"
            label="敌人最大生命"
            value={enemyMaxHp}
            onChange={(e) => setEnemyMaxHp(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
          <TextField
            size="small"
            fullWidth
            type="number"
            label="灼热抗性 (%)"
            value={hotResist}
            onChange={(e) => setHotResist(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
        </Box>

        <Accordion disableGutters sx={{ mb: 1 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2">技力 / 终结技</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
              <TextField
                size="small"
                type="number"
                label="起始技力"
                value={spStart}
                onChange={(e) => setSpStart(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label="自然回能时长 (s)"
                value={spSeconds}
                onChange={(e) => setSpSeconds(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label="起始终结充能"
                value={ultStart}
                onChange={(e) => setUltStart(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label="生命汲取率"
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
            <Typography variant="body2">治疗（三乘区）</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
              <TextField
                size="small"
                type="number"
                label="治疗基础值"
                value={baseHealFlat}
                onChange={(e) => setBaseHealFlat(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label="每点意志+"
                value={statPerPoint}
                onChange={(e) => setStatPerPoint(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label="治疗效率"
                value={healEfficiency}
                onChange={(e) => setHealEfficiency(parseFloat(e.target.value) || 0)}
                onBlur={runEstimate}
              />
              <TextField
                size="small"
                type="number"
                label="独立治疗加成"
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
              处决伤害: <strong>{result.execute_damage.toLocaleString()}</strong>（×
              {result.execute_multiplier.toFixed(2)}）| 恢复技力 {result.execute_sp_restore}
            </Typography>
            <Typography variant="body2">
              失衡: 上限 {result.imbalance_cap} / 持续 {result.imbalance_duration_sec}s | 有效累积{" "}
              {result.imbalance_gain_effective}（{result.imbalance_gain_percent.toFixed(1)}%）
            </Typography>
            <Typography variant="body2">
              快速打进惩罚: ×{result.fast_break_multiplier.toFixed(2)} | 燃烧{" "}
              {result.burn_tick_per_sec.toLocaleString()}/s
            </Typography>
            <Typography variant="body2">
              技力: {result.sp_after_regen.toFixed(1)}（{result.sp_regen_per_sec}/s）| 终结充能{" "}
              {result.ultimate_charge_after.toFixed(1)}
            </Typography>
            <Typography variant="body2">
              治疗: {result.healing_amount.toLocaleString()} | 生命汲取{" "}
              {result.life_steal_heal.toLocaleString()} | 角色生命 {result.character_max_hp.toLocaleString()}
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={runEstimate} disabled={loading}>
          刷新
        </Button>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}
