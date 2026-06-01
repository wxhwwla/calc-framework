import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography,
} from "@mui/material";
import DonationImages from "./DonationImages";

interface DonationDialogProps {
  open: boolean;
  onClose: () => void;
}

const DONATION_TEXT =
  "感谢使用！如果觉得有用，欢迎通过微信赞赏或爱发电支持开发者。\n\n" +
  "捐赠纯属自愿，不构成购买软件的对价，不授予商业使用授权。";

export default function DonationDialog({ open, onClose }: DonationDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>自愿捐赠</DialogTitle>
      <DialogContent dividers>
        <DonationImages />
        <Typography variant="body2" sx={{ whiteSpace: "pre-line", mt: 1 }}>
          {DONATION_TEXT}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}
