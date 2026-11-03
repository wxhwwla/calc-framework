import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import zhCN from "./locales/zh-CN";
import en from "./locales/en";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      "zh-CN": { translation: zhCN },
      en: { translation: en },
    },
    fallbackLng: "zh-CN",
    debug: false,
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      // localStorage 必须排在 navigator 之前：用户手动切换的语言会被缓存，
      // 但原先的顺序从不读取缓存，刷新后总被浏览器语言覆盖。
      // Cypress E2E 也依赖它把界面固定为 zh-CN（electron 不支持 --lang 启动参数）。
      order: ["localStorage", "navigator", "htmlTag"],
      caches: ["localStorage"],
    },
  });

export default i18n;
