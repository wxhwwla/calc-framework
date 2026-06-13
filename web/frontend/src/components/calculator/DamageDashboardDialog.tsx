import { useTranslation } from "react-i18next";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Box,
} from "@mui/material";
import type { DamageSnapshot } from "../../api/compute";
import DamageChart from "./DamageChart";

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
              <DamageChart outputValues={segmentPie} nodeValues={null} />
            </Box>
            <Box sx={{ flex: "1 1 320px", minWidth: 280 }}>
              <DamageChart outputValues={null} nodeValues={null} zoneShare={zoneShare} />
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
