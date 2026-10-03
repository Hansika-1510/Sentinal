// Ad-hoc probe for the WebGL scenes. Verifies a scene mounts and paints, that
// scroll actually re-poses it, and that the context budget holds across a full
// page sweep. Not part of the committed harness.
//
// Note: `locator.screenshot()` scrolls its element into view first, which would
// reset the scroll-driven pose. Progress is read from the host's
// `data-scene-progress` attribute instead.
import { chromium } from "playwright";
import sharp from "sharp";

const origin = process.env.BASE_URL || "http://127.0.0.1:3000";
const executablePath =
  process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";

const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});

await page.goto(origin, { waitUntil: "networkidle" });
await page.waitForTimeout(3500);

const mount = await page.evaluate(() => {
  const canvas = document.querySelector(".lens-canvas canvas");
  const host = document.querySelector(".lens-canvas");
  return {
    canvasPresent: Boolean(canvas),
    canvasSize: canvas instanceof HTMLCanvasElement ? `${canvas.width}x${canvas.height}` : null,
    lensReady: document.querySelector(".lens-art")?.classList.contains("is-ready") ?? false,
    liveContexts: window.__SENTINEL_LIVE_CONTEXTS ?? null,
    progressAttr: host?.dataset.sceneProgress ?? null,
  };
});

// Composited screenshot: the only honest read of a WebGL canvas, since the
// drawing buffer clears after compositing without preserveDrawingBuffer.
const shot = await page.screenshot({ clip: { x: 900, y: 60, width: 520, height: 700 } });
await sharp(shot).toFile("artifacts/probe-lens-rest.png");
const restStats = await sharp(shot).stats();

const progressAt = async (top) => {
  await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), top);
  await page.waitForTimeout(700);
  return page.evaluate(() =>
    Number(document.querySelector(".lens-canvas")?.dataset.sceneProgress ?? NaN),
  );
};

const viewport = await page.evaluate(() => innerHeight);
const samples = [];
for (const factor of [0, 0.3, 0.6, 0.9, 1.2, 1.6]) {
  const top = Math.round(viewport * factor);
  samples.push({ scroll: top, progress: await progressAt(top) });
}
await page.screenshot({ path: "artifacts/probe-lens-scrolled.png" });

// Back to rest, then confirm the composited hero region still has full range.
await progressAt(0);
const restShot = await page.screenshot({ clip: { x: 900, y: 60, width: 520, height: 700 } });
const restSpread = (await sharp(restShot).stats()).channels.map((c) => Math.round(c.max - c.min));

const rises = samples.every(
  (sample, index) => index === 0 || sample.progress >= samples[index - 1].progress - 1e-3,
);

// Full-page sweep: the live-context counter must never exceed the budget.
let peakContexts = 0;
const height = await page.evaluate(() => document.documentElement.scrollHeight);
for (let y = 0; y <= height; y += 700) {
  await page.evaluate((top) => window.scrollTo({ top: top, behavior: "instant" }), y);
  await page.waitForTimeout(160);
  const live = await page.evaluate(() => window.__SENTINEL_LIVE_CONTEXTS ?? 0);
  peakContexts = Math.max(peakContexts, live);
}

console.log(
  JSON.stringify(
    {
      mount,
      samples,
      monotonic: rises,
      reachedFullProgress: (samples.at(-1)?.progress ?? 0) > 0.98,
      restSpread,
      peakContexts,
      webglWarnings: errors.filter((error) => /webgl|context/i.test(error)),
      errors,
    },
    null,
    2,
  ),
);
await browser.close();
