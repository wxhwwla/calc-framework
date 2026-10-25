import { useCallback, useState } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid2 as Grid,
  Snackbar,
  Alert,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import DagEditorCanvas from "../components/dag/DagEditorCanvas";
import NodePalette from "../components/dag/NodePalette";
import NodeEditDialog from "../components/dag/NodeEditDialog";
import { useEditorStore, type DagNodeData } from "../store/editorStore";

export default function EditorPage() {
  const { t } = useTranslation();
  const dagJson = useEditorStore((s) => s.dagJson);
  const dagName = useEditorStore((s) => s.dagName);
  const error = useEditorStore((s) => s.error);
  const nodes = useEditorStore((s) => s.nodes);
  const setDagJson = useEditorStore((s) => s.setDagJson);
  const setDagName = useEditorStore((s) => s.setDagName);
  const parseAndRender = useEditorStore((s) => s.parseAndRender);
  const saveToJson = useEditorStore((s) => s.saveToJson);
  const updateNodeData = useEditorStore((s) => s.updateNodeData);

  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editNodeId, setEditNodeId] = useState<string | null>(null);
  const [editNodeData, setEditNodeData] = useState<DagNodeData | null>(null);
  const [snackMsg, setSnackMsg] = useState("");

  const handleDoubleClick = useCallback(
    (_event: React.MouseEvent, node: import("@xyflow/react").Node) => {
      setEditNodeId(node.id);
      setEditNodeData(node.data as DagNodeData);
      setEditDialogOpen(true);
    },
    [],
  );

  const handleEditSave = useCallback(
    (nodeId: string, data: Partial<DagNodeData>) => {
      updateNodeData(nodeId, data);
      setSnackMsg(t("dag.editor.nodeUpdated", { id: nodeId }));
    },
    [updateNodeData, t],
  );

  const handleSaveToJson = useCallback(() => {
    const json = saveToJson();
    setDagJson(json);
    setSnackMsg(t("dag.editor.jsonExported"));
  }, [saveToJson, setDagJson, t]);

  const handleLoadExample = useCallback(async () => {
    try {
      const r = await fetch("/api/compute/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          adapter: "终末地伤害计算",
          context: {
            character: { "基础攻击": 600, "力量": 100, "敏捷": 80, "智识": 60, "意志": 70, "暴击率": 0.05, "暴击伤害": 0.5 },
            weapon: { "基础攻击": 400, "攻击力+": 0, "附加攻击力+": 0 },
            enemy: { "防御": 100 },
            equipment: { "攻击力平值": 0 },
            computed: { "主能力平值加算": 100, "副能力平值加算": 80, "主能力百分比": 0, "副能力百分比": 0, "技能倍率": 1, "伤害加成": 0, "伤害减免": 0, "增幅": 0, "虚弱": 0, "庇护": 0, "脆弱": 0, "易伤": 0, "失衡易伤": 0, "抗性": 0, "非主控减伤": 0, "连击增伤": 0, "特殊乘区": 0, "力量加成值": 0, "敏捷加成值": 0, "智识加成值": 0, "意志加成值": 0 },
            user_input: {},
          },
        }),
      });
      const data = await r.json();
      if (data.node_values) {
        setDagJson(JSON.stringify({ name: "终末地伤害计算样例", nodes: data.node_values }, null, 2));
        setSnackMsg(t("dag.editor.exampleLoaded"));
      }
    } catch {
      setSnackMsg(t("dag.editor.loadExampleFailed"));
    }
  }, [setDagJson, t]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {t("dag.editor.title")}
      </Typography>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 3 }}>
          <NodePalette />
          <Paper sx={{ p: 1.5, mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {t("dag.editor.tips")}
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              {t("dag.editor.tip1")}
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              {t("dag.editor.tip2")}
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              {t("dag.editor.tip3")}
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              {t("dag.editor.tip4")}
            </Typography>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 9 }}>
          <DagEditorCanvas onNodeDoubleClick={handleDoubleClick} />
        </Grid>
      </Grid>

      <Paper sx={{ p: 2, mt: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1, flexWrap: "wrap" }}>
          <TextField
            label={t("dag.editor.dagName")}
            value={dagName}
            onChange={(e) => setDagName(e.target.value)}
            size="small"
            sx={{ minWidth: 200 }}
          />
          <Button variant="contained" onClick={handleSaveToJson}>
            {t("dag.editor.exportJson")}
          </Button>
          <Button variant="outlined" onClick={handleLoadExample}>
            {t("dag.editor.loadExample")}
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            onClick={() => {
              setDagJson(JSON.stringify({ name: dagName, nodes: {} }, null, 2));
              parseAndRender();
            }}
          >
            {t("dag.editor.clear")}
          </Button>
          <Typography variant="caption" sx={{ color: "#888", ml: "auto" }}>
            {t("dag.editor.nodesCount", { n: nodes.length })}
          </Typography>
        </Box>
        <TextField
          multiline
          rows={6}
          fullWidth
          placeholder={t("dag.editor.dagJsonPlaceholder")}
          value={dagJson}
          onChange={(e) => setDagJson(e.target.value)}
          sx={{ fontFamily: "monospace", fontSize: 12 }}
        />
        <Box sx={{ mt: 1, display: "flex", gap: 1 }}>
          <Button variant="contained" onClick={parseAndRender}>
            {t("dag.editor.render")}
          </Button>
        </Box>
        {error && (
          <Typography color="error" variant="caption" sx={{ mt: 1, display: "block" }}>
            {error}
          </Typography>
        )}
      </Paper>

      <NodeEditDialog
        open={editDialogOpen}
        nodeId={editNodeId}
        data={editNodeData}
        onClose={() => setEditDialogOpen(false)}
        onSave={handleEditSave}
      />

      <Snackbar
        open={!!snackMsg}
        autoHideDuration={2000}
        onClose={() => setSnackMsg("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="success" variant="filled" sx={{ width: "100%" }}>
          {snackMsg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
