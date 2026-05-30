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
import { fetchCharacters, fetchWeapons, fetchEquipments } from "../../api/data";
import { fetchLayout, fetchDag } from "../../api/layout";
import { fetchDefaultTheme, previewExport, downloadCalcpack, type ThemeConfig } from "../../api/pack";

const COLOR_KEYS: (keyof ThemeConfig["colors"])[] = [
  "primary", "background", "surface", "text",
  "text_secondary", "border", "success", "warning", "error",
];

export default function ThemeExportTab() {
  const [theme, setTheme] = useState<ThemeConfig | null>(null);
  const [fontFamily, setFontFamily] = useState("Microsoft YaHei");
  const [fontSize, setFontSize] = useState(12);
  const [colors, setColors] = useState<Record<string, string>>({});
  const [packName, setPackName] = useState("自定义计算配置");
  const [dataInfo, setDataInfo] = useState<Record<string, number>>({});
  const [dagInfo, setDagInfo] = useState<string>("未加载");
  const [layoutInfo, setLayoutInfo] = useState<string>("未加载");
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

  const loadData = useCallback(async () => {
    try {
      const chars = await fetchCharacters();
      const weapons = await fetchWeapons();
      const equips = await fetchEquipments();
      setDataInfo({ characters: chars.length, weapons: weapons.length, equipments: equips.length });
    } catch {
      setDataInfo({});
    }
  }, []);

  const loadDag = useCallback(async () => {
    try {
      const dag = await fetchDag();
      const nodeCount = Object.keys(dag.nodes ?? {}).length;
      setDagInfo(`${nodeCount} 个节点`);
    } catch {
      setDagInfo("未加载");
    }
  }, []);

  const loadLayout = useCallback(async () => {
    try {
      const layout = await fetchLayout();
      const sectionCount = (layout.sections ?? []).length;
      setLayoutInfo(`${sectionCount} 个区块`);
    } catch {
      setLayoutInfo("未加载");
    }
  }, []);

  useEffect(() => {
    loadData();
    loadDag();
    loadLayout();
  }, [loadData, loadDag, loadLayout]);

  const setColor = useCallback((key: string, value: string) => {
    setColors((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleExport = useCallback(async () => {
    setError(null);
    setSuccess(null);
    try {
      const [chars, weapons, equips, dag, layout] = await Promise.all([
        fetchCharacters().catch(() => []),
        fetchWeapons().catch(() => []),
        fetchEquipments().catch(() => []),
        fetchDag().catch(() => ({ nodes: {} })),
        fetchLayout().catch(() => ({ sections: [] })),
      ] as const);

      const themePayload = theme ? {
        schema_version: theme.schema_version,
        name: theme.name,
        font: { family: fontFamily, size: fontSize, weight: "normal" },
        colors,
        spacing: { padding: 8, gap: 4 },
      } : undefined;

      const meta = {
        name: packName,
        game: "自定义",
        version: "1.0.0",
        schema_version: "dag-v1",
        author: "",
        description: "由配置包设计器导出",
        entry_dag: "dag/formula.dag.json",
        ui_layout: "ui/layout.json",
        ui_theme: "ui/theme.json",
        entry_data: ["data/characters.json", "data/weapons.json", "data/equipments.json"],
      };

      await downloadCalcpack({
        meta,
        dag: dag as Record<string, unknown>,
        layout: layout as Record<string, unknown>,
        theme: themePayload,
        data_files: {
          characters: chars as unknown as Record<string, unknown>[],
          weapons: weapons as unknown as Record<string, unknown>[],
          equipments: equips as unknown as Record<string, unknown>[],
        },
        filename: `${packName}.calcpack`,
      });

      setSuccess(`已导出 ${packName}.calcpack`);
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [theme, fontFamily, fontSize, colors, packName]);

  const handlePreview = useCallback(async () => {
    setError(null);
    setSuccess(null);
    try {
      const [dag, layout] = await Promise.all([
        fetchDag().catch(() => ({ nodes: {} })),
        fetchLayout().catch(() => ({ sections: [] })),
      ]);

      const preview = await previewExport({
        meta: { name: packName },
        dag: dag as Record<string, unknown>,
        layout: layout as Record<string, unknown>,
        data_files: {
          characters: [],
          weapons: [],
          equipments: [],
        },
      });

      setSuccess(
        `预览: DAG ${preview.dag_nodes} 节点, ` +
        `Layout ${preview.layout_sections} 区块, ` +
        `数据文件: ${JSON.stringify(preview.data_files)}`
      );
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [packName]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        主题与导出
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>已加载数据</Typography>
        <TableContainer>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell sx={{ border: "none", pl: 0 }}>数据文件</TableCell>
                <TableCell sx={{ border: "none" }}>
                  {Object.entries(dataInfo).map(([k, v]) => (
                    <Chip key={k} label={`${k}: ${v}条`} size="small" sx={{ mr: 0.5 }} />
                  ))}
                  {Object.keys(dataInfo).length === 0 && "未加载"}
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
