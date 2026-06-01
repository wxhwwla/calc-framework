import { Box, Link, Typography } from "@mui/material";
import {
  REPO_URL,
  REPO_DISPLAY_NAME,
  LICENSE_URL,
  DATA_LICENSE_URL,
  ATTRIBUTION_DOC_URL,
} from "../constants/attribution";

/** 页脚署名 — 各路由主内容区底部展示 */
export default function SiteFooter() {
  return (
    <Box
      component="footer"
      sx={{
        mt: 4,
        pt: 2,
        borderTop: 1,
        borderColor: "divider",
        textAlign: "center",
      }}
    >
      <Typography variant="caption" color="text.secondary" component="div">
        非官方爱好者项目 · 计算结果仅供参考
      </Typography>
      <Typography variant="caption" color="text.secondary" component="div" sx={{ mt: 0.5 }}>
        源代码{" "}
        <Link href={REPO_URL} target="_blank" rel="noopener" underline="hover">
          {REPO_DISPLAY_NAME}
        </Link>
        {" · "}
        <Link href={LICENSE_URL} target="_blank" rel="noopener" underline="hover">
          AGPL-3.0
        </Link>
        {" · "}
        <Link href={DATA_LICENSE_URL} target="_blank" rel="noopener" underline="hover">
          DATA_LICENSE
        </Link>
        {" · "}
        <Link href={ATTRIBUTION_DOC_URL} target="_blank" rel="noopener" underline="hover">
          完整说明
        </Link>
      </Typography>
    </Box>
  );
}
