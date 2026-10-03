// Ad-hoc: is the evidence canvas actually painting? Compares the hero lens
// region against the evidence region. Not part of the committed harness.
import { chromium } from "playwright";
import sharp from "sharp";

const origin = process.env.BASE_URL || "http://127.0.0.1:3000";
const executablePath =
  process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";

const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});

await page.goto(origin, { waitUntil: "networkidle" });
await page.waitForTimeout(3000);

const spread = async (clip, name) => {
  const buf = await page.screenshot({ clip });
  await sharp(buf).toFile(`artifacts/diag-${name}.png`);
  const stats = await sharp(buf).stats();
  return stats.channels.map((c) => Math.round(c.max - c.min));
};

const hero = await spread({ x: 890, y: 80, width: 540, height: 560 }, "hero");

const box = await page.locator(".evidence-canvas").boundingBox();
await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), Math.max(0, box.y - 60));
await page.waitForTimeout(2500);

const hostBox = await page.locator(".evidence-3d").boundingBox();
const canvasBox = await page.locator(".evidence-3d canvas").boundingBox();
const evidence = await spread(
  { x: 60, y: 120, width: 1320, height: 620 },
  "evidence",
);

const info = await page.evaluate(() => {
  const host = document.querySelector(".evidence-3d");
  const canvas = host?.querySelector("canvas");
  const style = host ? getComputedStyle(host) : null;
  const canvasStyle = canvas ? getComputedStyle(canvas) : null;
  return {
    hostRect: host ? host.getBoundingClientRect().toJSON() : null,
    hostStyle: style
      ? { position: style.position, zIndex: style.zIndex, opacity: style.opacity, display: style.display }
      : null,
    canvasStyle: canvasStyle
      ? { width: canvasStyle.width, height: canvasStyle.height, display: canvasStyle.display }
      : null,
    canvasPixels: canvas ? `${canvas.width}x${canvas.height}` : null,
    liveContexts: window.__SENTINEL_LIVE_CONTEXTS ?? null,
    svgOpacity: getComputedStyle(document.querySelector(".evidence-connections")).opacity,
    nodeCount: document.querySelectorAll(".evidence-node").length,
    firstNodeRect: document.querySelector(".evidence-node")?.getBoundingClientRect().toJSON() ?? null,
  };
});

console.log(JSON.stringify({ heroSpread: hero, evidenceSpread: evidence, hostBox, canvasBox, info, errors }, null, 2));
await browser.close();
