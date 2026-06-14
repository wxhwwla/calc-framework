import { create } from "zustand";
import type { Node, Edge, Connection } from "@xyflow/react";

export type DagNodeTypeName = "const" | "var" | "unary" | "binary" | "condition" | "expr" | "user_input" | "call";

export interface DagNodeData {
  label: string;
  nodeType: DagNodeTypeName;
  value?: number;
  path?: string;
  op?: string;
  lhs?: string;
  rhs?: string;
  cond?: string;
  true_val?: string;
  false_val?: string;
  expr?: string;
  inputs?: Record<string, string>;
  subgraph?: string;
  bindings?: Record<string, string>;
  default?: number;
  min?: number;
  max?: number;
  step?: number;
  [key: string]: unknown;
}

const NODE_TYPE_COLORS: Record<string, string> = {
  const: "#4caf50",
  var: "#2196f3",
  unary: "#ff9800",
  binary: "#ff9800",
  condition: "#f44336",
  expr: "#9c27b0",
  user_input: "#00bcd4",
  call: "#e91e63",
  output: "#9c27b0",
  default: "#616161",
};

export function getNodeColor(nodeType: string): string {
  return NODE_TYPE_COLORS[nodeType] ?? NODE_TYPE_COLORS.default;
}

export function dagToFlow(dag: Record<string, unknown>): { nodes: Node<DagNodeData>[]; edges: Edge[] } {
  const nodes: Node<DagNodeData>[] = [];
  const edges: Edge[] = [];
  const rawNodes = (dag.nodes ?? dag) as Record<string, Record<string, unknown>>;

  let ix = 0;
  for (const [id, n] of Object.entries(rawNodes)) {
    const nodeType = (n.type as string) || "?";
    const data: DagNodeData = {
      label: (n.label as string) || id,
      nodeType: nodeType as DagNodeTypeName,
    };
    if (nodeType === "const") data.value = n.value as number;
    if (nodeType === "var") data.path = n.path as string;
    if (nodeType === "unary" || nodeType === "binary") {
      data.op = n.op as string;
      if (nodeType === "unary") data.lhs = n.input as string;
      if (nodeType === "binary") { data.lhs = n.lhs as string; data.rhs = n.rhs as string; }
    }
    if (nodeType === "condition") {
      data.cond = n.cond as string;
      data.true_val = n.true_val as string;
      data.false_val = n.false_val as string;
    }
    if (nodeType === "expr") {
      data.expr = n.expr as string;
      data.inputs = n.inputs as Record<string, string> || {};
      data.path = n.path as string;
    }
    if (nodeType === "user_input") {
      data.default = n.default as number;
      data.min = n.min as number;
      data.max = n.max as number;
      data.step = n.step as number;
    }
    if (nodeType === "call") {
      data.subgraph = n.subgraph as string;
      data.bindings = n.bindings as Record<string, string> || {};
    }

    nodes.push({
      id,
      position: { x: 50 + (ix % 4) * 220, y: 50 + Math.floor(ix / 4) * 140 },
      data,
      type: "dagNode",
    });

    const inputs = n.inputs as Record<string, string> | undefined;
    if (inputs) {
      for (const [inputName, refId] of Object.entries(inputs)) {
        edges.push({ id: `${refId}->${id}__${inputName}`, source: String(refId), target: id, sourceHandle: undefined, targetHandle: inputName, label: inputName, animated: true });
      }
    }
    if (nodeType === "unary" && n.input) {
      edges.push({ id: `${n.input}->${id}`, source: String(n.input), target: id, animated: true });
    }
    if (nodeType === "binary") {
      if (n.lhs) edges.push({ id: `${n.lhs}->${id}__lhs`, source: String(n.lhs), target: id, sourceHandle: undefined, targetHandle: "lhs", label: "lhs", animated: true });
      if (n.rhs) edges.push({ id: `${n.rhs}->${id}__rhs`, source: String(n.rhs), target: id, sourceHandle: undefined, targetHandle: "rhs", label: "rhs", animated: true });
    }
    if (nodeType === "condition") {
      if (n.cond) edges.push({ id: `${n.cond}->${id}__cond`, source: String(n.cond), target: id, sourceHandle: undefined, targetHandle: "cond", label: "cond", animated: true });
      if (n.true_val) edges.push({ id: `${n.true_val}->${id}__true`, source: String(n.true_val), target: id, sourceHandle: undefined, targetHandle: "true", label: "true", animated: true });
      if (n.false_val) edges.push({ id: `${n.false_val}->${id}__false`, source: String(n.false_val), target: id, sourceHandle: undefined, targetHandle: "false", label: "false", animated: true });
    }
    if (nodeType === "call") {
      const bindings = (n.bindings as Record<string, string>) || {};
      for (const [param, sourceId] of Object.entries(bindings)) {
        edges.push({ id: `${sourceId}->${id}__${param}`, source: String(sourceId), target: id, sourceHandle: undefined, targetHandle: param, label: param, animated: true });
      }
    }
    ix++;
  }
  return { nodes, edges };
}

