import { useState } from "react";
import { Box, FormControl, InputLabel, MenuItem, Paper, Select, Tab, Tabs, Typography } from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { useTranslation } from "react-i18next";
import BuildIcon from "@mui/icons-material/Build";
import EditIcon from "@mui/icons-material/Edit";
import VisibilityIcon from "@mui/icons-material/Visibility";
import InverseTab from "../components/designer/InverseTab";
import ProfileDataEditor from "../components/designer/ProfileDataEditor";
import ProfileDataBrowser from "../components/designer/ProfileDataBrowser";
import { DATA_PROFILES } from "../constants/dataProfileConfig";

export default function DesignerPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  const [profileId, setProfileId] = useState(DATA_PROFILES[0]?.id ?? "endfield");

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2, flexWrap: "wrap" }}>
        <Typography variant="h5">{t("designer.title")}</Typography>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>{t("designer.dataProfile")}</InputLabel>
          <Select
            value={profileId}
            label={t("designer.dataProfile")}
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
          <Tab icon={<BuildIcon />} label={t("designer.inverse")} />
          <Tab icon={<EditIcon />} label={t("designer.dataEdit")} />
          <Tab icon={<VisibilityIcon />} label={t("designer.dataBrowse")} />
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
