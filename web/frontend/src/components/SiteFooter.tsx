import { useTranslation } from "react-i18next";
import { Box, Link, Typography } from "@mui/material";
import {
  REPO_URL,
  REPO_DISPLAY_NAME,
  LICENSE_URL,
  DATA_LICENSE_URL,
  ATTRIBUTION_DOC_URL,
} from "../constants/attribution";

export default function SiteFooter() {
  const { t } = useTranslation();

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
        {t("siteFooter.disclaimer")}
      </Typography>
      <Typography variant="caption" color="text.secondary" component="div" sx={{ mt: 0.5 }}>
        {t("siteFooter.sourceCodeLabel")}{" "}
        <Link href={REPO_URL} target="_blank" rel="noopener" underline="hover">
          {REPO_DISPLAY_NAME}
        </Link>
        {" · "}
        <Link href={LICENSE_URL} target="_blank" rel="noopener" underline="hover">
          {t("siteFooter.licenseLabel")}
        </Link>
        {" · "}
        <Link href={DATA_LICENSE_URL} target="_blank" rel="noopener" underline="hover">
          {t("siteFooter.dataLicenseLabel")}
        </Link>
        {" · "}
        <Link href={ATTRIBUTION_DOC_URL} target="_blank" rel="noopener" underline="hover">
          {t("siteFooter.fullNotice")}
        </Link>
      </Typography>
    </Box>
  );
}
