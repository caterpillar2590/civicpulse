import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ApiError, StatsOut } from "../api/types";

export function Stats() {
  const [stats, setStats] = useState<(StatsOut & { __cache?: string }) | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await api.getStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load stats.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="page stats-page">
      <h1>Aggregate statistics</h1>

      <button onClick={load} disabled={loading}>
        {loading ? "Refreshing..." : "Refresh"}
      </button>

      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}

      {stats && (
        <>
          {/* Showing our own cache behaviour in the UI, straight from X-Cache */}
          <p className="cache-indicator" data-testid="cache-indicator">
            Cache:{" "}
            <span className={`badge badge-${stats.__cache === "HIT" ? "resolved" : "open"}`}>
              {stats.__cache ?? "unknown"}
            </span>
          </p>

          <p className="total-count">
            Total complaints: <strong>{stats.total}</strong>
          </p>

          <div className="stats-columns">
            <section>
              <h2>By category</h2>
              <ul>
                {Object.entries(stats.by_category).map(([k, v]) => (
                  <li key={k}>
                    <span>{k}</span>
                    <span>{v}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h2>By priority</h2>
              <ul>
                {Object.entries(stats.by_priority).map(([k, v]) => (
                  <li key={k}>
                    <span>{k}</span>
                    <span>{v}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
