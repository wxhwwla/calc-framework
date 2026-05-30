import { useState, useCallback } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Chip,
  Alert,
  LinearProgress,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import EstimateIcon from "@mui/icons-material/Calculate";
import { estimateSearch, runSearch, type SearchRequest, type SearchResult, type SearchEstimate } from "../../api/search";

interface SearchPanelProps {
  currentParams: SearchRequest;
}

type SearchStatus = "idle" | "estimating" | "ready" | "running" | "done" | "error";

export default function SearchPanel({ currentParams }: SearchPanelProps) {
  const [status, setStatus] = useState<SearchStatus>("idle");
  const [estimate, setEstimate] = useState<SearchEstimate | null>(null);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [topN, setTopN] = useState(10);
  const [maxWorkers, setMaxWorkers] = useState(4);

  const handleEstimate = useCallback(async () => {
    setStatus("estimating");
    setError(null);
    setResult(null);
    try {
      const est = await estimateSearch(currentParams);
      setEstimate(est);
      setStatus(est.total_combinations > 0 ? "ready" : "idle");
    } catch (e: unknown) {
      setError(String(e));
      setStatus("error");
    }
  }, [currentParams]);

  const handleRun = useCallback(async () => {
    setStatus("running");
    setError(null);
    try {
      const res = await runSearch({
        ...currentParams,
        top_n: topN,
        max_workers: maxWorkers,
      });
      setResult(res);
      setStatus("done");
    } catch (e: unknown) {
      setError(String(e));
      setStatus("error");
    }
  }, [currentParams, topN, maxWorkers]);

  const handleReset = useCallback(() => {
    setStatus("idle");
    setEstimate(null);
    setResult(null);
    setError(null);
  }, []);

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)} 秒`;
    if (seconds < 3600) return `${Math.round(seconds / 60)} 分 ${Math.round(seconds % 60)} 秒`;
    const h = Math.floor(seconds / 3600);
    const m = Math.round((seconds % 3600) / 60);
    return `${h} 时 ${m} 分`;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        全量搜索
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2, flexWrap: "wrap" }}>
          <TextField
            size="small"
            label="Top-N"
            type="number"
            value={topN}
            onChange={(e) => setTopN(Math.max(1, parseInt(e.target.value) || 10))}
            sx={{ width: 100 }}
          />
          <TextField
            size="small"
            label="并行线程"
            type="number"
            value={maxWorkers}
            onChange={(e) => setMaxWorkers(Math.max(1, parseInt(e.target.value) || 4))}
            sx={{ width: 100 }}
          />
          <Button
            variant="outlined"
            startIcon={<EstimateIcon />}
            onClick={handleEstimate}
            disabled={status === "estimating" || status === "running"}
          >
            预估
          </Button>
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleRun}
            disabled={status === "estimating" || status === "running"}
            color={status === "ready" ? "success" : "primary"}
          >
            {status === "ready" ? "开始搜索" : "全量搜索"}
          </Button>
          {(status !== "idle" && status !== "error") && (
            <Button size="small" variant="text" onClick={handleReset}>
              重置
            </Button>
          )}
        </Box>

        {status === "estimating" && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" color="text.secondary">正在预估搜索规模…</Typography>
            <LinearProgress />
          </Box>
        )}

        {estimate && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              预估: <strong>{estimate.total_combinations.toLocaleString()}</strong> 种组合
              ({estimate.weapon_count} 武器 × {estimate.loadout_combinations.toLocaleString()} 配装)
            </Typography>
            <Typography variant="body2" color="text.secondary">
              预计耗时: <strong>{formatDuration(estimate.estimated_seconds)}</strong>
              {estimate.warnings.length > 0 && (
                <Chip label={estimate.warnings[0]} size="small" color="warning" sx={{ ml: 1 }} />
              )}
            </Typography>
          </Box>
        )}

        {status === "running" && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" color="info.main">搜索进行中…请耐心等待</Typography>
            <LinearProgress color="info" />
          </Box>
        )}
      </Paper>

      {result && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
            <Typography variant="subtitle2">
              搜索结果 (Top-{result.top_results.length})
            </Typography>
            <Typography variant="caption" color="text.secondary">
              已完成 {result.searched_combinations.toLocaleString()} / {result.total_combinations.toLocaleString()} 组合
              {result.cancelled && <Chip label="已取消" size="small" color="warning" sx={{ ml: 1 }} />}
            </Typography>
          </Box>

          <TableContainer sx={{ maxHeight: 400 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>武器</TableCell>
                  <TableCell>护甲</TableCell>
                  <TableCell>护手</TableCell>
                  <TableCell>配件A</TableCell>
                  <TableCell>配件B</TableCell>
                  <TableCell align="right">伤害</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {result.top_results.map((r, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell>{r.weapon_name}</TableCell>
                    <TableCell>{r.chest}</TableCell>
                    <TableCell>{r.gloves}</TableCell>
                    <TableCell>{r.accessory_a}</TableCell>
                    <TableCell>{r.accessory_b}</TableCell>
                    <TableCell align="right">
                      <strong>{Math.round(r.final_damage).toLocaleString()}</strong>
                    </TableCell>
                  </TableRow>
                ))}
                {result.top_results.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="text.secondary">无结果</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
    </Box>
  );
}
