import { Box, CircularProgress, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

/** 路由/懒加载组件占位 */
export default function PageFallback({ label }: { label?: string }) {
  const { t } = useTranslation();
  const displayLabel = label ?? t("pageFallback.loading");
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", py: 8, gap: 2 }}>
      <CircularProgress size={32} />
      <Typography variant="body2" color="text.secondary">
        {displayLabel}
      </Typography>
    </Box>
  );
}
