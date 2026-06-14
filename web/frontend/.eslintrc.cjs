/** @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react/jsx-runtime",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: { jsx: true },
  },
  plugins: ["@typescript-eslint", "react", "react-hooks", "jsx-a11y"],
  settings: {
    react: { version: "detect" },
  },
  rules: {
    // TypeScript 放松（与现有 tsc 配置一致）
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],

    // React 放松
    "react/prop-types": "off",
    "react/display-name": "off",

    // a11y
    "jsx-a11y/anchor-is-valid": "warn",
    "jsx-a11y/click-events-have-key-events": "warn",
    "jsx-a11y/no-static-element-interactions": "warn",

    // 通用
    "no-console": ["warn", { allow: ["warn", "error"] }],
    "no-constant-condition": ["error", { "checkLoops": false }],
    "no-empty": ["error", { "allowEmptyCatch": true }],
  },
  ignorePatterns: ["dist/", "node_modules/", "cypress/", "*.config.*"],
};
