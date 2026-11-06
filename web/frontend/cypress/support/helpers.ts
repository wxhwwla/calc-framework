/// <reference types="cypress" />

/**
 * 在计算页选择第一个可用角色与武器。
 *
 * 高级页的 SearchPanel 只在 loadout 完整（角色 + 武器均已选中）时渲染，
 * 因此所有需要断言「全量搜索 / 预估」的用例都要先调用本函数。
 */
export function selectFirstLoadout(): void {
  cy.get('[data-testid="char-select"] [role="combobox"]', { timeout: 15000 }).click();
  cy.get('li[role="option"]', { timeout: 15000 }).first().click();
  // 等角色详情加载完成（AI 推荐按钮随 selectedChar 一起出现）：
  // 此时武器候选才会按角色武器类型过滤，避免选中不匹配的武器后被清空。
  // 注意文案来自 i18n 的 ai.recommend（"AI 推荐"），不是组件里的兜底字符串。
  cy.contains("AI 推荐", { timeout: 15000 }).should("be.visible");
  cy.get('[data-testid="weapon-select"] [role="combobox"]').click();
  cy.get('li[role="option"]', { timeout: 15000 }).first().click();
}
