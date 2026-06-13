import { useState, useMemo, useCallback, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { fetchEquipmentCatalog } from "../../api/search";

const SLOT_KEYS = ["chest", "gloves", "accessory_a", "accessory_b"] as const;
type SlotKey = typeof SLOT_KEYS[number];

function slotI18nKey(key: SlotKey): string {
  switch (key) {
    case "chest": return "fixedLoadout.chest";
    case "gloves": return "fixedLoadout.gloves";
    case "accessory_a": return "fixedLoadout.accessoryA";
    case "accessory_b": return "fixedLoadout.accessoryB";
  }
}

export interface FixedLoadoutSelection {
  chest: string | null;
  gloves: string | null;
  accessory_a: string | null;
  accessory_b: string | null;
}

interface FixedLoadoutPanelProps {
  onChange?: (selection: FixedLoadoutSelection | null) => void;
  equipmentScope?: string;
}

/** 与 GUI qt_control_dock.populate_fixed_loadout_slots 一致：配件 A/B 共用 accessories 列表 */
function catalogKeyForSlot(slotKey: string): string {
  if (slotKey === "accessory_a" || slotKey === "accessory_b") return "accessories";
  return slotKey;
}

export default function FixedLoadoutPanel({ onChange, equipmentScope }: FixedLoadoutPanelProps) {
  const { t } = useTranslation();
  const [catalog, setCatalog] = useState<Record<string, { 名称: string }[]>>({});
  const [selection, setSelection] = useState<FixedLoadoutSelection>({
    chest: null,
    gloves: null,
    accessory_a: null,
    accessory_b: null,
  });

  useEffect(() => {
    fetchEquipmentCatalog(equipmentScope ?? "全部装备").then(setCatalog).catch(() => {});
  }, [equipmentScope]);

  const hasAnyFixed = useMemo(
    () => Object.values(selection).some((v) => v !== null),
    [selection],
  );

  const handleSlotChange = useCallback(
    (slotKey: string, equipmentName: string) => {
      const next = { ...selection, [slotKey]: equipmentName || null };
      setSelection(next);
      if (onChange) {
        const hasAny = Object.values(next).some((v) => v !== null);
        onChange(hasAny ? next : null);
      }
    },
    [selection, onChange],
  );

  const noFixLabel = t("fixedLoadout.noFix");

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        {t("fixedLoadout.title")}
        {hasAnyFixed && (
          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
            {t("fixedLoadout.fixedCount", { n: Object.values(selection).filter((v) => v !== null).length })}
          </Typography>
        )}
      </Typography>

      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1.5 }}>
        {t("fixedLoadout.hint")}
      </Typography>

      <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
        {SLOT_KEYS.map((key) => (
          <FormControl key={key} size="small" sx={{ minWidth: 160, flex: 1 }}>
            <InputLabel>{t(slotI18nKey(key))}</InputLabel>
            <Select
              value={selection[key] ?? ""}
              label={t(slotI18nKey(key))}
              onChange={(e) => handleSlotChange(key, e.target.value)}
            >
              <MenuItem value="">
                <em>{noFixLabel}</em>
              </MenuItem>
              {(catalog[catalogKeyForSlot(key)] || []).map((eq) => (
                <MenuItem key={eq.名称} value={eq.名称}>
                  {eq.名称}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        ))}
      </Box>
    </Paper>
  );
}
