import { useState } from "react";
import { Button, IconButton, useMediaQuery, useTheme } from "@mui/material";
import VolunteerActivismIcon from "@mui/icons-material/VolunteerActivism";
import DonationDialog from "./calculator/DonationDialog";

/** Web 全局捐赠入口（各页面 AppBar 共用，微信 + 爱发电同一弹窗） */
export default function GlobalDonationButton() {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <>
      {isMobile ? (
        <IconButton
          color="inherit"
          onClick={() => setOpen(true)}
          title="自愿捐赠"
        >
          <VolunteerActivismIcon />
        </IconButton>
      ) : (
        <Button
          color="inherit"
          startIcon={<VolunteerActivismIcon />}
          onClick={() => setOpen(true)}
          sx={{ ml: 0.5, textTransform: "none" }}
          title="自愿捐赠"
        >
          捐赠
        </Button>
      )}
      <DonationDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}
