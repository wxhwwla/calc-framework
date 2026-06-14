import { lazy, Suspense, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Collapse,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import MenuIcon from "@mui/icons-material/Menu";
import CalculateIcon from "@mui/icons-material/Calculate";
import ExtensionIcon from "@mui/icons-material/Extension";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import BuildIcon from "@mui/icons-material/Build";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import { useNavigate, useLocation } from "react-router-dom";
import StorefrontIcon from "@mui/icons-material/Storefront";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import NoteAddIcon from "@mui/icons-material/NoteAdd";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import BottomNavigation from "@mui/material/BottomNavigation";
import BottomNavigationAction from "@mui/material/BottomNavigationAction";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import Paper from "@mui/material/Paper";
import PageFallback from "./components/PageFallback";
import GlobalDonationButton from "./components/GlobalDonationButton";
import { useThemeMode } from "./main";
import GlobalHelpDialog from "./components/GlobalHelpDialog";
import PluginManagerDialog from "./components/calculator/PluginManagerDialog";
import GlobalAttributionButton from "./components/GlobalAttributionButton";
import SiteFooter from "./components/SiteFooter";

const ComputePage = lazy(() => import("./pages/ComputePage"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const ArknightsComputePage = lazy(() => import("./pages/ArknightsComputePage"));
const AdaptersPage = lazy(() => import("./pages/AdaptersPage"));
const EditorPage = lazy(() => import("./pages/EditorPage"));
const DesignerPage = lazy(() => import("./pages/DesignerPage"));
const PackDesignerPage = lazy(() => import("./pages/PackDesignerPage"));
const MarketplacePage = lazy(() => import("./pages/MarketplacePage"));
const DataContributePage = lazy(() => import("./pages/DataContributePage"));
const GeneratorPage = lazy(() => import("./pages/GeneratorPage"));

const drawerWidth = 240;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

function useNavItems(): { gameItems: NavItem[]; toolItems: NavItem[] } {
  const { t } = useTranslation();
  return {
    gameItems: [
      { label: t("nav.endfieldCalc"), path: "/compute", icon: <CalculateIcon /> },
      { label: t("nav.arknights"), path: "/arknights", icon: <AutoAwesomeIcon /> },
    ],
    toolItems: [
      { label: t("nav.adapters"), path: "/adapters", icon: <ExtensionIcon /> },
      { label: t("nav.editor"), path: "/editor", icon: <AccountTreeIcon /> },
      { label: t("nav.designer"), path: "/designer", icon: <BuildIcon /> },
      { label: t("nav.packDesigner"), path: "/pack-designer", icon: <Inventory2Icon /> },
      { label: t("nav.contribute"), path: "/contribute", icon: <NoteAddIcon /> },
      { label: t("nav.marketplace"), path: "/hub", icon: <StorefrontIcon /> },
      { label: t("nav.generator"), path: "/generator", icon: <SmartToyIcon /> },
    ],
  };
}

function NavGroup({
  title,
  icon,
  items,
  currentPath,
  onNavigate,
  defaultOpen,
}: {
  title: string;
  icon: React.ReactNode;
  items: NavItem[];
  currentPath: string;
  onNavigate: (path: string) => void;
  defaultOpen: boolean;
}) {
  const isActive = items.some((i) => i.path === currentPath);
  const [open, setOpen] = useState(defaultOpen || isActive);

  return (
    <>
      <ListSubheader
        component="div"
        sx={{ display: "flex", alignItems: "center", gap: 1, cursor: "pointer", bgcolor: "transparent" }}
        onClick={() => setOpen(!open)}
      >
        {icon}
        <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>{title}</Typography>
        {open ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
      </ListSubheader>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List disablePadding>
          {items.map((item) => (
            <ListItemButton
              key={item.path}
              selected={currentPath === item.path}
              sx={{ pl: 4 }}
              onClick={() => onNavigate(item.path)}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Collapse>
    </>
  );
}

function Shell() {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const { mode, toggle: toggleTheme } = useThemeMode();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [pluginOpen, setPluginOpen] = useState(false);
  const { t, i18n } = useTranslation();
  const { gameItems, toolItems } = useNavItems();

  const toggleLanguage = () => {
    const next = i18n.language === "zh-CN" ? "en" : "zh-CN";
    i18n.changeLanguage(next);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) setMobileOpen(false);
  };

  const drawerContent = (
    <>
      <Toolbar />
      <NavGroup
        title={t("nav.games")}
        icon={<SportsEsportsIcon fontSize="small" />}
        items={gameItems}
        currentPath={location.pathname}
        onNavigate={handleNavigate}
        defaultOpen={true}
      />
      <NavGroup
        title={t("nav.devTools")}
        icon={<BuildIcon fontSize="small" />}
        items={toolItems}
        currentPath={location.pathname}
        onNavigate={handleNavigate}
        defaultOpen={false}
      />
    </>
  );

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setMobileOpen(!mobileOpen)}
              sx={{ mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            {t("app.title")}
          </Typography>
          <IconButton color="inherit" onClick={toggleTheme} title={mode === "dark" ? t("common.lightMode", "亮色模式") : t("common.darkMode", "暗色模式")} size="small" sx={{ mr: 1 }}>
            {mode === "dark" ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}
          </IconButton>
          <IconButton color="inherit" onClick={toggleLanguage} title={t("common.language")} size="small" sx={{ mr: 1 }}>
            <Typography variant="body2">{i18n.language === "zh-CN" ? "EN" : t("common.language")}</Typography>
          </IconButton>
          <IconButton color="inherit" onClick={() => setPluginOpen(true)} title={t("plugins.title", "插件")} size="small" sx={{ mr: 1 }}>
            <ExtensionIcon fontSize="small" />
          </IconButton>
          <GlobalAttributionButton />
          <GlobalDonationButton />
          <GlobalHelpDialog />
          <PluginManagerDialog open={pluginOpen} onClose={() => setPluginOpen(false)} />
        </Toolbar>
      </AppBar>

      {isMobile ? (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" },
          }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 1.5, md: 3 },
          pb: { xs: 8, md: 3 },
          minWidth: 0,
          overflowX: "hidden",
        }}
      >
        <Toolbar />
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/compute" element={<ComputePage />} />
            <Route path="/arknights" element={<ArknightsComputePage />} />
            <Route path="/adapters" element={<AdaptersPage />} />
            <Route path="/editor" element={<EditorPage />} />
            <Route path="/designer" element={<DesignerPage />} />
            <Route path="/pack-designer" element={<PackDesignerPage />} />
            <Route path="/hub" element={<MarketplacePage />} />
            <Route path="/contribute" element={<DataContributePage />} />
            <Route path="/generator" element={<GeneratorPage />} />
            <Route path="*" element={<Navigate to="/compute" replace />} />
          </Routes>
        </Suspense>
        {isMobile && (
          <Paper sx={{ position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 1000 }} elevation={3}>
            <BottomNavigation
              value={location.pathname}
              onChange={(_, path) => navigate(path)}
              showLabels
            >
              <BottomNavigationAction label={t("nav.games")} value="/compute" icon={<CalculateIcon />} />
              <BottomNavigationAction label={t("nav.editor")} value="/editor" icon={<AccountTreeIcon />} />
              <BottomNavigationAction label={t("nav.marketplace")} value="/hub" icon={<StorefrontIcon />} />
              <BottomNavigationAction label={t("nav.designer")} value="/designer" icon={<BuildIcon />} />
            </BottomNavigation>
          </Paper>
        )}
        <SiteFooter />
      </Box>
    </Box>
  );
}

export default function App() {
  return <Shell />;
}
