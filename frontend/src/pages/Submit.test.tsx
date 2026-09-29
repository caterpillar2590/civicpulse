import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { Submit } from "../pages/Submit";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: { submitComplaint: vi.fn() },
}));

describe("Submit view", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a client-side error and does not call the API when text is too short", async () => {
    const user = userEvent.setup();
    render(<Submit />);

    await user.type(screen.getByLabelText(/what happened/i), "too short");
    await user.type(screen.getByLabelText(/location/i), "Street 12");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    expect(await screen.findByText(/at least 10 characters/i)).toBeInTheDocument();
    expect(api.submitComplaint).not.toHaveBeenCalled();
  });

  it("shows an honest loading state while the AI triage call is in flight", async () => {
    let resolvePromise: (value: unknown) => void = () => {};
    (api.submitComplaint as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      })
    );

    const user = userEvent.setup();
    render(<Submit />);

    await user.type(screen.getByLabelText(/what happened/i), "Burst water main flooding street");
    await user.type(screen.getByLabelText(/location/i), "Street 12");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    expect(await screen.findByText(/triaging your complaint/i)).toBeInTheDocument();

    resolvePromise({
      id: "1",
      text: "Burst water main flooding street",
      location: "Street 12",
      reporter_contact: null,
      category: "water",
      priority: "high",
      status: "open",
      ai_summary: "Burst water main flooding street",
      triaged_by: "rules",
      triage_latency_ms: 12,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    await waitFor(() => expect(screen.getByTestId("triage-result")).toBeInTheDocument());
    expect(screen.getByText(/rules/)).toBeInTheDocument();
  });

  it("renders the returned category, priority and provider after a successful submit", async () => {
    (api.submitComplaint as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: "2",
      text: "Streetlight has been broken for weeks",
      location: "Street 9",
      reporter_contact: null,
      category: "streetlights",
      priority: "normal",
      status: "open",
      ai_summary: "Streetlight broken",
      triaged_by: "llm:groq",
      triage_latency_ms: 800,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    const user = userEvent.setup();
    render(<Submit />);
    await user.type(screen.getByLabelText(/what happened/i), "Streetlight has been broken for weeks");
    await user.type(screen.getByLabelText(/location/i), "Street 9");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    expect(await screen.findByText("streetlights")).toBeInTheDocument();
    expect(screen.getByText("normal")).toBeInTheDocument();
    expect(screen.getByText(/llm:groq/)).toBeInTheDocument();
  });
});
