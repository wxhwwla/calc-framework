#!/usr/bin/env node
// 构建产物守门：确保 PWA 预缓存与首屏 modulepreload 不会把懒加载资源一次性拉下来。
//
// 失败条件：
//   1. Service Worker 预缓存包含 local-backend.zip / sql-wasm / wasm-golden
//   2. Service Worker 预缓存了入口以外的 assets/*（懒加载 chunk 应走运行时缓存）
//   3. 入口未预缓存（glob 配置失效时 Workbox 会静默跳过全部 assets）
//   4. index.html 提前 modulepreload 编辑器/图表等懒加载 chunk
//
// 用法：npm run check:build（需先 npm run build）

import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const distDir = resolve(projectRoot, "dist");
const failures = [];

function readDist(name) {
  const path = resolve(distDir, name);
  if (!existsSync(path)) {
    failures.push(`缺少构建产物 dist/${name}，请先执行 npm run build`);
    return null;
  }
  return readFileSync(path, "utf8");
}

function collectPrecacheUrls(swSource) {
  return [...swSource.matchAll(/url:"([^"]+)"/g)].map((m) => m[1]);
}

function collectModulePreloads(htmlSource) {
  return [...htmlSource.matchAll(/<link[^>]+rel="modulepreload"[^>]*>/g)]
    .map((m) => /href="([^"]+)"/.exec(m[0])?.[1])
    .filter(Boolean);
}

const swSource = readDist("sw.js");
if (swSource) {
  const urls = collectPrecacheUrls(swSource);
  console.log(`[check-build] SW 预缓存 ${urls.length} 项：`);
  for (const url of urls) console.log(`  - ${url}`);

  const banned = ["local-backend.zip", "sql-wasm", "wasm-golden"];
  for (const marker of banned) {
    if (urls.some((url) => url.includes(marker))) {
      failures.push(`SW 预缓存不应包含 ${marker}（大文件按需下载，不进首访）`);
    }
  }

  const assetUrls = urls.filter((url) => url.startsWith("assets/"));
  if (assetUrls.length === 0) {
    failures.push("SW 未预缓存任何 assets/*，Workbox glob 可能失效");
  }
  for (const url of assetUrls) {
    if (!/^assets\/index-[^/]+\.(?:js|css)$/.test(url)) {
      failures.push(`SW 只应预缓存入口 assets/index-*，发现懒加载资源：${url}`);
    }
  }
}

const htmlSource = readDist("index.html");
if (htmlSource) {
  const preloads = collectModulePreloads(htmlSource);
  console.log(`[check-build] index.html modulepreload ${preloads.length} 项：`);
  for (const href of preloads) console.log(`  - ${href}`);

  const lazyChunkPattern = /xyflow|echarts|ComputePage|ArknightsComputePage|AdapterGamePage|EditorPage|DesignerPage|PackDesignerPage|MarketplacePage|DataContributePage|GeneratorPage/;
  for (const href of preloads) {
    if (lazyChunkPattern.test(href)) {
      failures.push(`index.html 不应 modulepreload 懒加载 chunk：${href}`);
    }
  }
}

if (failures.length > 0) {
  console.error("\n[check-build] 失败：");
  for (const failure of failures) console.error(`  ✗ ${failure}`);
  process.exit(1);
}

console.log("\n[check-build] 通过：首访只加载入口，懒加载资源按需缓存。");
