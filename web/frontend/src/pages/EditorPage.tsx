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
import DagEditorCanvas from "../components/dag/DagEditorCanvas";
import NodePalette from "../components/dag/NodePalette";
import NodeEditDialog from "../components/dag/NodeEditDialog";
import { useEditorStore, type DagNodeData } from "../store/editorStore";

export default function EditorPage() {
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
    (_event: React.MouseEvent, node: any) => {
      setEditNodeId(node.id);
      setEditNodeData(node.data as DagNodeData);
      setEditDialogOpen(true);
    },
    [],
  );

  const handleEditSave = useCallback(
    (nodeId: string, data: Partial<DagNodeData>) => {
      updateNodeData(nodeId, data);
      setSnackMsg(`节点 ${nodeId} 已更新`);
    },
    [updateNodeData],
  );

  const handleSaveToJson = useCallback(() => {
    const json = saveToJson();
    setDagJson(json);
    setSnackMsg("已导出为 DAG JSON");
  }, [saveToJson, setDagJson]);

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
        setSnackMsg("已加载示例数据，点击「渲染」查看");
      }
    } catch {
      setSnackMsg("加载示例失败");
    }
  }, [setDagJson]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        DAG 公式图编辑器
      </Typography>

      <Grid container spacing={2}>
        <Grid size={3}>
          <NodePalette />
          <Paper sx={{ p: 1.5, mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              操作提示
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              • 从节点面板拖拽到画布创建节点
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              • 从节点底部拖出连线到其他节点
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              • 双击节点编辑属性
            </Typography>
            <Typography variant="caption" sx={{ color: "#888", display: "block" }}>
              • 选中后按 Delete/Backspace 删除
            </Typography>
          </Paper>
        </Grid>

        <Grid size={9}>
          <DagEditorCanvas onNodeDoubleClick={handleDoubleClick} />
        </Grid>
      </Grid>

      <Paper sx={{ p: 2, mt: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
          <TextField
            label="DAG 名称"
            value={dagName}
            onChange={(e) => setDagName(e.target.value)}
            size="small"
            sx={{ minWidth: 200 }}
          />
          <Button variant="contained" onClick={handleSaveToJson}>
            导出 JSON
          </Button>
          <Button variant="outlined" onClick={handleLoadExample}>
            加载示例
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            onClick={() => {
              setDagJson(JSON.stringify({ name: dagName, nodes: {} }, null, 2));
              parseAndRender();
            }}
          >
            清空
          </Button>
          <Typography variant="caption" sx={{ color: "#888", ml: "auto" }}>
            {nodes.length} 个节点
          </Typography>
        </Box>
        <TextField
          multiline
          rows={6}
          fullWidth
          placeholder='DAG JSON（如 {"nodes": {...}}）'
          value={dagJson}
          onChange={(e) => setDagJson(e.target.value)}
          sx={{ fontFamily: "monospace", fontSize: 12 }}
        />
        <Box sx={{ mt: 1, display: "flex", gap: 1 }}>
          <Button variant="contained" onClick={parseAndRender}>
            渲染
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
