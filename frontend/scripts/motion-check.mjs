import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { chromium } from "playwright";

const browser = await chromium.launch({
  executablePath:
    process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe",
  headless: true,
});
const page = await browser.newPage({
  viewport: { width: 1440, height: 960 },
  reducedMotion: "no-preference",
});
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});
try {
  await page.goto(process.env.BASE_URL || "http://127.0.0.1:3000", { waitUntil: "networkidle" });
  await page.locator(".lens-art.is-ready").waitFor({ timeout: 20000 });
  assert.equal(
    await page.locator(".pin-spacer").count(),
    2,
    "Lifecycle and agent scenes should both be pinned on desktop",
  );
  const frameTimes = await page.evaluate(
    () =>
      new Promise((resolve) => {
        const samples = [];
        let last = 0;
        function frame(time) {
          if (last) samples.push(time - last);
          last = time;
          if (samples.length < 120) requestAnimationFrame(frame);
          else resolve(samples);
        }
        requestAnimationFrame(frame);
      }),
  );
  const sorted = [...frameTimes].sort((a, b) => a - b);
  await page.screenshot({ path: "artifacts/hero-motion-desktop.png" });
  const systemTop = await page
    .locator("#platform")
    .evaluate((el) => el.parentElement.getBoundingClientRect().top + scrollY);
  await page.evaluate((top) => window.scrollTo({ top, behavior: "instant" }), systemTop + 120);
  await page.waitForTimeout(1200);
  const firstNode = await page.locator(".system-node.is-active").innerText();
  await page.evaluate((top) => window.scrollTo({ top, behavior: "instant" }), systemTop + 1080);
  await page.waitForTimeout(1200);
  const nextNode = await page.locator(".system-node.is-active").innerText();
  assert.notEqual(firstNode, nextNode, "Scrolling must advance the active lifecycle node");
  const agentsTop = await page
    .locator("#agents")
    .evaluate((el) => el.parentElement.getBoundingClientRect().top + scrollY);
  await page.evaluate((top) => window.scrollTo({ top, behavior: "instant" }), agentsTop + 1250);
  await page.waitForTimeout(1800);
  const transform = await page
    .locator(".agents-track")
    .evaluate((el) => getComputedStyle(el).transform);
  assert.notEqual(transform, "none");
  assert.notEqual(transform, "matrix(1, 0, 0, 1, 0, 0)");
  await page.screenshot({ path: "artifacts/agents-motion-desktop.png" });
  await page.getByRole("button", { name: "Meet the agent: MEMORY", exact: true }).click();
  assert.equal(await page.getByRole("dialog").isVisible(), true);
  await page.keyboard.press("Escape");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.waitForTimeout(1000);
  assert.equal(
    await page.locator(".pin-spacer").count(),
    0,
    "Changing reduced-motion preference must remove pinned behavior",
  );
  const result = {
    errors,
    activeNodes: [firstNode, nextNode],
    agentTransform: transform,
    frames: {
      medianMs: sorted[Math.floor(sorted.length / 2)],
      p95Ms: sorted[Math.floor(sorted.length * 0.95)],
      averageFps: Math.round(1000 / (frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length)),
    },
  };
  await fs.writeFile("artifacts/motion-results.json", JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
  assert.equal(errors.length, 0);
} finally {
  await browser.close();
}
