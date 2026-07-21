import React, { useCallback, useRef, type DragEvent } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  type Node,
  type Edge,
  type OnNodesDelete,
  type OnEdgesDelete,
  type Connection,
  type ReactFlowInstance,
  SelectionMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Box } from "@mui/material";
import DagNode from "./DagNode";
import { useEditorStore, type DagNodeTypeName, type DagNodeData } from "../../store/editorStore";

const nodeTypes = { dagNode: DagNode };

const DEFAULT_EDGE_OPTIONS = {
  style: { stroke: "#90caf9", strokeWidth: 2 },
  labelStyle: { fill: "#90caf9", fontSize: 10 },
};

interface DagEditorCanvasProps {
  onNodeDoubleClick?: (event: React.MouseEvent, node: Node) => void;
}

const isValidConnection = (connection: Edge | Connection): boolean => {
  if (!connection.source || !connection.target) return false;
  if (connection.source === connection.target) return false;
  return true;
};

const DagEditorCanvas: React.FC<DagEditorCanvasProps> = ({ onNodeDoubleClick }) => {
  const storeNodes = useEditorStore((s) => s.nodes);
  const storeEdges = useEditorStore((s) => s.edges);
  const setNodes = useEditorStore((s) => s.setNodes);
  const onConnectAction = useEditorStore((s) => s.onConnect);
  const addNode = useEditorStore((s) => s.addNode);

  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState(storeNodes);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState(storeEdges);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const reactFlowInstance = useRef<ReactFlowInstance<Node<DagNodeData>> | null>(null);

  const onInit = useCallback((instance: ReactFlowInstance<Node<DagNodeData>>) => {
    reactFlowInstance.current = instance;
  }, []);

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      const nodeType = event.dataTransfer.getData("application/dag-node-type") as DagNodeTypeName;
      if (!nodeType || !reactFlowInstance.current) return;

      const bounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!bounds) return;

      const position = reactFlowInstance.current.screenToFlowPosition({ x: event.clientX, y: event.clientY });
      const id = addNode(nodeType, position);

      const newFlowNode: Node<DagNodeData> = {
        id,
        position,
        data: useEditorStore.getState().nodes.find((n) => n.id === id)!.data as DagNodeData,
        type: "dagNode",
      };
      setFlowNodes((nds) => [...nds, newFlowNode]);
    },
    [reactFlowInstance, addNode, setFlowNodes],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      onConnectAction(connection);
      const edgeId = `${connection.source}->${connection.target}${connection.targetHandle ? "__" + connection.targetHandle : ""}`;
      const newEdge: Edge = {
        id: edgeId,
        source: connection.source!,
        target: connection.target!,
        sourceHandle: connection.sourceHandle,
        targetHandle: connection.targetHandle,
        animated: true,
        ...(connection.targetHandle ? { label: connection.targetHandle } : {}),
      };
      setFlowEdges((eds) => [...eds, newEdge]);
    },
    [onConnectAction, setFlowEdges],
  );

  const onNodesDeleteHandler: OnNodesDelete = useCallback(
    (deletedNodes) => {
      const deletedIds = new Set(deletedNodes.map((n) => n.id));
      setFlowNodes((nds) => nds.filter((n) => !deletedIds.has(n.id)));
      setFlowEdges((eds) => eds.filter((e) => !deletedIds.has(e.source) && !deletedIds.has(e.target)));
      setNodes(useEditorStore.getState().nodes.filter((n) => !deletedIds.has(n.id)));
    },
    [setNodes, setFlowNodes, setFlowEdges],
  );

  const onEdgesDeleteHandler: OnEdgesDelete = useCallback(
    (deletedEdges) => {
      const deletedIds = new Set(deletedEdges.map((e) => e.id));
      setFlowEdges((eds) => eds.filter((e) => !deletedIds.has(e.id)));
    },
    [setFlowEdges],
  );

  return (
    <Box
      ref={reactFlowWrapper}
      sx={{ height: { xs: 360, md: 560 }, border: "1px solid #333", borderRadius: 1, position: "relative" }}
    >
      <ReactFlowProvider>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={onInit}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNodesDelete={onNodesDeleteHandler}
          onEdgesDelete={onEdgesDeleteHandler}
          onNodeDoubleClick={onNodeDoubleClick}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={DEFAULT_EDGE_OPTIONS}
          isValidConnection={isValidConnection}
          fitView
          colorMode="dark"
          deleteKeyCode={["Backspace", "Delete"]}
          multiSelectionKeyCode="Shift"
          selectionMode={SelectionMode.Partial}
          snapToGrid
          snapGrid={[20, 20]}
        >
          <Background color="#333" gap={20} />
          <Controls />
          <MiniMap
            style={{ background: "#1e1e1e" }}
            nodeColor={(n) => {
              const t = n.data?.nodeType as string | undefined;
              switch (t) {
                case "const": return "#4caf50";
                case "var": return "#2196f3";
                case "unary": case "binary": return "#ff9800";
                case "condition": return "#f44336";
                case "expr": return "#9c27b0";
                case "user_input": return "#00bcd4";
                default: return "#616161";
              }
            }}
          />
        </ReactFlow>
      </ReactFlowProvider>
    </Box>
  );
}

export default DagEditorCanvas;
