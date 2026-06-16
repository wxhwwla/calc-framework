import type {
  CallNodeRaw,
  DAGGraphRaw,
  DAGNodeRaw,
  DAGOutputDef,
  ExpandedGraph,
} from "./types";

function deepCopyNode(node: DAGNodeRaw): DAGNodeRaw {
  return JSON.parse(JSON.stringify(node)) as DAGNodeRaw;
}

function mapRef(ref: string, prefix: string): string {
  return ref.startsWith(`${prefix}.`) ? ref : `${prefix}.${ref}`;
}

function prefixedNode(node: DAGNodeRaw, prefix: string): DAGNodeRaw {
  const n = deepCopyNode(node);
  if (n.type === "binary") {
    n.lhs = mapRef(n.lhs, prefix);
    n.rhs = mapRef(n.rhs, prefix);
  } else if (n.type === "var") {
    n.path = mapRef(n.path, prefix);
  } else if (n.type === "call") {
    n.bindings = Object.fromEntries(
      Object.entries(n.bindings).map(([k, v]) => [k, mapRef(v, prefix)]),
    );
  }
  return n;
}

function applyRefMapToNode(node: DAGNodeRaw, refMap: Record<string, string>): void {
  const resolve = (ref: string): string => {
    const visited = new Set<string>();
    let current = ref;
    while (refMap[current] !== undefined) {
      if (visited.has(current)) break;
      visited.add(current);
      current = refMap[current];
    }
    return current;
  };

  if (node.type === "binary") {
    node.lhs = resolve(node.lhs);
    node.rhs = resolve(node.rhs);
  } else if (node.type === "var") {
    node.path = resolve(node.path);
  } else if (node.type === "call") {
    node.bindings = Object.fromEntries(
      Object.entries(node.bindings).map(([k, v]) => [k, resolve(v)]),
    );
  }
}

function finalizeOutputs(
  expanded: ExpandedGraph,
  original: DAGGraphRaw,
  refMap: Record<string, string>,
): void {
  const newOutputs: Record<string, DAGOutputDef> = {};
  for (const [oid, odef] of Object.entries(original.outputs)) {
    const resolved = refMap[odef.node] ?? odef.node;
    if (expanded.nodes[resolved]) {
      newOutputs[oid] = { ...odef, node: resolved };
    } else {
      newOutputs[oid] = odef;
    }
  }
  expanded.outputs = newOutputs;
}

/** 将 call 节点内联为普通节点（对齐 Python expand_subgraphs）。 */
export function expandSubgraphs(graph: DAGGraphRaw): ExpandedGraph {
  const expanded: ExpandedGraph = {
    schema_version: graph.schema_version,
    name: graph.name,
    description: graph.description,
    variables: { ...graph.variables },
    subgraphs: { ...graph.subgraphs },
    nodes: {},
    outputs: {},
  };

  for (const [nid, node] of Object.entries(graph.nodes)) {
    expanded.nodes[nid] = deepCopyNode(node);
  }

  const refMap: Record<string, string> = {};
  let changed = true;

  while (changed) {
    changed = false;
    const callItems = Object.entries(expanded.nodes).filter(
      (entry): entry is [string, CallNodeRaw] => entry[1].type === "call",
    );

    for (const [callId, callNode] of callItems) {
      const sub = graph.subgraphs[callNode.subgraph];
      if (!sub) {
        delete expanded.nodes[callId];
        continue;
      }
      changed = true;
      delete expanded.nodes[callId];

      for (const [snid, snode] of Object.entries(sub.nodes)) {
        const prefixedId = `${callId}.${snid}`;
        expanded.nodes[prefixedId] = prefixedNode(snode, callId);
      }

      for (const [bindingName, targetNid] of Object.entries(callNode.bindings)) {
        if (targetNid) {
          refMap[`${callId}.${bindingName}`] = targetNid;
        }
      }

      for (const [subOid, subOdef] of Object.entries(sub.outputs)) {
        const resolved = `${callId}.${subOdef.node}`;
        const alias = `${callId}.${subOid}`;
        if (alias !== resolved) {
          refMap[alias] = resolved;
        }
      }

      const primaryOutputs = Object.values(sub.outputs).filter((o) => o.is_primary);
      const firstOutput = primaryOutputs[0] ?? Object.values(sub.outputs)[0];
      if (firstOutput) {
        const callOut = `${callId}.${firstOutput.node}`;
        if (callId !== callOut) {
          refMap[callId] = callOut;
        }
      }
    }
  }

  for (const node of Object.values(expanded.nodes)) {
    applyRefMapToNode(node, refMap);
  }

  finalizeOutputs(expanded, graph, refMap);
  return expanded;
}
