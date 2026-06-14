import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Chip,
} from "@mui/material";
import RestoreIcon from "@mui/icons-material/Restore";
import { useTranslation } from "react-i18next";
import { fetchHistory, saveHistory, type HistoryEntry } from "../../api/history";

interface CalcHistoryDialogProps {
  open: boolean;
  onClose: () => void;
  onRestore: (entry: HistoryEntry) => void;
  currentEntry?: HistoryEntry | null;
}

export default function CalcHistoryDialog({
  open,
  onClose,
  onRestore,
  currentEntry,
}: CalcHistoryDialogProps) {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  const loadEntries = useCallback(async () => {
    try {
      const data = await fetchHistory();
      setEntries(data);
    } catch {
      setEntries([]);
    }
  }, []);

  useEffect(() => {
    if (open) loadEntries();
  }, [open, loadEntries]);

  useEffect(() => {
    if (open && currentEntry) {
      saveHistory(currentEntry).then(loadEntries).catch(() => {});
    }
  }, [open, currentEntry, loadEntries]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t("calcHistory.title")}</DialogTitle>
      <DialogContent>
        {entries.length === 0 ? (
          <Typography color="text.secondary" textAlign="center" sx={{ py: 4 }}>
            {t("calcHistory.empty")}
          </Typography>
        ) : (
          <List>
            {entries.map((entry, idx) => (
              <ListItem
                key={idx}
                divider
                secondaryAction={
                  <Button
                    size="small"
                    startIcon={<RestoreIcon />}
                    onClick={() => onRestore(entry)}
                  >
                    {t("calcHistory.restore")}
                  </Button>
                }
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Typography variant="body2">
                        {entry.char_name} + {entry.weapon_name}
                      </Typography>
                      {entry.outputs && (
                        <Chip
                          label={`${t("calcHistory.damageLabel")}: ${Object.values(entry.outputs)[0]?.toFixed(1) ?? "?"}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {entry.saved_at
                        ? new Date(entry.saved_at).toLocaleString("zh-CN")
                        : ""}
                      {entry.label ? ` · ${entry.label}` : ""}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
