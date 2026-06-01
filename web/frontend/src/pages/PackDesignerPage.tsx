import { useState, lazy, Suspense } from "react";
import { Box, Paper, Tabs, Tab, Typography } from "@mui/material";
import EditNoteIcon from "@mui/icons-material/EditNote";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import PaletteIcon from "@mui/icons-material/Palette";
import DataEditorTab from "../components/designer/DataEditorTab";
import ThemeExportTab from "../components/pack_designer/ThemeExportTab";
import PageFallback from "../components/PageFallback";

const EditorPage = lazy(() => import("./EditorPage"));

export default function PackDesignerPage() {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        配置包设计器
      </Typography>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)} variant="fullWidth">
          <Tab icon={<EditNoteIcon />} label="数据录入" />
          <Tab icon={<AccountTreeIcon />} label="布局编辑" />
          <Tab icon={<PaletteIcon />} label="主题与导出" />
        </Tabs>
      </Paper>

      {tab === 0 && (
        <Paper sx={{ p: 3 }}>
          <DataEditorTab />
        </Paper>
      )}
      {tab === 1 && (
        <Suspense fallback={<PageFallback label="加载布局编辑器…" />}>
          <Box>
            <EditorPage />
          </Box>
        </Suspense>
      )}
      {tab === 2 && (
        <Paper sx={{ p: 3 }}>
          <ThemeExportTab />
        </Paper>
      )}
    </Box>
  );
}
