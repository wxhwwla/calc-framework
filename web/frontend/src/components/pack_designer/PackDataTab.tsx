import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { fetchAdapterDataSummary, type DataEntitySummary } from "../../api/adapterPack";
import { usePackDesignerStore } from "../../store/packDesignerStore";
import ProfileDataEditor from "../designer/ProfileDataEditor";
import { getProfile } from "../../constants/dataProfileConfig";

/** 配置包设计器 — 数据录入（按适配器分轨，可编辑实体走 ProfileDataEditor） */
export default function PackDataTab() {
  const { t } = useTranslation();
  const adapterId = usePackDesignerStore((s) => s.adapterId);
  const [entities, setEntities] = useState<DataEntitySummary[]>([]);
  const [entityKey, setEntityKey] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const profile = getProfile(adapterId);

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

  const editable = entities.filter((e) => !e.read_only);
  const currentKey = entityKey || editable[0]?.key || entities[0]?.key || "";

  if (profile && editable.length > 0) {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t("packDesigner.dataTab.webEditableHint", { label: profile.label })}
        </Typography>
        {editable.length > 1 && (
          <FormControl size="small" sx={{ mb: 2, minWidth: 160 }}>
            <InputLabel>{t("packDesigner.dataTab.entityType")}</InputLabel>
            <Select
              value={currentKey}
              label={t("packDesigner.dataTab.entityType")}
              onChange={(e: SelectChangeEvent) => setEntityKey(e.target.value)}
            >
              {editable.map((e) => (
                <MenuItem key={e.key} value={e.key}>
                  {e.label} ({e.count})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
        <ProfileDataEditor profileId={adapterId} entityKey={currentKey} compact />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t("packDesigner.dataTab.noWebEditable")}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {entities.length === 0 && !error && (
        <Typography color="text.secondary">{t("packDesigner.dataTab.noBuiltinData")}</Typography>
      )}
    </Box>
  );
}
