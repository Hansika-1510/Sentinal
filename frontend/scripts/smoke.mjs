import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

const origin = process.env.BASE_URL || "http://127.0.0.1:3000";
const executablePath =
  process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
await fs.mkdir("artifacts", { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 960 },
  reducedMotion: "reduce",
  permissions: ["clipboard-read", "clipboard-write"],
});
const page = await context.newPage();
const errors = [];
const checks = [];
const accessibility = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});
const check = async (name, test) => {
  await test();
  checks.push(name);
  console.log("PASS:", name);
};
const bodyIncludes = async (text) =>
  assert.ok((await page.locator("body").innerText()).includes(text), `Expected text: ${text}`);
const within = (selector, role, name) =>
  page.locator(selector).getByRole(role, { name, exact: true });

try {
  await check("Landing page and full narrative", async () => {
    const response = await page.goto(origin, { waitUntil: "networkidle" });
    assert.equal(response.status(), 200);
    assert.equal(await page.getByRole("heading", { level: 1 }).count(), 1);
    assert.equal(await page.locator("main > section").count(), 17);
    for (const id of [
      "platform",
      "runtime",
      "investigation",
      "root-cause",
      "fix-advisor",
      "verification",
      "recovery",
      "memory",
      "human-control",
      "agents",
      "console-preview",
      "security",
    ])
      assert.equal(await page.locator(`#${id}`).count(), 1);
    assert.equal(
      await page.locator(".lens-canvas canvas").count(),
      0,
      "Reduced motion should use the static lens",
    );
  });
  await check("Architecture nodes and evidence are explorable", async () => {
    await within("#platform", "button", "Developer").click();
    assert.match(await page.locator(".journey-main").innerText(), /developer chooses the change/i);
    await page
      .locator("#root-cause")
      .getByRole("button", { name: /Runtime stack trace/ })
      .click();
    assert.match(await page.locator(".evidence-detail").innerText(), /stack frame/);
    await page
      .locator("#fix-advisor")
      .getByRole("button", { name: /^Line 47:/ })
      .click();
    assert.match(await page.locator(".code-insight").innerText(), /Early return/);
    await within("#fix-advisor", "button", "Copy guidance").click();
    await within("#fix-advisor", "button", "Copied").waitFor();
    assert.equal(await within("#fix-advisor", "button", "Copied").count(), 1);
  });
  await check("Human approval can be rejected, reset, and approved with a reason", async () => {
    await within("#human-control", "button", "Reject").click();
    assert.match(await page.locator("#human-control").innerText(), /Rejected. You’re in control./);
    await within("#human-control", "button", "Reset example").click();
    await within("#human-control", "button", "Approve").click();
    const dialog = page.getByRole("dialog");
    assert.equal(await dialog.getByRole("button", { name: "Confirm approval" }).isDisabled(), true);
    await dialog
      .getByLabel("Reason for approval")
      .fill("The failing release is isolated and the rollback path is available.");
    await dialog.getByRole("button", { name: "Confirm approval" }).click();
    assert.match(await page.locator("#human-control").innerText(), /Approved. With a record./);
  });
  await check("Agent details support modal and keyboard dismissal", async () => {
    await page.getByRole("button", { name: "Meet the agent: INVESTIGATOR", exact: true }).click();
    await bodyIncludes("Treats conclusions as hypotheses to validate.");
    await page.keyboard.press("Escape");
    assert.equal(await page.getByRole("dialog").count(), 0);
  });
  await check("Responsive layouts at 1440, 1280, 1024, 768, and 390 pixels", async () => {
    for (const width of [1440, 1280, 1024, 768, 390]) {
      await page.setViewportSize({ width, height: width < 768 ? 844 : 960 });
      await page.goto(origin, { waitUntil: "networkidle" });
      await page.waitForTimeout(200);
      const layout = await page.evaluate(() => {
        const line = document.querySelector(".hero-last-line > span");
        const range = document.createRange();
        range.selectNodeContents(line);
        return {
          width: innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          headlineRight: range.getBoundingClientRect().right,
        };
      });
      assert.ok(
        layout.scrollWidth <= width + 1,
        `${width}px page overflows: ${JSON.stringify(layout)}`,
      );
      assert.ok(
        layout.headlineRight <= width + 1,
        `${width}px headline is clipped: ${JSON.stringify(layout)}`,
      );
      await page.screenshot({ path: `artifacts/viewport-${width}.png` });
    }
    await page.getByRole("button", { name: "Open navigation" }).click();
    await page.getByRole("dialog").getByRole("link", { name: "Security", exact: true }).click();
    assert.ok(page.url().endsWith("#security"));
  });
  await check("Documentation, architecture, and unknown routes", async () => {
    for (const route of ["/docs", "/architecture"]) {
      const response = await page.goto(origin + route, { waitUntil: "networkidle" });
      assert.equal(response.status(), 200);
      assert.equal(await page.getByRole("heading", { level: 1 }).count(), 1);
    }
    const missing = await page.goto(origin + "/missing-signal", { waitUntil: "networkidle" });
    assert.equal(missing.status(), 404);
    await bodyIncludes("This signal");
  });
  await page.setViewportSize({ width: 1440, height: 960 });
  await check("Console search, empty states, and incident memory", async () => {
    await page.goto(origin + "/console", { waitUntil: "networkidle" });
    await page.getByRole("searchbox", { name: "Search incidents" }).fill("no-such-service-xyz");
    await bodyIncludes("No matching incidents.");
    await page.getByRole("button", { name: "Clear search", exact: true }).click();
    await page.getByRole("searchbox", { name: "Search incidents" }).fill("billing");
    await page.getByRole("button", { name: /INC-0981/ }).click();
    await bodyIncludes("Exercise cleanup under both successful and failed requests.");
    await page.getByRole("button", { name: "Return to INC-1042", exact: true }).click();
  });
  await check("Console evidence tabs and developer guidance", async () => {
    await page.getByRole("tab", { name: "Root cause", exact: true }).click();
    await page.getByRole("button", { name: "Database errors", exact: true }).click();
    await bodyIncludes("The pool reaches its connection limit");
    await page.getByRole("tab", { name: "Root cause", exact: true }).press("ArrowRight");
    assert.equal(
      await page
        .getByRole("tab", { name: "Fix Advisor", exact: true })
        .getAttribute("aria-selected"),
      "true",
    );
    await bodyIncludes(
      "The developer writes the fix. Sentinel never modifies application source code.",
    );
    await page.getByRole("button", { name: "View developer’s example fix", exact: true }).click();
    await bodyIncludes("// Developer-authored example");
  });
  await check("Approved action persists across tabs and recovery is verified", async () => {
    await page.getByRole("tab", { name: /Approval queue/ }).click();
    await page.getByRole("button", { name: "Approve", exact: true }).click();
    const dialog = page.getByRole("dialog");
    await dialog
      .getByLabel("Reason for approval")
      .fill("Restore the known healthy release while the developer prepares the fix.");
    await dialog.getByRole("button", { name: "Confirm approval" }).click();
    await page.getByRole("tab", { name: "Audit trail", exact: true }).click();
    await bodyIncludes("Rollback approved by you");
    await page.getByRole("tab", { name: "Approval queue", exact: true }).click();
    await bodyIncludes("Approved. With a record.");
    assert.equal(
      await page.getByRole("button", { name: "Approve", exact: true }).count(),
      0,
      "A recorded decision must not re-open as pending",
    );
    await page.getByRole("button", { name: "Verify recovery", exact: true }).click();
    await page.getByText("Recovery verified", { exact: true }).waitFor();
    await page.getByRole("tab", { name: "Audit trail", exact: true }).click();
    await bodyIncludes("The approved rollback restored v1.8.2.");
    await page.screenshot({ path: "artifacts/console-recovered.png", fullPage: true });
  });
  await check("Replay resets demo and rejected actions stay rejected", async () => {
    await page.getByRole("button", { name: "Replay incident", exact: true }).click();
    await page.getByRole("button", { name: "Replay incident", exact: true }).waitFor();
    await page.getByRole("tab", { name: /Approval queue/ }).click();
    await page.getByRole("button", { name: "Reject", exact: true }).click();
    await page.getByRole("tab", { name: "Evidence timeline", exact: true }).click();
    await page.getByRole("tab", { name: "Approval queue", exact: true }).click();
    await bodyIncludes("Rejected. You’re in control.");
    assert.equal(
      await page.getByRole("button", { name: "Verify recovery", exact: true }).count(),
      0,
    );
  });
  await check("Accessibility audit of landing, console, docs, and architecture", async () => {
    const scanPage = async (label) => {
      const scan = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      accessibility.push({
        route: label,
        violations: scan.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          nodes: v.nodes.map((n) => ({
            target: n.target,
            html: n.html,
            failureSummary: n.failureSummary,
          })),
        })),
      });
    };
    for (const route of ["/", "/console", "/docs", "/architecture"]) {
      await page.goto(origin + route, { waitUntil: "networkidle" });
      if (route === "/") {
        // Scan before scrolling as well: scroll-reveal "from" states only exist
        // while their sections are still below the fold.
        await page.waitForTimeout(500);
        await scanPage("/ (top)");
        await page.locator("#console-preview").scrollIntoViewIfNeeded();
        await page.waitForTimeout(700);
      }
      await scanPage(route);
    }
    await fs.writeFile("artifacts/accessibility.json", JSON.stringify(accessibility, null, 2));
    const serious = accessibility.flatMap((result) =>
      result.violations
        .filter((v) => ["critical", "serious"].includes(v.impact))
        .map((v) => ({ route: result.route, ...v })),
    );
    if (serious.length) console.log(JSON.stringify(serious, null, 2));
    assert.equal(serious.length, 0, "Resolve critical and serious accessibility violations");
  });
  const actionableErrors = errors.filter((error) => !error.includes("404 (Not Found)"));
  if (actionableErrors.length)
    console.log("Browser errors:", JSON.stringify(actionableErrors, null, 2));
  assert.equal(actionableErrors.length, 0, "No runtime or hydration errors");
  await fs.writeFile(
    "artifacts/smoke-results.json",
    JSON.stringify({ checks, errors: actionableErrors, passed: true }, null, 2),
  );
  console.log(`All ${checks.length} browser checks passed.`);
} catch (error) {
  await page.screenshot({ path: "artifacts/test-failure.png", fullPage: false }).catch(() => {});
  await fs.writeFile(
    "artifacts/smoke-results.json",
    JSON.stringify({ checks, errors, error: String(error), passed: false }, null, 2),
  );
  console.error(error);
  process.exitCode = 1;
} finally {
  await browser.close();
}
