import { test, expect } from "@playwright/test";
test("dashboard loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-hero")).toBeVisible();
  await expect(page.getByTestId("dashboard-kpis")).toBeVisible();
  await expect(page.getByTestId("sidebar-toggle")).toBeVisible();
});
