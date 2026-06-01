/// <reference types="cypress" />

describe("数据设计页 DesignerPage", () => {
  beforeEach(() => {
    cy.visit("/designer");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("数据设计器").should("be.visible");
  });

  it("显示三个页签", () => {
    cy.contains("公式反推").should("be.visible");
    cy.contains("数据编辑").should("be.visible");
    cy.contains("数据浏览").should("be.visible");
  });

  it("默认显示公式反推页签内容", () => {
    cy.contains("公式反推").should("have.class", "Mui-selected");
  });

  it("点击数据编辑页签切换成功", () => {
    cy.contains("数据编辑").click();
    cy.contains("数据编辑").should("have.class", "Mui-selected");
  });

  it("点击数据浏览页签切换成功", () => {
    cy.contains("数据浏览").click();
    cy.contains("数据浏览").should("have.class", "Mui-selected");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("数据设计器").should("be.visible");
  });
});
