import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, Chip, Paper, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography,
} from "@mui/material";
import { fetchAdapterLayout } from "../../api/adapterPack";
import { usePackDesignerStore } from "../../store/packDesignerStore";
import type { LayoutSection } from "../../api/layout";

/** 配置包设计器 — 布局编辑（JSON，导出时使用草稿） */
export default function PackLayoutTab() {
  const { t } = useTranslation();
  const adapterId = usePackDesignerStore((s) => s.adapterId);
  const adapters = usePackDesignerStore((s) => s.adapters);
  const layoutDraft = usePackDesignerStore((s) => s.layoutDraft);
  const setLayoutDraft = usePackDesignerStore((s) => s.setLayoutDraft);
  const [sections, setSections] = useState<LayoutSection[]>([]);
  const [layoutName, setLayoutName] = useState("");
  const [jsonText, setJsonText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const adapterLabel = adapters.find((a) => a.id === adapterId)?.name ?? adapterId;

  const applyLayout = useCallback((layout: Record<string, unknown>) => {
    setLayoutName(String(layout.name ?? adapterId));
    setSections((layout.sections as LayoutSection[]) ?? []);
    setJsonText(JSON.stringify(layout, null, 2));
    setLayoutDraft(layout);
  }, [adapterId, setLayoutDraft]);

  const reload = useCallback(async () => {
    setError(null);
    try {
      const layout = await fetchAdapterLayout(adapterId);
      applyLayout(layout);
    } catch (e: unknown) {
      setSections([]);
      setError(String(e));
    }
  }, [adapterId, applyLayout]);

  useEffect(() => {
    reload();
  }, [reload]);

  const handleApplyJson = () => {
    try {
      const parsed = JSON.parse(jsonText) as Record<string, unknown>;
      applyLayout(parsed);
      setError(null);
    } catch (e: unknown) {
      setError(`${t("packDesigner.layoutTab.jsonInvalid")}: ${e}`);
    }
  };

  const handleReset = () => {
    setLayoutDraft(null);
    reload();
  };

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t("packDesigner.layoutTab.adapterLabel")} <strong>{adapterLabel}</strong> · {t("packDesigner.layoutTab.hintText")}
        {layoutDraft && <Chip size="small" label={t("packDesigner.layoutTab.draftModified")} color="warning" sx={{ ml: 1 }} />}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          {layoutName || "—"} · {t("packDesigner.layoutTab.sectionsCount", { n: sections.length })}
        </Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
          {sections.map((s) => (
            <Chip key={s.id} size="small" label={`${s.title || s.id} (${s.type})`} />
          ))}
        </Box>
        <TextField
          fullWidth
          multiline
          minRows={12}
          maxRows={24}
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          sx={{ fontFamily: "monospace", fontSize: 12, mb: 1 }}
        />
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button size="small" variant="contained" onClick={handleApplyJson}>{t("packDesigner.layoutTab.applyJson")}</Button>
          <Button size="small" variant="outlined" onClick={handleReset}>{t("packDesigner.layoutTab.reload")}</Button>
        </Box>
      </Paper>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t("packDesigner.layoutTab.tableId")}</TableCell>
              <TableCell>{t("packDesigner.layoutTab.tableType")}</TableCell>
              <TableCell>{t("packDesigner.layoutTab.tableTitle")}</TableCell>
              <TableCell>{t("packDesigner.layoutTab.tableVarOutputCount")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sections.map((s) => (
              <TableRow key={s.id}>
                <TableCell>{s.id}</TableCell>
                <TableCell>{s.type}</TableCell>
                <TableCell>{s.title}</TableCell>
                <TableCell>
                  {s.type === "inputs" ? (s.variables?.length ?? 0)
                    : s.type === "outputs" ? (s.outputs?.length ?? 0)
                    : s.widget_type ?? "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
