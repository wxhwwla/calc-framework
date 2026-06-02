/// <reference types="cypress" />

describe("数据贡献页 DataContributePage", () => {
  beforeEach(() => {
    cy.visit("/contribute");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("数据贡献").should("be.visible");
  });

  it("显示游戏选择下拉框", () => {
    cy.contains("终末地").should("be.visible");
    cy.contains("明日方舟").should("be.visible");
  });

  it("显示前往完整设计器的链接", () => {
    cy.contains("前往完整数据设计器").should("be.visible");
  });

  it("默认显示终末地数据编辑器", () => {
    cy.contains("角色").should("be.visible");
    cy.contains("武器").should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("数据贡献").should("be.visible");
    cy.get('nav').contains("数据贡献").should("exist");
  });

  it("点击新增按钮打开表单", () => {
    cy.contains("新增").click();
    cy.contains("名称").should("be.visible");
    cy.contains("保存").should("be.visible");
  });
});
