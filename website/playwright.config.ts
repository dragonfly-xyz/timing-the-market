import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: "http://localhost:3000",
    headless: true,
  },
  webServer: {
    command: "python3 -m http.server 3000 --directory out",
    port: 3000,
    reuseExistingServer: true,
  },
});
