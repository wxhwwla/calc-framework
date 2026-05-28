import { create } from "zustand";
import type { Node, Edge } from "@xyflow/react";

interface DagNodeData {
  label: string;
  nodeType: string;
  expr?: string;
  [key: string]: unknown;
}

interface EditorStoreState {
  nodes: Node<DagNodeData>[];
  edges: Edge[];
  dagJson: string;
  error: string | null;
  setDagJson: (json: string) => void;
  parseAndRender: () => void;
}

function dagNodeToFlow(dag: Record<string, any>): { nodes: Node<DagNodeData>[]; edges: Edge[] } {
  const nodes: Node<DagNodeData>[] = [];
  const edges: Edge[] = [];
  const graph = dag.nodes || dag;

  let ix = 0;
  for (const [id, node] of Object.entries(graph)) {
    const n = node as Record<string, any>;
    nodes.push({
      id,
      position: { x: 50 + (ix % 4) * 220, y: 50 + Math.floor(ix / 4) * 140 },
      data: {
        label: id,
        nodeType: n.type || "?",
        expr: n.expr || n.path || n.cond || "",
      },
      type: "default",
    });

    if (n.inputs) {
      for (const [inputName, inputRef] of Object.entries(n.inputs)) {
        edges.push({
          id: `${inputRef}->${id}`,
          source: String(inputRef),
          target: id,
          label: inputName,
          animated: true,
        });
      }
    }
    ix++;
  }

  return { nodes, edges };
}

export const useEditorStore = create<EditorStoreState>((set, get) => ({
  nodes: [],
  edges: [],
  dagJson: "",
  error: null,

  setDagJson: (json: string) => {
    set({ dagJson: json, error: null });
  },

  parseAndRender: () => {
    const { dagJson } = get();
    try {
      const dag = JSON.parse(dagJson);
      const { nodes, edges } = dagNodeToFlow(dag);
      set({ nodes, edges, error: null });
    } catch (e: unknown) {
      set({ error: String(e), nodes: [], edges: [] });
    }
  },
}));
