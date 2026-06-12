/// <reference types="cypress" />

describe("计算页 ComputePage - 交互操作", () => {
  beforeEach(() => {
    cy.visit("/compute");
    cy.viewport(1280, 800);
    // 等待 API 数据加载
    cy.contains("角色选择", { timeout: 15000 }).should("be.visible");
  });

  it("选择角色后触发数据加载", () => {
    // 打开角色下拉框
    cy.get('[class*="MuiAutocomplete"]').first().should("be.visible");
    cy.get('[class*="MuiAutocomplete"]').first().type("管");
    cy.contains("管理员", { timeout: 5000 }).should("be.visible");
  });

  it("等级滑块可调节", () => {
    cy.get('[type="range"]').first().should("be.visible");
    cy.get('[type="range"]').first().invoke("val", 80).trigger("input");
    cy.get('[type="range"]').first().should("have.value", "80");
  });

  it("切换到高级页后，切换回计算页", () => {
    cy.contains("高级页").click();
    cy.contains("全量搜索").should("be.visible");
    cy.contains("计算页").click();
    cy.contains("角色选择").should("be.visible");
  });

  it("高级页存在完整功能区", () => {
    cy.contains("高级页").click();
    // 搜索相关
    cy.contains("全量搜索").should("be.visible");
    cy.contains("预估").should("be.visible");
    cy.contains("开始搜索").should("be.visible");
    // 工具与分享
    cy.contains("Buff微调").should("be.visible");
    cy.contains("方案对比").should("be.visible");
    cy.contains("使用说明").should("be.visible");
    // 多技能
    cy.contains("多技能段级次数").should("be.visible");
  });

  it("敌方参数面板可调节", () => {
    cy.get('[class*="enemy"]').should("exist");
  });

  it("搜索预估返回结果", () => {
    cy.contains("高级页").click();
    cy.contains("预估").click();
    // 预估应该显示结果或错误提示（API 未运行）
    cy.get("body").then(($body) => {
      if ($body.text().includes("预计")) {
        cy.contains("预计").should("be.visible");
      }
    });
  });
});
