import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  Box,
  Typography,
} from "@mui/material";
import type { DagNodeData } from "../../store/editorStore";
import { getNodeColor } from "../../store/editorStore";

const BINARY_OPS = ["+", "-", "*", "/", "^", "min", "max", "mod"];
const UNARY_OPS = ["neg", "floor", "ceil", "abs", "sqrt", "ln", "log10", "sin", "cos", "tan"];

interface NodeEditDialogProps {
  open: boolean;
  nodeId: string | null;
  data: DagNodeData | null;
  onClose: () => void;
  onSave: (nodeId: string, data: Partial<DagNodeData>) => void;
}

export default function NodeEditDialog({ open, nodeId, data, onClose, onSave }: NodeEditDialogProps) {
  const { t } = useTranslation();
  const [form, setForm] = useState<DagNodeData>({ label: "", nodeType: "const" });

  useEffect(() => {
    if (data) setForm({ ...data });
  }, [data]);

  if (!nodeId || !data) return null;

  const handleSave = () => {
    onSave(nodeId, form);
    onClose();
  };

  const color = getNodeColor(data.nodeType);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ borderLeft: `4px solid ${color}`, pl: 2 }}>
        {t("dag.nodeEdit.title")}: {nodeId}
        <Typography variant="caption" sx={{ ml: 1, color: "#888" }}>
          ({data.nodeType})
        </Typography>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1 }}>
          <TextField
            label={t("dag.nodeEdit.nodeId")}
            value={nodeId}
            size="small"
            disabled
            fullWidth
          />
          <TextField
            label={t("dag.nodeEdit.label")}
            value={form.label || ""}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
            size="small"
            fullWidth
          />

          {data.nodeType === "const" && (
            <TextField
              label={t("dag.nodeEdit.value")}
              type="number"
              value={form.value ?? 0}
              onChange={(e) => setForm({ ...form, value: parseFloat(e.target.value) || 0 })}
              size="small"
              fullWidth
            />
          )}

          {data.nodeType === "var" && (
            <TextField
              label={t("dag.nodeEdit.variablePath")}
              value={form.path || ""}
              onChange={(e) => setForm({ ...form, path: e.target.value })}
              size="small"
              fullWidth
              placeholder={t("dag.nodeEdit.varPathPlaceholder")}
            />
          )}

          {(data.nodeType === "unary" || data.nodeType === "binary") && (
            <TextField
              label={t("dag.nodeEdit.operator")}
              select
              value={form.op || (data.nodeType === "binary" ? "+" : "neg")}
              onChange={(e) => setForm({ ...form, op: e.target.value })}
              size="small"
              fullWidth
            >
              {(data.nodeType === "binary" ? BINARY_OPS : UNARY_OPS).map((op) => (
                <MenuItem key={op} value={op}>{op}</MenuItem>
              ))}
            </TextField>
          )}

          {data.nodeType === "expr" && (
            <>
              <TextField
                label={t("dag.nodeEdit.expression")}
                value={form.expr || ""}
                onChange={(e) => setForm({ ...form, expr: e.target.value })}
                size="small"
                fullWidth
                multiline
                rows={2}
                placeholder={t("dag.nodeEdit.exprPlaceholder")}
              />
              <Typography variant="caption" sx={{ color: "#888" }}>
                {t("dag.nodeEdit.exprHint")}
              </Typography>
            </>
          )}

          {data.nodeType === "condition" && (
            <Typography variant="caption" sx={{ color: "#888" }}>
              {t("dag.nodeEdit.conditionHint")}
            </Typography>
          )}

          {data.nodeType === "user_input" && (
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              <TextField label={t("dag.nodeEdit.defaultVal")} type="number" value={form.default ?? 0} onChange={(e) => setForm({ ...form, default: parseFloat(e.target.value) || 0 })} size="small" />
              <TextField label={t("dag.nodeEdit.minVal")} type="number" value={form.min ?? 0} onChange={(e) => setForm({ ...form, min: parseFloat(e.target.value) || 0 })} size="small" />
              <TextField label={t("dag.nodeEdit.maxVal")} type="number" value={form.max ?? 100} onChange={(e) => setForm({ ...form, max: parseFloat(e.target.value) || 100 })} size="small" />
              <TextField label={t("dag.nodeEdit.step")} type="number" value={form.step ?? 1} onChange={(e) => setForm({ ...form, step: parseFloat(e.target.value) || 1 })} size="small" />
            </Box>
          )}

          {data.nodeType === "call" && (
            <>
              <TextField
                label={t("dag.nodeEdit.subgraphName", "子图名称")}
                value={form.subgraph || ""}
                onChange={(e) => setForm({ ...form, subgraph: e.target.value })}
                size="small"
                fullWidth
                placeholder="endfield_full"
                helperText={t("dag.nodeEdit.subgraphHint", "引用 DAG JSON 中 subgraphs 下定义的子图")}
              />
              <Typography variant="subtitle2" sx={{ mt: 1 }}>
                {t("dag.nodeEdit.bindings", "参数绑定")}
              </Typography>
              {form.bindings && Object.entries(form.bindings).map(([param, sourceId], i) => (
                <Box key={i} sx={{ display: "flex", gap: 1 }}>
                  <TextField
                    label={t("dag.nodeEdit.paramName", "参数")}
                    size="small"
                    value={param}
                    onChange={(e) => {
                      const newBindings = { ...form.bindings };
                      delete newBindings[param];
                      newBindings[e.target.value] = sourceId;
                      setForm({ ...form, bindings: newBindings });
                    }}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    label={t("dag.nodeEdit.sourceNode", "源节点")}
                    size="small"
                    value={sourceId || ""}
                    onChange={(e) => {
                      const newBindings = { ...form.bindings };
                      newBindings[param] = e.target.value;
                      setForm({ ...form, bindings: newBindings });
                    }}
                    sx={{ flex: 2 }}
                  />
                </Box>
              ))}
              <Button
                size="small"
                onClick={() => setForm({ ...form, bindings: { ...(form.bindings || {}), "": "" } })}
              >
                + {t("generator.addStep", "添加参数")}
              </Button>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.cancel")}</Button>
        <Button variant="contained" onClick={handleSave}>{t("common.save")}</Button>
      </DialogActions>
    </Dialog>
  );
}
