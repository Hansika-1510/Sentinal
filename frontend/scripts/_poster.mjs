/**
 * Reduced-motion hero check: with WebGL suppressed the poster is what ships, so
 * its dark lens has to read against the slate ground rather than the light one
 * it was authored on. Captures the hero at rest under `prefers-reduced-motion`.
 *
 *   node scripts/_poster.mjs [baseUrl]
 */
import { chromium } from "playwright";

const BASE = (process.argv[2] || "http://127.0.0.1:3000").replace(/\/$/, "");
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  reducedMotion: "reduce",
});
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
await page.waitForTimeout(1500);

const info = await page.evaluate(() => {
  const canvas = document.querySelector(".lens-canvas canvas");
  const art = document.querySelector(".lens-art");
  const img = document.querySelector(".lens-art img");
  const cs = art ? getComputedStyle(art) : null;
  return {
    canvases: document.querySelectorAll(".lens-canvas canvas").length,
    hasArt: !!art,
    artOpacity: cs && cs.opacity,
    imgSrc: img && img.currentSrc,
    imgComplete: img && img.complete,
    imgNatural: img && `${img.naturalWidth}x${img.naturalHeight}`,
    heroBg: getComputedStyle(document.body).backgroundColor,
  };
});
console.log(JSON.stringify({ errors, ...info }, null, 2));

await page.screenshot({ path: "artifacts/slate-poster-hero.png" });
await browser.close();
