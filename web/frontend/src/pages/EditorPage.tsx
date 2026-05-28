import { useMemo } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid2 as Grid,
} from "@mui/material";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useEditorStore } from "../store/editorStore";

function EditorCanvas() {
  const nodes = useEditorStore((s) => s.nodes);
  const edges = useEditorStore((s) => s.edges);

  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState(nodes);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState(edges);

  useMemo(() => {
    setFlowNodes(nodes);
    setFlowEdges(edges);
  }, [nodes, edges]);

  const defaultEdgeOptions = useMemo(
    () => ({
      style: { stroke: "#90caf9", strokeWidth: 2 },
      labelStyle: { fill: "#90caf9", fontSize: 10 },
    }),
    [],
  );

  return (
    <Box sx={{ height: 500, border: "1px solid #333", borderRadius: 1 }}>
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        colorMode="dark"
      >
        <Background color="#333" gap={20} />
        <Controls />
        <MiniMap
          style={{ background: "#1e1e1e" }}
          nodeColor={(n) => {
            const t = (n.data as any)?.nodeType;
            switch (t) {
              case "const":
                return "#4caf50";
              case "var":
                return "#2196f3";
              case "expr":
                return "#ff9800";
              case "condition":
                return "#f44336";
              case "output":
                return "#9c27b0";
              default:
                return "#616161";
            }
          }}
        />
      </ReactFlow>
    </Box>
  );
}

export default function EditorPage() {
  const dagJson = useEditorStore((s) => s.dagJson);
  const error = useEditorStore((s) => s.error);
  const setDagJson = useEditorStore((s) => s.setDagJson);
  const parseAndRender = useEditorStore((s) => s.parseAndRender);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        DAG 可视化编辑器 (DAG Editor)
      </Typography>
      <Grid container spacing={2}>
        <Grid size={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              DAG JSON 输入
            </Typography>
            <TextField
              multiline
              rows={18}
              fullWidth
              placeholder='粘贴 DAG JSON（如 {"nodes": {...}}）'
              value={dagJson}
              onChange={(e) => setDagJson(e.target.value)}
              sx={{ fontFamily: "monospace", fontSize: 12 }}
            />
            <Box sx={{ mt: 1, display: "flex", gap: 1 }}>
              <Button variant="contained" onClick={parseAndRender}>
                渲染 (Render)
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  fetch("/api/compute/evaluate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      adapter: "MOBA 英雄伤害计算",
                      context: {
                        character: { attack_damage: 100 },
                        enemy: { armor: 50 },
                        user_input: { skill_base: 200, is_physical: 1, is_crit: 0 },
                      },
                    }),
                  })
                    .then((r) => r.json())
                    .then((data) => {
                      setDagJson(JSON.stringify(data.node_values, null, 2));
                    });
                }}
              >
                加载示例
              </Button>
            </Box>
            {error && (
              <Typography color="error" variant="caption" sx={{ mt: 1, display: "block" }}>
                {error}
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid size={8}>
          <EditorCanvas />
        </Grid>
      </Grid>
    </Box>
  );
}
