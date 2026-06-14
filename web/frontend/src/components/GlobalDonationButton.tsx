import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, IconButton, useMediaQuery, useTheme } from "@mui/material";
import VolunteerActivismIcon from "@mui/icons-material/VolunteerActivism";
import DonationDialog from "./calculator/DonationDialog";

export default function GlobalDonationButton() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <>
      {isMobile ? (
        <IconButton
          color="inherit"
          onClick={() => setOpen(true)}
          title={t("donation.dialogTitle")}
        >
          <VolunteerActivismIcon />
        </IconButton>
      ) : (
        <Button
          color="inherit"
          startIcon={<VolunteerActivismIcon />}
          onClick={() => setOpen(true)}
          sx={{ ml: 0.5, textTransform: "none" }}
          title={t("donation.dialogTitle")}
        >
          {t("common.donate")}
        </Button>
      )}
      <DonationDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}
