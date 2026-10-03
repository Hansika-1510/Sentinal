// Ad-hoc: capture the lifecycle map at a few scroll positions inside the pin.
import { chromium } from "playwright";
const origin = "http://127.0.0.1:3000";
const executablePath = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const browser = await chromium.launch({ executablePath, headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto(origin, { waitUntil: "networkidle" });
await page.waitForTimeout(2500);
const top = await page.locator("#platform").evaluate((el) => el.getBoundingClientRect().top + window.scrollY);
for (const frac of [0.12, 0.5, 0.95]) {
  await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), Math.round(top + 1250 * frac));
  await page.waitForTimeout(1800);
  await page.screenshot({ path: `artifacts/craft-journey-${frac}.png` });
}
const info = await page.evaluate(() => {
  const map = document.querySelector(".system-map");
  const host = document.querySelector(".journey-3d");
  const canvas = host?.querySelector("canvas");
  return {
    sections: document.querySelectorAll("main > section").length,
    pinSpacers: document.querySelectorAll(".pin-spacer").length,
    icons: document.querySelectorAll(".system-node .node-icon").length,
    activeNode: document.querySelector(".system-node.is-active")?.innerText,
    host: host ? host.getBoundingClientRect().toJSON() : null,
    canvas: canvas ? { w: canvas.width, h: canvas.height } : null,
    wiringOpacity: getComputedStyle(document.querySelector(".system-wiring")).opacity,
    liveContexts: window.__SENTINEL_LIVE_CONTEXTS ?? null,
    journeyHostPresent: Boolean(host),
    probe: map ? getComputedStyle(map).position : null,
  };
});
console.log(JSON.stringify({ info, errors }, null, 2));
await browser.close();
