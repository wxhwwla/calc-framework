import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography,
} from "@mui/material";
import { DONATION_TEXT } from "../../constants/donation";
import DonationImages from "./DonationImages";

interface DonationDialogProps {
  open: boolean;
  onClose: () => void;
}

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
