/** 本地验证：各页面 AppBar 捐赠按钮 + 弹窗图片 */
import { chromium } from "playwright-core";

const base = process.argv[2] || "http://127.0.0.1:8180";
const routes = ["/compute", "/arknights", "/designer", "/pack-designer", "/editor"];

const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];

for (const route of routes) {
  const url = `${base}${route}`;
  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(800);

  const donateBtn = page.getByRole("button", { name: "捐赠" }).first();
  const visible = await donateBtn.isVisible().catch(() => false);
  if (!visible) {
    errors.push(`${route}: AppBar 无「捐赠」按钮`);
    continue;
  }

  await donateBtn.click();
  await page.waitForTimeout(500);

  const imgs = page.locator('[role="dialog"] img');
  const count = await imgs.count();
  if (count < 1) {
    errors.push(`${route}: 捐赠弹窗无图片 (manifest/静态资源异常)`);
  }
  await page.keyboard.press("Escape");
}

const manifest = await fetch(`${base}/api/donation/manifest`).then((r) => r.json()).catch(() => []);
console.log(
  JSON.stringify({ base, manifest, routesChecked: routes.length, errors }, null, 2),
);
await browser.close();
process.exit(errors.length ? 1 : 0);
