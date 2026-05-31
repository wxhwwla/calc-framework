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
import { fetchEquipmentCatalog } from "../../api/search";

const SLOT_SPECS: { key: string; label: string }[] = [
  { key: "chest", label: "护甲" },
  { key: "gloves", label: "护手" },
  { key: "accessory_a", label: "配件A" },
  { key: "accessory_b", label: "配件B" },
];

export interface FixedLoadoutSelection {
  chest: string | null;
  gloves: string | null;
  accessory_a: string | null;
  accessory_b: string | null;
}

interface FixedLoadoutPanelProps {
  onChange?: (selection: FixedLoadoutSelection | null) => void;
}

const NO_FIX_LABEL = "（不固定）";

export default function FixedLoadoutPanel({ onChange }: FixedLoadoutPanelProps) {
  const [catalog, setCatalog] = useState<Record<string, { 名称: string }[]>>({});
  const [selection, setSelection] = useState<FixedLoadoutSelection>({
    chest: null,
    gloves: null,
    accessory_a: null,
    accessory_b: null,
  });

  useEffect(() => {
    fetchEquipmentCatalog().then(setCatalog).catch(() => {});
  }, []);

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

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        固定配装
        {hasAnyFixed && (
          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
            （已固定 {Object.values(selection).filter((v) => v !== null).length} 件）
          </Typography>
        )}
      </Typography>

      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1.5 }}>
        选择装备名称固定该槽位，选「（不固定）」则遍历。
      </Typography>

      <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
        {SLOT_SPECS.map((slot) => (
          <FormControl key={slot.key} size="small" sx={{ minWidth: 160, flex: 1 }}>
            <InputLabel>{slot.label}</InputLabel>
            <Select
              value={selection[slot.key as keyof FixedLoadoutSelection] ?? ""}
              label={slot.label}
              onChange={(e) => handleSlotChange(slot.key, e.target.value)}
            >
              <MenuItem value="">
                <em>{NO_FIX_LABEL}</em>
              </MenuItem>
              {(catalog[slot.key] || []).map((eq) => (
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
