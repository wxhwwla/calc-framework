import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
  TextField,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import {
  createProfileRow,
  deleteProfileRow,
  fetchProfileRows,
  updateProfileRow,
} from "../../api/dataProfiles";
import { getEntity, getProfile, type FieldDef } from "../../constants/dataProfileConfig";

interface Props {
  profileId: string;
  /** 锁定实体类型（配置包页用） */
  entityKey?: string;
  /** 隐藏 profile / 实体选择器 */
  compact?: boolean;
}

/** 多游戏通用数据录入（对齐桌面 data_editor） */
export default function ProfileDataEditor({ profileId, entityKey: fixedEntity, compact }: Props) {
  const { t } = useTranslation();
  const profile = getProfile(profileId);
  const [entityKey, setEntityKey] = useState(fixedEntity ?? profile?.entities[0]?.key ?? "");
  const entity = getEntity(profileId, entityKey);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (fixedEntity) setEntityKey(fixedEntity);
  }, [fixedEntity]);

  const loadData = useCallback(async () => {
    if (!entityKey) return;
    try {
      setRows(await fetchProfileRows(profileId, entityKey));
      setError(null);
    } catch (e: unknown) {
      setRows([]);
      setError(String(e));
    }
  }, [profileId, entityKey]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const fields: FieldDef[] = entity?.fields ?? [];
  const columns = entity?.columns ?? [];

  const openAdd = () => {
    setEditingIndex(null);
    const init: Record<string, string> = {};
    for (const f of fields) init[f.key] = f.type === "number" ? "0" : "";
    setFormData(init);
    setDialogOpen(true);
  };

  const openEdit = (idx: number) => {
    setEditingIndex(idx);
    const item = rows[idx];
    const init: Record<string, string> = {};
    for (const f of fields) init[f.key] = String(item[f.key] ?? "");
    setFormData(init);
    setDialogOpen(true);
  };

  const handleDelete = async (idx: number) => {
    const name = String(rows[idx]["名称"] ?? "");
    try {
      await deleteProfileRow(profileId, entityKey, name);
      await loadData();
    } catch (e: unknown) {
      setError(String(e));
    }
  };

  const handleSave = async () => {
    const payload: Record<string, unknown> = {};
    for (const f of fields) {
      payload[f.key] = f.type === "number" ? parseFloat(formData[f.key] || "0") : formData[f.key];
    }
    try {
      if (editingIndex === null) {
        await createProfileRow(profileId, entityKey, payload);
      } else {
        const oldName = String(rows[editingIndex]["名称"] ?? "");
        await updateProfileRow(profileId, entityKey, oldName, payload);
      }
      setDialogOpen(false);
      await loadData();
    } catch (e: unknown) {
      setError(String(e));
    }
  };

  if (!profile || !entity) {
    return <Typography color="text.secondary">{t("designer.dataEditorTab.unknownProfile")}: {profileId}</Typography>;
  }

  return (
    <Box>
      {!compact && (
        <Box sx={{ display: "flex", gap: 2, mb: 2, alignItems: "center", flexWrap: "wrap" }}>
          {!fixedEntity && profile.entities.length > 1 && (
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>{t("designer.dataEditorTab.entityType")}</InputLabel>
              <Select
                value={entityKey}
                label={t("designer.dataEditorTab.entityType")}
                onChange={(e: SelectChangeEvent) => setEntityKey(e.target.value)}
              >
                {profile.entities.map((e) => (
                  <MenuItem key={e.key} value={e.key}>
                    {e.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <Typography variant="body2" color="text.secondary">
            {t("designer.dataEditorTab.countLabel", { profile: profile.label, entity: entity.label, count: rows.length })}
          </Typography>
        </Box>
      )}

      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <Button variant="contained" size="small" onClick={openAdd}>
          {t("designer.dataEditorTab.new")}
        </Button>
        <Button variant="outlined" size="small" onClick={loadData}>
          {t("common.refresh")}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer sx={{ maxHeight: 450, overflowX: 'auto' }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col}>{col}</TableCell>
              ))}
              <TableCell>{t("designer.dataEditorTab.operations")}</TableCell>
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
                    {t("designer.dataEditorTab.edit")}
                  </Button>
                  <Button size="small" color="error" onClick={() => handleDelete(idx)}>
                    {t("common.delete")}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length + 1} align="center">
                  <Typography color="text.secondary">{t("common.noData")}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingIndex === null ? t("designer.dataEditorTab.new") : t("designer.dataEditorTab.edit")}</DialogTitle>
        <DialogContent>
          {fields.map((f) => (
            <Box key={f.key} sx={{ mt: 2 }}>
              {f.type === "select" ? (
                <FormControl fullWidth size="small">
                  <InputLabel>{f.label}</InputLabel>
                  <Select
                    value={formData[f.key] ?? ""}
                    label={f.label}
                    onChange={(e) => setFormData((p) => ({ ...p, [f.key]: e.target.value }))}
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
                  onChange={(e) => setFormData((p) => ({ ...p, [f.key]: e.target.value }))}
                />
              )}
            </Box>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t("common.cancel")}</Button>
          <Button variant="contained" onClick={handleSave}>
            {t("common.save")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
