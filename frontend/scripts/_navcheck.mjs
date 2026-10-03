/**
 * The navigation pill's own contract — the parts `smoke.mjs` does not reach.
 *
 * Smoke runs entirely under `reducedMotion: "reduce"`, where the pill is
 * permanently expanded, and it only asserts the 390px toggle-and-dialog path.
 * The collapsed state, the hover and keyboard expansion, and the focus ring are
 * therefore never exercised by the main suite. This checks them directly.
 *
 *   node scripts/_navcheck.mjs [baseUrl]
 */
import { chromium } from "playwright";

const BASE = (process.argv[2] || "http://127.0.0.1:3000").replace(/\/$/, "");
const BEIGE = "rgb(239, 227, 200)"; // --surface, the panel plane
const ACCENT = "rgb(77, 60, 96)"; // --accent inside the panel plane

const failures = [];
const check = (ok, label, detail = "") => {
  if (!ok) failures.push(`${label}${detail ? ` — ${detail}` : ""}`);
  console.log(`${ok ? "PASS" : "FAIL"}: ${label}${detail ? ` — ${detail}` : ""}`);
};

const browser = await chromium.launch();
const errors = [];

/** Everything the pill is doing right now, read from one page. */
const readPill = (page) =>
  page.evaluate(() => {
    const pill = document.querySelector(".nav-pill");
    if (!pill) return null;
    const cs = getComputedStyle(pill);
    const links = [...pill.querySelectorAll("a")].map((a) => {
      const s = getComputedStyle(a);
      const focused = document.activeElement === a ? getComputedStyle(a) : null;
      return {
        label: a.textContent.trim(),
        href: a.getAttribute("href"),
        active: a.getAttribute("data-active") === "true",
        current: a.getAttribute("aria-current"),
        opacity: Number(s.opacity),
        width: Math.round(a.getBoundingClientRect().width),
        color: s.color,
        outlineStyle: focused && focused.outlineStyle,
        outlineColor: focused && focused.outlineColor,
      };
    });
    const pillRect = pill.getBoundingClientRect();
    return {
      label: pill.getAttribute("aria-label"),
      background: cs.backgroundColor,
      overflow: cs.overflow,
      links,
      rect: { top: Math.round(pillRect.top), width: Math.round(pillRect.width) },
      expanded: pill.matches(":hover") || pill.matches(":focus-within"),
    };
  });

