import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  List, ListItemButton, ListItemText, Box, Typography, Divider,
} from "@mui/material";

interface HelpSection {
  id: typeof SECTION_IDS[number];
  titleKey: string;
  contentKey: string;
}

const SECTION_IDS = ["overview", "calc-page", "advanced-page", "search", "faq"] as const;

interface HelpDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function HelpDialog({ open, onClose }: HelpDialogProps) {
  const { t } = useTranslation();
  const [activeId, setActiveId] = useState<typeof SECTION_IDS[number]>(SECTION_IDS[0]);

  const sections: HelpSection[] = [
    { id: "overview", titleKey: "helpDialog.sections.overview", contentKey: "overview" },
    { id: "calc-page", titleKey: "helpDialog.sections.calcPage", contentKey: "calc-page" },
    { id: "advanced-page", titleKey: "helpDialog.sections.advancedPage", contentKey: "advanced-page" },
    { id: "search", titleKey: "helpDialog.sections.search", contentKey: "search" },
    { id: "faq", titleKey: "helpDialog.sections.faq", contentKey: "faq" },
  ];

  const activeSection = sections.find((s) => s.id === activeId) ?? sections[0];

  const content = useMemo(() => {
    switch (activeSection.contentKey) {
      case "overview":
        return (
          <Box>
            <Typography variant="body2" paragraph>
              {t("helpDialog.overviewContent.intro")}
            </Typography>
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.overviewContent.flowTitle")}</strong>
              <ol>
                <li>{t("helpDialog.overviewContent.flow1")}</li>
                <li>{t("helpDialog.overviewContent.flow2")}</li>
                <li>{t("helpDialog.overviewContent.flow3")}</li>
                <li>{t("helpDialog.overviewContent.flow4")}</li>
                <li>{t("helpDialog.overviewContent.flow5")}</li>
              </ol>
            </Typography>
          </Box>
        );
      case "calc-page":
        return (
          <Box>
            <Typography variant="body2" paragraph>
              {t("helpDialog.calcPageContent.intro")}
            </Typography>
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.calcPageContent.leftTitle")}</strong>
              <ul>
                <li>{t("helpDialog.calcPageContent.left1")}</li>
                <li>{t("helpDialog.calcPageContent.left2")}</li>
                <li>{t("helpDialog.calcPageContent.left3")}</li>
                <li>{t("helpDialog.calcPageContent.left4")}</li>
                <li>{t("helpDialog.calcPageContent.left5")}</li>
                <li>{t("helpDialog.calcPageContent.left6")}</li>
                <li>{t("helpDialog.calcPageContent.left7")}</li>
                <li>{t("helpDialog.calcPageContent.left8")}</li>
              </ul>
              <strong>{t("helpDialog.calcPageContent.rightTitle")}</strong>
              <ul>
                <li>{t("helpDialog.calcPageContent.right1")}</li>
                <li>{t("helpDialog.calcPageContent.right2")}</li>
                <li>{t("helpDialog.calcPageContent.right3")}</li>
              </ul>
            </Typography>
          </Box>
        );
      case "advanced-page":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.advancedPageContent.leftTitle")}</strong>
              <ul>
                {t("helpDialog.advancedPageContent.leftItems").split(" / ").map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
              <strong>{t("helpDialog.advancedPageContent.rightTitle")}</strong>
              <Box component="ul" sx={{ m: 0, pl: 2.5, typography: "body2" }}>
                {t("helpDialog.advancedPageContent.rightItems").split(" / ").map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </Box>
            </Typography>
          </Box>
        );
      case "search":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.searchContent.modesTitle")}</strong>
              <ul>
                <li>{t("helpDialog.searchContent.mode1")}</li>
                <li>{t("helpDialog.searchContent.mode2")}</li>
                <li>{t("helpDialog.searchContent.mode3")}</li>
              </ul>
              <strong>{t("helpDialog.searchContent.paramsTitle")}</strong>
              <ul>
                <li>{t("helpDialog.searchContent.param1")}</li>
                <li>{t("helpDialog.searchContent.param2")}</li>
                <li>{t("helpDialog.searchContent.param3")}</li>
              </ul>
              <strong>{t("helpDialog.searchContent.tipsTitle")}</strong>
              <ul>
                <li>{t("helpDialog.searchContent.tip1")}</li>
                <li>{t("helpDialog.searchContent.tip2")}</li>
              </ul>
            </Typography>
          </Box>
        );
      case "faq":
        return (
          <Box>
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.faqContent.q1")}</strong>
              <br />
              {t("helpDialog.faqContent.a1")}
            </Typography>
            <Divider sx={{ my: 1 }} />
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.faqContent.q2")}</strong>
              <br />
              {t("helpDialog.faqContent.a2")}
            </Typography>
            <Divider sx={{ my: 1 }} />
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.faqContent.q3")}</strong>
              <br />
              {t("helpDialog.faqContent.a3")}
            </Typography>
            <Divider sx={{ my: 1 }} />
            <Typography variant="body2" component="div">
              <strong>{t("helpDialog.faqContent.q4")}</strong>
              <br />
              {t("helpDialog.faqContent.a4")}
            </Typography>
          </Box>
        );
      default:
        return null;
    }
  }, [activeSection.contentKey, t]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t("helpDialog.title")}</DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: "flex", gap: 2, minHeight: 360, flexDirection: { xs: "column", sm: "row" } }}>
          <List dense sx={{ width: { xs: "100%", sm: 180 }, flexShrink: 0, borderRight: { xs: 0, sm: 1 }, borderColor: "divider", pt: 0 }}>
            {sections.map((section) => (
              <ListItemButton
                key={section.id}
                selected={activeId === section.id}
                onClick={() => setActiveId(section.id)}
                sx={{ borderRadius: 1, mb: 0.5 }}
              >
                <ListItemText
                  primary={t(section.titleKey)}
                  primaryTypographyProps={{ variant: "body2" }}
                />
              </ListItemButton>
            ))}
          </List>
          <Box sx={{ flex: 1, overflow: "auto", maxHeight: 400 }}>
            {content}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
