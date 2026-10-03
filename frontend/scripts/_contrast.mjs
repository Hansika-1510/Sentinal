/**
 * Contrast sweep — the arbiter for a two-plane theme.
 *
 * The stylesheets cannot tell us which surface an element lands on: DOM nesting
 * crosses class-name boundaries, so `.root-card-bottom` inherits the panel its
 * `.root-cause-card` ancestor paints without sharing a substring of its name.
 * Only the live tree knows. This walks every text-bearing element on every
 * route, composites the real background behind it, and reports anything under
 * the WCAG floor.
 *
 * It walks each route top to bottom rather than sampling the top: state-driven
 * rules (`.loop-word.is-past`, pinned scenes, the scrolled nav) only exist at
 * some offsets. Every step waits for the scroll and the reveal tweens to come
 * to rest, and anything still flagged is measured a second time at rest before
 * it is reported — so what comes out is text a reader can actually see, at the
 * contrast it actually has.
 *
 *   node scripts/_contrast.mjs [baseUrl] [--all]
 */
import { chromium } from "playwright";

const BASE = (process.argv[2] || process.env.BASE_URL || "http://127.0.0.1:3001").replace(/\/$/, "");
const SHOW_ALL = process.argv.includes("--all");
const ROUTES = ["/", "/console", "/docs", "/architecture"];

const SWEEP = () => {
  const srgb = (c) => {
    c /= 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  };
  const lum = ([r, g, b]) => 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b);
  const parse = (s) => {
    const m = /rgba?\(([^)]+)\)/.exec(s || "");
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    if (p.length < 3 || p.some(Number.isNaN)) return null;
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  };
  const over = (f, b) => [
    f[0] * f[3] + b[0] * (1 - f[3]),
    f[1] * f[3] + b[1] * (1 - f[3]),
    f[2] * f[3] + b[2] * (1 - f[3]),
    1,
  ];
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
    return (x + 0.05) / (y + 0.05);
  };
  const gradStop = (img) => {
    if (!img || img === "none" || !/gradient\(/.test(img)) return null;
    const cols = img.match(/rgba?\([^)]+\)/g);
    if (!cols) return null;
    const ps = cols.map(parse).filter(Boolean);
    if (!ps.length) return null;
    // Average the stops: a panel painted as a gradient is uniformly beige in
    // practice, so the mean lands within a point of contrast of any stop.
    const n = ps.length;
    return [
      ps.reduce((s, p) => s + p[0], 0) / n,
      ps.reduce((s, p) => s + p[1], 0) / n,
      ps.reduce((s, p) => s + p[2], 0) / n,
      1,
    ];
  };
  const effBg = (el) => {
    const chain = [];
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const cs = getComputedStyle(n);
      const g = gradStop(cs.backgroundImage);
      const bg = parse(cs.backgroundColor);
      // A gradient paints over the background colour, so it wins when present.
      if (g) chain.push(g);
      else if (bg && bg[3] > 0) chain.push(bg);
    }
    let base = [255, 255, 255, 1];
    for (let i = chain.length - 1; i >= 0; i--) base = over(chain[i], base);
    return base;
  };
  const path = (el) => {
    const parts = [];
    for (let n = el; n && n.nodeType === 1 && parts.length < 4; n = n.parentElement) {
      let s = n.tagName.toLowerCase();
      if (n.id) s += "#" + n.id;
      const cls = (n.getAttribute("class") || "").trim().split(/\s+/).filter(Boolean).slice(0, 2);
      if (cls.length) s += "." + cls.join(".");
      parts.unshift(s);
    }
    return parts.join(" > ");
  };

  // Every rule that could be setting this element's colour, media queries
  // included. This is the whole point of the tool: the browser can say which
  // declaration is responsible, and no static reading of the stylesheets can.
  const flatten = (list, out) => {
    for (const r of list) {
      // A style rule also carries `cssRules` now that CSS nesting exists, so it
      // must be tested for, not treated as a container.
      if (r.selectorText) out.push(r);
      if (r.cssRules && r.cssRules.length) flatten(r.cssRules, out);
    }
    return out;
  };
  const allRules = [];
  for (const sh of document.styleSheets) {
    try {
      flatten(sh.cssRules, allRules);
    } catch {
      /* cross-origin sheet — none here, but never let it kill the sweep */
    }
  }
  const ownRules = (el) =>
    allRules
      .filter((r) => r.style.getPropertyValue("color"))
      .filter((r) => {
        try {
          return el.matches(r.selectorText);
        } catch {
          return false;
        }
      })
      .map((r) => `${r.selectorText} { color: ${r.style.getPropertyValue("color")} }`);

  const out = [];
  for (const el of document.querySelectorAll("body *")) {
    if (el.closest("nextjs-portal")) continue;
    // direct text only — an ancestor is reported on its own turn
    const text = [...el.childNodes]
      .filter((n) => n.nodeType === 3)
      .map((n) => n.textContent.trim())
      .join(" ")
      .trim();
    if (!text) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none") continue;
    if (el.getBoundingClientRect().width < 1) continue;
    const fill = parse(cs.webkitTextFillColor || cs.color) || parse(cs.color);
    if (!fill) continue;
    // Element opacity composites too. A paragraph left at opacity 0.4 is
    // genuinely lower-contrast than its colour alone suggests, and scoring the
    // colour at full strength would report a pass for text nobody can read.
    let alpha = fill[3];
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const o = parseFloat(getComputedStyle(n).opacity);
      if (!Number.isNaN(o)) alpha *= o;
    }
    if (alpha < 0.05) continue;
    const bg = effBg(el);
    const fg = over([fill[0], fill[1], fill[2], alpha], bg);
    const size = parseFloat(cs.fontSize);
    const weight = parseInt(cs.fontWeight, 10) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const need = large ? 3 : 4.5;
    const c = ratio(fg, bg);
    if (c + 0.005 < need) {
      out.push({
        sel: path(el),
        text: text.slice(0, 42),
        c: Math.round(c * 100) / 100,
        need,
        fg: cs.color,
        bg: `rgb(${bg.slice(0, 3).map(Math.round).join(", ")})`,
        size: Math.round(size * 10) / 10,
        rules: ownRules(el),
      });
    }
  }
  return out;
};

