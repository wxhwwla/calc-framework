import { useCallback, useEffect, useState } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, LinearProgress,
} from "@mui/material";

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
      <DialogTitle>搜索浏览器</DialogTitle>
      <DialogContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        {results === null && !loading && (
          <Typography variant="body2" color="text.secondary" textAlign="center">
            尚无搜索结果，请执行搜索
          </Typography>
        )}
        {results && results.length === 0 && (
          <Typography variant="body2" color="text.secondary" textAlign="center">
            未找到结果
          </Typography>
        )}
        {results && results.length > 0 && (
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>名称</TableCell>
                  <TableCell align="right">分数</TableCell>
                  <TableCell align="right">总伤</TableCell>
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
        <Button onClick={onClose}>关闭</Button>
        <Button variant="contained" onClick={runSearch} disabled={loading}>
          {loading ? "搜索中..." : "刷新"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
