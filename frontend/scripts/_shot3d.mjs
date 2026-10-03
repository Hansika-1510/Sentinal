import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
await p.goto("http://127.0.0.1:3000/", { waitUntil: "networkidle" });
for (const [sel, name] of [["#root-cause","beige-evidence3d"],["#platform","beige-journey3d"]]) {
  await p.locator(sel).scrollIntoViewIfNeeded();
  await p.waitForTimeout(2600);
  await p.screenshot({ path: `artifacts/${name}.png` });
  console.log(name, "ok");
}
await b.close();
