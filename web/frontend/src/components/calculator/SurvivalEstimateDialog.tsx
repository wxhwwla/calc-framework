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
} from "@mui/material";
import { fetchSurvivalEstimate, type SurvivalEstimateResult } from "../../api/survival";
import type { EnemyParams } from "../../api/search";

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
  const [enemyMaxHp, setEnemyMaxHp] = useState(6605);

  useEffect(() => {
    if (open) {
      setEnemyTier(enemyParams.enemy_tier ?? "普通");
    }
  }, [open, enemyParams.enemy_tier]);

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
        imbalance_efficiency_bonus: enemyParams.imbalance_efficiency_bonus ?? 0,
        enemy_max_hp: enemyMaxHp,
        enemy_id: selectedEnemyId,
        imbalance_gain_base: imbGainBase,
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
    enemyParams.imbalance_efficiency_bonus,
    enemyMaxHp,
    selectedEnemyId,
    imbGainBase,
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
          <TextField
            size="small"
            fullWidth
            label="敌人等阶"
            value={enemyTier}
            onChange={(e) => setEnemyTier(e.target.value)}
            onBlur={runEstimate}
          />
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
            label="敌人最大生命"
            value={enemyMaxHp}
            onChange={(e) => setEnemyMaxHp(parseFloat(e.target.value) || 0)}
            onBlur={runEstimate}
          />
        </Box>

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
              快速打进惩罚: ×{result.fast_break_multiplier.toFixed(2)} | 燃烧 {result.burn_tick_per_sec.toLocaleString()}/s
            </Typography>
            <Typography variant="body2">
              技力: {result.sp_after_regen.toFixed(1)}（{result.sp_regen_per_sec}/s）| 终结充能{" "}
              {result.ultimate_charge_after.toFixed(1)}
            </Typography>
            <Typography variant="body2">
              治疗: {result.healing_amount.toLocaleString()} | 生命汲取 {result.life_steal_heal.toLocaleString()}
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
