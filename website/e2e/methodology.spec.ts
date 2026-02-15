import { test, expect } from "@playwright/test";

test.describe("Methodology Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/methodology.html");
  });

  test("loads with 200 status", async ({ page }) => {
    const response = await page.goto("/methodology.html");
    expect(response?.status()).toBe(200);
  });

  test("renders page heading", async ({ page }) => {
    const heading = page.locator("h1");
    await expect(heading).toContainText("Methodology");
  });

  test("renders data source section with API links", async ({ page }) => {
    await expect(page.getByText("Data Source")).toBeVisible();
    await expect(page.getByText("Binance announcements")).toBeVisible();
    await expect(page.getByText("CoinGecko API")).toBeVisible();
  });

  test("renders data filtering section", async ({ page }) => {
    await expect(page.getByText("Data Filtering")).toBeVisible();
    // Should mention stablecoins and wrapped tokens
    await expect(page.getByText("Stablecoins")).toBeVisible();
    await expect(page.getByText(/[Ww]rapped/)).toBeVisible();
  });

  test("renders launch date determination section", async ({ page }) => {
    await expect(page.getByText("Launch Date Determination")).toBeVisible();
    // Should mention genesis_date
    await expect(page.getByText("genesis_date")).toBeVisible();
  });

  test("renders dead token imputation section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Dead Token Imputation" })).toBeVisible();
    // Check for the minus 100% ROI mention (uses &minus; HTML entity)
    const section = page.locator("section").filter({ hasText: "Dead Token Imputation" }).first();
    const text = await section.textContent();
    expect(text).toMatch(/100%\s*ROI/);
  });

  test("renders market cycle definitions with table", async ({ page }) => {
    await expect(page.getByText("Market Cycle Definitions")).toBeVisible();

    // Table should have cycle data
    const table = page.locator("table").first();
    await expect(table).toBeVisible();
    await expect(table.getByText("Cycle")).toBeVisible();
    await expect(table.getByText("Start")).toBeVisible();
    await expect(table.getByText("End")).toBeVisible();
    await expect(table.getByText("Type")).toBeVisible();
  });

  test("renders metrics section with correct definitions", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Metrics" })).toBeVisible();

    // Check key metrics are documented
    await expect(page.getByText("ROI since launch", { exact: true })).toBeVisible();
    await expect(page.getByText("Annualized ROI (CAGR)")).toBeVisible();
    await expect(page.getByText("ROI vs BTC", { exact: true })).toBeVisible();
    await expect(page.getByText("Drawdown from ATH", { exact: true })).toBeVisible();
    await expect(page.getByText("Fraction currently in top 100")).toBeVisible();
    await expect(page.getByText("Delist rate", { exact: true })).toBeVisible();
  });

  test("documents geometric excess return for BTC-relative", async ({ page }) => {
    // The methodology should mention the geometric formula
    const content = await page.textContent("body");
    expect(content).toContain("(1 + token_ROI) / (1 + BTC_ROI) - 1");
  });

  test("renders statistical tests section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Statistical Tests" })).toBeVisible();
    await expect(page.getByText("Mann-Whitney U test")).toBeVisible();
    await expect(page.getByText("rank-biserial correlation")).toBeVisible();
    await expect(page.getByText("bootstrap 95% confidence intervals")).toBeVisible();
  });

  test("does not mention t-test", async ({ page }) => {
    const content = await page.textContent("body");
    expect(content?.toLowerCase()).not.toContain("t-test");
    expect(content?.toLowerCase()).not.toContain("welch");
  });

  test("renders important caveats section", async ({ page }) => {
    await expect(page.getByText("Important Caveats")).toBeVisible();

    const caveatsSection = page.locator("section").filter({
      hasText: "Important Caveats",
    });
    const items = caveatsSection.locator("li");
    expect(await items.count()).toBeGreaterThanOrEqual(5);
  });

  test("caveats include dead token imputation", async ({ page }) => {
    const caveatsSection = page.locator("section").filter({
      hasText: "Important Caveats",
    });
    await expect(caveatsSection.getByText("Dead token imputation")).toBeVisible();
  });

  test("mentions not financial advice", async ({ page }) => {
    await expect(page.getByText("Not financial advice", { exact: true })).toBeVisible();
  });
});
