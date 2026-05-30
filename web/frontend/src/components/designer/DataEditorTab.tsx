import { useEffect, useState, useCallback } from "react";
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { fetchCharacters, fetchWeapons, fetchEquipments } from "../../api/data";
import {
  createCharacter,
  updateCharacter,
  deleteCharacter,
  createWeapon,
  updateWeapon,
  deleteWeapon,
  createEquipment,
  updateEquipment,
  deleteEquipment,
} from "../../api/designer";

type DataType = "character" | "weapon" | "equipment";

interface FieldDef {
  key: string;
  label: string;
  type: "text" | "number" | "select";
  options?: string[];
}

const FIELDS: Record<DataType, FieldDef[]> = {
  character: [
    { key: "名称", label: "名称", type: "text" },
    { key: "类型", label: "类型", type: "select", options: ["物理", "能量", "电磁", "热熔", "异裂"] },
    { key: "星级", label: "星级", type: "number" },
    { key: "武器", label: "武器", type: "text" },
    { key: "主能力", label: "主能力", type: "select", options: ["力量", "敏捷", "智识", "意志"] },
    { key: "副能力", label: "副能力", type: "select", options: ["力量", "敏捷", "智识", "意志"] },
    { key: "力量", label: "力量", type: "number" },
    { key: "敏捷", label: "敏捷", type: "number" },
    { key: "智识", label: "智识", type: "number" },
    { key: "意志", label: "意志", type: "number" },
    { key: "信赖", label: "信赖", type: "number" },
  ],
  weapon: [
    { key: "名称", label: "名称", type: "text" },
    { key: "类型", label: "类型", type: "select", options: ["尖兵", "刀锋", "重装", "射手", "术士", "医疗", "支援"] },
    { key: "星级", label: "星级", type: "number" },
  ],
  equipment: [
    { key: "名称", label: "名称", type: "text" },
    { key: "部位", label: "部位", type: "select", options: ["胸甲", "护手", "饰品"] },
    { key: "稀有度", label: "稀有度", type: "text" },
    { key: "所属套组", label: "套组", type: "text" },
  ],
};

const COLUMN_KEYS: Record<DataType, string[]> = {
  character: ["名称", "类型", "星级", "主能力", "副能力"],
  weapon: ["名称", "类型", "星级"],
  equipment: ["名称", "部位", "稀有度"],
};

export default function DataEditorTab() {
  const [dataType, setDataType] = useState<DataType>("character");
  const [rows, setRows] = useState<any[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      if (dataType === "character") setRows(await fetchCharacters());
      else if (dataType === "weapon") setRows(await fetchWeapons());
      else setRows(await fetchEquipments());
    } catch {
      setRows([]);
    }
  }, [dataType]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openAdd = useCallback(() => {
    setEditingIndex(null);
    const init: Record<string, string> = {};
    for (const f of FIELDS[dataType]) {
      init[f.key] = f.type === "number" ? "0" : "";
    }
    setFormData(init);
    setDialogOpen(true);
  }, [dataType]);

  const openEdit = useCallback(
    (idx: number) => {
      setEditingIndex(idx);
      const item = rows[idx];
      const init: Record<string, string> = {};
      for (const f of FIELDS[dataType]) {
        init[f.key] = String(item[f.key] ?? "");
      }
      setFormData(init);
      setDialogOpen(true);
    },
    [dataType, rows],
  );

  const handleDelete = useCallback(
    async (idx: number) => {
      const item = rows[idx];
      const name = String(item["名称"] ?? "");
      try {
        if (dataType === "character") await deleteCharacter(name);
        else if (dataType === "weapon") await deleteWeapon(name);
        else await deleteEquipment(name);
        await loadData();
      } catch (e: unknown) {
        setError(String(e));
      }
    },
    [dataType, rows, loadData],
  );

  const handleSave = useCallback(async () => {
    const payload: Record<string, unknown> = {};
    for (const f of FIELDS[dataType]) {
      payload[f.key] = f.type === "number" ? parseFloat(formData[f.key] || "0") : formData[f.key];
    }

    try {
      if (editingIndex === null) {
        if (dataType === "character") await createCharacter(payload);
        else if (dataType === "weapon") await createWeapon(payload);
        else await createEquipment(payload);
      } else {
        const oldName = String(rows[editingIndex]["名称"] ?? "");
        if (dataType === "character") await updateCharacter(oldName, payload);
        else if (dataType === "weapon") await updateWeapon(oldName, payload);
        else await updateEquipment(oldName, payload);
      }
      setDialogOpen(false);
      await loadData();
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [dataType, editingIndex, formData, rows, loadData]);

  const setField = useCallback((key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }, []);

  const columns = COLUMN_KEYS[dataType];
  const fields = FIELDS[dataType];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        数据编辑
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 2, alignItems: "center" }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>数据类型</InputLabel>
          <Select
            value={dataType}
            label="数据类型"
            onChange={(e: SelectChangeEvent) => setDataType(e.target.value as DataType)}
          >
            <MenuItem value="character">角色数据</MenuItem>
            <MenuItem value="weapon">武器数据</MenuItem>
            <MenuItem value="equipment">装备数据</MenuItem>
          </Select>
        </FormControl>

        <Button variant="contained" size="small" onClick={openAdd}>
          新增
        </Button>

        <Typography variant="body2" color="text.secondary">
          共 {rows.length} 条记录
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer sx={{ maxHeight: 450 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col}>{col}</TableCell>
              ))}
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, idx) => (
              <TableRow key={idx}>
                {columns.map((col) => (
                  <TableCell key={col}>{String(row[col] ?? "--")}</TableCell>
                ))}
                <TableCell>
                  <Button size="small" onClick={() => openEdit(idx)} sx={{ mr: 1 }}>
                    编辑
                  </Button>
                  <Button size="small" color="error" onClick={() => handleDelete(idx)}>
                    删除
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length + 1} align="center">
                  <Typography color="text.secondary">暂无数据</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingIndex === null ? "新增" : "编辑"}</DialogTitle>
        <DialogContent>
          {fields.map((f) => (
            <Box key={f.key} sx={{ mt: 2 }}>
              {f.type === "select" ? (
                <FormControl fullWidth size="small">
                  <InputLabel>{f.label}</InputLabel>
                  <Select
                    value={formData[f.key] ?? ""}
                    label={f.label}
                    onChange={(e) => setField(f.key, e.target.value)}
                  >
                    {(f.options ?? []).map((opt) => (
                      <MenuItem key={opt} value={opt}>
                        {opt}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ) : (
                <TextField
                  fullWidth
                  size="small"
                  label={f.label}
                  type={f.type === "number" ? "number" : "text"}
                  value={formData[f.key] ?? ""}
                  onChange={(e) => setField(f.key, e.target.value)}
                />
              )}
            </Box>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSave}>
            保存
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
