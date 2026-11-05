/// <reference types="cypress" />

import { selectFirstLoadout } from "../support/helpers";

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
    cy.contains("角色 / 武器选择").should("be.visible");
    cy.contains("敌方参数").should("be.visible");
  });

  it("切换到高级页显示搜索面板", () => {
    selectFirstLoadout();
    cy.contains("高级页").click();
    cy.contains("全量搜索").should("be.visible");
    cy.contains("预估").should("be.visible");
    cy.contains("结果条数").should("be.visible");
    cy.contains("并行线程").should("be.visible");
  });

  it("高级页有结果条数和并行线程输入", () => {
    selectFirstLoadout();
    cy.contains("高级页").click();
    cy.get('input[aria-label="结果条数"]').should("be.visible");
    cy.get('input[aria-label="并行线程"]').should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("终末地计算").should("be.visible");
    cy.get('[class*="Mui-selected"]').contains("计算").should("exist");
  });
});
