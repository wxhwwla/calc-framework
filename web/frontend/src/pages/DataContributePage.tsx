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
import EditNoteIcon from "@mui/icons-material/EditNote";
import DeveloperModeIcon from "@mui/icons-material/DeveloperMode";
import ProfileDataEditor from "../components/designer/ProfileDataEditor";
import SimpleDataForm from "../components/contribute/SimpleDataForm";
import { DATA_PROFILES } from "../constants/dataProfileConfig";

const DEFAULT_PROFILE = "endfield";

export default function DataContributePage() {
  const [tab, setTab] = useState(0);
  const [profileId, setProfileId] = useState(DEFAULT_PROFILE);
  const profile = DATA_PROFILES.find((p) => p.id === profileId);

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          数据贡献
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          欢迎贡献游戏数据！在这里可以新增角色、武器或装备信息。
          选择游戏和数据类型后，填写表单即可添加新数据。
          提交的数据会直接保存到服务器，帮助完善计算器的数据覆盖。
        </Typography>

        <Box sx={{ display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>游戏</InputLabel>
            <Select
              value={profileId}
              label="游戏"
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
            前往完整数据设计器
          </Button>
        </Box>
      </Paper>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)} variant="fullWidth">
          <Tab icon={<EditNoteIcon />} label="简易录入" />
          <Tab icon={<DeveloperModeIcon />} label="专业编辑" />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        {tab === 0 && <SimpleDataForm />}
        {tab === 1 && (
          profile ? (
            <ProfileDataEditor profileId={profileId} compact />
          ) : (
            <Alert severity="warning">未找到该游戏的数据配置</Alert>
          )
        )}
      </Paper>
    </Box>
  );
}
