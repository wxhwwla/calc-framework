import { useCallback, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import CancelIcon from "@mui/icons-material/Cancel";
import CloudOffIcon from "@mui/icons-material/CloudOff";
import DownloadIcon from "@mui/icons-material/Download";
import EstimateIcon from "@mui/icons-material/Calculate";
import SearchIcon from "@mui/icons-material/Search";
import { estimateSearch, runSearch, runSearchStream, type LoadoutResult, type SearchEstimate, type SearchRequest, type SearchResult, type StreamEvent } from "../../api/search";

interface SearchPanelProps {
  currentParams: SearchRequest;
}

type SearchStatus = "idle" | "estimating" | "ready" | "running" | "done" | "error";

/** 检测是否运行在 PythonAnywhere（不支持全量搜索） */
const isPythonAnywhere = window.location.hostname.includes("pythonanywhere.com");

const handleDownloadClient = () => {
  window.location.href = "/api/download/client";
};

export default function SearchPanel({ currentParams }: SearchPanelProps) {
  const [status, setStatus] = useState<SearchStatus>("idle");
  const [estimate, setEstimate] = useState<SearchEstimate | null>(null);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [topN, setTopN] = useState(10);
  const [maxWorkers, setMaxWorkers] = useState(4);
  const [streamProgress, setStreamProgress] = useState<{ processed: number; total: number } | null>(null);
  const [streamResults, setStreamResults] = useState<LoadoutResult[]>([]);
  const [useStreaming, setUseStreaming] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

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
    setStreamProgress(null);
    setStreamResults([]);

    if (useStreaming) {
      const abortController = new AbortController();
      abortRef.current = abortController;
      let accumulatedResults: LoadoutResult[] = [];

      try {
        await runSearchStream(
          { ...currentParams, top_n: topN, max_workers: maxWorkers },
          (event: StreamEvent) => {
            switch (event.type) {
              case "start":
                setStreamProgress({ processed: 0, total: event.total_combinations || 0 });
                break;
              case "summary":
                setStreamProgress({
                  processed: event.searched_combinations || 0,
                  total: event.total_combinations || 0,
                });
                break;
              case "chunk":
                if (event.results) {
                  accumulatedResults = [...accumulatedResults, ...event.results];
                  setStreamResults(accumulatedResults);
                }
                break;
              case "stream_end":
                setResult({
                  top_results: accumulatedResults,
                  total_combinations: 0,
                  searched_combinations: 0,
                  cancelled: false,
                  warnings: [],
                });
                setStatus("done");
                break;
              case "error":
                setError(event.message || "搜索失败");
                setStatus("error");
                break;
            }
          },
          abortController.signal,
        );
      } catch (e: unknown) {
        if ((e as Error).name === "AbortError") {
          setStatus("idle");
          setStreamProgress(null);
        } else {
          setError(String(e));
          setStatus("error");
        }
      } finally {
        abortRef.current = null;
      }
    } else {
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
    }
  }, [currentParams, topN, maxWorkers, useStreaming]);

  const handleReset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus("idle");
    setEstimate(null);
    setResult(null);
    setError(null);
    setStreamProgress(null);
    setStreamResults([]);
  }, []);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus("idle");
    setStreamProgress(null);
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

      {isPythonAnywhere && (
        <Alert severity="info" icon={<CloudOffIcon />} sx={{ mb: 2 }}>
          线上环境仅支持<strong>组合规模预估</strong>；全量搜索与流式搜索请下载本地服务器。
          <Box sx={{ mt: 1 }}>
            <Button
              variant="contained"
              size="small"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadClient}
              sx={{ mr: 1, textTransform: "none" }}
            >
              下载本地搜索服务器
            </Button>
            解压后双击 exe，在 localhost 使用完整搜索
          </Box>
        </Alert>
      )}

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2, flexWrap: "wrap" }}>
          <TextField
            size="small"
            label="结果条数"
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
            disabled={status === "estimating" || status === "running" || isPythonAnywhere}
            color={status === "ready" ? "success" : "primary"}
          >
            {status === "ready" ? "开始搜索" : "全量搜索"}
          </Button>
          {status === "running" && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<CancelIcon />}
              onClick={handleCancel}
            >
              取消
            </Button>
          )}
          {(status !== "idle" && status !== "error") && (
            <Button size="small" variant="text" onClick={handleReset}>
              重置
            </Button>
          )}
          {!isPythonAnywhere && (
            <Chip
              label={useStreaming ? "流式模式" : "批量模式"}
              size="small"
              color={useStreaming ? "info" : "default"}
              variant="outlined"
              onClick={() => setUseStreaming(!useStreaming)}
              sx={{ cursor: "pointer" }}
            />
          )}
        </Box>

        <Box
          sx={{
            display: "flex", gap: 1, alignItems: "center", mb: 1.5,
            p: 1, bgcolor: "action.hover", borderRadius: 1,
          }}
        >
          <Chip
            label={
              status === "idle" ? "空闲" :
              status === "estimating" ? "预估中" :
              status === "ready" ? "已就绪" :
              status === "running" ? "搜集中" :
              status === "done" ? "已完成" : "错误"
            }
            size="small"
            color={
              status === "idle" ? "default" :
              status === "running" ? "info" :
              status === "done" ? "success" : "warning"
            }
          />
          <Chip label={`${maxWorkers} 线程`} size="small" variant="outlined" />
          {status === "running" && streamProgress && (
            <Chip
              label={`${streamProgress.processed.toLocaleString()} / ${streamProgress.total.toLocaleString()}`}
              size="small"
              color="info"
              variant="outlined"
            />
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
              &nbsp;预计 {formatDuration(estimate.estimated_seconds)}
              {estimate.warnings.length > 0 && (
                <Chip label={estimate.warnings[0]} size="small" color="warning" sx={{ ml: 1 }} />
              )}
            </Typography>
          </Box>
        )}

        {status === "running" && (
          <Box sx={{ mb: 1 }}>
            {streamProgress ? (
              <Box>
                <Typography variant="body2" color="info.main">
                  搜索中: {streamProgress.processed.toLocaleString()} / {streamProgress.total.toLocaleString()} 组合
                </Typography>
                <LinearProgress
                  color="info"
                  variant={streamProgress.total > 0 ? "determinate" : "indeterminate"}
                  value={streamProgress.total > 0 ? (streamProgress.processed / streamProgress.total) * 100 : undefined}
                />
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" color="info.main">搜索进行中…请耐心等待</Typography>
                <LinearProgress color="info" />
              </Box>
            )}
          </Box>
        )}
      </Paper>

      {status === "running" && streamResults.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
            <Typography variant="subtitle2">
              实时结果 (已到 {streamResults.length} 条)
            </Typography>
          </Box>

          <TableContainer sx={{ maxHeight: 300 }}>
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
                {streamResults.slice(0, topN).map((r, idx) => (
                  <TableRow key={idx} hover selected>
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
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

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

          <TableContainer sx={{ maxHeight: 400, overflowX: 'auto' }}>
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
