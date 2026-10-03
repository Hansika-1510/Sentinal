import { chromium } from "playwright";
import fs from "node:fs/promises";
import sharp from "sharp";

await fs.mkdir("artifacts", { recursive: true });
await fs.mkdir("public/visuals", { recursive: true });
const browser = await chromium.launch({
  executablePath:
    process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe",
  headless: true,
});
const origin = process.env.BASE_URL || "http://127.0.0.1:3000";
const page = await browser.newPage({
  viewport: { width: 1440, height: 960 },
  deviceScaleFactor: 1,
});
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(origin, { waitUntil: "networkidle", timeout: 90000 });
await page
  .locator(".lens-art.is-ready")
  .waitFor({ timeout: 25000 })
  .catch(() => {});
await page.waitForTimeout(1800);
if (await page.locator(".lens-canvas canvas").count()) {
  const data = await page.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() =>
          resolve(document.querySelector(".lens-canvas canvas").toDataURL("image/png")),
        ),
      ),
  );
  const buffer = Buffer.from(data.split(",")[1], "base64");
  await sharp(buffer)
    .webp({ quality: 94, alphaQuality: 100 })
    .toFile("public/visuals/signal-lens.webp");
}
await page.screenshot({ path: "artifacts/desktop-hero.png" });
console.log(
  JSON.stringify(
    {
      title: await page.title(),
      errors,
      size: await page.evaluate(() => ({
        width: innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        height: document.documentElement.scrollHeight,
      })),
    },
    null,
    2,
  ),
);
await page
  .getByRole("heading", { name: "An incident is never just an incident." })
  .scrollIntoViewIfNeeded();
await page.waitForTimeout(1200);
await page.screenshot({ path: "artifacts/desktop-problem.png" });
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(origin, { waitUntil: "networkidle" });
await page.waitForTimeout(1600);
await page.screenshot({ path: "artifacts/mobile-hero.png" });
console.log(
  "mobile",
  await page.evaluate(() => ({
    width: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  })),
);
await browser.close();
