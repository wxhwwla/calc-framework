import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
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

function useColumns(t: ReturnType<typeof useTranslation>["t"]): Record<DataType, ColumnDef[]> {
  return {
    character: [
      { key: "名称", label: t("designer.dataBrowserTab.columns.name") },
      { key: "类型", label: t("designer.dataBrowserTab.columns.type") },
      { key: "星级", label: t("designer.dataBrowserTab.columns.star"), render: (v) => `${v}★` },
      { key: "主能力", label: t("designer.dataBrowserTab.columns.mainAbility") },
      { key: "副能力", label: t("designer.dataBrowserTab.columns.subAbility") },
      { key: "武器", label: t("designer.dataBrowserTab.columns.weapon") },
    ],
    weapon: [
      { key: "名称", label: t("designer.dataBrowserTab.columns.name") },
      { key: "类型", label: t("designer.dataBrowserTab.columns.type") },
      { key: "星级", label: t("designer.dataBrowserTab.columns.star"), render: (v) => `${v}★` },
    ],
    equipment: [
      { key: "名称", label: t("designer.dataBrowserTab.columns.name") },
      { key: "装备种类", label: t("designer.dataBrowserTab.columns.equipmentKind") },
      { key: "部位", label: t("designer.dataBrowserTab.columns.part") },
      { key: "稀有度", label: t("designer.dataBrowserTab.columns.rarity") },
      { key: "所属套组", label: t("designer.dataBrowserTab.columns.setGroup") },
    ],
  };
}

export default function DataBrowserTab() {
  const { t } = useTranslation();
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

  const rows: Record<string, unknown>[] =
    dataType === "character" ? characters : dataType === "weapon" ? weapons : equipments;

  const columns = useColumns(t)[dataType];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t("designer.dataBrowserTab.title")}
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 2, alignItems: "center" }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>{t("designer.dataBrowserTab.dataSource")}</InputLabel>
          <Select
            value={dataType}
            label={t("designer.dataBrowserTab.dataSource")}
            onChange={(e: SelectChangeEvent) => setDataType(e.target.value as DataType)}
          >
            <MenuItem value="character">{t("designer.dataBrowserTab.characterData")}</MenuItem>
            <MenuItem value="weapon">{t("designer.dataBrowserTab.weaponData")}</MenuItem>
            <MenuItem value="equipment">{t("designer.dataBrowserTab.equipmentData")}</MenuItem>
          </Select>
        </FormControl>

        <Button variant="outlined" size="small" onClick={loadData}>
          {t("designer.dataBrowserTab.refresh")}
        </Button>

        <Typography variant="body2" color="text.secondary">
          {t("designer.dataBrowserTab.totalRecords", { n: rows.length })}
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
                  <Typography color="text.secondary">{t("common.noData")}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
