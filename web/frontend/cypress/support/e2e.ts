/// <reference types="cypress" />

// 用例断言的是中文界面，但 CI/act 容器的 navigator.language 为 en-US，
// 且 electron 不支持 before:browser:launch 里的 --lang=zh-CN（Cypress 会警告并忽略）。
// 在页面脚本执行前写入 i18next 的语言缓存，保证各环境渲染一致。
Cypress.on("window:before:load", (win) => {
  win.localStorage.setItem("i18nextLng", "zh-CN");
});
