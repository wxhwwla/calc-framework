import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box } from "@mui/material";

interface DonationDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function DonationDialog({ open, onClose }: DonationDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>自愿捐赠</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" paragraph>
          本应用完全免费开源。如果觉得好用，可以自愿支持作者。
        </Typography>
        <Box sx={{ textAlign: "center", py: 2 }}>
          <Typography variant="body2" color="text.secondary">
            暂未配置捐赠方式
          </Typography>
        </Box>
        <Typography variant="caption" color="text.secondary">
          所有捐赠将用于服务器维护和持续开发。
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}
