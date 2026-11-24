import { beforeEach, describe, expect, it } from "vitest";
import { useEditorStore } from "./editorStore";

const dag = {
  schema_version: "dag-v1",
  name: "完整图",
  variables: {
    "user_input.x": { type: "float", source: "user_input", default: 1 },
  },
  nodes: {
    x: { type: "user_input", default: 1 },
    out: { type: "expr", expr: "x + 1", inputs: { x: "x" } },
  },
  outputs: {
    result: { node: "out", label: "结果", is_primary: true },
  },
  subgraphs: {
    inner: {
      nodes: { one: { type: "const", value: 1 } },
      outputs: { value: { node: "one" } },
    },
  },
};

describe("editorStore DAG roundtrip", () => {
  beforeEach(() => {
    useEditorStore.setState({
      nodes: [],
      edges: [],
      dagJson: "",
      dagName: "新DAG图",
      error: null,
      variables: {},
      outputs: {},
      subgraphs: {},
    });
  });

  it("preserves variables, outputs and subgraphs on export", () => {
    const store = useEditorStore.getState();
    store.setDagJson(JSON.stringify(dag));
    store.parseAndRender();

    const exported = JSON.parse(useEditorStore.getState().saveToJson());

    expect(exported.variables).toEqual(dag.variables);
    expect(exported.outputs).toEqual(dag.outputs);
    expect(exported.subgraphs).toEqual(dag.subgraphs);
    expect(exported.nodes.out.inputs).toEqual({ x: "x" });
  });

  it("removes deleted edges from export", () => {
    const store = useEditorStore.getState();
    store.setDagJson(JSON.stringify(dag));
    store.parseAndRender();
    useEditorStore.getState().setEdges([]);

    const exported = JSON.parse(useEditorStore.getState().saveToJson());

    expect(exported.nodes.out.inputs).toBeUndefined();
  });

  it("rebuilds call bindings and removes dangling outputs after deleting edges", () => {
    const callDag = {
      name: "调用图",
      description: "顶层说明",
      nodes: {
        one: { type: "const", value: 1, description: "常量说明" },
        call: { type: "call", subgraph: "inner", bindings: { x: "one" } },
      },
      outputs: { result: { node: "call", label: "结果" } },
      subgraphs: dag.subgraphs,
    };
    const store = useEditorStore.getState();
    store.setDagJson(JSON.stringify(callDag));
    store.parseAndRender();
    useEditorStore.getState().setEdges([]);
    useEditorStore.getState().deleteNodes(["call"]);

    const exported = JSON.parse(useEditorStore.getState().saveToJson());

    expect(exported.nodes.call).toBeUndefined();
    expect(exported.outputs).toEqual({});
    expect(exported.outputs).toEqual({});
    expect(exported.description).toBe("顶层说明");
    expect(exported.nodes.one.description).toBe("常量说明");
  });

  it("accepts the unary lhs handle when exporting", () => {
    const unaryDag = {
      name: "一元图",
      nodes: {
        one: { type: "const", value: 1 },
        neg: { type: "unary", op: "neg", input: "one" },
      },
    };
    const store = useEditorStore.getState();
    store.setDagJson(JSON.stringify(unaryDag));
    store.parseAndRender();
    const edge = useEditorStore.getState().edges[0];
    useEditorStore.getState().setEdges([{ ...edge, targetHandle: "lhs" }]);

    const exported = JSON.parse(useEditorStore.getState().saveToJson());

    expect(exported.nodes.neg.input).toBe("one");
  });
});
