// Scroll the whole page and watch the WebGL context budget, then sample frame
// times while the evidence scene is on screen.
//
// The counter is published by src/lib/three/context-budget.ts. Browsers drop the
// oldest context past their own limit (commonly 16), which blanks a scene
// mid-scroll, so the app caps itself well under that and lets a scene decline to
// mount. This is the check that the cap actually holds under a full sweep.
import assert from "node:assert/strict";
import { chromium } from "playwright";

const origin = process.env.BASE_URL || "http://127.0.0.1:3000";
const executablePath =
  process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";

const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

const errors = [];
const dropped = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
  if (/too many active webgl contexts/i.test(message.text())) dropped.push(message.text());
});

try {
  await page.goto(origin, { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  const samples = [];
  for (let top = 0; top <= height; top += 400) {
    await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), top);
    await page.waitForTimeout(200);
    samples.push(await page.evaluate(() => window.__SENTINEL_LIVE_CONTEXTS ?? 0));
  }
  const peak = Math.max(...samples);
  assert.ok(peak <= 4, `Live WebGL contexts peaked at ${peak}, above the cap of 4`);
  assert.deepEqual(dropped, [], "The browser reported too many active WebGL contexts");

  // Frame times with the evidence scene centred. Read the absolute document
  // offset: the sweep above leaves the page at the bottom, so a viewport-relative
  // rect would scroll to nonsense.
  const canvasTop = await page
    .locator(".evidence-canvas")
    .evaluate((element) => element.getBoundingClientRect().top + window.scrollY);
  await page.evaluate(
    (y) => window.scrollTo({ top: y, behavior: "instant" }),
    Math.max(0, canvasTop - 120),
  );
  await page.waitForTimeout(1500);
  await page.locator(".evidence-3d canvas").waitFor({ timeout: 15000 });

  const frames = await page.evaluate(
    () =>
      new Promise((resolve) => {
        const times = [];
        let last = 0;
        function frame(time) {
          if (last) times.push(time - last);
          last = time;
          if (times.length < 120) requestAnimationFrame(frame);
          else resolve(times);
        }
        requestAnimationFrame(frame);
      }),
  );
  const sorted = [...frames].sort((a, b) => a - b);
  const summary = {
    peakContexts: peak,
    distinctContextCounts: [...new Set(samples)].sort((a, b) => a - b),
    evidence: {
      medianMs: Number(sorted[Math.floor(sorted.length / 2)].toFixed(2)),
      p95Ms: Number(sorted[Math.floor(sorted.length * 0.95)].toFixed(2)),
      averageFps: Math.round(1000 / (frames.reduce((a, b) => a + b, 0) / frames.length)),
    },
    errors,
  };

  assert.ok(summary.evidence.averageFps >= 55, `Evidence scene ran at ${summary.evidence.averageFps} fps`);
  assert.deepEqual(errors, [], "Console or page errors during the sweep");

  // Reduced motion is a hard no-op: no WebGL anywhere, no pins, and the SVG
  // connectors left at full opacity as the fallback the scene degrades to.
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  const reducedHeight = await page.evaluate(() => document.documentElement.scrollHeight);
  let reducedCanvases = 0;
  for (let top = 0; top <= reducedHeight; top += 400) {
    await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), top);
    await page.waitForTimeout(120);
    reducedCanvases = Math.max(reducedCanvases, await page.locator("canvas").count());
  }
  const reduced = {
    canvases: reducedCanvases,
    pinSpacers: await page.locator(".pin-spacer").count(),
    connectorsOpacity: await page.evaluate(
      () => getComputedStyle(document.querySelector(".evidence-connections")).opacity,
    ),
  };
  assert.equal(reduced.canvases, 0, "Reduced motion must mount no canvas at all");
  assert.equal(reduced.pinSpacers, 0, "Reduced motion must leave no pin spacers");
  assert.equal(reduced.connectorsOpacity, "1", "Reduced motion must keep the SVG connectors");

  console.log(
    JSON.stringify({ ...summary, reduced }, null, 2),
  );
  console.log("PASS: context budget, evidence frame budget, and reduced-motion contract held");
} finally {
  await browser.close();
}
