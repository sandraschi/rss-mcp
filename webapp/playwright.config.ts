import { defineConfig } from "@playwright/test";
export default defineConfig({ testDir: "./e2e", webServer: { command: "bun run dev --port 11975", port: 11975, reuseExistingServer: true } });
