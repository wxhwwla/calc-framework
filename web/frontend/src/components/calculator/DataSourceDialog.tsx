import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Link } from "@mui/material";

interface DataSourceDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function DataSourceDialog({ open, onClose }: DataSourceDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>数据来源与许可</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" gutterBottom>
          本应用使用的游戏数据来源于 <Link href="https://wiki.biligame.com/endfield/" target="_blank" rel="noopener">BWIKI 社区</Link>，
          感谢社区贡献者的辛勤整理。
        </Typography>
        <Typography variant="body2" sx={{ mt: 2 }} gutterBottom>
          项目使用 GPLv3 开源许可证发布。
        </Typography>
        <Typography variant="body2" sx={{ mt: 2 }} gutterBottom>
          计算结果仅供参考，可能与游戏实际数值存在微小差异。
        </Typography>
        <Typography variant="body2" sx={{ mt: 2 }} color="text.secondary">
          源代码: <Link href="https://github.com/" target="_blank" rel="noopener">GitHub</Link>
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}
