import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  CircularProgress,
  Alert,
} from "@mui/material";

interface PluginInfo {
  name: string;
  version: string;
  description: string;
  author: string;
  type: string;
  installed: boolean;
  tags: string[];
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function PluginManagerDialog({ open, onClose }: Props) {
  const { t } = useTranslation();
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError("");
    fetch("/api/plugins")
      .then((r) => {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(setPlugins)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [open]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t("plugins.title", "插件管理器")}</DialogTitle>
      <DialogContent dividers>
        {loading && <CircularProgress />}
        {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}

        {!loading && !error && plugins.length === 0 && (
          <Typography color="text.secondary">
            {t("plugins.noPlugins", "暂无已安装的插件")}
          </Typography>
        )}

        {plugins.length > 0 && (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t("common.name")}</TableCell>
                  <TableCell>{t("common.version")}</TableCell>
                  <TableCell>{t("common.description")}</TableCell>
                  <TableCell>{t("common.status")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {plugins.map((p) => (
                  <TableRow key={p.name}>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>{p.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{p.author}</Typography>
                    </TableCell>
                    <TableCell>{p.version}</TableCell>
                    <TableCell sx={{ maxWidth: 300 }}>
                      <Typography variant="body2" noWrap>{p.description}</Typography>
                      {p.tags.map((tag) => (
                        <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ mr: 0.5, mt: 0.5 }} />
                      ))}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={p.installed ? t("plugins.installed", "已安装") : t("plugins.available", "可安装")}
                        size="small"
                        color={p.installed ? "success" : "default"}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: "block" }}>
          {t("plugins.hint", "插件可扩展 DAG 计算能力（暴击、闪避、距离衰减等）。安装 .calcplugin 文件即可添加新插件。")}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
