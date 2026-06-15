import { describe, it, expect } from "vitest";
import { expandSubgraphs } from "./expand";
import type { DAGGraphRaw } from "./types";

describe("expandSubgraphs", () => {
  it("空图保持结构完整", () => {
    const graph: DAGGraphRaw = {
      schema_version: "1",
      name: "empty",
      variables: {},
      subgraphs: {},
      nodes: {},
      outputs: {},
    };
    const result = expandSubgraphs(graph);
    expect(result.nodes).toEqual({});
    expect(result.outputs).toEqual({});
  });

  it("常数节点保持不变", () => {
    const graph: DAGGraphRaw = {
      schema_version: "1",
      name: "test",
      variables: {},
      subgraphs: {},
      nodes: {
        a: { type: "const", value: 42 },
        b: { type: "const", value: 100 },
      },
      outputs: {},
    };
    const result = expandSubgraphs(graph);
    expect(Object.keys(result.nodes)).toHaveLength(2);
  });

  it("变量节点保持不变", () => {
    const graph: DAGGraphRaw = {
      schema_version: "1",
      name: "test",
      variables: {},
      subgraphs: {},
      nodes: {
        v: { type: "var", path: "x" },
      },
      outputs: {},
    };
    const result = expandSubgraphs(graph);
    expect(Object.keys(result.nodes)).toHaveLength(1);
    expect(result.nodes.v?.type).toBe("var");
  });

  it("二元节点保持不变", () => {
    const graph: DAGGraphRaw = {
      schema_version: "1",
      name: "test",
      variables: {},
      subgraphs: {},
      nodes: {
        a: { type: "const", value: 1 },
        b: { type: "const", value: 2 },
        sum: { type: "binary", op: "+", lhs: "a", rhs: "b" },
      },
      outputs: {},
    };
    const result = expandSubgraphs(graph);
    expect(Object.keys(result.nodes)).toHaveLength(3);
  });

  it("展开 call 节点为内联节点", () => {
    const graph: DAGGraphRaw = {
      schema_version: "1",
      name: "test",
      variables: {},
      subgraphs: {
        my_sub: {
          nodes: {
            inner: { type: "const", value: 10 },
          },
          outputs: { out: { node: "inner", is_primary: true } },
        },
      },
      nodes: {
        call1: { type: "call", subgraph: "my_sub", bindings: {} },
      },
      outputs: {},
    };
    const result = expandSubgraphs(graph);
    // call1 展开后变成 call1.inner
    expect(Object.keys(result.nodes)).toEqual(["call1.inner"]);
  });

  it("call 节点 output 重定向", () => {
    const graph: DAGGraphRaw = {
      schema_version: "1",
      name: "test",
      variables: {},
      subgraphs: {
        add_sub: {
          nodes: {
            lhs: { type: "const", value: 2 },
            rhs: { type: "const", value: 3 },
            sum: { type: "binary", op: "+", lhs: "lhs", rhs: "rhs" },
          },
          outputs: { result: { node: "sum", is_primary: true } },
        },
      },
      nodes: {
        calc: { type: "call", subgraph: "add_sub", bindings: {} },
        consumer: { type: "const", value: 1 },
      },
      outputs: {},
    };
    const result = expandSubgraphs(graph);
    expect(Object.keys(result.nodes)).toContain("calc.lhs");
    expect(Object.keys(result.nodes)).toContain("calc.rhs");
    expect(Object.keys(result.nodes)).toContain("calc.sum");
  });

  it("嵌套子图递归展开", () => {
    const graph: DAGGraphRaw = {
      schema_version: "1",
      name: "test",
      variables: {},
      subgraphs: {
        leaf_sub: {
          nodes: { leaf: { type: "const", value: 99 } },
          outputs: { result: { node: "leaf" } },
        },
        outer_sub: {
          nodes: { inner_call: { type: "call", subgraph: "leaf_sub", bindings: {} } },
          outputs: { result: { node: "inner_call" } },
        },
      },
      nodes: {
        top: { type: "call", subgraph: "outer_sub", bindings: {} },
      },
      outputs: {},
    };
    const result = expandSubgraphs(graph);
    const allNodeIds = Object.keys(result.nodes);
    expect(allNodeIds.some((id) => id.endsWith(".leaf"))).toBe(true);
  });
});
