// Ad-hoc: capture the hero viewport across the morph's five story states so the
// arc can be judged visually. Not part of the committed harness.
//
// The ScrollTrigger range is `+=44%` of the viewport, so story progress p maps
// to a scroll offset of `0.44 * innerHeight * p`.
import { chromium } from "playwright";

const origin = process.env.BASE_URL || "http://127.0.0.1:3000";
const executablePath =
  process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";

const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
await page.goto(origin, { waitUntil: "networkidle" });
await page.waitForTimeout(3500);

const height = await page.evaluate(() => innerHeight);
const states = [
  [0, "observe"],
  [0.25, "trace"],
  [0.5, "evidence"],
  [0.75, "root-cause"],
  [1, "resolve"],
];

for (const [p, label] of states) {
  const top = Math.round(height * 0.44 * p);
  await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), top);
  await page.waitForTimeout(900);
  const progress = await page.evaluate(
    () => document.querySelector(".lens-canvas")?.dataset.sceneProgress,
  );
  const name = `artifacts/hero-state-${label}.png`;
  await page.screenshot({ path: name });
  console.log(name, `scroll=${top}`, "progress=", progress);
}

await browser.close();
