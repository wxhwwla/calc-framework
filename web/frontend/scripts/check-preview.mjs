import { chromium } from "playwright-core";

const url = process.argv[2] || "http://127.0.0.1:4173/compute";

const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(`console: ${msg.text()}`);
});

await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
await page.waitForTimeout(2000);

const rootText = await page.locator("#root").innerText().catch(() => "");
const title = await page.title();
const hasCompute = rootText.includes("终末地") || rootText.includes("计算");
const hasLoading = rootText.includes("加载中");

console.log(JSON.stringify({ url, title, hasCompute, hasLoading, rootLen: rootText.length, rootPreview: rootText.slice(0, 200), errors }, null, 2));
await browser.close();
process.exit(errors.length || !hasCompute ? 1 : 0);
