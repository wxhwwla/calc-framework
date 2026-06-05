import { useCallback, useRef, useState } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Typography, Box, LinearProgress,
} from "@mui/material";

interface OCRUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onResult: (data: { char_name?: string; weapon_name?: string; preset?: Record<string, unknown> }) => void;
}

const isPythonAnywhere = (() => {
  const hostname = typeof window !== "undefined" ? window.location.hostname.toLowerCase() : "";
  return hostname === "pythonanywhere.com" || hostname.endsWith(".pythonanywhere.com");
})();

export default function OCRUploadDialog({ open, onClose, onResult }: OCRUploadDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleUpload = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const r = await fetch("/api/ocr/detect", { method: "POST", body: formData });
      if (r.status === 501) {
        throw new Error("OCR 未部署（线上站不支持；请用桌面版截图识装）");
      }
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      onResult(data);
      onClose();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [file, onResult, onClose]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>截图识装 (OCR)</DialogTitle>
      <DialogContent>
        {isPythonAnywhere && (
          <Typography variant="body2" color="warning.main" sx={{ mb: 2 }}>
            PythonAnywhere 未安装 OCR 依赖；请使用桌面计算器「截图识装」。
          </Typography>
        )}
        <Box sx={{ mb: 2 }}>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            style={{ width: "100%" }}
          />
        </Box>
        {file && (
          <Typography variant="body2" color="text.secondary">
            已选择: {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </Typography>
        )}
        {loading && <LinearProgress sx={{ mt: 1 }} />}
        {error && (
          <Typography variant="caption" color="error" sx={{ mt: 1, display: "block" }}>
            {error}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button variant="contained" onClick={handleUpload} disabled={!file || loading}>
          {loading ? "识别中..." : "识别"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
