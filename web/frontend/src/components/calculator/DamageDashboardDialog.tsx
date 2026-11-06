import { lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Box,
} from "@mui/material";
import type { DamageSnapshot } from "../../api/compute";

// 与 ComputePage 保持一致使用动态导入，避免同一模块既静态又动态导入而无法分包
const DamageChart = lazy(() => import("./DamageChart"));

interface DamageDashboardDialogProps {
  open: boolean;
  onClose: () => void;
  snapshot: DamageSnapshot | null;
}

export default function DamageDashboardDialog({ open, onClose, snapshot }: DamageDashboardDialogProps) {
  const { t } = useTranslation();
  const segmentPie = snapshot?.segment_totals ?? null;
  const zoneShare = snapshot?.zone_share_percent ?? undefined;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>{t("damageDashboard.title")}</DialogTitle>
      <DialogContent dividers>
        {!snapshot ? (
          <Box sx={{ py: 4, textAlign: "center", color: "text.secondary" }}>
            {t("damageDashboard.selectCharWeaponHint")}
          </Box>
        ) : (
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2 }}>
            <Box sx={{ flex: "1 1 320px", minWidth: 280 }}>
              <Suspense fallback={null}>
                <DamageChart outputValues={segmentPie} nodeValues={null} />
              </Suspense>
            </Box>
            <Box sx={{ flex: "1 1 320px", minWidth: 280 }}>
              <Suspense fallback={null}>
                <DamageChart outputValues={null} nodeValues={null} zoneShare={zoneShare} />
              </Suspense>
            </Box>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
