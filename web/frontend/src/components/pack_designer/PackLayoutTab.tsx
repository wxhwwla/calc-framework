import { useEffect, useState, useCallback } from "react";
import {
  Alert,
  Box,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { fetchAdapterLayout } from "../../api/adapterPack";
import { usePackDesignerStore } from "../../store/packDesignerStore";
import type { LayoutSection } from "../../api/layout";

/** 配置包设计器 — 布局预览（按所选适配器加载 ui/layout.json） */
export default function PackLayoutTab() {
  const adapterId = usePackDesignerStore((s) => s.adapterId);
  const adapters = usePackDesignerStore((s) => s.adapters);
  const [sections, setSections] = useState<LayoutSection[]>([]);
  const [layoutName, setLayoutName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const adapterLabel = adapters.find((a) => a.id === adapterId)?.name ?? adapterId;

  const reload = useCallback(async () => {
    setError(null);
    try {
      const layout = await fetchAdapterLayout(adapterId);
      setLayoutName(String(layout.name ?? adapterId));
      setSections((layout.sections as LayoutSection[]) ?? []);
    } catch (e: unknown) {
      setSections([]);
      setError(String(e));
    }
  }, [adapterId]);

  useEffect(() => {
    reload();
  }, [reload]);

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        加载适配器 <strong>{adapterLabel}</strong> 的 layout.json（与桌面布局页「选择适配器」一致）。
        可视化拖拽编辑请用桌面配置包设计器。
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          {layoutName || "—"} · {sections.length} 个区块
        </Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          {sections.map((s) => (
            <Chip key={s.id} size="small" label={`${s.title || s.id} (${s.type})`} />
          ))}
          {sections.length === 0 && !error && (
            <Typography variant="caption" color="text.secondary">无 sections</Typography>
          )}
        </Box>
      </Paper>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>类型</TableCell>
              <TableCell>标题</TableCell>
              <TableCell>变量/输出数</TableCell>
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
