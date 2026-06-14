import { useState, useCallback, useMemo } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, LinearProgress, Chip,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import type { EnemyParams } from "../../api/search";

const BASE = "/api";

interface CompareEntry {
  label: string;
  char_name: string;
  weapon_name: string;
  enemy_defense?: number;
  enemy_resistance?: number;
  ignore_resistance?: number;
  imbalance_vulnerability_coeff?: number;
  is_unbalanced?: boolean;
  is_true_damage?: boolean;
  combo_stacks?: number;
  break_defense_stacks?: number;
}

interface CompareResult {
  label: string;
  total: number;
  error?: string;
}

interface BatchCompareDialogProps {
  open: boolean;
  onClose: () => void;
  enemyParams: EnemyParams;
}

export default function BatchCompareDialog({ open, onClose, enemyParams }: BatchCompareDialogProps) {
  const { t } = useTranslation();

  const defaultEntries = useMemo<CompareEntry[]>(() => [
    { label: `${t("common.plan")}1`, char_name: "", weapon_name: "" },
    { label: `${t("common.plan")}2`, char_name: "", weapon_name: "" },
  ], [t]);

  const [entries, setEntries] = useState<CompareEntry[]>(defaultEntries);
  const [results, setResults] = useState<CompareResult[] | null>(null);
  const [loading, setLoading] = useState(false);

  const addEntry = useCallback(() => {
    setEntries((prev) => [...prev, { label: `${t("common.plan")}${prev.length + 1}`, char_name: "", weapon_name: "" }]);
  }, [t]);

  const updateEntry = useCallback((idx: number, field: keyof CompareEntry, value: string) => {
    setEntries((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], [field]: value };
      return next;
    });
  }, []);

  const removeEntry = useCallback((idx: number) => {
    setEntries((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  const runCompare = useCallback(async () => {
    setLoading(true);
    setResults(null);
    try {
      const payload = entries.map((entry) => ({
        ...entry,
        enemy_defense: enemyParams.enemy_defense,
        enemy_resistance: enemyParams.enemy_resistance,
        ignore_resistance: enemyParams.ignore_resistance,
        imbalance_vulnerability_coeff: enemyParams.imbalance_vulnerability_coeff,
        is_unbalanced: enemyParams.is_unbalanced,
        is_true_damage: enemyParams.is_true_damage,
        combo_stacks: enemyParams.combo_stacks,
        break_defense_stacks: enemyParams.break_defense_stacks,
      }));
      const r = await fetch(`${BASE}/compute/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries: payload }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data: CompareResult[] = await r.json();
      setResults(data);
    } catch (e) {
      setResults([{ label: t("batchCompare.error"), total: 0, error: String(e) }]);
    } finally {
      setLoading(false);
    }
  }, [entries, enemyParams, t]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t("batchCompare.title")}</DialogTitle>
      <DialogContent>
        <TableContainer component={Paper} variant="outlined" sx={{ mb: 2, overflowX: 'auto' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t("batchCompare.label")}</TableCell>
                <TableCell>{t("batchCompare.character")}</TableCell>
                <TableCell>{t("batchCompare.weapon")}</TableCell>
                <TableCell align="center">{t("batchCompare.operations")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((entry, idx) => (
                <TableRow key={idx}>
                  <TableCell>
                    <input
                      value={entry.label}
                      onChange={(e) => updateEntry(idx, "label", e.target.value)}
                      style={{ width: 80, border: "1px solid #ccc", borderRadius: 4, padding: "2px 6px" }}
                    />
                  </TableCell>
                  <TableCell>
                    <input
                      value={entry.char_name}
                      onChange={(e) => updateEntry(idx, "char_name", e.target.value)}
                      style={{ width: 140, border: "1px solid #ccc", borderRadius: 4, padding: "2px 6px" }}
                      placeholder={t("batchCompare.charPlaceholder")}
                    />
                  </TableCell>
                  <TableCell>
                    <input
                      value={entry.weapon_name}
                      onChange={(e) => updateEntry(idx, "weapon_name", e.target.value)}
                      style={{ width: 140, border: "1px solid #ccc", borderRadius: 4, padding: "2px 6px" }}
                      placeholder={t("batchCompare.weaponPlaceholder")}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Button size="small" color="error" onClick={() => removeEntry(idx)} disabled={entries.length <= 1}>
                      {t("batchCompare.delete")}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Button variant="outlined" size="small" onClick={addEntry} sx={{ mb: 2 }}>
          {t("batchCompare.addPlan")}
        </Button>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {results && results.length > 0 && (
          <TableContainer component={Paper} variant="outlined" sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t("common.rank")}</TableCell>
                  <TableCell>{t("common.plan")}</TableCell>
                  <TableCell align="right">{t("common.totalDamageShort")}</TableCell>
                  <TableCell>{t("common.status")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.map((r, idx) => (
                  <TableRow key={idx} selected={idx === 0}>
                    <TableCell>
                      <Chip
                        label={`#${idx + 1}`}
                        size="small"
                        color={idx === 0 ? "primary" : "default"}
                      />
                    </TableCell>
                    <TableCell>{r.label}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: idx === 0 ? "bold" : "normal" }}>
                      {r.total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </TableCell>
                    <TableCell>
                      {r.error ? (
                        <Typography variant="caption" color="error">{r.error}</Typography>
                      ) : (
                        <Typography variant="caption" color="success.main">{t("batchCompare.ok")}</Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
        <Button variant="contained" onClick={runCompare} disabled={loading}>
          {loading ? t("batchCompare.calculating") : t("batchCompare.compare")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
