import { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { useTranslation } from "react-i18next";
import EditNoteIcon from "@mui/icons-material/EditNote";
import ViewQuiltIcon from "@mui/icons-material/ViewQuilt";
import PaletteIcon from "@mui/icons-material/Palette";
import PackDataTab from "../components/pack_designer/PackDataTab";
import PackLayoutTab from "../components/pack_designer/PackLayoutTab";
import ThemeExportTab from "../components/pack_designer/ThemeExportTab";
import { usePackDesignerStore } from "../store/packDesignerStore";

export default function PackDesignerPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  const adapters = usePackDesignerStore((s) => s.adapters);
  const adapterId = usePackDesignerStore((s) => s.adapterId);
  const loadAdapters = usePackDesignerStore((s) => s.loadAdapters);
  const setAdapterId = usePackDesignerStore((s) => s.setAdapterId);

  useEffect(() => {
    loadAdapters();
  }, [loadAdapters]);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2, flexWrap: "wrap", gap: 2 }}>
        <Typography variant="h5">{t("packDesigner.title")}</Typography>
        <FormControl size="small" sx={{ minWidth: { xs: 160, sm: 260 } }}>
          <InputLabel>{t("packDesigner.adapter")}</InputLabel>
          <Select
            value={adapterId}
            label={t("packDesigner.adapter")}
            onChange={(e: SelectChangeEvent) => setAdapterId(e.target.value)}
          >
            {adapters.map((a) => (
              <MenuItem key={a.id} value={a.id}>
                {a.name} ({a.game || a.id})
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)} variant="fullWidth">
          <Tab icon={<EditNoteIcon />} label={t("packDesigner.dataEntry")} />
          <Tab icon={<ViewQuiltIcon />} label={t("packDesigner.layoutEdit")} />
          <Tab icon={<PaletteIcon />} label={t("packDesigner.themeExport")} />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        {tab === 0 && <PackDataTab />}
        {tab === 1 && <PackLayoutTab />}
        {tab === 2 && <ThemeExportTab />}
      </Paper>
    </Box>
  );
}
