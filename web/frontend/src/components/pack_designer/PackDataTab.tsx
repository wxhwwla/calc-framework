import { useEffect, useState, useCallback } from "react";
import {
  Alert,
  Box,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { fetchAdapterDataSummary, type DataEntitySummary } from "../../api/adapterPack";
import { usePackDesignerStore } from "../../store/packDesignerStore";
import DataEditorTab from "../designer/DataEditorTab";

/** 配置包设计器 — 数据录入（按适配器分轨） */
export default function PackDataTab() {
  const adapterId = usePackDesignerStore((s) => s.adapterId);
  const [entities, setEntities] = useState<DataEntitySummary[]>([]);
  const [entityKey, setEntityKey] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setError(null);
    try {
      const list = await fetchAdapterDataSummary(adapterId);
      setEntities(list);
      setEntityKey((prev) => (list.some((e) => e.key === prev) ? prev : list[0]?.key ?? ""));
    } catch (e: unknown) {
      setEntities([]);
      setError(String(e));
    }
  }, [adapterId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const current = entities.find((e) => e.key === entityKey);

  if (adapterId === "endfield") {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          终末地：可编辑角色 / 武器 / 装备（与桌面配置包设计器数据页一致）。
        </Typography>
        <DataEditorTab />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        当前适配器数据为只读预览；完整编辑请用桌面配置包设计器或 BWIKI 解析流程。
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {entities.length > 1 && (
        <FormControl size="small" sx={{ mb: 2, minWidth: 160 }}>
          <InputLabel>实体类型</InputLabel>
          <Select
            value={entityKey}
            label="实体类型"
            onChange={(e: SelectChangeEvent) => setEntityKey(e.target.value)}
          >
            {entities.map((e) => (
              <MenuItem key={e.key} value={e.key}>
                {e.label} ({e.count})
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {entities.length === 0 && !error && (
        <Typography color="text.secondary">此适配器无内置 data 文件（导出时仅含 DAG + layout）。</Typography>
      )}

      {current && (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>实体</TableCell>
                <TableCell>条数</TableCell>
                <TableCell>Web 录入</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>{current.label}</TableCell>
                <TableCell>{current.count.toLocaleString()}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={current.read_only ? "只读" : "可编辑"}
                    color={current.read_only ? "default" : "success"}
                  />
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
