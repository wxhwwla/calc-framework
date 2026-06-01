/// <reference types="cypress" />

const sampleDagJson = JSON.stringify({
  name: "测试 DAG",
  nodes: {
    const_val: { type: "const", value: 100, label: "攻击力" },
    var_str: { type: "var", path: "character.力量", label: "力量" },
    sum_node: { type: "binary", op: "+", lhs: "const_val", rhs: "var_str", label: "求和" },
  },
}, null, 2);

describe("DAG 编辑器 EditorPage", () => {
  beforeEach(() => {
    cy.visit("/editor");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("DAG 公式图编辑器").should("be.visible");
  });

  it("显示节点面板", () => {
    cy.contains("节点面板").should("be.visible");
    cy.contains("常量").should("be.visible");
    cy.contains("变量").should("be.visible");
    cy.contains("表达式").should("be.visible");
    cy.contains("二元运算").should("be.visible");
  });

  it("显示所有 7 种节点类型", () => {
    const types = ["常量", "变量", "一元运算", "二元运算", "条件", "表达式", "用户输入"];
    types.forEach((t) => {
      cy.contains(t).should("be.visible");
    });
  });

  it("显示操作提示", () => {
    cy.contains("操作提示").should("be.visible");
    cy.contains("从节点面板拖拽到画布创建节点").should("be.visible");
    cy.contains("双击节点编辑属性").should("be.visible");
  });

  it("DAG JSON 文本区存在", () => {
    cy.get("textarea").should("be.visible");
    cy.contains("渲染").should("be.visible");
    cy.contains("导出 JSON").should("be.visible");
    cy.contains("加载示例").should("be.visible");
  });

  it("输入 JSON 后渲染按钮可用", () => {
    cy.get("textarea").first().clear();
    cy.get("textarea").first().type(sampleDagJson, { parseSpecialCharSequences: false });
    cy.contains("渲染").click();
  });

  it("清空按钮重置画布", () => {
    cy.contains("清空").click();
    cy.contains("0 个节点").should("be.visible");
  });

  it("DAG 名称输入框存在", () => {
    cy.get("input").first().should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("公式图编辑器").should("be.visible");
  });
});
