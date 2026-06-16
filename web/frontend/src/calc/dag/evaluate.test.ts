import { describe, it, expect } from "vitest";
import { evaluateGraph } from "./evaluate";
import type { DAGGraphRaw } from "./types";

function makeGraph(nodes: Record<string, unknown>, outputs: Record<string, unknown> = {}): DAGGraphRaw {
  return {
    schema_version: "1",
    name: "test",
    variables: {},
    subgraphs: {},
    nodes: nodes as DAGGraphRaw["nodes"],
    outputs: outputs as DAGGraphRaw["outputs"],
  };
}

describe("evaluateGraph", () => {
  it("常数节点求值", () => {
    const result = evaluateGraph(makeGraph({ a: { type: "const", value: 42 } }), {});
    expect(result.node_values.a).toBe(42);
  });

  it("变量节点从上下文取值", () => {
    const result = evaluateGraph(makeGraph({ x: { type: "var", path: "foo" } }), { foo: 100 });
    expect(result.node_values.x).toBe(100);
  });

  it("变量在上下文中不存在时抛出错误", () => {
    expect(() => evaluateGraph(makeGraph({ x: { type: "var", path: "missing" } }), {})).toThrow(
      "未在上下文中找到",
    );
  });

  it("加法运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 3 },
        b: { type: "const", value: 4 },
        c: { type: "binary", op: "+", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBe(7);
  });

  it("减法运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 10 },
        b: { type: "const", value: 3 },
        c: { type: "binary", op: "-", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBe(7);
  });

  it("乘法运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 6 },
        b: { type: "const", value: 7 },
        c: { type: "binary", op: "*", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBe(42);
  });

  it("除法运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 10 },
        b: { type: "const", value: 3 },
        c: { type: "binary", op: "/", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBeCloseTo(3.333, 2);
  });

  it("幂运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 2 },
        b: { type: "const", value: 3 },
        c: { type: "binary", op: "^", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBe(8);
  });

  it("max 运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 5 },
        b: { type: "const", value: 10 },
        c: { type: "binary", op: "max", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBe(10);
  });

  it("min 运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 5 },
        b: { type: "const", value: 10 },
        c: { type: "binary", op: "min", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBe(5);
  });

  it("mod 运算", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 10 },
        b: { type: "const", value: 3 },
        c: { type: "binary", op: "mod", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.node_values.c).toBe(1);
  });

  it("输出列表过滤", () => {
    const result = evaluateGraph(
      makeGraph(
        {
          a: { type: "const", value: 1 },
          b: { type: "const", value: 2 },
          c: { type: "const", value: 3 },
        },
        { out_a: { node: "a" }, out_c: { node: "c" } },
      ),
      {},
    );
    expect(result.outputs).toEqual({ out_a: 1, out_c: 3 });
  });

  it("链式运算（a + b * c）", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 1 },
        b: { type: "const", value: 2 },
        c: { type: "const", value: 3 },
        mul1: { type: "binary", op: "*", lhs: "b", rhs: "c" },
        sum1: { type: "binary", op: "+", lhs: "a", rhs: "mul1" },
      }),
      {},
    );
    expect(result.node_values.mul1).toBe(6);
    expect(result.node_values.sum1).toBe(7);
  });

  it("execution_order 返回拓扑序", () => {
    const result = evaluateGraph(
      makeGraph({
        a: { type: "const", value: 1 },
        b: { type: "const", value: 2 },
        sum: { type: "binary", op: "+", lhs: "a", rhs: "b" },
      }),
      {},
    );
    expect(result.execution_order).toHaveLength(3);
    expect(result.execution_order.indexOf("a")).toBeLessThan(result.execution_order.indexOf("sum"));
    expect(result.execution_order.indexOf("b")).toBeLessThan(result.execution_order.indexOf("sum"));
  });

  it("嵌套路径变量解析（a.b.c）", () => {
    const result = evaluateGraph(
      makeGraph({ x: { type: "var", path: "a.b.c" } }),
      { a: { b: { c: 42 } } },
    );
    expect(result.node_values.x).toBe(42);
  });
});