const browser = await chromium.launch();
let total = 0;
for (const route of ROUTES) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(BASE + route, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(700);

  // Walk the document rather than sampling the top of it. State-dependent rules
  // — `.loop-word.is-past`, pinned scenes, the scrolled nav — only exist at some
  // offsets, so a single pass would report the page clean while a third of its
  // text was never looked at.
  //
  // Every step has to wait for the page to come to rest before it is believed.
  // The reveal tweens leave an element at opacity 0 with a 36px offset until
  // ScrollTrigger fires, and Lenis keeps gliding after `scrollTo` returns, so a
  // fixed sleep samples a page still in motion and reports the half-faded text
  // as a contrast failure. Wait for the scroll position to stop moving, then
  // give the reveal its own duration on top.
  const settle = async () => {
    let last = -1;
    let stable = 0;
    for (let i = 0; i < 50 && stable < 3; i++) {
      const y = await page.evaluate(() => Math.round(window.scrollY));
      stable = y === last ? stable + 1 : 0;
      last = y;
      await page.waitForTimeout(100);
    }
    await page.waitForTimeout(1100);
  };

  const fails = [];
  const seenKey = new Set();
  const STEPS = 10;
  for (let i = 0; i <= STEPS; i++) {
    if (i > 0) {
      await page.evaluate((frac) => {
        const h = document.documentElement.scrollHeight - window.innerHeight;
        window.scrollTo(0, Math.round(h * frac));
      }, i / STEPS);
      await settle();
    }
    for (const f of await page.evaluate(SWEEP)) {
      const key = f.sel + f.fg + f.bg;
      if (seenKey.has(key)) continue;
      seenKey.add(key);
      fails.push(f);
    }
  }
  // Anything still flagged is re-measured once more, at rest, before it is
  // reported — a candidate that resolves on a second look was an animation.
  const recheck = new Set(fails.map((f) => f.sel));
  await settle();
  const stillFailing = new Set(
    (await page.evaluate(SWEEP)).filter((f) => recheck.has(f.sel)).map((f) => f.sel + f.fg + f.bg),
  );
  const confirmed = fails.filter((f) => stillFailing.has(f.sel + f.fg + f.bg));
  total += confirmed.length;
  console.log(`\n=== ${route} — ${confirmed.length} failure(s) ===`);
  const seen = new Set();
  const culprits = new Set();
  for (const f of confirmed) {
    for (const r of f.rules) culprits.add(r);
    const key = f.sel + f.fg + f.bg;
    if (!SHOW_ALL && seen.has(key)) continue;
    seen.add(key);
    console.log(
      `  ${String(f.c).padEnd(6)} / ${f.need}  ${f.fg} on ${f.bg}  ${String(f.size).padStart(5)}px  ${f.sel}`,
    );
    for (const r of f.rules) console.log(`        ↳ ${r}`);
    console.log(`        "${f.text}"`);
  }
  if (culprits.size) {
    console.log(`\n  --- distinct rules setting a colour here (${culprits.size}) ---`);
    for (const r of [...culprits].sort()) console.log(`  ${r}`);
  }
  await page.close();
}
await browser.close();
console.log(`\nTOTAL: ${total}`);
process.exit(total ? 1 : 0);
