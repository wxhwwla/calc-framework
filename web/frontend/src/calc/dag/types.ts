/** DAG JSON 结构（终末地仅 const / var / binary / call）。 */

export interface DAGOutputDef {
  node: string;
  label?: string;
  is_primary?: boolean;
  format?: string;
}

export interface DAGSubgraph {
  description?: string;
  parameters?: Record<string, unknown>;
  nodes: Record<string, DAGNodeRaw>;
  outputs: Record<string, DAGOutputDef>;
}

export interface DAGGraphRaw {
  schema_version: string;
  name: string;
  description?: string;
  variables: Record<string, unknown>;
  subgraphs: Record<string, DAGSubgraph>;
  nodes: Record<string, DAGNodeRaw>;
  outputs: Record<string, DAGOutputDef>;
}

export type DAGNodeRaw =
  | ConstNodeRaw
  | VarNodeRaw
  | BinaryNodeRaw
  | CallNodeRaw;

export interface ConstNodeRaw {
  type: "const";
  value: number;
  label?: string;
}

export interface VarNodeRaw {
  type: "var";
  path: string;
  label?: string;
}

export interface BinaryNodeRaw {
  type: "binary";
  op: string;
  lhs: string;
  rhs: string;
  label?: string;
}

export interface CallNodeRaw {
  type: "call";
  subgraph: string;
  bindings: Record<string, string>;
  label?: string;
}

export interface ExpandedGraph {
  schema_version: string;
  name: string;
  description?: string;
  variables: Record<string, unknown>;
  subgraphs: Record<string, DAGSubgraph>;
  nodes: Record<string, DAGNodeRaw>;
  outputs: Record<string, DAGOutputDef>;
}

export interface DAGEvalResult {
  outputs: Record<string, number>;
  node_values: Record<string, number>;
  execution_order: string[];
}
