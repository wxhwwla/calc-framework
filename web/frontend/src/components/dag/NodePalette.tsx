import { type DragEvent } from "react";
import { useTranslation } from "react-i18next";
import { Box, Chip, Typography, Paper } from "@mui/material";
import type { DagNodeTypeName } from "../../store/editorStore";
import { getNodeColor } from "../../store/editorStore";

function useNodeOptions(): { type: DagNodeTypeName; label: string; desc: string }[] {
  const { t } = useTranslation();
  return [
    { type: "const", label: t("dag.nodeTypes.const"), desc: t("dag.nodeTypes.constDesc") },
    { type: "var", label: t("dag.nodeTypes.var"), desc: t("dag.nodeTypes.varDesc") },
    { type: "unary", label: t("dag.nodeTypes.unary"), desc: t("dag.nodeTypes.unaryDesc") },
    { type: "binary", label: t("dag.nodeTypes.binary"), desc: t("dag.nodeTypes.binaryDesc") },
    { type: "condition", label: t("dag.nodeTypes.condition"), desc: t("dag.nodeTypes.conditionDesc") },
    { type: "expr", label: t("dag.nodeTypes.expr"), desc: t("dag.nodeTypes.exprDesc") },
    { type: "user_input", label: t("dag.nodeTypes.userInput"), desc: t("dag.nodeTypes.userInputDesc") },
    { type: "call", label: t("dag.nodeTypes.call"), desc: t("dag.nodeTypes.callDesc") },
  ];
}

const onDragStart = (event: DragEvent, nodeType: DagNodeTypeName) => {
  event.dataTransfer.setData("application/dag-node-type", nodeType);
  event.dataTransfer.effectAllowed = "move";
};

export default function NodePalette() {
  const { t } = useTranslation();
  const NODE_OPTIONS = useNodeOptions();
  return (
    <Paper sx={{ p: 1.5 }}>
      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
        {t("dag.nodePaletteTitle")}
      </Typography>
      <Typography variant="caption" sx={{ color: "#888", display: "block", mb: 1 }}>
        {t("dag.nodePaletteHint")}
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
