import { test, expect } from "@playwright/test";

test.describe("Navigation & Cross-Page", () => {
  test("all pages return 200", async ({ page }) => {
    for (const path of ["/", "/analysis.html", "/explorer.html", "/methodology.html"]) {
      const response = await page.goto(path);
      expect(response?.status(), `Expected 200 for ${path}`).toBe(200);
    }
  });

  test("nav links are present on every page", async ({ page }) => {
    for (const path of ["/", "/analysis.html", "/explorer.html", "/methodology.html"]) {
      await page.goto(path);
      const nav = page.locator("nav");
      await expect(nav).toBeVisible();
      for (const label of ["Overview", "Explorer", "Analysis", "Methodology"]) {
        await expect(nav.getByText(label)).toBeVisible();
      }
    }
  });

  test("footer is present on every page", async ({ page }) => {
    for (const path of ["/", "/analysis.html", "/explorer.html", "/methodology.html"]) {
      await page.goto(path);
      const footer = page.locator("footer");
      await expect(footer).toBeVisible();
    }
  });

  test("pages have appropriate titles", async ({ page }) => {
    await page.goto("/");
    const title = await page.title();
    expect(title).toContain("Bull or Bear");
  });

  test("dark theme is applied (black background)", async ({ page }) => {
    await page.goto("/");
    const body = page.locator("body");
    const bg = await body.evaluate((el) => getComputedStyle(el).backgroundColor);
    // Should be black or very close to it
    expect(bg).toMatch(/rgb\(0,\s*0,\s*0\)/);
  });

  test("no broken images on homepage", async ({ page }) => {
    await page.goto("/");
    const images = page.locator("img");
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const img = images.nth(i);
      const naturalWidth = await img.evaluate(
        (el) => (el as HTMLImageElement).naturalWidth
      );
      const src = await img.getAttribute("src");
      expect(naturalWidth, `Image ${src} should load`).toBeGreaterThan(0);
    }
  });
});
