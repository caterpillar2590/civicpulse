import { useState } from "react";
import { Submit } from "./pages/Submit";
import { Dashboard } from "./pages/Dashboard";
import { Stats } from "./pages/Stats";

type Tab = "submit" | "dashboard" | "stats";

export function App() {
  const [tab, setTab] = useState<Tab>("submit");

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="brand">CivicPulse</h1>
        <nav aria-label="Main navigation">
          <button className={tab === "submit" ? "active" : ""} onClick={() => setTab("submit")}>
            Submit
          </button>
          <button className={tab === "dashboard" ? "active" : ""} onClick={() => setTab("dashboard")}>
            Dashboard
          </button>
          <button className={tab === "stats" ? "active" : ""} onClick={() => setTab("stats")}>
            Stats
          </button>
        </nav>
      </header>

      <main>
        {tab === "submit" && <Submit />}
        {tab === "dashboard" && <Dashboard />}
        {tab === "stats" && <Stats />}
      </main>
    </div>
  );
}
