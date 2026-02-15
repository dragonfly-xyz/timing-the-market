import { test, expect } from "@playwright/test";

test.describe("Homepage", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("loads with 200 status", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.status()).toBe(200);
  });

  test("renders hero section with main question", async ({ page }) => {
    const heading = page.locator("h1");
    await expect(heading).toContainText("Does it matter when a token launches");
  });

  test("renders navigation with all links", async ({ page }) => {
    const nav = page.locator("nav");
    await expect(nav).toBeVisible();

    for (const label of ["Overview", "Explorer", "Analysis", "Methodology"]) {
      await expect(nav.getByText(label)).toBeVisible();
    }
  });

  test("renders Dragonfly logo", async ({ page }) => {
    const logo = page.locator('img[alt="Dragonfly"]');
    await expect(logo).toBeVisible();
  });

  test("renders BULL or BEAR branding", async ({ page }) => {
    const nav = page.locator("nav");
    await expect(nav.locator("text=BULL")).toBeVisible();
    await expect(nav.locator("text=BEAR")).toBeVisible();
  });

  test("renders verdict section with dynamic content", async ({ page }) => {
    const verdictLabel = page.getByText("The Verdict");
    await expect(verdictLabel).toBeVisible();

    // Should show one of the two verdicts
    const verdictText = page.locator("section").filter({ hasText: "The Verdict" });
    const content = await verdictText.textContent();
    expect(
      content?.includes("No statistically significant difference") ||
      content?.includes("Statistically significant difference detected")
    ).toBeTruthy();
  });

  test("displays Mann-Whitney p-value in verdict", async ({ page }) => {
    const pValueText = page.getByText(/Mann-Whitney p\s*=/);
    await expect(pValueText).toBeVisible();
  });

  test("displays Key Limitations section", async ({ page }) => {
    const limitations = page.getByText("Key Limitations");
    await expect(limitations).toBeVisible();

    // Should have at least a few limitation items
    const section = page.locator("section").filter({ hasText: "Key Limitations" });
    const items = section.locator("li");
    expect(await items.count()).toBeGreaterThanOrEqual(2);
  });

  test("renders bull vs bear comparison cards", async ({ page }) => {
    await expect(page.getByText("Bull Market Launches")).toBeVisible();
    await expect(page.getByText("Bear Market Launches")).toBeVisible();

    // Check for metric labels
    await expect(page.getByText("median annualized ROI").first()).toBeVisible();
    await expect(page.getByText("vs BTC").first()).toBeVisible();
    await expect(page.getByText("delist rate").first()).toBeVisible();
  });

  test("displays sample sizes next to bull/bear headers", async ({ page }) => {
    // Sample size indicators like (n=123)
    const bullSection = page.locator("text=Bull Market Launches").locator("..");
    const bullContent = await bullSection.textContent();
    expect(bullContent).toMatch(/n=\d+/);
  });

  test("displays token count summary", async ({ page }) => {
    await expect(page.getByText(/\d+ tokens analyzed/)).toBeVisible();
    await expect(page.getByText(/\d+ with launch date/)).toBeVisible();
  });

  test("renders BTC timeline chart section", async ({ page }) => {
    await expect(page.getByText("Token Launches on the BTC Price Timeline")).toBeVisible();
  });

  test("renders launch distribution section", async ({ page }) => {
    await expect(page.getByText("Launches Per Market Cycle")).toBeVisible();
  });

  test("renders footer", async ({ page }) => {
    const footer = page.locator("footer");
    await expect(footer).toContainText("CoinGecko");
    await expect(footer).toContainText("not financial advice");
  });

  test("has no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto("/");
    await page.waitForTimeout(1000);
    // Filter out known non-critical errors (favicon, etc)
    const realErrors = errors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    );
    expect(realErrors).toHaveLength(0);
  });
});
