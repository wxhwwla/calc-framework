/// <reference types="cypress" />

describe("配置包设计页 PackDesignerPage", () => {
  beforeEach(() => {
    cy.visit("/pack-designer");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("配置包设计器").should("be.visible");
  });

  it("显示三个页签", () => {
    cy.contains("数据录入").should("be.visible");
    cy.contains("布局编辑").should("be.visible");
    cy.contains("主题与导出").should("be.visible");
  });

  it("默认显示数据录入页签", () => {
    cy.contains("数据录入").should("have.class", "Mui-selected");
  });

  it("切换到布局编辑页签显示 DAG 编辑器", () => {
    cy.contains("布局编辑").click();
    cy.contains("布局编辑").should("have.class", "Mui-selected");
    cy.contains("DAG 公式图编辑器").should("be.visible");
    cy.contains("节点面板").should("be.visible");
  });

  it("切换到主题与导出页签", () => {
    cy.contains("主题与导出").click();
    cy.contains("主题与导出").should("have.class", "Mui-selected");
  });

  it("主题与导出页签有包名输入框和导出按钮", () => {
    cy.contains("主题与导出").click();
    cy.get('input[value="自定义计算配置"]').should("be.visible");
    cy.contains("导出 .calcpack").should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("配置包设计器").should("be.visible");
  });
});
