import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  Container,
  Grid2 as Grid,
  Typography,
  Chip,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import CalculateIcon from "@mui/icons-material/Calculate";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import BuildIcon from "@mui/icons-material/Build";
import ExtensionIcon from "@mui/icons-material/Extension";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import Inventory2Icon from "@mui/icons-material/Inventory2";

export default function LandingPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const features = [
    {
      icon: <CalculateIcon fontSize="large" color="primary" />,
      title: t("landing.featureCalc", "精准伤害计算"),
      desc: t("landing.featureCalcDesc", "基于 DAG 引擎的 15 乘区完整公式，支持终末地、明日方舟等热门游戏"),
      path: "/compute",
    },
    {
      icon: <AccountTreeIcon fontSize="large" color="primary" />,
      title: t("landing.featureDag", "可视化 DAG 编辑器"),
      desc: t("landing.featureDagDesc", "拖拽式公式编辑器，无需写代码即可构建任意游戏的伤害公式"),
      path: "/editor",
    },
    {
      icon: <SmartToyIcon fontSize="large" color="primary" />,
      title: t("landing.featureAi", "AI 智能配装"),
      desc: t("landing.featureAiDesc", "自然语言描述需求，AI 理解意图并推荐最优配装方案"),
      path: "/compute",
    },
    {
      icon: <BuildIcon fontSize="large" color="primary" />,
      title: t("landing.featureDesigner", "数据设计器"),
      desc: t("landing.featureDesignerDesc", "角色/武器/装备数据的浏览、编辑、验证，支持公式反推"),
      path: "/designer",
    },
    {
      icon: <Inventory2Icon fontSize="large" color="primary" />,
      title: t("landing.featureMarket", "配置包市场"),
      desc: t("landing.featureMarketDesc", "社区共享 .calcpack 计算器包，一键下载使用"),
      path: "/hub",
    },
    {
      icon: <ExtensionIcon fontSize="large" color="primary" />,
      title: t("landing.featurePlugin", "插件系统"),
      desc: t("landing.featurePluginDesc", "暴击、闪避、距离衰减等可扩展插件，提升 DAG 计算能力"),
      path: "/adapters",
    },
  ];

  return (
    <Box>
      <Box
        sx={{
          textAlign: "center",
          py: isMobile ? 6 : 10,
          px: 2,
          background: "linear-gradient(135deg, #1976d2 0%, #9c27b0 100%)",
          color: "#fff",
        }}
      >
        <Typography variant={isMobile ? "h4" : "h2"} fontWeight={700} gutterBottom>
          Calc Framework
        </Typography>
        <Typography variant={isMobile ? "h6" : "h5"} sx={{ opacity: 0.9, mb: 3, maxWidth: 600, mx: "auto" }}>
          {t("landing.heroSubtitle", "通用游戏伤害计算引擎 — 一套框架，万物可算")}
        </Typography>

        <Box sx={{ display: "flex", gap: 2, justifyContent: "center", flexWrap: "wrap" }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate("/compute")}
            sx={{ bgcolor: "#fff", color: "#1976d2", "&:hover": { bgcolor: "#e3f2fd" } }}
          >
            {t("landing.startCalc", "🎮 开始计算")}
          </Button>
          <Button
            variant="outlined"
            size="large"
            onClick={() => navigate("/editor")}
            sx={{ color: "#fff", borderColor: "#fff", "&:hover": { borderColor: "#fff", bgcolor: "rgba(255,255,255,0.1)" } }}
          >
            {t("landing.createCalc", "🔧 创建计算器")}
          </Button>
        </Box>
      </Box>

      <Container maxWidth="lg" sx={{ py: isMobile ? 4 : 8 }}>
        <Typography variant={isMobile ? "h5" : "h4"} align="center" gutterBottom fontWeight={600}>
          {t("landing.featuresTitle", "核心能力")}
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: "auto" }}>
          {t("landing.featuresSubtitle", "从数据采集到公式验证，从可视化编辑到一键发布——全链路覆盖")}
        </Typography>

        <Grid container spacing={3}>
          {features.map((f) => (
            <Grid key={f.title} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card
                sx={{
                  height: "100%",
                  transition: "transform 0.2s, box-shadow 0.2s",
                  "&:hover": { transform: "translateY(-4px)", boxShadow: 4 },
                }}
              >
                <CardActionArea
                  onClick={() => navigate(f.path)}
                  aria-label={f.title}
                >
                  <Box sx={{ textAlign: "center", py: 3, px: 2 }}>
                    <Box sx={{ mb: 1 }}>{f.icon}</Box>
                    <Typography variant="h6" gutterBottom>{f.title}</Typography>
                    <Typography variant="body2" color="text.secondary">{f.desc}</Typography>
                  </Box>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      <Box sx={{ textAlign: "center", py: 4, bgcolor: "action.hover" }}>
        <Typography variant="h6" gutterBottom>{t("landing.ossTitle", "开源 & 免费")}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t("landing.ossLicense", "AGPL-3.0 开源许可 · 商业授权可选")}
        </Typography>
        <Box sx={{ display: "flex", gap: 1, justifyContent: "center" }}>
          <Chip label="Python 3.12+" size="small" variant="outlined" />
          <Chip label="React + TypeScript" size="small" variant="outlined" />
          <Chip label="FastAPI" size="small" variant="outlined" />
          <Chip label="PySide6" size="small" variant="outlined" />
        </Box>
      </Box>
    </Box>
  );
}
