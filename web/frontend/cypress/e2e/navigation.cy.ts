/// <reference types="cypress" />

describe("全局导航与布局 Navigation", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.viewport(1280, 800);
  });

  it("根路径重定向到计算页", () => {
    cy.url().should("include", "/compute");
  });

  it("侧边栏显示所有主要导航项", () => {
    const items = ["终末地计算", "明日方舟", "AI 生成器", "数据设计器", "配置包设计器", "数据贡献", "DAG 编辑器"];
    items.forEach((item) => {
      cy.contains(item).should("be.visible");
    });
  });

  it("点击侧边栏项切换页面", () => {
    cy.contains("数据设计器").click();
    cy.url().should("include", "/designer");
    cy.contains("数据设计器").should("be.visible");
  });

  it("侧边栏项高亮当前页面", () => {
    cy.contains("终末地计算").should("have.class", "Mui-selected");
    cy.contains("数据贡献").click();
    cy.contains("数据贡献").should("have.class", "Mui-selected");
    cy.contains("终末地计算").should("not.have.class", "Mui-selected");
  });

  it("在移动视口下显示汉堡菜单", () => {
    cy.viewport(480, 800);
    cy.get('[data-testid="MenuIcon"]').should("be.visible");
  });

  it("点击汉堡菜单打开侧边栏", () => {
    cy.viewport(480, 800);
    cy.get('[data-testid="MenuIcon"]').click();
    cy.get('[class*="MuiDrawer"]').should("be.visible");
  });
});
