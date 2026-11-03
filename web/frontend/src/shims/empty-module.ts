// 浏览器构建中替代 Node 内置模块（fs/path/crypto）。
// sql.js 的 Node 分支在浏览器不会执行，替换为空模块可避免 Vite
// 的 "Module has been externalized for browser compatibility" 警告。
const emptyModule = {};

export default emptyModule;
