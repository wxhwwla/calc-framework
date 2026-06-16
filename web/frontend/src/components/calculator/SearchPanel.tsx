import { useCallback, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
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
import { canUseLocalSearch, runLocalTopNSearch, downloadSearchOutputBundle, exportSearchRunsDb } from "../../calc/search";
import { getCalcBackend } from "../../config/calcBackend";
import { getCalcContextMode } from "../../config/calcContext";
import { getSearchBackendMode } from "../../config/searchBackend";
import { estimateSearch, persistSearchHistory, runSearch, runSearchStream, type LoadoutResult, type SearchEstimate, type SearchRequest, type SearchResult, type StreamEvent } from "../../api/search";

interface SearchPanelProps {
  currentParams: SearchRequest;
}

type SearchStatus = "idle" | "estimating" | "ready" | "running" | "done" | "error";

/** 检测是否运行在 PythonAnywhere（不支持全量搜索） */
const isPythonAnywhere = (() => {
  const hostname = window.location.hostname.toLowerCase();
  // 使用 === 和 .endsWith 防止域名子串绕过
  return hostname === "pythonanywhere.com" || hostname === "www.pythonanywhere.com" || hostname.endsWith(".pythonanywhere.com");
})();

const handleDownloadClient = () => {
  window.location.href = "/api/download/client";
};

export default function SearchPanel({ currentParams }: SearchPanelProps) {
  const { t } = useTranslation();
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
  const searchStartedAtRef = useRef(0);

  const finalizeSearch = useCallback(
    async (res: SearchResult, source: string) => {
      setResult(res);
      setStatus("done");
      const elapsed = (performance.now() - searchStartedAtRef.current) / 1000;
      await persistSearchHistory(currentParams, res, { topN, elapsedSeconds: elapsed, source });
    },
    [currentParams, topN],
  );

  const wasmLocalReady = getCalcBackend() === "wasm" && getCalcContextMode() === "local";
  const localSearchEligible = useMemo(
    () =>
      canUseLocalSearch({
        hasCatalog: Boolean(estimate?.weapons?.length && estimate?.equipment_catalog),
      }),
    [estimate],
  );
  const largeCatalogWarning =
    localSearchEligible && (estimate?.total_combinations ?? 0) > 50_000;
  const searchBlockedOnPa = isPythonAnywhere && !localSearchEligible;

  const handleEstimate = useCallback(async () => {
    setStatus("estimating");
    setError(null);
    setResult(null);
    try {
      const est = await estimateSearch(currentParams, { includeCatalog: wasmLocalReady });
      setEstimate(est);
      setStatus(est.total_combinations > 0 ? "ready" : "idle");
    } catch (e: unknown) {
      setError(String(e));
      setStatus("error");
    }
  }, [currentParams, wasmLocalReady]);

  const handleRun = useCallback(async () => {
    setStatus("running");
    setError(null);
    setStreamProgress(null);
    setStreamResults([]);
    searchStartedAtRef.current = performance.now();

    if (localSearchEligible && estimate?.weapons && estimate.equipment_catalog) {
      const abortController = new AbortController();
      abortRef.current = abortController;
      try {
        const res = await runLocalTopNSearch(
          { ...currentParams, top_n: topN, max_workers: maxWorkers },
          {
            weapons: estimate.weapons,
            equipmentCatalog: estimate.equipment_catalog,
            topN,
            signal: abortController.signal,
            onProgress: ({ processed, total, topResults }) => {
              setStreamProgress({ processed, total });
              setStreamResults(topResults);
            },
          },
        );
        if (!res.cancelled) {
          await finalizeSearch(res, "browser");
        } else {
          setResult(res);
          setStatus("idle");
        }
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
      return;
    }

    if (useStreaming) {
      const abortController = new AbortController();
      abortRef.current = abortController;
      let accumulatedResults: LoadoutResult[] = [];
      let streamTotal = 0;
      let streamProcessed = 0;

      try {
        await runSearchStream(
          { ...currentParams, top_n: topN, max_workers: maxWorkers },
          (event: StreamEvent) => {
            switch (event.type) {
              case "start":
                streamTotal = event.total_combinations || 0;
                setStreamProgress({ processed: 0, total: streamTotal });
                break;
              case "summary":
                streamProcessed = event.searched_combinations || 0;
                streamTotal = event.total_combinations || streamTotal;
                setStreamProgress({
                  processed: streamProcessed,
                  total: streamTotal,
                });
                break;
              case "chunk":
                if (event.results) {
                  accumulatedResults = [...accumulatedResults, ...event.results];
                  setStreamResults(accumulatedResults);
                }
                break;
              case "stream_end":
                void finalizeSearch(
                  {
                    top_results: accumulatedResults,
                    total_combinations: streamTotal,
                    searched_combinations: streamProcessed,
                    cancelled: false,
                    warnings: [],
                  },
                  "api-stream",
                );
                break;
              case "error":
                setError(event.message || t("api.searchRunFailed"));
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
        await finalizeSearch(res, "api");
      } catch (e: unknown) {
        setError(String(e));
        setStatus("error");
      }
    }
  }, [currentParams, topN, maxWorkers, useStreaming, t, localSearchEligible, estimate, finalizeSearch]);

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
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    const h = Math.floor(seconds / 3600);
    const m = Math.round((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t("searchPanel.title")}
      </Typography>

      {isPythonAnywhere && !localSearchEligible && (
        <Alert severity="info" icon={<CloudOffIcon />} sx={{ mb: 2 }}>
          <span dangerouslySetInnerHTML={{ __html: t("searchPanel.pythonAnywhereNotice") }} />
          <Box sx={{ mt: 1 }}>
            <Button
              variant="contained"
              size="small"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadClient}
              sx={{ mr: 1, textTransform: "none" }}
            >
              {t("searchPanel.downloadServer")}
            </Button>
            {t("searchPanel.downloadServerHint")}
          </Box>
        </Alert>
      )}

      {largeCatalogWarning && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t("searchPanel.largeCatalogWarning", {
            count: (estimate?.total_combinations ?? 0).toLocaleString(),
          })}
        </Alert>
      )}

      {localSearchEligible && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {t("searchPanel.localSearchReady")}
        </Alert>
      )}

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2, flexWrap: "wrap" }}>
          <TextField
            size="small"
            label={t("searchPanel.resultCount")}
            type="number"
            value={topN}
            onChange={(e) => setTopN(Math.max(1, parseInt(e.target.value) || 10))}
            sx={{ width: { xs: 80, sm: 100 } }}
          />
          <TextField
            size="small"
            label={t("searchPanel.parallelThreads")}
            type="number"
            value={maxWorkers}
            onChange={(e) => setMaxWorkers(Math.max(1, parseInt(e.target.value) || 4))}
            sx={{ width: { xs: 80, sm: 100 } }}
          />
          <Button
            variant="outlined"
            startIcon={<EstimateIcon />}
            onClick={handleEstimate}
            disabled={status === "estimating" || status === "running"}
          >
            {t("searchPanel.estimate")}
          </Button>
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleRun}
            disabled={status === "estimating" || status === "running" || searchBlockedOnPa}
            color={status === "ready" ? "success" : "primary"}
          >
            {localSearchEligible
              ? t("searchPanel.browserSearch")
              : status === "ready"
                ? t("searchPanel.startSearch")
                : t("searchPanel.fullSearch")}
          </Button>
          {status === "running" && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<CancelIcon />}
              onClick={handleCancel}
            >
              {t("searchPanel.cancel")}
            </Button>
          )}
          {(status !== "idle" && status !== "error") && (
            <Button size="small" variant="text" onClick={handleReset}>
              {t("searchPanel.reset")}
            </Button>
          )}
          {!searchBlockedOnPa && !localSearchEligible && (
            <Chip
              label={useStreaming ? t("searchPanel.streamMode") : t("searchPanel.batchMode")}
              size="small"
              color={useStreaming ? "info" : "default"}
              variant="outlined"
              onClick={() => setUseStreaming(!useStreaming)}
              sx={{ cursor: "pointer" }}
            />
          )}
          {getSearchBackendMode() === "local" && wasmLocalReady && (
            <Chip label={t("searchPanel.localBackend")} size="small" color="success" variant="outlined" />
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
              status === "idle" ? t("searchPanel.statusIdle") :
              status === "estimating" ? t("searchPanel.statusEstimating") :
              status === "ready" ? t("searchPanel.statusReady") :
              status === "running" ? t("searchPanel.statusRunning") :
              status === "done" ? t("searchPanel.statusDone") : t("searchPanel.statusError")
            }
            size="small"
            color={
              status === "idle" ? "default" :
              status === "running" ? "info" :
              status === "done" ? "success" : "warning"
            }
          />
          <Chip label={t("searchPanel.threads", { n: maxWorkers })} size="small" variant="outlined" />
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
            <Typography variant="body2" color="text.secondary">{t("searchPanel.estimating")}</Typography>
            <LinearProgress />
          </Box>
        )}

        {estimate && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              <span dangerouslySetInnerHTML={{
                __html: t("searchPanel.searchEstimate", {
                  combinations: estimate.total_combinations.toLocaleString(),
                  weapons: estimate.weapon_count,
                  loadouts: estimate.loadout_combinations.toLocaleString(),
                  time: formatDuration(estimate.estimated_seconds),
                }),
              }} />
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
                  {t("searchPanel.searching", {
                    processed: streamProgress.processed.toLocaleString(),
                    total: streamProgress.total.toLocaleString(),
                  })}
                </Typography>
                <LinearProgress
                  color="info"
                  variant={streamProgress.total > 0 ? "determinate" : "indeterminate"}
                  value={streamProgress.total > 0 ? (streamProgress.processed / streamProgress.total) * 100 : undefined}
                />
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" color="info.main">{t("searchPanel.searchingNoProgress")}</Typography>
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
              {t("searchPanel.liveResults", { n: streamResults.length })}
            </Typography>
          </Box>

          <TableContainer sx={{ maxHeight: 300 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>{t("searchPanel.tableWeapon")}</TableCell>
                  <TableCell>{t("searchPanel.tableChest")}</TableCell>
                  <TableCell>{t("searchPanel.tableGloves")}</TableCell>
                  <TableCell>{t("searchPanel.tableAccessoryA")}</TableCell>
                  <TableCell>{t("searchPanel.tableAccessoryB")}</TableCell>
                  <TableCell align="right">{t("searchPanel.tableDamage")}</TableCell>
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
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1, flexWrap: "wrap", gap: 1 }}>
            <Typography variant="subtitle2">
              {t("searchPanel.searchResults", { n: result.top_results.length })}
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
              <Button
                size="small"
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={() => downloadSearchOutputBundle(result.top_results, topN)}
              >
                {t("searchPanel.exportSearchOutput")}
              </Button>
              <Button
                size="small"
                variant="text"
                onClick={async () => {
                  const blob = await exportSearchRunsDb();
                  const url = URL.createObjectURL(blob);
                  const anchor = document.createElement("a");
                  anchor.href = url;
                  anchor.download = "search_runs.db";
                  anchor.click();
                  URL.revokeObjectURL(url);
                }}
              >
                {t("searchPanel.exportSqlite")}
              </Button>
              <Typography variant="caption" color="text.secondary">
                {t("searchPanel.completed", {
                  searched: result.searched_combinations.toLocaleString(),
                  total: result.total_combinations.toLocaleString(),
                })}
                {result.cancelled && <Chip label={t("searchPanel.cancelled")} size="small" color="warning" sx={{ ml: 1 }} />}
              </Typography>
            </Box>
          </Box>

          <TableContainer sx={{ maxHeight: 400, overflowX: 'auto' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>{t("searchPanel.tableWeapon")}</TableCell>
                  <TableCell>{t("searchPanel.tableChest")}</TableCell>
                  <TableCell>{t("searchPanel.tableGloves")}</TableCell>
                  <TableCell>{t("searchPanel.tableAccessoryA")}</TableCell>
                  <TableCell>{t("searchPanel.tableAccessoryB")}</TableCell>
                  <TableCell align="right">{t("searchPanel.tableDamage")}</TableCell>
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
                      <Typography color="text.secondary">{t("searchPanel.noResults")}</Typography>
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
