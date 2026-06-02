import { useEffect, useState } from "react";
import {
  Typography, Box, Paper, TextField, Button, Chip, IconButton,
  Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Dialog, DialogTitle, DialogContent, DialogActions,
  CircularProgress, Select, MenuItem, FormControl, InputLabel,
  Rating, Snackbar, Alert,
} from "@mui/material";
import UploadIcon from "@mui/icons-material/Upload";
import SearchIcon from "@mui/icons-material/Search";
import DownloadIcon from "@mui/icons-material/Download";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  listPacks,
  createPack,
  uploadPackFile,
  downloadPackFile,
  ratePack,
  type HubPackInfo,
} from "../api/hub";

export default function MarketplacePage() {
  const [packs, setPacks] = useState<HubPackInfo[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("updated_at");

  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadName, setUploadName] = useState("");
  const [uploadVersion, setUploadVersion] = useState("");
  const [uploadDesc, setUploadDesc] = useState("");
  const [uploadAuthor, setUploadAuthor] = useState("");
  const [uploadTags, setUploadTags] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const [ratePackId, setRatePackId] = useState<string | null>(null);
  const [rateScore, setRateScore] = useState(0);
  const [rateComment, setRateComment] = useState("");
  const [rating, setRating] = useState(false);

  const [snackMsg, setSnackMsg] = useState("");
  const [snackSeverity, setSnackSeverity] = useState<"success" | "error">("success");

  const loadPacks = async () => {
    setLoading(true);
    try {
      const data = await listPacks({ search, sort, order: "desc", limit: 100 });
      setPacks(data.packs);
      setTotal(data.total);
    } catch (e) {
      setPacks([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPacks();
  }, [sort]);

  const handleSearch = () => {
    loadPacks();
  };

  const handleUpload = async () => {
    if (!uploadName || !uploadVersion) {
      setSnackMsg("名称和版本为必填项");
      setSnackSeverity("error");
      return;
    }
    setUploading(true);
    try {
      const result = await createPack({
        name: uploadName,
        version: uploadVersion,
        description: uploadDesc,
        author: uploadAuthor,
        tags: uploadTags ? uploadTags.split(",").map((t) => t.trim()).filter(Boolean) : [],
      });
      if (uploadFile) {
        await uploadPackFile(result.id, uploadFile);
      }
      setSnackMsg(`上传成功: ${result.name} v${result.version}`);
      setSnackSeverity("success");
      setUploadOpen(false);
      resetUploadForm();
      loadPacks();
    } catch (e) {
      setSnackMsg(`上传失败: ${e}`);
      setSnackSeverity("error");
    } finally {
      setUploading(false);
    }
  };

  const resetUploadForm = () => {
    setUploadName("");
    setUploadVersion("");
    setUploadDesc("");
    setUploadAuthor("");
    setUploadTags("");
    setUploadFile(null);
  };

  const handleDownload = async (pack: HubPackInfo) => {
    try {
      await downloadPackFile(pack.id, `${pack.name}_v${pack.version}.calcpack`);
      setSnackMsg(`开始下载: ${pack.name}`);
      setSnackSeverity("success");
    } catch (e) {
      setSnackMsg(`下载失败: ${e}`);
      setSnackSeverity("error");
    }
  };

  const handleRate = async () => {
    if (!ratePackId || rateScore === 0) return;
    setRating(true);
    try {
      await ratePack(ratePackId, rateScore, rateComment);
      setSnackMsg("评分成功");
      setSnackSeverity("success");
      setRatePackId(null);
      setRateScore(0);
      setRateComment("");
      loadPacks();
    } catch (e) {
      setSnackMsg(`评分失败: ${e}`);
      setSnackSeverity("error");
    } finally {
      setRating(false);
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
        <Typography variant="h5">配置包市场</Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadPacks}>
            刷新
          </Button>
          <Button variant="contained" startIcon={<UploadIcon />} onClick={() => setUploadOpen(true)}>
            上传
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 2, mb: 2, display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
        <TextField
          size="small"
          label="搜索"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          sx={{ flexGrow: 1 }}
        />
        <IconButton onClick={handleSearch}><SearchIcon /></IconButton>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>排序</InputLabel>
          <Select value={sort} label="排序" onChange={(e) => setSort(e.target.value)}>
            <MenuItem value="updated_at">最近更新</MenuItem>
            <MenuItem value="created_at">最近上传</MenuItem>
            <MenuItem value="rating">评分最高</MenuItem>
            <MenuItem value="download_count">下载最多</MenuItem>
            <MenuItem value="name">名称</MenuItem>
          </Select>
        </FormControl>
      </Paper>

      <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>名称</TableCell>
              <TableCell>版本</TableCell>
              <TableCell>作者</TableCell>
              <TableCell>标签</TableCell>
              <TableCell align="center">评分</TableCell>
              <TableCell align="center">下载</TableCell>
              <TableCell align="center">大小</TableCell>
              <TableCell align="center">操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            )}
            {!loading && packs.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    {search ? "未找到匹配的配置包" : "暂无配置包，马上上传第一个吧！"}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {!loading && packs.map((p) => (
              <TableRow key={p.id}>
                <TableCell>
                  <Typography fontWeight="bold">{p.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {p.description?.slice(0, 80)}{p.description?.length > 80 ? "..." : ""}
                  </Typography>
                </TableCell>
                <TableCell>v{p.version}</TableCell>
                <TableCell>{p.author || "-"}</TableCell>
                <TableCell>
                  {(p.tags || []).map((t) => (
                    <Chip key={t} label={t} size="small" sx={{ mr: 0.5 }} />
                  ))}
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <IconButton size="small" onClick={() => { setRatePackId(p.id); setRateScore(Math.round(p.rating)); }}>
                      <Typography variant="body2">{p.rating > 0 ? p.rating.toFixed(1) : "0.0"}</Typography>
                    </IconButton>
                    <Typography variant="caption" color="text.secondary">
                      ({p.rating_count})
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center">{p.download_count}</TableCell>
                <TableCell align="center">{p.file_size > 0 ? formatSize(p.file_size) : "-"}</TableCell>
                <TableCell align="center">
                  <IconButton size="small" color="primary" onClick={() => handleDownload(p)}>
                    <DownloadIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
        共 {total} 个配置包
      </Typography>

      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>上传配置包</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1 }}>
            <TextField label="名称" required value={uploadName} onChange={(e) => setUploadName(e.target.value)} />
            <TextField label="版本" required value={uploadVersion} onChange={(e) => setUploadVersion(e.target.value)} />
            <TextField label="描述" multiline rows={3} value={uploadDesc} onChange={(e) => setUploadDesc(e.target.value)} />
            <TextField label="作者" value={uploadAuthor} onChange={(e) => setUploadAuthor(e.target.value)} />
            <TextField label="标签（逗号分隔）" value={uploadTags} onChange={(e) => setUploadTags(e.target.value)} />
            <Button variant="outlined" component="label">
              选择文件 {uploadFile?.name || ".calcpack"}
              <input type="file" hidden accept=".calcpack,.zip,.json" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} />
            </Button>
            {uploadFile && (
              <Typography variant="caption" color="text.secondary">
                已选: {uploadFile.name} ({formatSize(uploadFile.size)})
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleUpload} disabled={uploading}>
            {uploading ? <CircularProgress size={20} /> : "上传"}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={ratePackId !== null} onClose={() => setRatePackId(null)}>
        <DialogTitle>评分</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1, minWidth: 300 }}>
            <Rating value={rateScore} onChange={(_, v) => setRateScore(v || 0)} />
            <TextField label="评论（可选）" multiline rows={2} value={rateComment} onChange={(e) => setRateComment(e.target.value)} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRatePackId(null)}>取消</Button>
          <Button variant="contained" onClick={handleRate} disabled={rating || rateScore === 0}>
            {rating ? <CircularProgress size={20} /> : "提交评分"}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snackMsg} autoHideDuration={4000} onClose={() => setSnackMsg("")}>
        <Alert severity={snackSeverity} onClose={() => setSnackMsg("")}>{snackMsg}</Alert>
      </Snackbar>
    </Box>
  );
}
