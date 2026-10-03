import fs from "node:fs/promises";
import lighthouse from "lighthouse";
import { launch } from "chrome-launcher";

await fs.mkdir("artifacts", { recursive: true });
const chrome = await launch({
  chromePath: process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe",
  chromeFlags: ["--headless=new", "--no-first-run", "--no-default-browser-check"],
});
const results = [];
try {
  for (const profile of ["desktop", "mobile"]) {
    const options = {
      port: chrome.port,
      logLevel: "error",
      output: ["html", "json"],
      onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
      ...(profile === "desktop"
        ? {
            formFactor: "desktop",
            screenEmulation: {
              mobile: false,
              width: 1440,
              height: 960,
              deviceScaleFactor: 1,
              disabled: false,
            },
          }
        : { formFactor: "mobile" }),
    };
    const run = await lighthouse(process.env.BASE_URL || "http://127.0.0.1:3000", options);
    await fs.writeFile(`artifacts/lighthouse-${profile}.html`, run.report[0]);
    await fs.writeFile(`artifacts/lighthouse-${profile}.json`, run.report[1]);
    const metrics = Object.fromEntries(
      [
        "first-contentful-paint",
        "largest-contentful-paint",
        "total-blocking-time",
        "cumulative-layout-shift",
        "speed-index",
      ].map((id) => [id, run.lhr.audits[id].displayValue]),
    );
    const summary = {
      profile,
      scores: Object.fromEntries(
        Object.entries(run.lhr.categories).map(([name, category]) => [
          name,
          Math.round(category.score * 100),
        ]),
      ),
      metrics,
      failedAudits: Object.values(run.lhr.audits)
        .filter((a) => a.score !== null && a.score < 1 && a.details?.type !== "opportunity")
        .map((a) => ({ id: a.id, title: a.title, score: a.score, displayValue: a.displayValue })),
    };
    results.push(summary);
    console.log(JSON.stringify(summary, null, 2));
  }
  await fs.writeFile("artifacts/lighthouse-summary.json", JSON.stringify(results, null, 2));
} finally {
  await chrome.kill();
}
