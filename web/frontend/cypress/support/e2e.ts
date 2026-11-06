/// <reference types="cypress" />

// 用例断言的是中文界面，但 CI/act 容器的 navigator.language 为 en-US，
// 且 electron 不支持 before:browser:launch 里的 --lang=zh-CN（Cypress 会警告并忽略）。
// 在页面脚本执行前写入 i18next 的语言缓存，保证各环境渲染一致。
Cypress.on("window:before:load", (win) => {
  win.localStorage.setItem("i18nextLng", "zh-CN");
  // Vite PWA（registerType: autoUpdate）会在首个用例内完成安装并接管页面。
  // 之后文档由 Service Worker 返回，Cypress 的 window:before:load 注入不再执行，
  // 语言缓存失效，后续用例会按浏览器语言（en-US）渲染，中文断言全部超时。
  // E2E 中禁用 SW 注册，让每个用例的文档都经过 Cypress 代理。
  if ("serviceWorker" in win.navigator) {
    win.navigator.serviceWorker.register = () =>
      Promise.resolve(null as unknown as ServiceWorkerRegistration);
  }
});
