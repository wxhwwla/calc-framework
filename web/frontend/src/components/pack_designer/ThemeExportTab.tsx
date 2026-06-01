import { useEffect, useState, useCallback } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Chip,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { fetchDefaultTheme, previewExport, downloadCalcpack, type ThemeConfig } from "../../api/pack";
import { fetchAdapterMeta } from "../../api/adapters";
import {
  fetchAdapterDag,
  fetchAdapterLayout,
  fetchAdapterDataSummary,
  fetchAdapterPackBundle,
} from "../../api/adapterPack";
import { usePackDesignerStore } from "../../store/packDesignerStore";

const COLOR_KEYS: (keyof ThemeConfig["colors"])[] = [
  "primary", "background", "surface", "text",
  "text_secondary", "border", "success", "warning", "error",
];

export default function ThemeExportTab() {
  const adapterId = usePackDesignerStore((s) => s.adapterId);
  const [theme, setTheme] = useState<ThemeConfig | null>(null);
  const [fontFamily, setFontFamily] = useState("Microsoft YaHei");
  const [fontSize, setFontSize] = useState(12);
  const [colors, setColors] = useState<Record<string, string>>({});
  const [packName, setPackName] = useState("自定义计算配置");
  const [dataInfo, setDataInfo] = useState<Record<string, number>>({});
  const [dagInfo, setDagInfo] = useState("未加载");
  const [layoutInfo, setLayoutInfo] = useState("未加载");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchDefaultTheme().then((t) => {
      setTheme(t);
      setFontFamily(t.font.family);
      setFontSize(t.font.size);
      setColors({ ...t.colors });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    fetchAdapterMeta(adapterId)
      .then((m) => setPackName(String(m.name ?? "自定义计算配置")))
      .catch(() => {});
  }, [adapterId]);

  const refreshStatus = useCallback(async () => {
    try {
      const [summary, dag, layout] = await Promise.all([
        fetchAdapterDataSummary(adapterId),
        fetchAdapterDag(adapterId),
        fetchAdapterLayout(adapterId),
      ]);
      const info: Record<string, number> = {};
      for (const e of summary) info[e.key] = e.count;
      setDataInfo(info);
      setDagInfo(`${Object.keys(dag.nodes ?? {}).length} 个节点`);
      setLayoutInfo(`${(layout.sections as unknown[])?.length ?? 0} 个区块`);
    } catch {
      setDataInfo({});
      setDagInfo("未加载");
      setLayoutInfo("未加载");
    }
  }, [adapterId]);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  const setColor = useCallback((key: string, value: string) => {
    setColors((prev) => ({ ...prev, [key]: value }));
  }, []);

  const buildExportMeta = useCallback(async (dataKeys: string[]) => {
    const base = await fetchAdapterMeta(adapterId);
    const meta: Record<string, unknown> = { ...base };
    meta.name = packName;
    meta.entry_dag = "dag/formula.dag.json";
    meta.ui_layout = "ui/layout.json";
    meta.ui_theme = "ui/theme.json";
    if (dataKeys.length > 0) {
      meta.entry_data = dataKeys.map((k) => `data/${k}.json`);
    }
    return meta;
  }, [adapterId, packName]);

  const handleExport = useCallback(async () => {
    setError(null);
    setSuccess(null);
    try {
      const bundle = await fetchAdapterPackBundle(adapterId);
      const themePayload = theme ? {
        schema_version: theme.schema_version,
        name: theme.name,
        font: { family: fontFamily, size: fontSize, weight: "normal" },
        colors,
        spacing: { padding: 8, gap: 4 },
      } : undefined;

      const dataFiles = bundle.data_files;
      const meta = await buildExportMeta(
        Object.keys(dataFiles).filter((k) => dataFiles[k]?.length > 0),
      );
      meta.name = packName;

      await downloadCalcpack({
        meta,
        dag: bundle.dag,
        layout: bundle.layout,
        theme: themePayload,
        data_files: dataFiles,
        filename: `${packName}.calcpack`,
      });

      setSuccess(`已导出 ${packName}.calcpack（${adapterId}）`);
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [adapterId, theme, fontFamily, fontSize, colors, packName, buildExportMeta]);

  const handlePreview = useCallback(async () => {
    setError(null);
    setSuccess(null);
    try {
      const bundle = await fetchAdapterPackBundle(adapterId);
      const meta = await buildExportMeta(Object.keys(bundle.data_summary));

      const preview = await previewExport({
        meta,
        dag: bundle.dag,
        layout: bundle.layout,
        data_files: Object.fromEntries(
          Object.keys(bundle.data_summary).map((k) => [k, []]),
        ),
      });

      setSuccess(
        `预览 (${adapterId}): DAG ${preview.dag_nodes} 节点, ` +
        `Layout ${preview.layout_sections} 区块, ` +
        `数据: ${JSON.stringify(preview.data_files)}`,
      );
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [adapterId, buildExportMeta]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        主题与导出
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        导出内容随页顶所选适配器加载（DAG / layout / 数据分轨）。
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>已加载数据</Typography>
        <TableContainer>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>适配器</TableCell>
                <TableCell sx={{ border: "none" }}>{adapterId}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>数据文件</TableCell>
                <TableCell sx={{ border: "none" }}>
                  {Object.entries(dataInfo).map(([k, v]) => (
                    <Chip key={k} label={`${k}: ${v}条`} size="small" sx={{ mr: 0.5 }} />
                  ))}
                  {Object.keys(dataInfo).length === 0 && "无（仅公式+布局）"}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>DAG</TableCell>
                <TableCell sx={{ border: "none" }}>{dagInfo}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>Layout</TableCell>
                <TableCell sx={{ border: "none" }}>{layoutInfo}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>主题配置</Typography>

        <TextField
          fullWidth
          size="small"
          label="字体"
          value={fontFamily}
          onChange={(e) => setFontFamily(e.target.value)}
          sx={{ mb: 1 }}
        />

        <FormControl fullWidth size="small" sx={{ mb: 1 }}>
          <InputLabel>字号</InputLabel>
          <Select
            value={fontSize}
            label="字号"
            onChange={(e: SelectChangeEvent<number>) => setFontSize(e.target.value as number)}
          >
            {[10, 11, 12, 13, 14, 16, 18, 20, 24].map((s) => (
              <MenuItem key={s} value={s}>{s}px</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
          色板
        </Typography>

        <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1 }}>
          {COLOR_KEYS.map((key) => (
            <TextField
              key={key}
              size="small"
              label={key}
              value={colors[key] ?? ""}
              onChange={(e) => setColor(key, e.target.value)}
              InputProps={{
                startAdornment: (
                  <Box
                    sx={{
                      width: 16, height: 16, borderRadius: "2px",
                      bgcolor: colors[key] ?? "#000",
                      mr: 1, flexShrink: 0,
                      border: "1px solid #555",
                    }}
                  />
                ),
              }}
            />
          ))}
        </Box>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>导出配置</Typography>

        <TextField
          fullWidth
          size="small"
          label="配置包名称"
          value={packName}
          onChange={(e) => setPackName(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Box sx={{ display: "flex", gap: 1 }}>
          <Button variant="outlined" onClick={handlePreview}>
            预览
          </Button>
          <Button variant="contained" onClick={handleExport}>
            导出 .calcpack
          </Button>
        </Box>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
    </Box>
  );
}
