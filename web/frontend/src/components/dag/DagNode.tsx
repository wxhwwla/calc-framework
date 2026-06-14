import { memo } from "react";
import { useTranslation } from "react-i18next";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { Box, Chip, Typography } from "@mui/material";
import type { DagNodeData } from "../../store/editorStore";
import { getNodeColor } from "../../store/editorStore";

function useNodeTypeLabels() {
  const { t } = useTranslation();
  return {
    const: t("dag.nodeTypes.const"),
    var: t("dag.nodeTypes.var"),
    unary: t("dag.nodeTypes.unary"),
    binary: t("dag.nodeTypes.binary"),
    condition: t("dag.nodeTypes.condition"),
    expr: t("dag.nodeTypes.expr"),
    user_input: t("dag.nodeTypes.userInput"),
  };
}

function getNodePreview(data: DagNodeData): string {
  switch (data.nodeType) {
    case "const":
      return String(data.value ?? 0);
    case "var":
      return data.path || "?";
    case "unary":
      return `${data.op || "?"}( )`;
    case "binary":
      return `${data.op || "+"}`;
    case "condition":
      return "if ? then ? else ?";
    case "expr":
      return data.expr || "?";
    case "user_input":
      return `[${data.default ?? 0}]`;
    default:
      return "?";
  }
}

function DagNode({ data, selected }: NodeProps<Node<DagNodeData>>) {
  const NODE_TYPE_LABELS = useNodeTypeLabels();
  const color = getNodeColor(data.nodeType);
  const isBinaryOrUnary = data.nodeType === "binary" || data.nodeType === "unary";
  const isCondition = data.nodeType === "condition";
  const isExpr = data.nodeType === "expr";

  return (
    <Box
      sx={{
        background: "#1e1e1e",
        border: selected ? `2px solid ${color}` : "1px solid #444",
        borderRadius: 2,
        minWidth: 140,
        maxWidth: 220,
        boxShadow: selected ? `0 0 12px ${color}40` : "0 2px 6px rgba(0,0,0,0.3)",
        fontFamily: "monospace",
        fontSize: 12,
        position: "relative",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, px: 1, py: 0.5, bgcolor: `${color}22`, borderBottom: `1px solid ${color}44` }}>
        <Chip
          label={NODE_TYPE_LABELS[data.nodeType] || data.nodeType}
          size="small"
          sx={{ height: 18, fontSize: 10, bgcolor: color, color: "#fff", fontWeight: 600 }}
        />
        <Typography variant="caption" sx={{ color: "#ccc", ml: 0.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {data.label}
        </Typography>
      </Box>
      <Box sx={{ px: 1, py: 0.75 }}>
        <Typography variant="caption" sx={{ color: "#aaa" }}>
          {getNodePreview(data)}
        </Typography>
      </Box>

      <Handle type="source" position={Position.Bottom} style={{ background: color, width: 10, height: 10, border: "2px solid #1e1e1e" }} />

      {isBinaryOrUnary && (
        <>
          <Handle type="target" position={Position.Left} id="lhs" style={{ background: "#ff9800", width: 8, height: 8, top: "40%" }} />
          {data.nodeType === "binary" && (
            <Handle type="target" position={Position.Right} id="rhs" style={{ background: "#ff9800", width: 8, height: 8, top: "40%" }} />
          )}
        </>
      )}

      {isCondition && (
        <>
          <Handle type="target" position={Position.Left} id="cond" style={{ background: "#f44336", width: 8, height: 8, top: "30%" }} />
          <Handle type="target" position={Position.Right} id="true" style={{ background: "#4caf50", width: 8, height: 8, top: "30%" }} />
          <Handle type="target" position={Position.Left} id="false" style={{ background: "#9c27b0", width: 8, height: 8, top: "70%" }} />
        </>
      )}

      {isExpr && (
        <Handle type="target" position={Position.Top} id="input" style={{ background: "#9c27b0", width: 8, height: 8 }} />
      )}

      {data.nodeType === "var" && (
        <Handle type="target" position={Position.Top} id="input" style={{ background: "#2196f3", width: 8, height: 8 }} />
      )}

      {data.nodeType === "user_input" && (
        <Handle type="target" position={Position.Top} id="input" style={{ background: "#00bcd4", width: 8, height: 8 }} />
      )}

      {data.nodeType === "const" && (
        <Handle type="target" position={Position.Top} id="input" style={{ background: color, width: 8, height: 8 }} />
      )}
    </Box>
  );
}

export default memo(DagNode);
