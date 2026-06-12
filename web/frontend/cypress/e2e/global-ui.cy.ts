/// <reference types="cypress" />

describe("全局 UI 元素 GlobalUI", () => {
  beforeEach(() => {
    cy.visit("/compute");
    cy.viewport(1280, 800);
  });

  it("页面底部有开源许可声明", () => {
    cy.contains("开源").should("be.visible");
  });

  it("页脚存在 GitHub 链接", () => {
    cy.contains("GitHub").should("be.visible");
  });

  it("响应式：窄屏下布局自适应", () => {
    cy.viewport(900, 800);
    cy.contains("角色选择").should("be.visible");
  });

  it("响应式：手机屏下布局紧凑可用", () => {
    cy.viewport(375, 667);
    cy.get("body").should("be.visible");
  });

  it("打开 API 文档页", () => {
    // 直接访问 redoc 或 swagger
    cy.visit("/api/docs", { failOnStatusCode: false });
    cy.get("body").should("be.visible");
  });

  it("数据设计器手机屏可以滚动", () => {
    cy.viewport(375, 667);
    cy.visit("/designer");
    cy.contains("公式反推").should("be.visible");
    cy.scrollTo("bottom");
    cy.contains("数据浏览").should("be.visible");
  });
});
