/**
 * Non-text mark sweep — borders and SVG strokes that lost their surface.
 *
 * `_contrast.mjs` reads text colour, which says nothing about the hairline
 * rules, orbit rings and node outlines the page leans on. A mark tuned to be
 * "one step off the ground" is the first thing to disappear when the ground
 * moves, and WCAG's 3:1 floor for meaningful graphics does not catch it if
 * nothing measures the mark.
 *
 *   node scripts/_marks.mjs [baseUrl] [--all]
 */
import { chromium } from "playwright";

const BASE = (process.argv[2] || "http://127.0.0.1:3000").replace(/\/$/, "");
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
      if (g) chain.push(g);
      else if (bg && bg[3] > 0) chain.push(bg);
    }
    let base = [255, 255, 255, 1];
    for (let i = chain.length - 1; i >= 0; i--) base = over(chain[i], base);
    return base;
  };
  const path = (el) => {
    const parts = [];
    for (let n = el; n && n.nodeType === 1 && parts.length < 3; n = n.parentElement) {
      let s = n.tagName.toLowerCase();
      if (n.id) s += "#" + n.id;
      const cls = (n.getAttribute("class") || "").trim().split(/\s+/).filter(Boolean).slice(0, 2);
      if (cls.length) s += "." + cls.join(".");
      parts.unshift(s);
    }
    return parts.join(" > ");
  };

  const out = [];
  for (const el of document.querySelectorAll("body *")) {
    if (el.closest("nextjs-portal")) continue;
    if (el.tagName === "CANVAS" || el.tagName === "IMG" || el.tagName === "SVG") continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none") continue;
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const bg = effBg(el);
    // A shape filled with its own border colour has no outline at all — the
    // border and the fill are the same pixels. Comparing them reports 1:1 and
    // says nothing about whether the shape reads against the page, so those are
    // not marks and are skipped here.
    const own = parse(cs.backgroundColor);
    const filled = (col) =>
      own &&
      own[3] > 0.9 &&
      Math.abs(own[0] - col[0]) + Math.abs(own[1] - col[1]) + Math.abs(own[2] - col[2]) < 12;
    // A rule only reads as a mark if the element is drawn with one at all.
    const widths = [cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth]
      .map(parseFloat)
      .filter((w) => w >= 1);
    const candidates = [];
    if (widths.length) {
      for (const side of ["Top", "Right", "Bottom", "Left"]) {
        if (parseFloat(cs[`border${side}Width`]) < 1) continue;
        const bc = parse(cs[`border${side}Color`]);
        if (bc && bc[3] > 0.02) candidates.push({ kind: `border-${side.toLowerCase()}`, col: bc });
      }
    }
    const oc = parse(cs.outlineColor);
    if (oc && parseFloat(cs.outlineWidth) >= 1 && cs.outlineStyle !== "none" && oc[3] > 0.02) {
      candidates.push({ kind: "outline", col: oc });
    }
    for (const c of candidates) {
      if (filled(c.col)) continue;
      const mark = over(c.col, bg);
      const cr = ratio(mark, bg);
      // 3:1 is the floor for a mark that carries meaning. A 1px rule that sits
      // below it is a decorative divider, which is legitimate — but it is also
      // exactly what an orbit ring looks like, so report both and let the
      // caller judge rather than guessing here.
      if (cr + 0.005 < 3) {
        out.push({
          sel: path(el) + ` [${c.kind}]`,
          c: Math.round(cr * 100) / 100,
          mark: `rgb(${mark.slice(0, 3).map(Math.round).join(", ")})`,
          bg: `rgb(${bg.slice(0, 3).map(Math.round).join(", ")})`,
          w: cs[`border${c.kind.split("-")[1] === "outline" ? "Top" : "Top"}Width`],
          radius: cs.borderRadius,
        });
      }
    }
  }
  return out;
};

const browser = await chromium.launch();
let total = 0;
for (const route of ROUTES) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(BASE + route, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(900);
  const fails = await page.evaluate(SWEEP);
  total += fails.length;
  console.log(`\n=== ${route} — ${fails.length} mark(s) under 3:1 ===`);
  const seen = new Set();
  for (const f of fails.sort((a, b) => a.c - b.c)) {
    const key = f.sel + f.mark;
    if (!SHOW_ALL && seen.has(key)) continue;
    seen.add(key);
    console.log(`  ${String(f.c).padEnd(6)} ${f.mark} on ${f.bg}  radius=${f.radius}  ${f.sel}`);
  }
  await page.close();
}
await browser.close();
console.log(`\nTOTAL: ${total}`);
