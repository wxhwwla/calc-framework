import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  const adapterId = usePackDesignerStore((s) => s.adapterId);
  const layoutDraft = usePackDesignerStore((s) => s.layoutDraft);
  const [theme, setTheme] = useState<ThemeConfig | null>(null);
  const [fontFamily, setFontFamily] = useState("Microsoft YaHei");
  const [fontSize, setFontSize] = useState(12);
  const [colors, setColors] = useState<Record<string, string>>({});
  const [packName, setPackName] = useState("");
  const [dataInfo, setDataInfo] = useState<Record<string, number>>({});
  const [dagInfo, setDagInfo] = useState(t("packDesigner.themeExportTab.notLoaded"));
  const [layoutInfo, setLayoutInfo] = useState(t("packDesigner.themeExportTab.notLoaded"));
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
      .then((m) => setPackName(String(m.name ?? "")))
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
      setDagInfo(t("packDesigner.themeExportTab.nodesCount", { n: Object.keys(dag.nodes ?? {}).length }));
      setLayoutInfo(t("packDesigner.themeExportTab.sectionsCount", { n: (layout.sections as unknown[])?.length ?? 0 }));
    } catch {
      setDataInfo({});
      setDagInfo(t("packDesigner.themeExportTab.notLoaded"));
      setLayoutInfo(t("packDesigner.themeExportTab.notLoaded"));
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
      const layout = layoutDraft ?? bundle.layout;
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
        layout: layout as Record<string, unknown>,
        theme: themePayload,
        data_files: dataFiles,
        filename: `${packName}.calcpack`,
      });

      setSuccess(t("packDesigner.themeExportTab.exported", { file: `${packName}.calcpack`, adapter: adapterId }));
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [adapterId, layoutDraft, theme, fontFamily, fontSize, colors, packName, buildExportMeta]);

  const handlePreview = useCallback(async () => {
    setError(null);
    setSuccess(null);
    try {
      const bundle = await fetchAdapterPackBundle(adapterId);
      const layout = layoutDraft ?? bundle.layout;
      const meta = await buildExportMeta(Object.keys(bundle.data_summary));

      const preview = await previewExport({
        meta,
        dag: bundle.dag,
        layout: layout as Record<string, unknown>,
        data_files: Object.fromEntries(
          Object.keys(bundle.data_summary).map((k) => [k, []]),
        ),
      });

      setSuccess(
        t("packDesigner.themeExportTab.previewResult", {
          adapter: adapterId,
          dag: preview.dag_nodes,
          layout: preview.layout_sections,
          data: JSON.stringify(preview.data_files),
        })
      );
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [adapterId, layoutDraft, buildExportMeta]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t("packDesigner.themeExportTab.title")}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t("packDesigner.themeExportTab.description")}
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>{t("packDesigner.themeExportTab.loadedData")}</Typography>
        <TableContainer>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>{t("packDesigner.themeExportTab.adapter")}</TableCell>
                <TableCell sx={{ border: "none" }}>{adapterId}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>{t("packDesigner.themeExportTab.dataFiles")}</TableCell>
                <TableCell sx={{ border: "none" }}>
                  {Object.entries(dataInfo).map(([k, v]) => (
                    <Chip key={k} label={`${k}: ${v}${t("common.countUnit")}`} size="small" sx={{ mr: 0.5 }} />
                  ))}
                  {Object.keys(dataInfo).length === 0 && t("packDesigner.themeExportTab.noDataFiles")}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>{t("packDesigner.themeExportTab.dag")}</TableCell>
                <TableCell sx={{ border: "none" }}>{dagInfo}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>{t("packDesigner.themeExportTab.layout")}</TableCell>
                <TableCell sx={{ border: "none" }}>{layoutInfo}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>{t("packDesigner.themeExportTab.themeConfig")}</Typography>

        <TextField
          fullWidth
          size="small"
          label={t("packDesigner.themeExportTab.font")}
          value={fontFamily}
          onChange={(e) => setFontFamily(e.target.value)}
          sx={{ mb: 1 }}
        />

        <FormControl fullWidth size="small" sx={{ mb: 1 }}>
          <InputLabel>{t("packDesigner.themeExportTab.fontSize")}</InputLabel>
          <Select
            value={fontSize}
            label={t("packDesigner.themeExportTab.fontSize")}
            onChange={(e: SelectChangeEvent<number>) => setFontSize(e.target.value as number)}
          >
            {[10, 11, 12, 13, 14, 16, 18, 20, 24].map((s) => (
              <MenuItem key={s} value={s}>{s}px</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
          {t("packDesigner.themeExportTab.colorPalette")}
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
        <Typography variant="subtitle2" gutterBottom>{t("packDesigner.themeExportTab.exportConfig")}</Typography>

        <TextField
          fullWidth
          size="small"
          label={t("packDesigner.themeExportTab.packName")}
          value={packName}
          onChange={(e) => setPackName(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Box sx={{ display: "flex", gap: 1 }}>
          <Button variant="outlined" onClick={handlePreview}>
            {t("packDesigner.themeExportTab.preview")}
          </Button>
          <Button variant="contained" onClick={handleExport}>
            {t("packDesigner.themeExportTab.exportCalcpack")}
          </Button>
        </Box>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
    </Box>
  );
}