export function flowToDag(nodes: Node<DagNodeData>[], edges: Edge[]): Record<string, unknown> {
  const dagNodes: Record<string, Record<string, unknown>> = {};
  const edgeMap: Record<string, Edge[]> = {};
  for (const e of edges) {
    if (!edgeMap[e.target]) edgeMap[e.target] = [];
    edgeMap[e.target].push(e);
  }

  for (const n of nodes) {
    const d = n.data;
    const raw: Record<string, unknown> = { type: d.nodeType };
    if (d.label && d.label !== n.id) raw.label = d.label;

    const incoming = edgeMap[n.id] || [];
    switch (d.nodeType) {
      case "const":
        raw.value = d.value ?? 0;
        break;
      case "var":
        raw.path = d.path || n.id;
        break;
      case "unary": {
        raw.op = d.op || "neg";
        const inputEdge = incoming.find((e) => !e.targetHandle || e.targetHandle === "input");
        raw.input = inputEdge ? inputEdge.source : undefined;
        break;
      }
      case "binary": {
        raw.op = d.op || "+";
        const lhsEdge = incoming.find((e) => e.targetHandle === "lhs");
        const rhsEdge = incoming.find((e) => e.targetHandle === "rhs");
        if (lhsEdge) raw.lhs = lhsEdge.source;
        if (rhsEdge) raw.rhs = rhsEdge.source;
        break;
      }
      case "condition": {
        const condEdge = incoming.find((e) => e.targetHandle === "cond");
        const trueEdge = incoming.find((e) => e.targetHandle === "true");
        const falseEdge = incoming.find((e) => e.targetHandle === "false");
        if (condEdge) raw.cond = condEdge.source;
        if (trueEdge) raw.true_val = trueEdge.source;
        if (falseEdge) raw.false_val = falseEdge.source;
        break;
      }
      case "expr": {
        raw.expr = d.expr || "0";
        const inputs: Record<string, string> = {};
        for (const e of incoming) {
          if (e.targetHandle && e.targetHandle !== "lhs" && e.targetHandle !== "rhs" && e.targetHandle !== "cond" && e.targetHandle !== "true" && e.targetHandle !== "false") {
            inputs[e.targetHandle] = e.source;
          }
        }
        if (Object.keys(inputs).length > 0) raw.inputs = inputs;
        break;
      }
      case "user_input":
        raw.default = d.default ?? 0;
        raw.min = d.min ?? 0;
        raw.max = d.max ?? 100;
        raw.step = d.step ?? 1;
        break;
      case "call":
        raw.subgraph = d.subgraph || "";
        raw.bindings = d.bindings || {};
        break;
    }
    dagNodes[n.id] = raw;
  }

  return { nodes: dagNodes };
}

let _nextId = 100;
function generateId(): string {
  return `node_${_nextId++}`;
}

interface EditorStoreState {
  nodes: Node<DagNodeData>[];
  edges: Edge[];
  dagJson: string;
  dagName: string;
  error: string | null;
  setNodes: (nodes: Node<DagNodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (nodeType: DagNodeTypeName, position: { x: number; y: number }) => string;
  updateNodeData: (nodeId: string, data: Partial<DagNodeData>) => void;
  deleteSelected: () => void;
  onConnect: (connection: Connection) => void;
  parseAndRender: () => void;
  saveToJson: () => string;
  setDagJson: (json: string) => void;
  setDagName: (name: string) => void;
}

export const useEditorStore = create<EditorStoreState>((set, get) => ({
  nodes: [],
  edges: [],
  dagJson: "",
  dagName: "新DAG图",
  error: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  addNode: (nodeType, position) => {
    const id = generateId();
    const data: DagNodeData = {
      label: id,
      nodeType,
    };
    if (nodeType === "const") data.value = 0;
    if (nodeType === "var") data.path = "computed.新变量";
    if (nodeType === "unary" || nodeType === "binary") data.op = nodeType === "binary" ? "+" : "neg";
    if (nodeType === "expr") { data.expr = "0"; data.inputs = {}; }
    if (nodeType === "user_input") { data.default = 0; data.min = 0; data.max = 100; data.step = 1; }
    if (nodeType === "call") { data.subgraph = ""; data.bindings = {}; }

    const newNode: Node<DagNodeData> = { id, position, data, type: "dagNode" };
    set((s) => ({ nodes: [...s.nodes, newNode] }));
    return id;
  },

  updateNodeData: (nodeId, data) => {
    set((s) => ({
      nodes: s.nodes.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n)),
    }));
  },

  deleteSelected: () => {
    const { nodes, edges } = get();
    const selectedIds = new Set(nodes.filter((n) => n.selected).map((n) => n.id));
    const selectedEdgeIds = new Set(edges.filter((e) => e.selected).map((e) => e.id));
    set({
      nodes: nodes.filter((n) => !selectedIds.has(n.id)),
      edges: edges.filter((e) => !selectedEdgeIds.has(e.id) && !selectedIds.has(e.source) && !selectedIds.has(e.target)),
    });
  },

  onConnect: (connection) => {
    const edgeId = `${connection.source}->${connection.target}${connection.targetHandle ? "__" + connection.targetHandle : ""}`;
    const newEdge: Edge = {
      id: edgeId,
      source: connection.source!,
      target: connection.target!,
      sourceHandle: connection.sourceHandle,
      targetHandle: connection.targetHandle,
      animated: true,
    };
    if (connection.targetHandle) {
      newEdge.label = connection.targetHandle;
    }
    set((s) => ({ edges: [...s.edges, newEdge] }));
  },

  parseAndRender: () => {
    const { dagJson } = get();
    try {
      const dag = JSON.parse(dagJson);
      const dagName = (dag.name as string) || "新DAG图";
      const { nodes, edges } = dagToFlow(dag);
      set({ nodes, edges, dagName, error: null });
    } catch (e: unknown) {
      set({ error: String(e), nodes: [], edges: [] });
    }
  },

  saveToJson: () => {
    const { nodes, edges, dagName } = get();
    const dagNodes = flowToDag(nodes, edges);
    const result: Record<string, unknown> = {
      schema_version: "dag-v1",
      name: dagName,
      nodes: dagNodes.nodes,
      outputs: {},
    };
    return JSON.stringify(result, null, 2);
  },

  setDagJson: (json) => set({ dagJson: json, error: null }),
  setDagName: (name) => set({ dagName: name }),
}));
