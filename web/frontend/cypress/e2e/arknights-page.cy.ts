/// <reference types="cypress" />

describe("明日方舟计算页 ArknightsComputePage", () => {
  beforeEach(() => {
    cy.visit("/arknights");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("明日方舟伤害计算").should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("明日方舟").should("be.visible");
  });

  it("显示干员选择区域", () => {
    cy.contains("选择干员").should("be.visible");
  });

  it("显示技能等级调节", () => {
    cy.contains("技能等级").should("be.visible");
  });

  it("显示敌人参数面板", () => {
    cy.contains("敌方防御").should("be.visible");
    cy.contains("敌方法抗").should("be.visible");
  });

  it("显示计算结果区域", () => {
    cy.contains("最终攻击力").should("be.visible");
    cy.contains("物理伤害").should("be.visible");
    cy.contains("法术伤害").should("be.visible");
    cy.contains("真实伤害").should("be.visible");
  });

  it("搜索干员后显示结果", () => {
    cy.get('[class*="MuiAutocomplete"]').first().type("阿米娅");
    cy.contains("阿米娅", { timeout: 5000 }).should("be.visible");
  });

  it("敌人参数可输入", () => {
    cy.get('input[type="number"]').first().clear().type("500");
    cy.get('input[type="number"]').first().should("have.value", "500");
  });
});
