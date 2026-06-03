import { useEffect, useState } from "react";
import {
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Collapse,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Snackbar,
  Alert,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import UploadIcon from "@mui/icons-material/Upload";
import DownloadIcon from "@mui/icons-material/Download";
import { useAdapterStore } from "../store/adapterStore";
import { fetchSchema, type AdapterAttr } from "../api/compute";
import { uploadHubAdapter, downloadHubAdapter } from "../api/hub";

function AdapterDetail({ name }: { name: string }) {
  const [open, setOpen] = useState(false);
  const [schema, setSchema] = useState<AdapterAttr[]>([]);

  useEffect(() => {
    if (open) {
      fetchSchema(name).then(setSchema).catch(() => setSchema([]));
    }
  }, [open, name]);

  return (
    <Box>
      <IconButton size="small" onClick={() => setOpen(!open)}>
        {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </IconButton>
      <Collapse in={open}>
        <Paper sx={{ p: 2, mt: 1, bgcolor: "grey.900" }}>
          <Typography variant="caption" display="block" gutterBottom>
            属性清单 ({schema.length} 项)
          </Typography>
          {schema.map((attr) => (
            <Typography key={attr.name} variant="caption" display="block">
              {attr.name} ({attr.type}, source={attr.source}){attr.description ? ` — ${attr.description}` : ""}
            </Typography>
          ))}
        </Paper>
      </Collapse>
    </Box>
  );
}

export default function AdaptersPage() {
  const adapters = useAdapterStore((s) => s.adapters);
  const load = useAdapterStore((s) => s.load);

  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const [downloading, setDownloading] = useState<string | null>(null);

  const [snackMsg, setSnackMsg] = useState("");
  const [snackSeverity, setSnackSeverity] = useState<"success" | "error">("success");

  useEffect(() => {
    load();
  }, []);

  const handleUpload = async () => {
    if (!uploadFile) {
      setSnackMsg("请选择要上传的 .calcpack 文件");
      setSnackSeverity("error");
      return;
    }
    setUploading(true);
    try {
      const result = await uploadHubAdapter(uploadFile);
      setSnackMsg(`上传成功: ${result.name} v${result.version}`);
      setSnackSeverity("success");
      setUploadOpen(false);
      setUploadFile(null);
    } catch (e) {
      setSnackMsg(`上传失败: ${e}`);
      setSnackSeverity("error");
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (name: string) => {
    setDownloading(name);
    try {
      await downloadHubAdapter(name);
      setSnackMsg(`开始下载: ${name}`);
      setSnackSeverity("success");
    } catch (e) {
      setSnackMsg(`下载失败: ${e}`);
      setSnackSeverity("error");
    } finally {
      setDownloading(null);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5">适配器管理</Typography>
        <Button variant="contained" startIcon={<UploadIcon />} onClick={() => setUploadOpen(true)}>
          上传适配器
        </Button>
      </Box>
      <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox" />
              <TableCell>名称</TableCell>
              <TableCell>游戏</TableCell>
              <TableCell>版本</TableCell>
              <TableCell>说明</TableCell>
              <TableCell align="center">操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {adapters.map((a) => (
              <TableRow key={a.name}>
                <TableCell padding="checkbox">
                  <AdapterDetail name={a.name} />
                </TableCell>
                <TableCell>
                  <Typography fontWeight="bold">{a.name}</Typography>
                </TableCell>
                <TableCell>
                  <Chip label={a.game} size="small" variant="outlined" />
                </TableCell>
                <TableCell>v{a.version}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {a.description}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    color="primary"
                    disabled={downloading === a.name}
                    onClick={() => handleDownload(a.name)}
                    title="从市场下载"
                  >
                    {downloading === a.name ? <CircularProgress size={18} /> : <DownloadIcon />}
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {adapters.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary">暂无适配器</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>上传适配器到市场</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              选择 .calcpack 适配器包文件上传到市场。上传后其他用户即可下载使用。
            </Typography>
            <Button variant="outlined" component="label" sx={{ py: 3 }}>
              {uploadFile ? uploadFile.name : "选择 .calcpack 文件"}
              <input
                type="file"
                hidden
                accept=".calcpack"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              />
            </Button>
            {uploadFile && (
              <Typography variant="caption" color="text.secondary">
                已选: {uploadFile.name} ({formatSize(uploadFile.size)})
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setUploadOpen(false); setUploadFile(null); }}>取消</Button>
          <Button variant="contained" onClick={handleUpload} disabled={uploading || !uploadFile}>
            {uploading ? <CircularProgress size={20} /> : "上传"}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snackMsg} autoHideDuration={4000} onClose={() => setSnackMsg("")}>
        <Alert severity={snackSeverity} onClose={() => setSnackMsg("")}>{snackMsg}</Alert>
      </Snackbar>
    </Box>
  );
}
