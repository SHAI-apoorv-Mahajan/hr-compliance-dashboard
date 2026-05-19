import { describe, expect, it, vi } from "vitest";

vi.mock("./api/auth", () => ({
  me: vi.fn().mockRejectedValue(new Error("no token")),
  login: vi.fn(),
}));

import App from "./App.jsx";

describe("App smoke", () => {
  it("App is a component", () => {
    expect(typeof App).toBe("function");
  });
});
