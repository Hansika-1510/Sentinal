/**
 * Section-by-section capture of the slate theme, for eyeballing.
 *
 *   node scripts/_tour.mjs [baseUrl] [tag]
 */
import { chromium } from "playwright";

const BASE = (process.argv[2] || "http://127.0.0.1:3000").replace(/\/$/, "");
const TAG = process.argv[3] || "slate";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const shot = (name) => page.screenshot({ path: `artifacts/${TAG}-${name}.png` });

await page.goto(BASE + "/", { waitUntil: "networkidle" });
await page.waitForTimeout(1200);

// Each narrative section, framed one at a time so both planes are visible.
const ids = await page.evaluate(() =>
  [...document.querySelectorAll("main > section")].map((s) => s.id || s.className.split(" ")[0]),
);
for (const id of ids) {
  await page.evaluate((s) => {
    const el = document.getElementById(s) || document.querySelector(`.${CSS.escape(s)}`);
    window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 60);
  }, id);
  await page.waitForTimeout(1400);
  await shot(id);
}
await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
await page.waitForTimeout(1200);
await shot("footer");

// The two section-scoped WebGL scenes, given time to mount and settle.
for (const [id, name] of [["investigation", "evidence-3d"], ["platform", "journey-3d"]]) {
  await page.evaluate((s) => {
    const el = document.getElementById(s);
    window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 40);
  }, id);
  await page.waitForTimeout(3000);
  await shot(name);
}

for (const route of ["/console", "/docs", "/architecture"]) {
  await page.goto(BASE + route, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await shot(route.slice(1));
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await page.waitForTimeout(900);
  await shot(route.slice(1) + "-footer");
}

await browser.close();
console.log(`${ids.length + 2 + 6} captures written with tag "${TAG}"`);
