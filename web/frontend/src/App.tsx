import { Routes, Route, Navigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";
import CalculateIcon from "@mui/icons-material/Calculate";
import ExtensionIcon from "@mui/icons-material/Extension";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import BuildIcon from "@mui/icons-material/Build";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import { useNavigate, useLocation } from "react-router-dom";
import StorefrontIcon from "@mui/icons-material/Storefront";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ComputePage from "./pages/ComputePage";
import AdaptersPage from "./pages/AdaptersPage";
import EditorPage from "./pages/EditorPage";
import DesignerPage from "./pages/DesignerPage";
import PackDesignerPage from "./pages/PackDesignerPage";
import MarketplacePage from "./pages/MarketplacePage";
import ArknightsComputePage from "./pages/ArknightsComputePage";
import GlobalHelpDialog from "./components/GlobalHelpDialog";
import GlobalDonationButton from "./components/GlobalDonationButton";

const drawerWidth = 240;

const navItems = [
  { label: "计算 (Compute)", path: "/compute", icon: <CalculateIcon /> },
  { label: "明日方舟", path: "/arknights", icon: <AutoAwesomeIcon /> },
  { label: "适配器 (Adapters)", path: "/adapters", icon: <ExtensionIcon /> },
  { label: "DAG 编辑器 (Editor)", path: "/editor", icon: <AccountTreeIcon /> },
  { label: "数据设计器 (Designer)", path: "/designer", icon: <BuildIcon /> },
  { label: "配置包设计器 (Pack)", path: "/pack-designer", icon: <Inventory2Icon /> },
  { label: "Calc Hub 市场", path: "/hub", icon: <StorefrontIcon /> },
];

function Shell() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            Calc Framework Web
          </Typography>
          <GlobalDonationButton />
          <GlobalHelpDialog />
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <List>
          {navItems.map((item) => (
            <ListItemButton
              key={item.path}
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Routes>
          <Route path="/compute" element={<ComputePage />} />
          <Route path="/arknights" element={<ArknightsComputePage />} />
          <Route path="/adapters" element={<AdaptersPage />} />
          <Route path="/editor" element={<EditorPage />} />
          <Route path="/designer" element={<DesignerPage />} />
          <Route path="/pack-designer" element={<PackDesignerPage />} />
          <Route path="/hub" element={<MarketplacePage />} />
          <Route path="*" element={<Navigate to="/compute" replace />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default function App() {
  return <Shell />;
}
