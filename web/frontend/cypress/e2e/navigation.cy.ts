/// <reference types="cypress" />

describe("全局导航与布局 Navigation", () => {
  beforeEach(() => {
    cy.visit("/");
    cy.viewport(1280, 800);
  });

  it("根路径显示着陆页", () => {
    cy.url().should("not.include", "/compute");
    cy.contains("START CALCULATING").should("be.visible");
  });

  it("着陆页可以导航到计算页", () => {
    cy.contains("START CALCULATING").click();
    cy.url().should("include", "/compute");
  });

  it("侧边栏 Games 组默认展开显示游戏导航项", () => {
    cy.visit("/compute");
    const gameItems = ["终末地计算", "明日方舟"];
    gameItems.forEach((item) => {
      cy.contains(item).should("be.visible");
    });
  });

  it("侧边栏 Dev Tools 组默认折叠但可展开", () => {
    cy.visit("/compute");
    cy.contains("Dev Tools").click();
    const toolItems = ["AI 生成器", "数据设计器", "配置包设计器", "数据贡献", "DAG 编辑器"];
    toolItems.forEach((item) => {
      cy.contains(item).should("be.visible");
    });
  });

  it("点击侧边栏项切换页面", () => {
    cy.visit("/compute");
    cy.contains("数据设计器").click();
    cy.url().should("include", "/designer");
  });

  it("侧边栏项高亮当前页面", () => {
    cy.visit("/compute");
    cy.contains("终末地计算").should("have.class", "Mui-selected");
    cy.contains("数据贡献").click();
    cy.contains("数据贡献").should("have.class", "Mui-selected");
    cy.contains("终末地计算").should("not.have.class", "Mui-selected");
  });

  it("在移动视口下显示汉堡菜单", () => {
    cy.visit("/compute");
    cy.viewport(480, 800);
    cy.get('[data-testid="MenuIcon"]').should("be.visible");
  });

  it("点击汉堡菜单打开侧边栏", () => {
    cy.visit("/compute");
    cy.viewport(480, 800);
    cy.get('[data-testid="MenuIcon"]').click();
    cy.get('[class*="MuiDrawer"]').should("be.visible");
  });
});
