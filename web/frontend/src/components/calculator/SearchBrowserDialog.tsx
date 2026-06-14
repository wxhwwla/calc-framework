import { useCallback, useEffect, useState } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, LinearProgress,
} from "@mui/material";
import { useTranslation } from "react-i18next";

const BASE = "/api";

interface SearchHit {
  名称: string;
  score?: number;
  total_damage?: number;
}

interface SearchBrowserDialogProps {
  open: boolean;
  onClose: () => void;
  adapter: string;
  context: Record<string, unknown>;
}

export default function SearchBrowserDialog({ open, onClose, adapter, context }: SearchBrowserDialogProps) {
  const { t } = useTranslation();
  const [results, setResults] = useState<SearchHit[] | null>(null);
  const [loading, setLoading] = useState(false);

  const runSearch = useCallback(async () => {
    setLoading(true);
    setResults(null);
    try {
      const r = await fetch(`${BASE}/search/estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ adapter, context }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const hits: SearchHit[] = Array.isArray(data) ? data : data.results ?? [];
      setResults(hits);
    } catch (e) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [adapter, context]);

  useEffect(() => {
    if (open) runSearch();
  }, [open, runSearch]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>{t("searchBrowser.title")}</DialogTitle>
      <DialogContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        {results === null && !loading && (
          <Typography variant="body2" color="text.secondary" textAlign="center">
            {t("searchBrowser.noSearchYet")}
          </Typography>
        )}
        {results && results.length === 0 && (
          <Typography variant="body2" color="text.secondary" textAlign="center">
            {t("searchBrowser.noResults")}
          </Typography>
        )}
        {results && results.length > 0 && (
          <TableContainer component={Paper} variant="outlined" sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>{t("searchBrowser.name")}</TableCell>
                  <TableCell align="right">{t("searchBrowser.score")}</TableCell>
                  <TableCell align="right">{t("searchBrowser.totalDamage")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.slice(0, 50).map((hit, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell>{hit.名称}</TableCell>
                    <TableCell align="right">{hit.score?.toFixed(2) ?? "--"}</TableCell>
                    <TableCell align="right">
                      {hit.total_damage?.toLocaleString(undefined, { maximumFractionDigits: 0 }) ?? "--"}
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
        <Button variant="contained" onClick={runSearch} disabled={loading}>
          {loading ? t("searchBrowser.searchResultTable") : t("common.refresh")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
