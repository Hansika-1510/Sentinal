import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
for (const [route, name] of [["/console","beige-console"],["/docs","beige-docs"],["/architecture","beige-architecture"]]) {
  await p.goto("http://127.0.0.1:3000" + route, { waitUntil: "networkidle" });
  await p.waitForTimeout(1200);
  await p.screenshot({ path: `artifacts/${name}.png` });
  console.log(name, "ok");
}
await b.close();
