import { useTranslation } from "react-i18next";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Link, Box,
} from "@mui/material";
import {
  REPO_URL,
  REPO_DISPLAY_NAME,
  LICENSE_URL,
  DATA_LICENSE_URL,
  NOTICES_URL,
  ATTRIBUTION_DOC_URL,
  COMMERCIAL_OUTLINE_URL,
  BWIKI_ENDFIELD_URL,
  BWIKI_ARKNIGHTS_URL,
  CC_BY_SA_40_URL,
  AGPL_30_URL,
  COMMERCIAL_CONTACT,
} from "../../constants/attribution";

interface DataSourceDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function DataSourceDialog({ open, onClose }: DataSourceDialogProps) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t("dataSourceDialog.title")}</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" gutterBottom>
          <strong>【{t("common.notOfficial")}】</strong>
          {" "}
          {t("dataSourceDialog.unofficialNotice")}
        </Typography>

        <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
          {t("dataSourceDialog.sourceCodeSection")}
        </Typography>
        <Typography variant="body2" gutterBottom>
          {t("dataSourceDialog.sourceCodeText")}
          {" "}
          <Link href={REPO_URL} target="_blank" rel="noopener">
            {REPO_DISPLAY_NAME}
          </Link>
          （<Link href={AGPL_30_URL} target="_blank" rel="noopener">AGPL-3.0</Link>，
          <Link href={LICENSE_URL} target="_blank" rel="noopener">LICENSE</Link>）。
          {COMMERCIAL_CONTACT}
        </Typography>

        <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
          {t("dataSourceDialog.gameDataSection")}
        </Typography>
        <Typography variant="body2" gutterBottom>
          {t("dataSourceDialog.gameDataText")}
          {" "}
          <Link href={BWIKI_ENDFIELD_URL} target="_blank" rel="noopener">BWIKI</Link>
          <br />
          <Link href={BWIKI_ARKNIGHTS_URL} target="_blank" rel="noopener">BWIKI</Link>
          {" "}
          <Link href={CC_BY_SA_40_URL} target="_blank" rel="noopener">CC BY-SA 4.0</Link>
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }} gutterBottom>
          <Link href={DATA_LICENSE_URL} target="_blank" rel="noopener">DATA_LICENSE</Link>
          ：{t("dataSourceDialog.dataLicenseNote")}
        </Typography>

        <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
          {t("dataSourceDialog.moreDocsSection")}
        </Typography>
        <Box component="ul" sx={{ m: 0, pl: 2.5, typography: "body2" }}>
          <li>
            <Link href={ATTRIBUTION_DOC_URL} target="_blank" rel="noopener">{t("dataSourceDialog.docDataSource")}</Link>
          </li>
          <li>
            <Link href={COMMERCIAL_OUTLINE_URL} target="_blank" rel="noopener">{t("dataSourceDialog.docCommercial")}</Link>
          </li>
          <li>
            <Link href={NOTICES_URL} target="_blank" rel="noopener">{t("dataSourceDialog.docNotices")}</Link>
          </li>
        </Box>

        <Typography variant="body2" sx={{ mt: 2 }} color="text.secondary">
          {t("dataSourceDialog.disclaimer")}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button component="a" href={REPO_URL} target="_blank" rel="noopener">
          {t("dataSourceDialog.openGitHub")}
        </Button>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
