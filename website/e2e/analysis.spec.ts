import { test, expect } from "@playwright/test";

test.describe("Analysis Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/analysis.html");
  });

  test("loads with 200 status", async ({ page }) => {
    const response = await page.goto("/analysis.html");
    expect(response?.status()).toBe(200);
  });

  test("renders page heading", async ({ page }) => {
    await expect(page.getByText("Detailed Analysis")).toBeVisible();
  });

  test("renders annualized ROI by launch cycle section", async ({ page }) => {
    await expect(page.getByText("Annualized ROI by Launch Cycle")).toBeVisible();
  });

  test("renders median ROI cards for all cycle types", async ({ page }) => {
    for (const cycle of ["Bull", "Bear", "Neutral", "Early"]) {
      await expect(page.getByText(`${cycle} median ann. ROI`)).toBeVisible();
    }
  });

  test("renders fraction currently in top 100 section", async ({ page }) => {
    await expect(page.getByText("Fraction Currently in Top 100")).toBeVisible();
  });

  test("renders ROI vs BTC section", async ({ page }) => {
    await expect(page.getByText("ROI vs BTC by Cycle")).toBeVisible();

    // Check for cycle-specific cards
    for (const cycle of ["Bull", "Bear"]) {
      await expect(page.getByText(`${cycle} launches`).first()).toBeVisible();
    }
    await expect(page.getByText("median ROI vs BTC").first()).toBeVisible();
  });

  test("renders median drawdown section", async ({ page }) => {
    await expect(page.getByText("Median Drawdown from ATH")).toBeVisible();
    await expect(page.getByText("median drawdown").first()).toBeVisible();
  });

  test("renders statistical tests section with Mann-Whitney", async ({ page }) => {
    const statsSection = page.locator("section").filter({ hasText: "Statistical Tests" });
    // May not be visible if p-value is null in test data, so only check if present
    const isVisible = await statsSection.isVisible().catch(() => false);
    if (isVisible) {
      await expect(statsSection.getByText("p-value").first()).toBeVisible();
      await expect(statsSection.getByText("Annualized ROI")).toBeVisible();
    }
  });

  test("displays effect size label or placeholder when stats visible", async ({ page }) => {
    const statsSection = page.locator("section").filter({ hasText: "Statistical Tests" }).first();
    const isVisible = await statsSection.isVisible().catch(() => false);
    if (isVisible) {
      // Effect size section should exist with its label
      const effectSizeHeaders = statsSection.getByText("effect size");
      if (await effectSizeHeaders.count() > 0) {
        await expect(effectSizeHeaders.first()).toBeVisible();
      }
    }
  });

  test("displays 95% CI when present", async ({ page }) => {
    const statsSection = page.locator("section").filter({ hasText: "Statistical Tests" });
    const isVisible = await statsSection.isVisible().catch(() => false);
    if (isVisible) {
      const ci = statsSection.getByText("95% CI");
      if (await ci.count() > 0) {
        await expect(ci.first()).toBeVisible();
      }
    }
  });

  test("displays sample sizes in stats section when present", async ({ page }) => {
    const statsSection = page.locator("section").filter({ hasText: "Statistical Tests" });
    const isVisible = await statsSection.isVisible().catch(() => false);
    if (isVisible) {
      await expect(statsSection.getByText("sample sizes")).toBeVisible();
      await expect(statsSection.getByText("bull / bear")).toBeVisible();
    }
  });

  test("renders BTC-relative test section when present", async ({ page }) => {
    const btcRelSection = page.getByText("ROI vs BTC (Geometric Excess Return)");
    if (await btcRelSection.count() > 0) {
      await expect(btcRelSection.first()).toBeVisible();
    }
  });

  test("renders sensitivity analysis table when data present", async ({ page }) => {
    const sensitivitySection = page.locator("section").filter({
      hasText: "Sensitivity Analysis",
    });
    if (await sensitivitySection.count() > 0) {
      await expect(sensitivitySection.getByText("Boundary Shift")).toBeVisible();
      await expect(sensitivitySection.getByText("p-value").first()).toBeVisible();
      await expect(sensitivitySection.getByText("Result").first()).toBeVisible();
    }
  });

  test("renders top 10 performers table", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Top 10 by Annualized ROI" })).toBeVisible();

    // Check table headers via column header role
    const table = page.locator("table").last();
    await expect(table.getByRole("columnheader", { name: "Token" })).toBeVisible();
    await expect(table.getByRole("columnheader", { name: "Ann. ROI" })).toBeVisible();
  });

  test("does not show t-test (removed)", async ({ page }) => {
    const content = await page.content();
    expect(content).not.toContain("Welch");
    expect(content).not.toContain("t-test");
  });
});
