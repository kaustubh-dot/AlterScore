const statusItems = [
  "Feature registry foundation is in place.",
  "Backend runtime settings and path helpers are wired.",
  "API request and response schemas are defined.",
  "Frontend pages and flows are intentionally still pending.",
];

export default function App() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">AlterScore</p>
        <h1>Frontend package scaffold</h1>
        <p className="lede">
          This is the initial React and Vite skeleton for the borrower and evaluator
          interfaces. Product screens come after backend contracts and data assets
          settle.
        </p>
      </section>

      <section className="panel-grid" aria-label="Project readiness">
        <article className="panel">
          <h2>Current focus</h2>
          <ul className="status-list">
            {statusItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <h2>API base</h2>
          <p className="mono">{apiBaseUrl}</p>
          <p className="muted">
            The frontend reads its backend URL from <code>VITE_API_BASE_URL</code>.
          </p>
        </article>
      </section>
    </main>
  );
}
