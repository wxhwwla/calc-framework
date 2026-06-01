import { useState } from "react";
import { Box, FormControl, InputLabel, MenuItem, Paper, Select, Tab, Tabs, Typography } from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import BuildIcon from "@mui/icons-material/Build";
import EditIcon from "@mui/icons-material/Edit";
import VisibilityIcon from "@mui/icons-material/Visibility";
import InverseTab from "../components/designer/InverseTab";
import ProfileDataEditor from "../components/designer/ProfileDataEditor";
import ProfileDataBrowser from "../components/designer/ProfileDataBrowser";
import { DATA_PROFILES } from "../constants/dataProfileConfig";

export default function DesignerPage() {
  const [tab, setTab] = useState(0);
  const [profileId, setProfileId] = useState(DATA_PROFILES[0]?.id ?? "endfield");

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <Typography variant="h5">数据设计器</Typography>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>数据模板</InputLabel>
          <Select
            value={profileId}
            label="数据模板"
            onChange={(e: SelectChangeEvent) => setProfileId(e.target.value)}
          >
            {DATA_PROFILES.map((p) => (
              <MenuItem key={p.id} value={p.id}>
                {p.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)} variant="fullWidth">
          <Tab icon={<BuildIcon />} label="公式反推" />
          <Tab icon={<EditIcon />} label="数据编辑" />
          <Tab icon={<VisibilityIcon />} label="数据浏览" />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        {tab === 0 && <InverseTab />}
        {tab === 1 && <ProfileDataEditor profileId={profileId} />}
        {tab === 2 && <ProfileDataBrowser profileId={profileId} />}
      </Paper>
    </Box>
  );
}
