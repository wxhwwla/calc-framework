import { describe, it, expect } from "vitest";
import { topologicalSort, DAGCycleError } from "./topo";
import type { ExpandedGraph } from "./types";

function makeGraph(
  nodes: Record<string, unknown>,
): ExpandedGraph {
  return {
    schema_version: "1",
    name: "test",
    variables: {},
    subgraphs: {},
    nodes: nodes as ExpandedGraph["nodes"],
    outputs: {},
  };
}

function c(id: string, value: number): [string, unknown] {
  return [id, { type: "const", value }];
}

function b(id: string, lhs: string, rhs: string, op = "+"): [string, unknown] {
  return [id, { type: "binary", op, lhs, rhs }];
}

describe("topologicalSort", () => {
  it("空图返回空数组", () => {
    expect(topologicalSort(makeGraph({}))).toEqual([]);
  });

  it("单节点无依赖", () => {
    const g = makeGraph(Object.fromEntries([c("a", 1)]));
    expect(topologicalSort(g)).toEqual(["a"]);
  });

  it("简单链式依赖", () => {
    const g = makeGraph(Object.fromEntries([c("a", 1), c("b", 2), b("sum", "a", "b")]));
    const order = topologicalSort(g);
    expect(order).toContain("a");
    expect(order).toContain("b");
    expect(order.indexOf("sum")).toBeGreaterThan(order.indexOf("a"));
    expect(order.indexOf("sum")).toBeGreaterThan(order.indexOf("b"));
  });

  it("检测环并抛出 DAGCycleError", () => {
    const g = makeGraph(Object.fromEntries([b("a", "b", "c"), b("b", "c", "a"), b("c", "a", "b")]));
    expect(() => topologicalSort(g)).toThrow(DAGCycleError);
  });

  it("检测自环", () => {
    const g = makeGraph(Object.fromEntries([b("a", "a", "a")]));
    expect(() => topologicalSort(g)).toThrow(DAGCycleError);
  });

  it("孤立节点不影响排序", () => {
    const g = makeGraph(Object.fromEntries([c("a", 1), c("b", 2), c("c", 3), b("sum", "a", "b")]));
    const order = topologicalSort(g);
    expect(order).toHaveLength(4);
    expect(order).toContain("a");
    expect(order).toContain("b");
    expect(order).toContain("c");
    expect(order).toContain("sum");
  });
});