// ---------------------------------------------------------------- desktop
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1600); // let the opening cover finish and unmount

  const collapsed = await readPill(page);
  check(collapsed !== null, "the pill renders as .nav-pill");
  check(collapsed?.label === "Main navigation", "the pill is a named nav landmark", collapsed?.label);
  check(collapsed?.links.length === 5, "five links are in the DOM", `${collapsed?.links.length}`);
  check(
    collapsed?.links.filter((l) => l.active).length === 1,
    "exactly one link is active",
  );
  check(
    collapsed?.links.find((l) => l.active)?.current === "location",
    "the active link carries aria-current=location",
  );
  check(
    collapsed?.links.every((l) => l.href?.startsWith("/")),
    "every link is a real href, not an onClick handler",
  );
  check(collapsed?.background === BEIGE, "the pill paints the beige panel surface", collapsed?.background);
  check(
    collapsed?.links.filter((l) => !l.active).every((l) => l.opacity === 0 && l.width < 1),
    "collapsed: inactive links are drawn at zero width and exactly zero opacity",
    collapsed?.links.filter((l) => !l.active).map((l) => `${l.label}:${l.opacity}/${l.width}`).join(" "),
  );
  const activeAtRest = collapsed?.links.find((l) => l.active);
  check(activeAtRest?.opacity === 1 && activeAtRest.width > 20, "collapsed: the active label is drawn", `${activeAtRest?.label} ${activeAtRest?.width}px`);
  await page.screenshot({ path: "artifacts/nav-pill-collapsed.png", clip: { x: 0, y: 0, width: 1440, height: 120 } });

  // ---- hover expands
  await page.hover(".nav-pill");
  await page.waitForTimeout(600);
  const hovered = await readPill(page);
  check(
    hovered?.links.every((l) => l.opacity === 1 && l.width > 0),
    "hover: every link is fully drawn",
    hovered?.links.map((l) => `${l.label}:${l.width}`).join(" "),
  );
  const hoverOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  check(hoverOverflow <= 1, "hover: the expanded pill does not overflow the page", `${hoverOverflow}px`);
  await page.screenshot({ path: "artifacts/nav-pill-hover.png", clip: { x: 0, y: 0, width: 1440, height: 120 } });

  // ---- keyboard: Tab into the pill, and the ring that comes with it
  await page.mouse.move(1400, 700); // leave the pill, let it collapse again
  await page.waitForTimeout(800);
  await page.evaluate(() => document.body.focus());
  let inPill = false;
  for (let i = 0; i < 20 && !inPill; i++) {
    await page.keyboard.press("Tab");
    inPill = await page.evaluate(() => !!document.activeElement?.closest(".nav-pill"));
  }
  check(inPill, "keyboard: Tab reaches the pill without a mouse");
  await page.waitForTimeout(600);
  const focusedState = await readPill(page);
  check(
    focusedState?.links.every((l) => l.opacity === 1 && l.width > 0),
    "keyboard: focus-within opens the pill, so no link is an invisible tab stop",
    focusedState?.links.map((l) => `${l.label}:${l.opacity}`).join(" "),
  );
  const ring = focusedState?.links.find((l) => l.outlineStyle && l.outlineStyle !== "none");
  check(!!ring, "keyboard: the focused link draws a focus ring");
  check(ring?.outlineColor === ACCENT, "keyboard: the ring is the panel accent, not an inherited colour", ring?.outlineColor);
  await page.screenshot({ path: "artifacts/nav-pill-focus.png", clip: { x: 0, y: 0, width: 1440, height: 120 } });

  // ---- the pill must read the same over the slate ground and over a beige panel
  const surfaces = [];
  for (const y of [0, 2600, 6200, 9800]) {
    await page.evaluate((top) => window.scrollTo(0, top), y);
    await page.waitForTimeout(700);
    const at = await readPill(page);
    surfaces.push({ y, bg: at?.background, top: at?.rect.top, color: at?.links.find((l) => l.active)?.color });
  }
  check(
    surfaces.every((s) => s.bg === BEIGE),
    "both planes: the pill is opaque, so its surface is identical over slate and over beige",
    surfaces.map((s) => `${s.y}:${s.bg}`).join(" "),
  );
  check(
    surfaces.every((s) => s.top >= 0 && s.top < 200),
    "both planes: the pill stays pinned to the top of the viewport",
    surfaces.map((s) => `${s.y}:${s.top}`).join(" "),
  );

  await page.close();
}

// ------------------------------------------------------------- responsive
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  for (const width of [1440, 1280, 1024, 768, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(1200);
    const after = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      pill: document.querySelector(".nav-pill")?.getBoundingClientRect().width ?? 0,
      toggle: (() => {
        const b = document.querySelector(".menu-toggle");
        if (!b) return "none";
        const r = b.getBoundingClientRect();
        return `${getComputedStyle(b).display} ${Math.round(r.width)}x${Math.round(r.height)}`;
      })(),
    }));
    check(after.overflow <= 1, `no horizontal overflow at ${width}px`, `${after.overflow}px`);
    check(after.pill <= width, `the pill fits the viewport at ${width}px`, `${Math.round(after.pill)}px`);
    if (width < 1024) check(after.toggle !== "none", `the menu toggle is available at ${width}px`, after.toggle);
    if (width === 390) {
      await page.screenshot({
        path: "artifacts/nav-pill-mobile.png",
        clip: { x: 0, y: 0, width, height: 110 },
      });
    }
  }
  await page.close();
}

