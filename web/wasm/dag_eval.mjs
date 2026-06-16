/**
 * DAG 展开与求值（Node 校验用，与 web/frontend/src/calc/dag 逻辑对齐）。
 * SPDX-License-Identifier: AGPL-3.0
 */

const BINARY_OPS = {
  "+": (a, b) => a + b,
  "-": (a, b) => a - b,
  "*": (a, b) => a * b,
  "/": (a, b) => a / b,
  "^": (a, b) => a ** b,
  min: (a, b) => Math.min(a, b),
  max: (a, b) => Math.max(a, b),
  mod: (a, b) => (b !== 0 ? a % b : 0),
};

function deepCopyNode(node) {
  return JSON.parse(JSON.stringify(node));
}

function mapRef(ref, prefix) {
  return ref.startsWith(`${prefix}.`) ? ref : `${prefix}.${ref}`;
}

function prefixedNode(node, prefix) {
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

function applyRefMapToNode(node, refMap) {
  const resolve = (ref) => {
    const visited = new Set();
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

export function expandSubgraphs(graph) {
  const expanded = {
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

  const refMap = {};
  let changed = true;

  while (changed) {
    changed = false;
    const callItems = Object.entries(expanded.nodes).filter(([, node]) => node.type === "call");

    for (const [callId, callNode] of callItems) {
      const sub = graph.subgraphs[callNode.subgraph];
      if (!sub) {
        delete expanded.nodes[callId];
        continue;
      }
      changed = true;
      delete expanded.nodes[callId];

      for (const [snid, snode] of Object.entries(sub.nodes)) {
        expanded.nodes[`${callId}.${snid}`] = prefixedNode(snode, callId);
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

  const newOutputs = {};
  for (const [oid, odef] of Object.entries(graph.outputs)) {
    const resolved = refMap[odef.node] ?? odef.node;
    if (expanded.nodes[resolved]) {
      newOutputs[oid] = { ...odef, node: resolved };
    } else {
      newOutputs[oid] = odef;
    }
  }
  expanded.outputs = newOutputs;
  return expanded;
}

function nodeDependencies(node) {
  if (node.type === "binary") {
    return [node.lhs, node.rhs];
  }
  return [];
}

export function topologicalSort(graph) {
  const inDegree = {};
  const adj = {};
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
  const order = [];
  while (queue.length > 0) {
    const nid = queue.shift();
    order.push(nid);
    for (const downstream of adj[nid] ?? []) {
      inDegree[downstream] -= 1;
      if (inDegree[downstream] === 0) {
        queue.push(downstream);
      }
    }
  }
  if (order.length !== Object.keys(graph.nodes).length) {
    throw new Error("DAG 循环依赖");
  }
  return order;
}

function resolvePath(context, path) {
  const parts = path.split(".");
  let cursor = context;
  for (const part of parts) {
    if (cursor === null || cursor === undefined || typeof cursor !== "object") {
      return undefined;
    }
    cursor = cursor[part];
    if (cursor === undefined || cursor === null) {
      return undefined;
    }
  }
  return cursor;
}

function evalSingleNode(node, values, context) {
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
    const op = BINARY_OPS[node.op];
    if (op === undefined) {
      throw new Error(`未知运算符 ${node.op}`);
    }
    return op(lhs, rhs);
  }
  throw new Error(`不支持的节点类型 ${node.type}`);
}

export function evaluateGraph(graph, context) {
  const expanded = expandSubgraphs(graph);
  const order = topologicalSort(expanded);
  const values = {};
  for (const nid of order) {
    const node = expanded.nodes[nid];
    values[nid] = evalSingleNode(node, values, context);
  }
  const outputs = {};
  for (const [oid, odef] of Object.entries(expanded.outputs)) {
    const val = values[odef.node];
    if (val !== undefined) {
      outputs[oid] = val;
    }
  }
  return { outputs, node_values: values, execution_order: order };
}
