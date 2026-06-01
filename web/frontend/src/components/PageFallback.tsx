import { Box, CircularProgress, Typography } from "@mui/material";

/** 路由/懒加载组件占位 */
export default function PageFallback({ label = "加载中…" }: { label?: string }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", py: 8, gap: 2 }}>
      <CircularProgress size={32} />
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
}
