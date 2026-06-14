import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  List,
  ListItemButton,
  ListItemText,
  Typography,
  Select,
  MenuItem,
  TextField,
  FormControl,
  InputLabel,
  IconButton,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import { useTranslation } from "react-i18next";

export type ManualBuffEntry = { effect_type: string; value: number };
export type ManualBuffStore = Record<string, ManualBuffEntry[]>;

interface SegmentManualBuffDialogProps {
  open: boolean;
  onClose: () => void;
  store: ManualBuffStore;
  onApply: (store: ManualBuffStore) => void;
  manualCounts: Record<string, number>;
  physicalAbnormalCounts: Record<string, number>;
  spellAbnormalCounts: Record<string, number>;
}

function formatKeyLabel(key: string): string {
  const parts = key.split(":");
  if (parts.length >= 2 && /^\d+$/.test(parts[parts.length - 1])) {
    const occ = parts.pop();
    return `${parts.join(":")} 第${occ}次`;
  }
  return key;
}

export default function SegmentManualBuffDialog({
  open,
  onClose,
  store,
  onApply,
  manualCounts,
  physicalAbnormalCounts,
  spellAbnormalCounts,
}: SegmentManualBuffDialogProps) {
  const { t } = useTranslation();
  const [localStore, setLocalStore] = useState<ManualBuffStore>({});
  const [keys, setKeys] = useState<string[]>([]);
  const [selectedKey, setSelectedKey] = useState("");
  const [zoneOptions, setZoneOptions] = useState<{ label: string; id: string }[]>([]);
  const [presets, setPresets] = useState<{ name: string; entries: ManualBuffEntry[] }[]>([]);
  const [selectedPreset, setSelectedPreset] = useState("");

  useEffect(() => {
    if (!open) return;
    setLocalStore(JSON.parse(JSON.stringify(store)));
    fetch("/api/manual-buff/zone-options")
      .then((r) => r.json())
      .then(setZoneOptions)
      .catch(() => {});
    fetch("/api/manual-buff/consumable-presets")
      .then((r) => r.json())
      .then(setPresets)
      .catch(() => {});
    fetch("/api/manual-buff/active-keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        manual_counts: manualCounts,
        physical_abnormal_counts: physicalAbnormalCounts,
        spell_abnormal_counts: spellAbnormalCounts,
      }),
    })
      .then((r) => r.json())
      .then((data: { keys: string[] }) => {
        setKeys(data.keys);
        setSelectedKey((prev) => (data.keys.includes(prev) ? prev : data.keys[0] ?? ""));
      })
      .catch(() => setKeys([]));
  }, [open, store, manualCounts, physicalAbnormalCounts, spellAbnormalCounts]);

  const currentEntries = useMemo(
    () => localStore[selectedKey] ?? [],
    [localStore, selectedKey],
  );

  const updateEntries = useCallback(
    (entries: ManualBuffEntry[]) => {
      if (!selectedKey) return;
      setLocalStore((prev) => {
        const next = { ...prev };
        if (entries.length) next[selectedKey] = entries;
        else delete next[selectedKey];
        return next;
      });
    },
    [selectedKey],
  );

  const applyPreset = useCallback(async () => {
    if (!selectedPreset) return;
    const r = await fetch("/api/manual-buff/apply-consumable", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        preset_name: selectedPreset,
        manual_counts: manualCounts,
        physical_abnormal_counts: physicalAbnormalCounts,
        spell_abnormal_counts: spellAbnormalCounts,
        store: localStore,
        merge: true,
      }),
    });
    if (!r.ok) return;
    const data: { store: ManualBuffStore } = await r.json();
    setLocalStore(data.store);
  }, [selectedPreset, manualCounts, physicalAbnormalCounts, spellAbnormalCounts, localStore]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t("segmentManual.title")}</DialogTitle>
      <DialogContent sx={{ display: "flex", gap: 2, minHeight: 360, flexWrap: "wrap" }}>
        <Box sx={{ width: { xs: "100%", sm: 220 }, borderRight: { xs: 0, sm: 1 }, borderColor: "divider", pr: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {t("segmentManual.keyListLabel")}
          </Typography>
          <List dense>
            {keys.map((key) => (
              <ListItemButton
                key={key}
                selected={key === selectedKey}
                onClick={() => setSelectedKey(key)}
              >
                <ListItemText primary={formatKeyLabel(key)} secondary={key} />
              </ListItemButton>
            ))}
          </List>
        </Box>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
            <FormControl size="small" sx={{ flex: 1 }}>
              <InputLabel>{t("segmentManual.consumablePreset")}</InputLabel>
              <Select
                value={selectedPreset}
                label={t("segmentManual.consumablePreset")}
                onChange={(e) => setSelectedPreset(String(e.target.value))}
              >
                <MenuItem value="">
                  <em>{t("segmentManual.noApply")}</em>
                </MenuItem>
                {presets.map((p) => (
                  <MenuItem key={p.name} value={p.name}>
                    {p.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button size="small" onClick={applyPreset} disabled={!selectedPreset}>
              {t("segmentManual.writeAllActive")}
            </Button>
          </Box>
          {selectedKey ? (
            <>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                {formatKeyLabel(selectedKey)}
              </Typography>
              {currentEntries.map((entry, idx) => (
                <Box key={idx} sx={{ display: "flex", gap: 1, mb: 1, alignItems: "center" }}>
                  <FormControl size="small" sx={{ minWidth: 160 }}>
                    <Select
                      value={entry.effect_type}
                      onChange={(e) => {
                        const next = [...currentEntries];
                        next[idx] = { ...entry, effect_type: String(e.target.value) };
                        updateEntries(next);
                      }}
                    >
                      {zoneOptions.map((z) => (
                        <MenuItem key={z.label} value={z.label}>
                          {z.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <TextField
                    size="small"
                    type="number"
                    label={t("segmentManual.valueLabel")}
                    value={entry.value}
                    onChange={(e) => {
                      const next = [...currentEntries];
                      next[idx] = { ...entry, value: parseFloat(e.target.value) || 0 };
                      updateEntries(next);
                    }}
                    sx={{ width: 100 }}
                  />
                  <IconButton
                    size="small"
                    onClick={() => updateEntries(currentEntries.filter((_, i) => i !== idx))}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() =>
                  updateEntries([
                    ...currentEntries,
                    { effect_type: zoneOptions[0]?.label ?? "暴击率", value: 0 },
                  ])
                }
              >
                {t("segmentManual.addEntry")}
              </Button>
            </>
          ) : (
            <Typography color="text.secondary">{t("segmentManual.noKeysHint")}</Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.cancel")}</Button>
        <Button
          variant="contained"
          onClick={() => {
            onApply(localStore);
            onClose();
          }}
        >
          {t("segmentManual.apply")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
