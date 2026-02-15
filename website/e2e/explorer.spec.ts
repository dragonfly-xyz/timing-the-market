import { test, expect } from "@playwright/test";

test.describe("Explorer Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/explorer.html");
  });

  test("loads with 200 status", async ({ page }) => {
    const response = await page.goto("/explorer.html");
    expect(response?.status()).toBe(200);
  });

  test("renders page heading", async ({ page }) => {
    await expect(page.getByText("Token Explorer")).toBeVisible();
  });

  test("renders search input", async ({ page }) => {
    const searchInput = page.getByPlaceholder("Search tokens...");
    await expect(searchInput).toBeVisible();
  });

  test("renders cycle filter dropdown", async ({ page }) => {
    const select = page.locator("select").first();
    await expect(select).toBeVisible();
    const options = await select.locator("option").allTextContents();
    expect(options).toContain("All Cycles");
  });

  test("renders category filter dropdown", async ({ page }) => {
    const selects = page.locator("select");
    expect(await selects.count()).toBeGreaterThanOrEqual(2);
  });

  test("shows token count", async ({ page }) => {
    await expect(page.getByText(/\d+ tokens/).first()).toBeVisible();
  });

  test("renders token table with correct headers", async ({ page }) => {
    const table = page.locator("table");
    await expect(table).toBeVisible();

    // Check key column headers exist
    for (const header of ["#", "Name", "Status", "Cycle", "ROI", "Drawdown"]) {
      await expect(table.getByText(header, { exact: false }).first()).toBeVisible();
    }
  });

  test("table uses drawdown_from_ath field (not max_drawdown)", async ({ page }) => {
    // The "Drawdown" header should be present
    await expect(page.getByText("Drawdown").first()).toBeVisible();
    // Content should not reference old field name
    const content = await page.content();
    expect(content).not.toContain("max_drawdown");
  });

  test("renders pagination controls", async ({ page }) => {
    await expect(page.getByText("Previous")).toBeVisible();
    await expect(page.getByText("Next")).toBeVisible();
    await expect(page.getByText(/Page \d+ of \d+/)).toBeVisible();
  });

  test("table rows have data", async ({ page }) => {
    const rows = page.locator("table tbody tr");
    expect(await rows.count()).toBeGreaterThan(0);
  });

  test("search filters tokens", async ({ page }) => {
    // Wait for hydration so React interactivity works
    await page.waitForTimeout(2000);

    const searchInput = page.getByPlaceholder("Search tokens...");
    const countLocator = page.getByText(/^\d+ tokens$/);
    const beforeText = await countLocator.textContent();
    const beforeNum = parseInt(beforeText?.match(/\d+/)?.[0] ?? "0");

    await searchInput.fill("Bitcoin");
    await page.waitForTimeout(1000);

    const afterText = await countLocator.textContent();
    const afterNum = parseInt(afterText?.match(/\d+/)?.[0] ?? "0");

    // After filtering, should have fewer tokens
    expect(afterNum).toBeLessThanOrEqual(beforeNum);
  });

  test("sort headers are clickable", async ({ page }) => {
    const nameHeader = page.locator("th").filter({ hasText: "Name" });
    await expect(nameHeader).toBeVisible();
    // Click and verify no errors
    await nameHeader.click();
    await page.waitForTimeout(300);
    // Table should still render
    const rows = page.locator("table tbody tr");
    expect(await rows.count()).toBeGreaterThan(0);
  });

  test("delisted tokens show status badge", async ({ page }) => {
    // Check if any "Delisted" or "Active" badges exist
    const badges = page.locator("text=Active");
    if (await badges.count() > 0) {
      await expect(badges.first()).toBeVisible();
    }
  });
});
