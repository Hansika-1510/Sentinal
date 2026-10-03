import { chromium } from "playwright";
const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto("http://127.0.0.1:3000/architecture", { waitUntil: "networkidle" });
await page.waitForTimeout(2000);
const h = await page.evaluate(() => document.documentElement.scrollHeight);
for (let y = 0; y <= h; y += 400) {
  await page.evaluate((t) => window.scrollTo({ top: t, behavior: "instant" }), y);
  await page.waitForTimeout(150);
}
console.log(JSON.stringify({
  canvases: await page.locator("canvas").count(),
  journeyHost: await page.locator(".journey-3d").count(),
  wiringOpacity: await page.evaluate(() => getComputedStyle(document.querySelector(".system-wiring")).opacity),
  nodes: await page.locator(".system-node").count(),
  liveContexts: await page.evaluate(() => window.__SENTINEL_LIVE_CONTEXTS ?? null),
  errors,
}, null, 2));
await browser.close();
