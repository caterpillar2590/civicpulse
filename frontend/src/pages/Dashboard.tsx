import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import {
  ApiError,
  CATEGORIES,
  Category,
  ComplaintOut,
  PRIORITIES,
  Priority,
  STATUSES,
  Status,
  VALID_TRANSITIONS,
} from "../api/types";
import { Badge } from "../components/Badge";

const PAGE_SIZE = 10;

export function Dashboard() {
  const [items, setItems] = useState<ComplaintOut[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<Category | "">("");
  const [priority, setPriority] = useState<Priority | "">("");
  const [status, setStatus] = useState<Status | "">("");
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string>("");
  const [transitionError, setTransitionError] = useState<{ id: string; message: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const data = await api.listComplaints({ page, page_size: PAGE_SIZE, category, priority, status });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Could not load complaints.");
    } finally {
      setLoading(false);
    }
  }, [page, category, priority, status]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleTransition(complaint: ComplaintOut, newStatus: Status) {
    setTransitionError(null);
    try {
      const updated = await api.updateStatus(complaint.id, newStatus);
      setItems((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Server's 409 message surfaced verbatim - never a generic "error".
        setTransitionError({ id: complaint.id, message: err.message });
      } else {
        setTransitionError({
          id: complaint.id,
          message: err instanceof ApiError ? err.message : "Could not update status.",
        });
      }
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="page dashboard-page">
      <h1>Operations dashboard</h1>

      <div className="filters">
        <label>
          Category
          <select
            value={category}
            onChange={(e) => {
              setPage(1);
              setCategory(e.target.value as Category | "");
            }}
          >
            <option value="">All</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <label>
          Priority
          <select
            value={priority}
            onChange={(e) => {
              setPage(1);
              setPriority(e.target.value as Priority | "");
            }}
          >
            <option value="">All</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>

        <label>
          Status
          <select
            value={status}
            onChange={(e) => {
              setPage(1);
              setStatus(e.target.value as Status | "");
            }}
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && <p role="status">Loading complaints...</p>}
      {loadError && (
        <p role="alert" className="form-error">
          {loadError}
        </p>
      )}

      {!loading && !loadError && (
        <table className="complaints-table">
          <thead>
            <tr>
              <th>Location</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Summary</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td>{c.location}</td>
                <td>
                  <Badge label={c.category} />
                </td>
                <td>
                  <Badge label={c.priority} tone={c.priority} />
                </td>
                <td>
                  <Badge label={c.status} tone={c.status} />
                </td>
                <td className="summary-cell">{c.ai_summary}</td>
                <td>
                  {VALID_TRANSITIONS[c.status].length === 0 ? (
                    <span className="terminal-note">final</span>
                  ) : (
                    <div className="transition-buttons">
                      {VALID_TRANSITIONS[c.status].map((next) => (
                        <button key={next} onClick={() => handleTransition(c, next)}>
                          → {next}
                        </button>
                      ))}
                    </div>
                  )}
                  {transitionError?.id === c.id && (
                    <p role="alert" className="field-error">
                      {transitionError.message}
                    </p>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={6}>No complaints match these filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span>
          Page {page} of {totalPages} ({total} total)
        </span>
        <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </div>
    </div>
  );
}
