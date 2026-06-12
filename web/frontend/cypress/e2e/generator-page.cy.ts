/// <reference types="cypress" />

describe("生成器页 GeneratorPage", () => {
  beforeEach(() => {
    cy.visit("/generator");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("AI 计算器生成器").should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("AI 生成器").should("be.visible");
  });

  it("显示步骤导航", () => {
    cy.contains("选择模板").should("be.visible");
    cy.contains("配置公式").should("be.visible");
    cy.contains("生成计算器").should("be.visible");
  });

  it("显示模板列表", () => {
    cy.contains("简单伤害计算").should("be.visible");
  });

  it("显示公式输入区域", () => {
    cy.contains("公式描述").should("be.visible");
  });

  it("选择模板后进入下一步", () => {
    cy.contains("简单伤害计算").click();
    cy.contains("下一步").should("be.visible");
  });
});
