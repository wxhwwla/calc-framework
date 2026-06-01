import { Box, Paper, Typography, Divider } from "@mui/material";
import type { DamageSnapshot } from "../../api/compute";

interface TotalDamagePanelProps {
  snapshot: DamageSnapshot | null;
  loading: boolean;
}

const SKILL_TYPE_ORDER = ["战技", "连携技", "终结技"];

function parseSegmentKey(key: string): { skillType: string; segNum: number } {
  const parts = key.split(":");
  const segNum = parts.length > 1 ? parseInt(parts[1], 10) || 0 : 0;
  return { skillType: parts[0], segNum };
}

export default function TotalDamagePanel({ snapshot, loading }: TotalDamagePanelProps) {
  if (loading && !snapshot) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          伤害快照
        </Typography>
      </Paper>
    );
  }

  if (!snapshot) return null;

  const segmentKeys = Object.keys(snapshot.segment_totals);

  const grouped = new Map<string, string[]>();
  for (const key of segmentKeys) {
    const { skillType } = parseSegmentKey(key);
    if (!grouped.has(skillType)) grouped.set(skillType, []);
    grouped.get(skillType)!.push(key);
  }

  const orderedTypes = SKILL_TYPE_ORDER.filter((t) => grouped.has(t));

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        伤害快照
      </Typography>

      <Box sx={{ textAlign: "center", mb: 2 }}>
        <Typography variant="caption" color="text.secondary">
          加权总伤
        </Typography>
        <Typography variant="h5" fontWeight="bold" color="primary">
          {snapshot.weighted_total_damage.toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          })}
        </Typography>
      </Box>

      {orderedTypes.map((skillType) => {
        const keys = grouped.get(skillType)!;
        const typeTotal = snapshot.skill_type_totals[skillType] ?? 0;
        return (
          <Box key={skillType} sx={{ mb: 1.5 }}>
            <Typography
              variant="body2"
              fontWeight="bold"
              color="warning.main"
              sx={{ mb: 0.5 }}
            >
              {skillType} ({typeTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })})
            </Typography>
            {keys.map((key) => {
              const { segNum } = parseSegmentKey(key);
              const single = snapshot.segment_damage[key] ?? 0;
              const count = snapshot.segment_counts[key] ?? 0;
              const st = snapshot.segment_totals[key] ?? 0;
              const pct = snapshot.rotation_share_percent[key] ?? 0;
              return (
                <Typography
                  key={key}
                  variant="caption"
                  sx={{ display: "block", ml: 2, lineHeight: 1.8, color: "text.secondary" }}
                >
                  第{segNum}段: {single.toFixed(1)} x {count} = {st.toFixed(1)} ({pct.toFixed(1)}%)
                </Typography>
              );
            })}
            <Typography
              variant="caption"
              sx={{ display: "block", ml: 2, color: "success.main", fontWeight: "bold" }}
            >
              小计: {typeTotal.toFixed(1)}
            </Typography>
          </Box>
        );
      })}

      <Divider sx={{ my: 1 }} />

      <Typography variant="caption" color="text.secondary">
        选中: {snapshot.selected_skill_label}
      </Typography>
    </Paper>
  );
}
