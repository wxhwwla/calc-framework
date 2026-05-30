import { useState, useEffect } from "react";
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
        编辑节点: {nodeId}
        <Typography variant="caption" sx={{ ml: 1, color: "#888" }}>
          ({data.nodeType})
        </Typography>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1 }}>
          <TextField
            label="节点 ID"
            value={nodeId}
            size="small"
            disabled
            fullWidth
          />
          <TextField
            label="标签"
            value={form.label || ""}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
            size="small"
            fullWidth
          />

          {data.nodeType === "const" && (
            <TextField
              label="数值"
              type="number"
              value={form.value ?? 0}
              onChange={(e) => setForm({ ...form, value: parseFloat(e.target.value) || 0 })}
              size="small"
              fullWidth
            />
          )}

          {data.nodeType === "var" && (
            <TextField
              label="变量路径"
              value={form.path || ""}
              onChange={(e) => setForm({ ...form, path: e.target.value })}
              size="small"
              fullWidth
              placeholder="character.力量"
            />
          )}

          {(data.nodeType === "unary" || data.nodeType === "binary") && (
            <TextField
              label="运算符"
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
                label="表达式"
                value={form.expr || ""}
                onChange={(e) => setForm({ ...form, expr: e.target.value })}
                size="small"
                fullWidth
                multiline
                rows={2}
                placeholder="a + b * 2"
              />
              <Typography variant="caption" sx={{ color: "#888" }}>
                表达式中的变量名需与连线上的 handle 名称匹配
              </Typography>
            </>
          )}

          {data.nodeType === "condition" && (
            <Typography variant="caption" sx={{ color: "#888" }}>
              条件节点通过连线绑定 cond/true/false 三个输入
            </Typography>
          )}

          {data.nodeType === "user_input" && (
            <Box sx={{ display: "flex", gap: 1 }}>
              <TextField label="默认值" type="number" value={form.default ?? 0} onChange={(e) => setForm({ ...form, default: parseFloat(e.target.value) || 0 })} size="small" />
              <TextField label="最小值" type="number" value={form.min ?? 0} onChange={(e) => setForm({ ...form, min: parseFloat(e.target.value) || 0 })} size="small" />
              <TextField label="最大值" type="number" value={form.max ?? 100} onChange={(e) => setForm({ ...form, max: parseFloat(e.target.value) || 100 })} size="small" />
              <TextField label="步长" type="number" value={form.step ?? 1} onChange={(e) => setForm({ ...form, step: parseFloat(e.target.value) || 1 })} size="small" />
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button variant="contained" onClick={handleSave}>保存</Button>
      </DialogActions>
    </Dialog>
  );
}
