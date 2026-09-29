import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Stats } from "../pages/Stats";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: { getStats: vi.fn() },
}));

describe("Stats view", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays HIT when the X-Cache header comes back as a hit", async () => {
    (api.getStats as ReturnType<typeof vi.fn>).mockResolvedValue({
      total: 42,
      by_category: { water: 10, roads: 5 },
      by_priority: { high: 3, normal: 30, low: 9 },
      __cache: "HIT",
    });

    render(<Stats />);

    expect(await screen.findByTestId("cache-indicator")).toHaveTextContent("HIT");
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("displays MISS when the X-Cache header comes back as a miss", async () => {
    (api.getStats as ReturnType<typeof vi.fn>).mockResolvedValue({
      total: 5,
      by_category: {},
      by_priority: {},
      __cache: "MISS",
    });

    render(<Stats />);
    expect(await screen.findByTestId("cache-indicator")).toHaveTextContent("MISS");
  });
});
