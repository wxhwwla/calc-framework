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
    cy.contains("填写游戏信息").should("be.visible");
    cy.contains("预览与生成").should("be.visible");
    cy.contains("导出").should("be.visible");
  });

  it("显示模板列表", () => {
    cy.contains("简单伤害计算").should("be.visible");
  });

  it("选择模板后显示游戏信息表单", () => {
    cy.contains("简单伤害计算").click();
    cy.contains("下一步").click();
    cy.contains("游戏名称").should("be.visible");
  });

  it("选择模板后进入下一步", () => {
    cy.contains("简单伤害计算").click();
    cy.contains("下一步").should("be.visible");
  });
});
