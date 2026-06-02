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
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import {
  fetchCharacters,
  fetchWeapons,
  fetchEquipments,
  type CharacterSummary,
  type WeaponSummary,
  type EquipmentSummary,
} from "../../api/data";

type DataType = "character" | "weapon" | "equipment";

interface ColumnDef {
  key: string;
  label: string;
  render?: (val: unknown) => string;
}

const COLUMNS: Record<DataType, ColumnDef[]> = {
  character: [
    { key: "名称", label: "名称" },
    { key: "类型", label: "类型" },
    { key: "星级", label: "星级", render: (v) => `${v}★` },
    { key: "主能力", label: "主能力" },
    { key: "副能力", label: "副能力" },
    { key: "武器", label: "武器" },
  ],
  weapon: [
    { key: "名称", label: "名称" },
    { key: "类型", label: "类型" },
    { key: "星级", label: "星级", render: (v) => `${v}★` },
  ],
  equipment: [
    { key: "名称", label: "名称" },
    { key: "装备种类", label: "种类" },
    { key: "部位", label: "部位" },
    { key: "稀有度", label: "稀有度" },
    { key: "所属套组", label: "套组" },
  ],
};

export default function DataBrowserTab() {
  const [dataType, setDataType] = useState<DataType>("character");
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [weapons, setWeapons] = useState<WeaponSummary[]>([]);
  const [equipments, setEquipments] = useState<EquipmentSummary[]>([]);

  const loadData = useCallback(async () => {
    try {
      if (dataType === "character") setCharacters(await fetchCharacters());
      else if (dataType === "weapon") setWeapons(await fetchWeapons());
      else setEquipments(await fetchEquipments());
    } catch {
      // ignore
    }
  }, [dataType]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const rows: any[] =
    dataType === "character" ? characters : dataType === "weapon" ? weapons : equipments;

  const columns = COLUMNS[dataType];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        数据浏览
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 2, alignItems: "center" }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>数据源</InputLabel>
          <Select
            value={dataType}
            label="数据源"
            onChange={(e: SelectChangeEvent) => setDataType(e.target.value as DataType)}
          >
            <MenuItem value="character">角色数据</MenuItem>
            <MenuItem value="weapon">武器数据</MenuItem>
            <MenuItem value="equipment">装备数据</MenuItem>
          </Select>
        </FormControl>

        <Button variant="outlined" size="small" onClick={loadData}>
          刷新
        </Button>

        <Typography variant="body2" color="text.secondary">
          共 {rows.length} 条记录
        </Typography>
      </Box>

      <TableContainer sx={{ maxHeight: 500, overflowX: 'auto' }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.key}>{col.label}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, idx) => (
              <TableRow key={idx}>
                {columns.map((col) => (
                  <TableCell key={col.key}>
                    {col.render
                      ? col.render(row[col.key])
                      : String(row[col.key] ?? "--")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
            {rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length} align="center">
                  <Typography color="text.secondary">暂无数据</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
