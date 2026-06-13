import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, IconButton,
  List, ListItemButton, ListItemText, Box, Typography, useMediaQuery, useTheme,
} from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";

interface HelpEntry {
  id: string;
  titleKey: string;
}

const ENTRIES: HelpEntry[] = [
  { id: "process", titleKey: "globalHelp.sections.process" },
  { id: "endfield", titleKey: "globalHelp.sections.endfield" },
  { id: "arknights", titleKey: "globalHelp.sections.arknights" },
  { id: "dag-editor", titleKey: "globalHelp.sections.dagEditor" },
  { id: "designer", titleKey: "globalHelp.sections.designer" },
  { id: "pack-designer", titleKey: "globalHelp.sections.packDesigner" },
  { id: "hub", titleKey: "globalHelp.sections.hub" },
  { id: "license", titleKey: "globalHelp.sections.license" },
];

export default function GlobalHelpDialog() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [activeId, setActiveId] = useState(ENTRIES[0].id);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const content = useMemo(() => {
    switch (activeId) {
      case "process":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <p><b>{t("globalHelp.processContent.title")}</b></p>
              <ol>
                <li><b>{t("globalHelp.processContent.step1")}</b></li>
                <li><b>{t("globalHelp.processContent.step2")}</b></li>
                <li><b>{t("globalHelp.processContent.step3")}</b></li>
                <li><b>{t("globalHelp.processContent.step4")}</b></li>
                <li><b>{t("globalHelp.processContent.step5")}</b></li>
                <li><b>{t("globalHelp.processContent.step6")}</b></li>
                <li><b>{t("globalHelp.processContent.step7")}</b></li>
              </ol>
              <p>{t("globalHelp.dialogSubtitle")}</p>
            </Typography>
          </Box>
        );
      case "endfield":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <p><b>{t("globalHelp.endfieldContent.calcTitle")}</b></p>
              <Box component="ul" sx={{ m: 0, pl: 2.5, typography: "body2" }}>
                {t("globalHelp.endfieldContent.calcItems").split(" / ").map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </Box>
              <p><b>{t("globalHelp.endfieldContent.advancedTitle")}</b></p>
              <Box component="ul" sx={{ m: 0, pl: 2.5, typography: "body2" }}>
                {t("globalHelp.endfieldContent.advancedItems").split(" / ").map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </Box>
            </Typography>
          </Box>
        );
      case "arknights":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <Box component="ul" sx={{ m: 0, pl: 2.5, typography: "body2" }}>
                {t("globalHelp.arknightsContent.items").split(" / ").map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </Box>
            </Typography>
          </Box>
        );
      case "dag-editor":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <p><b>{t("globalHelp.dagEditorContent.layout")}</b></p>
              <p><b>{t("globalHelp.dagEditorContent.nodeTypesTitle")}</b></p>
              <ul>
                <li><b>{t("globalHelp.dagEditorContent.constNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.varNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.userInputNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.unaryNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.binaryNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.conditionNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.callNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.outputNode")}</b></li>
                <li><b>{t("globalHelp.dagEditorContent.exprNode")}</b></li>
              </ul>
              <p><b>{t("globalHelp.dagEditorContent.toolbar")}</b></p>
              <p><b>{t("globalHelp.dagEditorContent.canvasOps")}</b></p>
            </Typography>
          </Box>
        );
      case "designer":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <p><b>{t("globalHelp.designerContent.inverseTab")}</b></p>
              <p><b>{t("globalHelp.designerContent.dataTab")}</b></p>
            </Typography>
          </Box>
        );
      case "pack-designer":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <p>{t("globalHelp.packDesignerContent.dataTab")}</p>
              <p>{t("globalHelp.packDesignerContent.layoutTab")}</p>
              <p>{t("globalHelp.packDesignerContent.themeTab")}</p>
            </Typography>
          </Box>
        );
      case "hub":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <Box component="ul" sx={{ m: 0, pl: 2.5, typography: "body2" }}>
                {t("globalHelp.hubContent.items").split(" / ").map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </Box>
            </Typography>
          </Box>
        );
      case "license":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <p>{t("globalHelp.licenseContent.source")}</p>
              <p>{t("globalHelp.licenseContent.commercial")}</p>
            </Typography>
          </Box>
        );
      default:
        return null;
    }
  }, [activeId, t]);

  return (
    <>
      {isMobile ? (
        <IconButton
          color="inherit"
          onClick={() => setOpen(true)}
          title={t("globalHelp.buttonTitle")}
        >
          <HelpOutlineIcon />
        </IconButton>
      ) : (
        <Button
          color="inherit"
          startIcon={<HelpOutlineIcon />}
          onClick={() => setOpen(true)}
          sx={{ ml: 0.5, textTransform: "none" }}
          title={t("globalHelp.buttonTitle")}
        >
          {t("globalHelp.buttonLabel")}
        </Button>
      )}
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {t("globalHelp.dialogTitle")}
          <Typography variant="caption" sx={{ ml: 2, color: "text.secondary" }}>
            {t("globalHelp.dialogSubtitle")}
          </Typography>
        </DialogTitle>
        <DialogContent dividers sx={{ display: "flex", gap: 2, minHeight: 400, flexDirection: { xs: "column", sm: "row" } }}>
          <List sx={{ width: { xs: "100%", sm: 220 }, flexShrink: 0 }}>
            {ENTRIES.map((entry) => (
              <ListItemButton
                key={entry.id}
                selected={activeId === entry.id}
                onClick={() => setActiveId(entry.id)}
              >
                <ListItemText
                  primary={t(entry.titleKey)}
                  primaryTypographyProps={{ variant: "body2" }}
                />
              </ListItemButton>
            ))}
          </List>
          <Box sx={{ flex: 1, overflow: "auto" }}>
            {content}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>{t("common.close")}</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
