import { type DragEvent } from "react";
import { Box, Chip, Typography, Paper } from "@mui/material";
import type { DagNodeTypeName } from "../../store/editorStore";
import { getNodeColor } from "../../store/editorStore";

const NODE_OPTIONS: { type: DagNodeTypeName; label: string; desc: string }[] = [
  { type: "const", label: "常量", desc: "固定数值" },
  { type: "var", label: "变量", desc: "引用上下文变量" },
  { type: "unary", label: "一元运算", desc: "neg/abs/sqrt/ln..." },
  { type: "binary", label: "二元运算", desc: "+ - * / ^ min max" },
  { type: "condition", label: "条件", desc: "if-else 分支" },
  { type: "expr", label: "表达式", desc: "数学公式" },
  { type: "user_input", label: "用户输入", desc: "滑块/数值输入" },
];

const onDragStart = (event: DragEvent, nodeType: DagNodeTypeName) => {
  event.dataTransfer.setData("application/dag-node-type", nodeType);
  event.dataTransfer.effectAllowed = "move";
};

export default function NodePalette() {
  return (
    <Paper sx={{ p: 1.5 }}>
      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
        节点面板
      </Typography>
      <Typography variant="caption" sx={{ color: "#888", display: "block", mb: 1 }}>
        拖拽节点到画布创建
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 0.75 }}>
        {NODE_OPTIONS.map((opt) => {
          const color = getNodeColor(opt.type);
          return (
            <Box
              key={opt.type}
              draggable
              onDragStart={(e) => onDragStart(e, opt.type)}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                p: 0.75,
                borderRadius: 1,
                border: `1px solid ${color}44`,
                bgcolor: `${color}11`,
                cursor: "grab",
                "&:hover": { bgcolor: `${color}22`, borderColor: color },
                userSelect: "none",
              }}
            >
              <Chip
                label={opt.label}
                size="small"
                sx={{ height: 20, fontSize: 10, bgcolor: color, color: "#fff", fontWeight: 600, minWidth: 56 }}
              />
              <Typography variant="caption" sx={{ color: "#999" }}>
                {opt.desc}
              </Typography>
            </Box>
          );
        })}
      </Box>
    </Paper>
  );
}
