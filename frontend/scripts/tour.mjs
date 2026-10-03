import { chromium } from "playwright";
import sharp from "sharp";
import fs from "node:fs/promises";

await fs.mkdir("artifacts", { recursive: true });
const browser = await chromium.launch({
  executablePath:
    process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe",
  headless: true,
});
const page = await browser.newPage({
  viewport: { width: 1440, height: 960 },
  reducedMotion: "reduce",
});
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
await page.goto(process.env.BASE_URL || "http://127.0.0.1:3000", { waitUntil: "networkidle" });
const scenes = [
  "#platform",
  "#runtime",
  "#root-cause",
  "#fix-advisor",
  "#recovery",
  "#agents",
  "#console-preview",
  "#human-control",
];
for (const selector of scenes) {
  await page
    .locator(selector)
    .evaluate((el) =>
      window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - 98, behavior: "instant" }),
    );
  await page.waitForTimeout(selector === "#console-preview" ? 1600 : 250);
  await page.screenshot({ path: `artifacts/scene-${selector.slice(1)}.png` });
}
const tiles = await Promise.all(
  scenes.map(async (selector) => ({
    input: await sharp(`artifacts/scene-${selector.slice(1)}.png`)
      .resize(720, 480)
      .toBuffer(),
  })),
);
await sharp({ create: { width: 1440, height: 480 * 4, channels: 3, background: "#12110f" } })
  .composite(
    tiles.map((tile, index) => ({
      ...tile,
      left: (index % 2) * 720,
      top: Math.floor(index / 2) * 480,
    })),
  )
  .png()
  .toFile("artifacts/desktop-tour.png");
await page.goto((process.env.BASE_URL || "http://127.0.0.1:3000") + "/console", {
  waitUntil: "networkidle",
});
await page.screenshot({ path: "artifacts/console-desktop.png", fullPage: true });
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(process.env.BASE_URL || "http://127.0.0.1:3000", { waitUntil: "networkidle" });
for (const selector of ["#root-cause", "#fix-advisor", "#agents", "#console-preview"]) {
  await page
    .locator(selector)
    .evaluate((el) =>
      window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - 90, behavior: "instant" }),
    );
  await page.waitForTimeout(selector === "#console-preview" ? 1000 : 200);
  await page.screenshot({ path: `artifacts/mobile-${selector.slice(1)}.png` });
}
console.log(
  JSON.stringify(
    {
      errors,
      mobile: await page.evaluate(() => ({
        width: innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        height: document.documentElement.scrollHeight,
      })),
    },
    null,
    2,
  ),
);
await browser.close();
