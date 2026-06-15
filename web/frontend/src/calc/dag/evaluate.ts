import { expandSubgraphs } from "./expand";
import { topologicalSort } from "./topo";
import type { DAGGraphRaw, DAGEvalResult, DAGNodeRaw } from "./types";

const BINARY_OPS: Record<string, (a: number, b: number) => number> = {
  "+": (a, b) => a + b,
  "-": (a, b) => a - b,
  "*": (a, b) => a * b,
  "/": (a, b) => a / b,
  "^": (a, b) => a ** b,
  min: (a, b) => Math.min(a, b),
  max: (a, b) => Math.max(a, b),
  mod: (a, b) => (b !== 0 ? a % b : 0),
};

function resolvePath(context: Record<string, unknown>, path: string): unknown {
  const parts = path.split(".");
  let cursor: unknown = context;
  for (const part of parts) {
    if (cursor === null || cursor === undefined || typeof cursor !== "object") {
      return undefined;
    }
    cursor = (cursor as Record<string, unknown>)[part];
    if (cursor === undefined || cursor === null) {
      return undefined;
    }
  }
  return cursor;
}

function evalSingleNode(
  node: DAGNodeRaw,
  values: Record<string, number>,
  context: Record<string, unknown>,
): number {
  if (node.type === "const") {
    return node.value;
  }
  if (node.type === "var") {
    const val = resolvePath(context, node.path);
    if (val === undefined || val === null) {
      throw new Error(`变量 ${node.path} 未在上下文中找到`);
    }
    return Number(val);
  }
  if (node.type === "binary") {
    const lhs = values[node.lhs];
    const rhs = values[node.rhs];
    if (lhs === undefined || rhs === undefined) {
      throw new Error(`二元节点缺少输入: lhs=${node.lhs} rhs=${node.rhs}`);
    }
    const op = BINARY_OPS[node.op];
    if (!op) {
      throw new Error(`未知二元运算符: ${node.op}`);
    }
    return op(lhs, rhs);
  }
  throw new Error(`不支持的节点类型: ${(node as DAGNodeRaw).type}`);
}

/** 展开子图并求值，返回 outputs / node_values / execution_order。 */
export function evaluateGraph(
  graph: DAGGraphRaw,
  context: Record<string, unknown>,
): DAGEvalResult {
  const expanded = expandSubgraphs(graph);
  const order = topologicalSort(expanded);
  const values: Record<string, number> = {};

  for (const nid of order) {
    const node = expanded.nodes[nid];
    if (!node || node.type === "call") {
      throw new Error(`节点 ${nid} 无效或未展开`);
    }
    values[nid] = evalSingleNode(node, values, context);
  }

  const outputs: Record<string, number> = {};
  for (const [oid, odef] of Object.entries(expanded.outputs)) {
    const val = values[odef.node];
    if (val !== undefined) {
      outputs[oid] = val;
    }
  }

  return {
    outputs,
    node_values: values,
    execution_order: order,
  };
}
