import { useState } from "react";
import { Button } from "@mui/material";
import VolunteerActivismIcon from "@mui/icons-material/VolunteerActivism";
import DonationDialog from "./calculator/DonationDialog";

/** Web 全局捐赠入口（各页面 AppBar 共用，微信 + 爱发电同一弹窗） */
export default function GlobalDonationButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        color="inherit"
        onClick={() => setOpen(true)}
        sx={{ minWidth: 40, ml: 0.5 }}
        title="自愿捐赠"
      >
        <VolunteerActivismIcon />
      </Button>
      <DonationDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}
