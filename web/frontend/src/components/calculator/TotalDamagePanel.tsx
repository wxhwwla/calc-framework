import { Box, Paper, Typography, LinearProgress, Chip, Divider } from "@mui/material";
import type { DamageSnapshot } from "../../api/compute";

interface TotalDamagePanelProps {
  snapshot: DamageSnapshot | null;
  loading: boolean;
}

export default function TotalDamagePanel({ snapshot, loading }: TotalDamagePanelProps) {
  if (loading && !snapshot) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          伤害快照
        </Typography>
        <LinearProgress />
      </Paper>
    );
  }

  if (!snapshot) return null;

  const segmentKeys = Object.keys(snapshot.segment_totals);
  const typeTotals = Object.entries(snapshot.skill_type_totals);

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        伤害快照
      </Typography>

      <Box sx={{ textAlign: "center", mb: 2 }}>
        <Typography variant="caption" color="text.secondary">
          加权总伤
        </Typography>
        <Typography variant="h5" fontWeight="bold">
          {snapshot.weighted_total_damage.toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          })}
        </Typography>
      </Box>

      {typeTotals.length > 0 && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary" gutterBottom display="block">
            技能类型汇总
          </Typography>
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
            {typeTotals.map(([st, total]) => (
              <Chip
                key={st}
                label={`${st}: ${total.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}

      {snapshot.weighted_total_damage > 0 && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary" gutterBottom display="block">
            段级占比
          </Typography>
          {segmentKeys.map((key) => {
            const pct = snapshot.rotation_share_percent[key] ?? 0;
            const total = snapshot.segment_totals[key] ?? 0;
            const count = snapshot.segment_counts[key] ?? 0;
            return (
              <Box key={key} sx={{ mb: 0.5 }}>
                <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                  <Typography variant="caption">
                    {key} ×{count}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {total.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({pct.toFixed(1)}%)
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(pct, 100)}
                  sx={{ height: 6, borderRadius: 1 }}
                />
              </Box>
            );
          })}
        </Box>
      )}

      <Divider sx={{ my: 1 }} />

      <Typography variant="caption" color="text.secondary">
        选中: {snapshot.selected_skill_label}
      </Typography>
    </Paper>
  );
}
