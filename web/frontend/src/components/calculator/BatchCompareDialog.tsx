import { useState, useCallback } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, LinearProgress, Chip,
} from "@mui/material";

const BASE = "/api";

interface CompareEntry {
  label: string;
  char_name: string;
  weapon_name: string;
}

interface CompareResult {
  label: string;
  total: number;
  error?: string;
}

interface BatchCompareDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function BatchCompareDialog({ open, onClose }: BatchCompareDialogProps) {
  const [entries, setEntries] = useState<CompareEntry[]>([
    { label: "方案1", char_name: "", weapon_name: "" },
    { label: "方案2", char_name: "", weapon_name: "" },
  ]);
  const [results, setResults] = useState<CompareResult[] | null>(null);
  const [loading, setLoading] = useState(false);

  const addEntry = useCallback(() => {
    setEntries((prev) => [...prev, { label: `方案${prev.length + 1}`, char_name: "", weapon_name: "" }]);
  }, []);

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
      const r = await fetch(`${BASE}/compute/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data: CompareResult[] = await r.json();
      setResults(data);
    } catch (e) {
      setResults([{ label: "错误", total: 0, error: String(e) }]);
    } finally {
      setLoading(false);
    }
  }, [entries]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>多方案对比</DialogTitle>
      <DialogContent>
        <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>标签</TableCell>
                <TableCell>角色</TableCell>
                <TableCell>武器</TableCell>
                <TableCell align="center">操作</TableCell>
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
                      placeholder="角色名"
                    />
                  </TableCell>
                  <TableCell>
                    <input
                      value={entry.weapon_name}
                      onChange={(e) => updateEntry(idx, "weapon_name", e.target.value)}
                      style={{ width: 140, border: "1px solid #ccc", borderRadius: 4, padding: "2px 6px" }}
                      placeholder="武器名"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Button size="small" color="error" onClick={() => removeEntry(idx)} disabled={entries.length <= 1}>
                      删除
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Button variant="outlined" size="small" onClick={addEntry} sx={{ mb: 2 }}>
          + 添加方案
        </Button>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {results && results.length > 0 && (
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>排名</TableCell>
                  <TableCell>方案</TableCell>
                  <TableCell align="right">总伤</TableCell>
                  <TableCell>状态</TableCell>
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
                        <Typography variant="caption" color="success.main">OK</Typography>
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
        <Button onClick={onClose}>关闭</Button>
        <Button variant="contained" onClick={runCompare} disabled={loading}>
          {loading ? "计算中..." : "对比"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
