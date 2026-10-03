// Ad-hoc: verify the opening sequence paints, wipes, and leaves no residue, and
// that the cursor overlay arms only for a fine pointer. Not committed harness.
import { chromium } from "playwright";

const origin = process.env.BASE_URL || "http://127.0.0.1:3000";
const executablePath =
  process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";

const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  hasTouch: false,
  isMobile: false,
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});

// Do not wait for networkidle — the point is to catch the cover while it is up.
await page.goto(origin, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(320);
const during = await page.evaluate(() => {
  const intro = document.querySelector(".intro");
  if (!intro) return { present: false };
  const style = getComputedStyle(intro);
  return {
    present: true,
    display: style.display,
    clipPath: style.clipPath,
    pointerEvents: style.pointerEvents,
    zIndex: style.zIndex,
  };
});
await page.screenshot({ path: "artifacts/craft-intro.png" });

await page.waitForTimeout(1500);
const after = await page.evaluate(() => ({
  introInDom: Boolean(document.querySelector(".intro")),
  headings: document.querySelectorAll("main > section").length,
  cursorDisplay: getComputedStyle(document.querySelector(".cursor")).display,
}));

// Move the mouse so the cursor arms, then confirm the native cursor is hidden.
await page.mouse.move(700, 420);
await page.waitForTimeout(400);
const cursor = await page.evaluate(() => {
  const root = document.querySelector(".cursor");
  const ring = document.querySelector(".cursor-ring");
  const dot = document.querySelector(".cursor-dot");
  return {
    active: root?.classList.contains("is-active") ?? false,
    hasCursorClass: document.documentElement.classList.contains("has-cursor"),
    ringTransform: ring ? getComputedStyle(ring).transform : null,
    dotTransform: dot ? getComputedStyle(dot).transform : null,
  };
});
await page.screenshot({ path: "artifacts/craft-cursor.png" });

// Hover a link so the ring should grow, then a non-interactive area.
await page.hover(".button-primary");
await page.waitForTimeout(500);
const hovering = await page.evaluate(() => ({
  isHovering: document.querySelector(".cursor")?.classList.contains("is-hovering") ?? false,
  ringTransform: getComputedStyle(document.querySelector(".cursor-ring")).transform,
}));

console.log(JSON.stringify({ during, after, cursor, hovering, errors }, null, 2));
await browser.close();
