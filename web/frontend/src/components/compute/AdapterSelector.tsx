import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { useComputeStore } from "../../store/computeStore";

export default function AdapterSelector() {
  const { t } = useTranslation();
  const adapters = useComputeStore((s) => s.adapters);
  const selectedAdapter = useComputeStore((s) => s.selectedAdapter);
  const loadAdapters = useComputeStore((s) => s.loadAdapters);
  const selectAdapter = useComputeStore((s) => s.selectAdapter);

  useEffect(() => {
    if (adapters.length === 0) {
      loadAdapters();
    }
  }, []);

  return (
    <Box sx={{ mb: 3 }}>
      <FormControl fullWidth>
        <InputLabel>{t('packDesigner.adapter', '游戏品类 / 适配器')}</InputLabel>
        <Select
          value={selectedAdapter ?? ""}
          label={t('packDesigner.adapter', '游戏品类 / 适配器')}
          onChange={(e: SelectChangeEvent) => selectAdapter(e.target.value)}
        >
          {adapters.map((a) => (
            <MenuItem key={a.name} value={a.name}>
              {a.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      {selectedAdapter && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {adapters.find((a) => a.name === selectedAdapter)?.game}
        </Typography>
      )}
    </Box>
  );
}
