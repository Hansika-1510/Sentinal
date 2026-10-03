import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
await p.goto("http://127.0.0.1:3000/", { waitUntil: "networkidle" });
console.log(JSON.stringify(await p.evaluate(() =>
  [...document.querySelectorAll(".telemetry-chart svg linearGradient stop")].map((s) => ({
    attr: s.getAttribute("stop-color"),
    computed: getComputedStyle(s).stopColor,
  })),
), null, 1));
await b.close();
