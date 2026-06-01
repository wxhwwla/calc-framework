import { useState } from "react";
import { Box, Paper, Tabs, Tab, Typography } from "@mui/material";
import BuildIcon from "@mui/icons-material/Build";
import EditIcon from "@mui/icons-material/Edit";
import VisibilityIcon from "@mui/icons-material/Visibility";
import InverseTab from "../components/designer/InverseTab";
import DataEditorTab from "../components/designer/DataEditorTab";
import DataBrowserTab from "../components/designer/DataBrowserTab";

export default function DesignerPage() {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        数据设计器
      </Typography>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)} variant="fullWidth">
          <Tab icon={<BuildIcon />} label="公式反推" />
          <Tab icon={<EditIcon />} label="数据编辑" />
          <Tab icon={<VisibilityIcon />} label="数据浏览" />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        {tab === 0 && <InverseTab />}
        {tab === 1 && <DataEditorTab />}
        {tab === 2 && <DataBrowserTab />}
      </Paper>
    </Box>
  );
}