// ------------------------------------------------------------- the brand
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1600);

  const readBrand = () =>
    page.evaluate(() => {
      const el = document.querySelector(".site-nav .brand");
      if (!el) return null;
      const box = el.getBoundingClientRect();
      const label = el.querySelector("span:last-child");
      return {
        href: el.getAttribute("href"),
        name: el.getAttribute("aria-label"),
        background: getComputedStyle(el).backgroundColor,
        ink: getComputedStyle(label).color,
        centre: Math.round(box.left + box.width / 2),
      };
    });

  const brand = await readBrand();
  check(brand !== null, "the brand plate renders in the header");
  check(brand?.href === "/", "the brand links to the home page", brand?.href);
  check(brand?.name === "Sentinel home", "the brand link is named for screen readers", brand?.name);
  check(brand?.background === BEIGE, "the brand paints the pill's beige", brand?.background);
  check(
    brand?.centre < 1440 / 3,
    "the brand sits in the top-left",
    `centre ${brand?.centre}px of 1440`,
  );
  check(
    brand?.ink === "rgb(31, 21, 12)",
    "the brand's ink is the panel ink, not the ground's near-white",
    brand?.ink,
  );

  // The pill must stay optically centred now that it has a neighbour.
  const pillCentre = await page.evaluate(() => {
    const r = document.querySelector(".nav-pill").getBoundingClientRect();
    return Math.round(r.left + r.width / 2);
  });
  check(Math.abs(pillCentre - 720) <= 2, "the pill stays centred in the viewport", `centre ${pillCentre}px of 720`);

  // The header is fixed and the page scrolls beige panels under it, so the
  // brand has to carry its own surface rather than depend on what is behind it.
  const surfaces = [];
  for (const y of [0, 2600, 6200, 9800]) {
    await page.evaluate((top) => window.scrollTo(0, top), y);
    await page.waitForTimeout(700);
    const at = await readBrand();
    surfaces.push(`${y}:${at?.background}`);
    if (at?.background !== BEIGE) check(false, `brand surface over the page at y=${y}`, at?.background);
  }
  check(surfaces.length === 4, "brand surface sampled across the page", surfaces.join(" "));

  await page.screenshot({ path: "artifacts/nav-brand.png", clip: { x: 0, y: 0, width: 1440, height: 120 } });
  await page.close();
}

// --------------------------------------------------------- per-route label
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const readLabel = () =>
    page.evaluate(
      () => document.querySelector('.nav-pill a[data-active="true"]')?.textContent.trim() ?? null,
    );
  const park = async (fraction) => {
    await page.evaluate((f) => {
      const el = document.getElementById("security");
      window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - window.innerHeight * f);
    }, fraction);
    await page.waitForTimeout(900);
  };

  // `/docs` carries its own `#agents` and `#security`, so a fallback that only
  // fired when *no* target existed would never fire there and the pill would sit
  // on the first link until the reader happened to scroll into one.
  for (const [route, want] of [
    ["/", "Platform"],
    ["/docs", "Docs"],
    ["/architecture", "Platform"],
  ]) {
    await page.goto(BASE + route, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(1400);
    const got = await readLabel();
    check(got === want, `${route} at the top reads "${want}"`, `got "${got}"`);
  }

  await page.goto(BASE + "/docs", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1400);
  await park(0.25); // section top lands inside the spy's band
  const inSection = await readLabel();
  check(inSection === "Security", "a section in the band outranks the page label", `got "${inSection}"`);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(900);
  const backAtTop = await readLabel();
  check(backAtTop === "Docs", "scrolling back above the first section restores the page label", `got "${backAtTop}"`);

  await page.close();
}

await browser.close();
console.log(`\n${failures.length ? `FAILED — ${failures.length} problem(s)` : "OK — every nav check passed"}`);
for (const f of failures) console.log(`  ${f}`);
if (errors.length) console.log(`page errors: ${JSON.stringify(errors)}`);
process.exit(failures.length ? 1 : 0);
