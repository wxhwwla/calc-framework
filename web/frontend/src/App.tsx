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
import { useNavigate, useLocation } from "react-router-dom";
import ComputePage from "./pages/ComputePage";
import AdaptersPage from "./pages/AdaptersPage";
import EditorPage from "./pages/EditorPage";
import DesignerPage from "./pages/DesignerPage";

const drawerWidth = 240;

const navItems = [
  { label: "计算 (Compute)", path: "/compute", icon: <CalculateIcon /> },
  { label: "适配器 (Adapters)", path: "/adapters", icon: <ExtensionIcon /> },
  { label: "DAG 编辑器 (Editor)", path: "/editor", icon: <AccountTreeIcon /> },
  { label: "数据设计器 (Designer)", path: "/designer", icon: <BuildIcon /> },
];

function Shell() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap>
            Calc Framework Web
          </Typography>
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
          <Route path="/adapters" element={<AdaptersPage />} />
          <Route path="/editor" element={<EditorPage />} />
          <Route path="/designer" element={<DesignerPage />} />
          <Route path="*" element={<Navigate to="/compute" replace />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default function App() {
  return <Shell />;
}
