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
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>数据来源与许可</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" gutterBottom>
          <strong>【非官方工具】</strong>
          本 Web 版为爱好者计算器，不代表游戏官方或 BWIKI 运营方。
        </Typography>

        <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
          源代码
        </Typography>
        <Typography variant="body2" gutterBottom>
          本项目托管于 GitHub：
          {" "}
          <Link href={REPO_URL} target="_blank" rel="noopener">
            {REPO_DISPLAY_NAME}
          </Link>
          （默认 <Link href={AGPL_30_URL} target="_blank" rel="noopener">AGPL-3.0</Link>，
          详见 <Link href={LICENSE_URL} target="_blank" rel="noopener">LICENSE</Link>）。
          闭源商用须书面商业许可（{COMMERCIAL_CONTACT}）。
        </Typography>

        <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
          游戏数据
        </Typography>
        <Typography variant="body2" gutterBottom>
          · 终末地 JSON：仓库维护，参考{" "}
          <Link href={BWIKI_ENDFIELD_URL} target="_blank" rel="noopener">终末地 BWIKI</Link>
          <br />
          · 明日方舟干员：参考{" "}
          <Link href={BWIKI_ARKNIGHTS_URL} target="_blank" rel="noopener">明日方舟 BWIKI</Link>
          （CC BY-SA 4.0 等，见{" "}
          <Link href={CC_BY_SA_40_URL} target="_blank" rel="noopener">署名说明</Link>）
          <br />
          · 游戏名称、数值、美术等版权归各游戏权利方
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }} gutterBottom>
          数据汇编许可见{" "}
          <Link href={DATA_LICENSE_URL} target="_blank" rel="noopener">DATA_LICENSE</Link>
          （商用禁止使用本仓库 JSON 与采集流程）。
        </Typography>

        <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
          更多文档
        </Typography>
        <Box component="ul" sx={{ m: 0, pl: 2.5, typography: "body2" }}>
          <li>
            <Link href={ATTRIBUTION_DOC_URL} target="_blank" rel="noopener">数据来源与许可（完整）</Link>
          </li>
          <li>
            <Link href={COMMERCIAL_OUTLINE_URL} target="_blank" rel="noopener">商业许可要点</Link>
          </li>
          <li>
            <Link href={NOTICES_URL} target="_blank" rel="noopener">NOTICES（第三方与商标）</Link>
          </li>
        </Box>

        <Typography variant="body2" sx={{ mt: 2 }} color="text.secondary">
          计算结果仅供参考，可能与游戏内数值存在差异。
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button component="a" href={REPO_URL} target="_blank" rel="noopener">
          打开 GitHub
        </Button>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}
