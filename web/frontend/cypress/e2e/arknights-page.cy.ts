/// <reference types="cypress" />

describe("明日方舟计算页 ArknightsComputePage", () => {
  beforeEach(() => {
    cy.visit("/arknights");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("明日方舟 伤害计算器").should("be.visible");
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
    cy.contains("敌军防御力").should("be.visible");
    // 敌人面板中的法抗输入用 arknights.magicResistance（"法术抗性"）；
    // "敌军法抗"只出现在计算结果表里，计算前不可见。
    cy.contains("法术抗性").should("be.visible");
  });

  it("选择干员并计算后显示结果区域", () => {
    cy.get('[class*="MuiAutocomplete"]').first().type("阿米娅");
    cy.contains("阿米娅", { timeout: 10000 }).first().click();
    cy.contains("开始计算").click();
    cy.contains("最终攻击力", { timeout: 20000 }).should("be.visible");
    cy.contains("物理伤害").should("exist");
    cy.contains("真实伤害").should("exist");
  });

  it("搜索干员后显示结果", () => {
    cy.get('[class*="MuiAutocomplete"]').first().type("阿米娅");
    cy.contains("阿米娅", { timeout: 5000 }).should("be.visible");
  });

  it("敌人参数可输入", () => {
    cy.contains("敌军防御力")
      .parent()
      .find('input[type="number"]')
      .invoke("val", "500")
      .trigger("input")
      .should("have.value", "500");
  });
});
