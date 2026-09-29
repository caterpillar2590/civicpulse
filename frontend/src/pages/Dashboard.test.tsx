import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Dashboard } from "../pages/Dashboard";
import { api } from "../api/client";
import { ApiError } from "../api/types";

vi.mock("../api/client", () => ({
  api: { listComplaints: vi.fn(), updateStatus: vi.fn() },
}));

const SAMPLE = {
  id: "abc-123",
  text: "Pothole on main road",
  location: "Main Road",
  reporter_contact: null,
  category: "roads",
  priority: "high",
  status: "resolved", // terminal - has no valid transitions
  ai_summary: "Pothole on main road",
  triaged_by: "rules",
  triage_latency_ms: 10,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("Dashboard view", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("marks a terminal-status complaint as final with no transition buttons", async () => {
    (api.listComplaints as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [SAMPLE],
      total: 1,
      page: 1,
      page_size: 10,
    });

    render(<Dashboard />);
    expect(await screen.findByText("final")).toBeInTheDocument();
  });

  it("surfaces the server's 409 message verbatim instead of a generic error", async () => {
    const openComplaint = { ...SAMPLE, status: "open" };
    (api.listComplaints as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [openComplaint],
      total: 1,
      page: 1,
      page_size: 10,
    });
    (api.updateStatus as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(409, "Invalid transition: cannot move from 'open' to 'resolved'")
    );

    const user = userEvent.setup();
    render(<Dashboard />);

    const button = await screen.findByRole("button", { name: /in_progress/i });
    await user.click(button);

    expect(
      await screen.findByText("Invalid transition: cannot move from 'open' to 'resolved'")
    ).toBeInTheDocument();
  });
});
