import { Box, Paper, Typography, CircularProgress } from "@mui/material";
import { useTranslation } from "react-i18next";

interface SearchPreviewPanelProps {
  lines: string[] | null;
  loading?: boolean;
  error?: string | null;
}

export default function SearchPreviewPanel({ lines, loading, error }: SearchPreviewPanelProps) {
  const { t } = useTranslation();
  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        {t("searchPreview.title")}
      </Typography>
      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}
      {error && (
        <Typography variant="body2" color="error">
          {error}
        </Typography>
      )}
      {lines && !loading && (
        <Box
          component="pre"
          sx={{
            m: 0,
            fontFamily: "inherit",
            fontSize: "0.82rem",
            whiteSpace: "pre-wrap",
            lineHeight: 1.5,
          }}
        >
          {lines.join("\n")}
        </Box>
      )}
    </Paper>
  );
}
