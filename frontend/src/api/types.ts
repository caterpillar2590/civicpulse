export type Category = "water" | "electricity" | "sanitation" | "roads" | "streetlights" | "other";
export type Priority = "high" | "normal" | "low";
export type Status = "open" | "in_progress" | "resolved" | "rejected";

export const CATEGORIES: Category[] = ["water", "electricity", "sanitation", "roads", "streetlights", "other"];
export const PRIORITIES: Priority[] = ["high", "normal", "low"];
export const STATUSES: Status[] = ["open", "in_progress", "resolved", "rejected"];

// Mirrors app.models.schemas.VALID_TRANSITIONS on the backend. This is NOT
// used to decide anything here - only to grey out obviously-invalid buttons
// in the UI. The backend's 409 response is always the source of truth.
export const VALID_TRANSITIONS: Record<Status, Status[]> = {
  open: ["in_progress", "rejected"],
  in_progress: ["resolved", "rejected"],
  resolved: [],
  rejected: [],
};

export interface ComplaintCreate {
  text: string;
  location: string;
  reporter_contact?: string | null;
}

export interface ComplaintOut {
  id: string;
  text: string;
  location: string;
  reporter_contact: string | null;
  category: Category;
  priority: Priority;
  status: Status;
  ai_summary: string | null;
  triaged_by: string;
  triage_latency_ms: number | null;
  created_at: string;
  updated_at: string;
}

export interface ComplaintListOut {
  items: ComplaintOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface StatsOut {
  total: number;
  by_category: Partial<Record<Category, number>>;
  by_priority: Partial<Record<Priority, number>>;
}

export interface ProviderOutcome {
  provider: string;
  latency_ms: number;
  fallback: boolean;
  timestamp: string;
}

export interface ProvidersMeta {
  active_provider: string;
  recent_outcomes: ProviderOutcome[];
}

export interface FieldError {
  field: string;
  message: string;
}

export class ApiError extends Error {
  status: number;
  fieldErrors: FieldError[];
  retryAfter: number | null;

  constructor(status: number, message: string, fieldErrors: FieldError[] = [], retryAfter: number | null = null) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
    this.retryAfter = retryAfter;
  }
}
