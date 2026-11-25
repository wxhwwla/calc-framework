import { useEffect, useState } from "react";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { getAdminToken, setAdminToken } from "../../api/adminAuth";

interface AdminTokenDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function AdminTokenDialog({ open, onClose }: AdminTokenDialogProps) {
  const { t } = useTranslation();
  const [token, setToken] = useState("");

  useEffect(() => {
    if (open) setToken(getAdminToken());
  }, [open]);

  const save = () => {
    setAdminToken(token.trim());
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t("adminAuth.title")}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t("adminAuth.description")}
        </Typography>
        <TextField
          fullWidth
          type="password"
          label={t("adminAuth.tokenLabel")}
          value={token}
          onChange={(event) => setToken(event.target.value)}
          autoComplete="off"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.cancel")}</Button>
        <Button variant="contained" onClick={save}>{t("common.save")}</Button>
      </DialogActions>
    </Dialog>
  );
}
