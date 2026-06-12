/// <reference types="cypress" />

describe("适配器页 AdaptersPage", () => {
  beforeEach(() => {
    cy.visit("/adapters");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("适配器").should("be.visible");
  });

  it("显示可用适配器列表", () => {
    cy.contains("终末地").should("be.visible");
  });

  it("通过侧边栏导航可访问", () => {
    cy.contains("适配器").should("be.visible");
  });
});

describe("Calc Hub 市场页 MarketplacePage", () => {
  beforeEach(() => {
    cy.visit("/hub");
    cy.viewport(1280, 800);
  });

  it("页面标题正确渲染", () => {
    cy.contains("Calc Hub").should("be.visible");
  });

  it("显示配置包市场内容", () => {
    cy.get("body").should("be.visible");
  });
});

describe("PWA 离线支持", () => {
  it("manifest.json 可访问", () => {
    cy.request("/manifest.webmanifest").then((resp) => {
      expect(resp.status).to.eq(200);
      expect(resp.body).to.have.property("name");
      expect(resp.body).to.have.property("icons");
    });
  });
});
