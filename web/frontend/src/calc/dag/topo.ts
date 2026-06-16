import type { DAGNodeRaw, ExpandedGraph } from "./types";

export class DAGCycleError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DAGCycleError";
  }
}

function nodeDependencies(node: DAGNodeRaw): string[] {
  if (node.type === "binary") {
    return [node.lhs, node.rhs];
  }
  return [];
}

/** Kahn 拓扑排序，返回节点执行顺序。 */
export function topologicalSort(graph: ExpandedGraph): string[] {
  const inDegree: Record<string, number> = {};
  const adj: Record<string, string[]> = {};

  for (const nid of Object.keys(graph.nodes)) {
    inDegree[nid] = 0;
    adj[nid] = [];
  }

  for (const [nid, node] of Object.entries(graph.nodes)) {
    for (const ref of nodeDependencies(node)) {
      if (adj[ref]) {
        adj[ref].push(nid);
        inDegree[nid] += 1;
      }
    }
  }

  const queue = Object.entries(inDegree)
    .filter(([, deg]) => deg === 0)
    .map(([nid]) => nid);
  const order: string[] = [];

  while (queue.length > 0) {
    const nid = queue.shift()!;
    order.push(nid);
    for (const downstream of adj[nid] ?? []) {
      inDegree[downstream] -= 1;
      if (inDegree[downstream] === 0) {
        queue.push(downstream);
      }
    }
  }

  if (order.length !== Object.keys(graph.nodes).length) {
    const remaining = Object.entries(inDegree)
      .filter(([, deg]) => deg > 0)
      .map(([nid]) => nid);
    throw new DAGCycleError(`循环依赖: ${remaining.join(", ")}`);
  }

  return order;
}
