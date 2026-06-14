import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Alert,
} from "@mui/material";
import { dagVerify, type DagVerifyResult } from "../../api/dataProfiles";

interface Props {
  open: boolean;
  onClose: () => void;
  profileId: string;
  entityKey: string;
  entityName: string;
  level?: number;
}

export default function DagVerifyDialog({ open, onClose, profileId, entityKey, entityName, level = 90 }: Props) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DagVerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !entityName) return;
    setLoading(true);
    setError(null);
    setResult(null);

    dagVerify(profileId, entityKey, entityName, level)
      .then(setResult)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [open, profileId, entityKey, entityName, level]);

  const handleClose = () => {
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        DAG 验证 → {entityName} Lv.{level}
      </DialogTitle>
      <DialogContent dividers>
        {loading && (
          <CircularProgress />
        )}

        {error && (
          <Alert severity="error">{error}</Alert>
        )}

        {result && (
          <>
            <Typography variant="subtitle1" gutterBottom>
              {t("designer.dagVerify.outputs", "输出节点")} ({Object.keys(result.outputs).length}):
            </Typography>
            <TableContainer sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t("designer.dagVerify.nodeName", "节点")}</TableCell>
                    <TableCell align="right">{t("designer.dagVerify.value", "值")}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(result.outputs).map(([key, val]) => (
                    <TableRow key={key}>
                      <TableCell>{key}</TableCell>
                      <TableCell align="right">{typeof val === "number" ? val.toFixed(4) : String(val)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Divider sx={{ my: 1 }} />

            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t("designer.dagVerify.allNodes", "全部节点值")} ({result.node_count}):
            </Typography>
            <TableContainer sx={{ maxHeight: 360 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>{t("designer.dagVerify.nodeId", "节点 ID")}</TableCell>
                    <TableCell align="right">{t("designer.dagVerify.value", "值")}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(result.node_values)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([nid, val]) => (
                      <TableRow key={nid}>
                        <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}>{nid}</TableCell>
                        <TableCell align="right">{typeof val === "number" ? val.toFixed(4) : String(val)}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
