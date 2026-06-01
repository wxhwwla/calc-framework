import { useState, useCallback, useEffect } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Table, TableBody, TableCell, TableRow, TextField, Typography,
  MenuItem, Select, FormControl, InputLabel, Box,
} from "@mui/material";

const BUFF_SLOTS = [
  { key: "攻击倍率乘区", label: "攻击倍率乘区", default: 1.0 },
  { key: "增伤乘区", label: "增伤乘区", default: 1.0 },
  { key: "防御乘区", label: "防御乘区", default: 1.0 },
  { key: "抗性乘区", label: "抗性乘区", default: 1.0 },
  { key: "暴击乘区", label: "暴击乘区", default: 1.0 },
  { key: "易伤乘区", label: "易伤乘区", default: 1.0 },
  { key: "失衡易伤乘区", label: "失衡易伤乘区", default: 1.3 },
  { key: "伤害类型乘区", label: "伤害类型乘区", default: 1.0 },
  { key: "精英伤乘区", label: "精英伤乘区", default: 1.0 },
  { key: "额外伤害乘区", label: "额外伤害乘区", default: 1.0 },
  { key: "元素反应乘区", label: "元素反应乘区", default: 1.0 },
];

interface ManualBuffDialogProps {
  open: boolean;
  onClose: () => void;
  values: Record<string, number>;
  onApply: (values: Record<string, number>) => void;
}

export default function ManualBuffDialog({ open, onClose, values, onApply }: ManualBuffDialogProps) {
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [presets, setPresets] = useState<{ name: string; entries: { effect_type: string; value: number }[] }[]>([]);
  const [selectedPreset, setSelectedPreset] = useState("");

  useEffect(() => {
    if (open) {
      fetch("/api/manual-buff/consumable-presets")
        .then((r) => r.json())
        .then(setPresets)
        .catch(() => setPresets([]));
    }
  }, [open]);

  useEffect(() => {
    if (open) {
      const initial: Record<string, string> = {};
      for (const slot of BUFF_SLOTS) {
        initial[slot.key] = String(values[slot.key] ?? slot.default);
      }
      setEdits(initial);
    }
  }, [open, values]);

  const handleChange = useCallback((key: string, v: string) => {
    setEdits((prev) => ({ ...prev, [key]: v }));
  }, []);

  const handleApply = useCallback(() => {
    const parsed: Record<string, number> = {};
    for (const [key, val] of Object.entries(edits)) {
      const n = parseFloat(val);
      parsed[key] = isNaN(n) ? 1.0 : n;
    }
    onApply(parsed);
    onClose();
  }, [edits, onApply, onClose]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>手动 Buff 微调</DialogTitle>
      <DialogContent>
        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
          修改乘区系数后点击"应用"。消耗品预设为参考条目（完整段级写入见桌面版）。
        </Typography>
        {presets.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <FormControl size="small" fullWidth>
              <InputLabel>消耗品预设（参考）</InputLabel>
              <Select
                value={selectedPreset}
                label="消耗品预设（参考）"
                onChange={(e) => {
                  const name = String(e.target.value);
                  setSelectedPreset(name);
                  const preset = presets.find((p) => p.name === name);
                  if (!preset) return;
                  const next = { ...edits };
                  for (const entry of preset.entries) {
                    if (entry.effect_type === "其他伤害加成") {
                      next["增伤乘区"] = String(1 + entry.value);
                    }
                    if (entry.effect_type === "暴击率") {
                      next["暴击乘区"] = String(parseFloat(next["暴击乘区"] || "1") + entry.value);
                    }
                  }
                  setEdits(next);
                }}
              >
                <MenuItem value="">
                  <em>不应用</em>
                </MenuItem>
                {presets.map((p) => (
                  <MenuItem key={p.name} value={p.name}>
                    {p.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        )}
        <Table size="small">
          <TableBody>
            {BUFF_SLOTS.map((slot) => (
              <TableRow key={slot.key}>
                <TableCell sx={{ pl: 0, fontSize: "0.85rem" }}>{slot.label}</TableCell>
                <TableCell sx={{ width: 100 }}>
                  <TextField
                    size="small"
                    variant="outlined"
                    value={edits[slot.key] ?? String(slot.default)}
                    onChange={(e) => handleChange(slot.key, e.target.value)}
                    type="number"
                    slotProps={{ htmlInput: { step: 0.01, style: { textAlign: "right" } } }}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button variant="contained" onClick={handleApply}>应用</Button>
      </DialogActions>
    </Dialog>
  );
}
