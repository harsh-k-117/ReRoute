import { expect, test } from "@playwright/test";

test("initial plan to disruption preview and confirmation", async ({ page }) => {
  await page.goto("http://127.0.0.1:5173/");
  await expect(page.getByRole("heading", { name: "Dispatch board" })).toBeVisible();
  const navigation = page.getByRole("navigation", { name: "Sections" });
  await navigation.getByRole("button", { name: "Disruptions" }).click();
  await page.getByRole("button", { name: "Preview impact" }).click();
  await expect(page.getByText("Pending confirmation")).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirm proposal" })).toBeEnabled();
  await page.getByRole("button", { name: "Confirm proposal" }).click();
  await expect(page.getByText("Confirmed", { exact: true })).toBeVisible();
  await navigation.getByRole("button", { name: "Compare" }).click();
  await expect(page.getByText("Impact diff")).toBeVisible();
  await expect(page.getByText("Plan comparison")).toBeVisible();
  await navigation.getByRole("button", { name: "Verify" }).click();
  await expect(page.getByText("Verify I1–I12")).toBeVisible();
});