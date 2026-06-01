/// <reference types="cypress" />

describe("计算页 ComputePage", () => {
  beforeEach(() => {
    cy.visit("/compute");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("终末地伤害计算器").should("be.visible");
  });

  it("显示计算页/高级页两个页签", () => {
    cy.contains("计算页").should("be.visible");
    cy.contains("高级页").should("be.visible");
  });

  it("默认显示计算页内容", () => {
    cy.contains("角色选择").should("be.visible");
  });

  it("切换到高级页显示搜索面板", () => {
    cy.contains("高级页").click();
    cy.contains("全量搜索").should("be.visible");
    cy.contains("预估").should("be.visible");
    cy.contains("开始搜索").should("be.visible");
  });

  it("高级页有结果条数和并行线程输入", () => {
    cy.contains("高级页").click();
    cy.get('input[type="number"]').first().should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("终末地计算").should("be.visible");
    cy.get('[class*="Mui-selected"]').contains("计算").should("exist");
  });
});
