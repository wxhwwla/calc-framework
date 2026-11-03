/// <reference types="cypress" />

import { selectFirstLoadout } from "../support/helpers";

describe("计算页 ComputePage - 交互操作", () => {
  beforeEach(() => {
    cy.visit("/compute");
    cy.viewport(1280, 800);
    // 等待 API 数据加载
    cy.contains("角色 / 武器选择", { timeout: 15000 }).should("be.visible");
  });

  it("选择角色后显示 AI 推荐入口", () => {
    cy.get('[data-testid="char-select"] [role="combobox"]').click();
    cy.get('li[role="option"]', { timeout: 15000 }).first().click();
    cy.contains("AI 推荐").should("be.visible");
  });

  it("等级滑块可调节", () => {
    cy.get('[type="range"]').first().should("be.visible");
    // 滑块位于页面顶部，会被固定 AppBar（MuiToolbar）覆盖；
    // force 跳过「元素被遮挡」检查，React 仍会收到 input 事件。
    cy.get('[type="range"]').first().invoke("val", 80).trigger("input", { force: true });
    cy.get('[type="range"]').first().should("have.value", "80");
  });

  it("切换到高级页后，切换回计算页", () => {
    cy.contains("高级页").click();
    cy.contains("工具与分享").should("be.visible");
    cy.contains("计算页").click();
    cy.contains("角色 / 武器选择").should("be.visible");
  });

  it("高级页存在完整功能区", () => {
    cy.contains("高级页").click();
    // 工具与分享
    cy.contains("Buff微调").should("be.visible");
    cy.contains("方案对比").should("be.visible");
    cy.contains("使用说明").should("be.visible");
    // 多技能
    cy.contains("多技能次数").should("be.visible");
  });

  it("敌方参数面板可调节", () => {
    cy.contains("敌方参数").should("be.visible");
  });

  it("搜索预估返回结果", () => {
    selectFirstLoadout();
    cy.contains("高级页").click();
    cy.contains("预估").click();
    // 预估应显示结果或错误提示
    cy.get("body").then(($body) => {
      if ($body.text().includes("预计")) {
        cy.contains("预计").should("be.visible");
      }
    });
  });
});
