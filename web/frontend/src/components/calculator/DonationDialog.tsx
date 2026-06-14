import { useTranslation } from "react-i18next";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography,
} from "@mui/material";
import DonationImages from "./DonationImages";

interface DonationDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function DonationDialog({ open, onClose }: DonationDialogProps) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t("donation.dialogTitle")}</DialogTitle>
      <DialogContent dividers>
        <DonationImages />
        <Typography variant="body2" sx={{ whiteSpace: "pre-line", mt: 1 }}>
          {t("donation.text")}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
