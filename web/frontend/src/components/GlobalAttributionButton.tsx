import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, IconButton, useMediaQuery, useTheme } from "@mui/material";
import SourceIcon from "@mui/icons-material/Source";
import DataSourceDialog from "./calculator/DataSourceDialog";

export default function GlobalAttributionButton() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <>
      {isMobile ? (
        <IconButton
          color="inherit"
          size="small"
          onClick={() => setOpen(true)}
          title={t("common.sourceCode")}
        >
          <SourceIcon />
        </IconButton>
      ) : (
        <Button
          color="inherit"
          size="small"
          startIcon={<SourceIcon />}
          onClick={() => setOpen(true)}
          sx={{ ml: 0.5, textTransform: "none" }}
          title={t("common.sourceCode")}
        >
          {t("common.openSource")}
        </Button>
      )}
      <DataSourceDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}
