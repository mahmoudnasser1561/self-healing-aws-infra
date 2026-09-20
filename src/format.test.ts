import { expect, test } from "vitest";
import { formatDate } from "./format";

test("formats an ISO timestamp for the requested locale and zone", () => {
  expect(
    formatDate("2026-01-02T03:04:05+00:00", { locale: "en-US", timeZone: "UTC" }),
  ).toBe("Jan 2, 2026, 3:04 AM");
});

test("respects the time zone", () => {
  expect(
    formatDate("2026-01-02T03:04:05+00:00", {
      locale: "en-US",
      timeZone: "America/New_York",
    }),
  ).toBe("Jan 1, 2026, 10:04 PM");
});
