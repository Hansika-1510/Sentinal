// Ad-hoc: screenshot one section, scrolled into view and after its reveal has
// played. Usage: node scripts/probe-section.mjs <selector> [outName]
// Not part of the committed harness.
import { chromium } from "playwright";

const selector = process.argv[2] || ".problem";
const out = process.argv[3] || "artifacts/section.png";
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

const box = await page.locator(selector).first().boundingBox();
if (!box) {
  console.log(JSON.stringify({ selector, error: "not found" }));
  await browser.close();
  process.exit(1);
}

// Land the section's top near the top of the viewport, then let the reveal play.
await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), Math.max(0, box.y - 70));
await page.waitForTimeout(2200);
await page.screenshot({ path: out });

const probe = await page.evaluate((sel) => {
  const root = document.querySelector(sel);
  if (!root) return null;
  const heading = root.querySelector("h2");
  const lines = root.querySelectorAll(".split-line");
  const chars = root.querySelectorAll(".char");
  const rect = heading?.getBoundingClientRect();
  return {
    headingTag: heading?.tagName ?? null,
    splitLines: lines.length,
    chars: chars.length,
    clipping: chars.length
      ? [...chars]
          .map((char) => {
            const mask = char.parentElement;
            return Number(
              (char.getBoundingClientRect().bottom - mask.getBoundingClientRect().bottom).toFixed(2),
            );
          })
          .filter((delta) => delta > 0.5).length
      : 0,
    headingRect: rect ? { h: Math.round(rect.height), w: Math.round(rect.width) } : null,
    docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    threeCanvas: (() => {
      const canvas = root.querySelector(".evidence-3d canvas, .lens-canvas canvas");
      if (!canvas) return null;
      const box = canvas.getBoundingClientRect();
      return { w: Math.round(box.width), h: Math.round(box.height) };
    })(),
    liveContexts: window.__SENTINEL_LIVE_CONTEXTS ?? null,
  };
}, selector);

console.log(JSON.stringify({ selector, out, probe, errors }, null, 2));
await browser.close();
