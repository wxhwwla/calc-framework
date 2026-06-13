import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { fetchSearchHistory, type SearchHistoryEntry } from "../../api/search";

interface SearchHistoryDialogProps {
  open: boolean;
  onClose: () => void;
}

function formatTime(s: number): string {
  if (s < 60) return `${s.toFixed(1)}s`;
  return `${Math.floor(s / 60)}m ${(s % 60).toFixed(0)}s`;
}

export default function SearchHistoryDialog({ open, onClose }: SearchHistoryDialogProps) {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<SearchHistoryEntry[]>([]);
  const [expandedEntry, setExpandedEntry] = useState<number | null>(null);

  const loadEntries = useCallback(async () => {
    try {
      const data = await fetchSearchHistory();
      setEntries(data);
    } catch {
      setEntries([]);
    }
  }, []);

  useEffect(() => {
    if (open) loadEntries();
  }, [open, loadEntries]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>{t("searchHistoryDialog.title")}</DialogTitle>
      <DialogContent>
        {entries.length === 0 ? (
          <Typography color="text.secondary" textAlign="center" sx={{ py: 4 }}>
            {t("searchHistoryDialog.empty")}
          </Typography>
        ) : (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {entries.map((entry, idx) => (
              <Paper key={idx} variant="outlined" sx={{ p: 1.5 }}>
                <Box
                  sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}
                  onClick={() => setExpandedEntry(expandedEntry === idx ? null : idx)}
                >
                  <Box>
                    <Typography variant="body2">
                      {entry.char_name} + {entry.weapon_name} · {entry.skill_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t("searchHistoryDialog.results", { n: entry.result_count })} · {t("searchHistoryDialog.combinations", { n: entry.total_combinations?.toLocaleString() ?? 0 })}
                      {entry.elapsed_seconds != null ? ` · ${formatTime(entry.elapsed_seconds)}` : ""}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {entry.saved_at ? new Date(entry.saved_at).toLocaleString("zh-CN") : ""}
                  </Typography>
                </Box>

                {expandedEntry === idx && entry.top_results && entry.top_results.length > 0 && (
                  <TableContainer sx={{ mt: 1, overflowX: 'auto' }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>{t("searchHistoryDialog.rank")}</TableCell>
                          <TableCell>{t("searchHistoryDialog.weapon")}</TableCell>
                          <TableCell>{t("searchHistoryDialog.chest")}</TableCell>
                          <TableCell>{t("searchHistoryDialog.gloves")}</TableCell>
                          <TableCell>{t("searchHistoryDialog.accessoryA")}</TableCell>
                          <TableCell>{t("searchHistoryDialog.accessoryB")}</TableCell>
                          <TableCell align="right">{t("searchHistoryDialog.damage")}</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {entry.top_results.slice(0, 5).map((r, ri) => (
                          <TableRow key={ri}>
                            <TableCell>{ri + 1}</TableCell>
                            <TableCell>{r.weapon_name}</TableCell>
                            <TableCell>{r.chest}</TableCell>
                            <TableCell>{r.gloves}</TableCell>
                            <TableCell>{r.accessory_a}</TableCell>
                            <TableCell>{r.accessory_b}</TableCell>
                            <TableCell align="right">{r.final_damage?.toFixed(1)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Paper>
            ))}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
