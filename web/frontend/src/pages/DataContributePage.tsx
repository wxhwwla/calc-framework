import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { useTranslation } from "react-i18next";
import EditNoteIcon from "@mui/icons-material/EditNote";
import DeveloperModeIcon from "@mui/icons-material/DeveloperMode";
import ProfileDataEditor from "../components/designer/ProfileDataEditor";
import SimpleDataForm from "../components/contribute/SimpleDataForm";
import { DATA_PROFILES } from "../constants/dataProfileConfig";

const DEFAULT_PROFILE = "endfield";

export default function DataContributePage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  const [profileId, setProfileId] = useState(DEFAULT_PROFILE);
  const profile = DATA_PROFILES.find((p) => p.id === profileId);

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {t("contribute.title")}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          {t("contribute.description")}
        </Typography>

        <Box sx={{ display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>{t("contribute.game")}</InputLabel>
            <Select
              value={profileId}
              label={t("contribute.game")}
              onChange={(e: SelectChangeEvent) => setProfileId(e.target.value)}
            >
              {DATA_PROFILES.map((p) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button variant="outlined" size="small" href="/designer">
            {t("contribute.goFullDesigner")}
          </Button>
        </Box>
      </Paper>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)} variant="fullWidth">
          <Tab icon={<EditNoteIcon />} label={t("contribute.simpleEntry")} />
          <Tab icon={<DeveloperModeIcon />} label={t("contribute.proEditor")} />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        {tab === 0 && <SimpleDataForm />}
        {tab === 1 && (
          profile ? (
            <ProfileDataEditor profileId={profileId} compact />
          ) : (
            <Alert severity="warning">{t("contribute.profileNotFound")}</Alert>
          )
        )}
      </Paper>
    </Box>
  );
}
