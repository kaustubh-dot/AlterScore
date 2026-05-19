const pillars = [
  {
    title: "27-Question Assessment",
    description:
      "Covering financial literacy, future orientation, risk preference, locus of control, resilience, social capital, and more.",
    type: "dots",
  },
  {
    title: "Behavioral Telemetry",
    description:
      "Response timing, answer confidence, scroll hesitation, typing cadence, and session patterns feed the model silently.",
    type: "wave",
  },
  {
    title: "6-Model Ensemble",
    description:
      "A calibrated stacking ensemble with SHAP explainability and DICE counterfactual generation.",
    type: "graph",
  },
];

function Icon({ type }) {
  if (type === "wave") {
    return (
      <svg className="pillar-icon" viewBox="0 0 80 80" aria-hidden="true">
        <path d="M8 42 C 20 18, 30 18, 42 42 S 64 66, 74 42" />
        <path d="M8 50 C 20 30, 30 30, 42 50 S 64 70, 74 50" />
        <path d="M8 34 C 20 10, 30 10, 42 34 S 64 58, 74 34" />
      </svg>
    );
  }

  if (type === "graph") {
    const nodes = [[18, 20], [58, 18], [66, 52], [38, 62], [12, 48], [40, 36]];
    return (
      <svg className="pillar-icon" viewBox="0 0 80 80" aria-hidden="true">
        {nodes.slice(0, 5).map(([x, y], index) => (
          <line key={index} x1={x} y1={y} x2="40" y2="36" />
        ))}
        {nodes.map(([x, y], index) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={index === 5 ? 6 : 4} />
        ))}
      </svg>
    );
  }

  return (
    <svg className="pillar-icon pillar-icon--dots" viewBox="0 0 80 80" aria-hidden="true">
      {Array.from({ length: 25 }, (_, index) => {
        const x = 16 + (index % 5) * 12;
        const y = 16 + Math.floor(index / 5) * 12;
        return <circle key={index} cx={x} cy={y} r="2.6" className={index < 22 ? "is-lit" : ""} />;
      })}
    </svg>
  );
}

function handleMove(event) {
  const rect = event.currentTarget.getBoundingClientRect();
  event.currentTarget.style.setProperty("--mx", `${event.clientX - rect.left}px`);
  event.currentTarget.style.setProperty("--my", `${event.clientY - rect.top}px`);
}

export default function PillarsSection() {
  return (
    <section className="pillars-section" data-section>
      <p className="section-label">How it works</p>
      <div className="pillar-grid">
        {pillars.map((pillar, index) => (
          <article
            className="pillar-card"
            key={pillar.title}
            onMouseMove={handleMove}
            style={{ "--stagger": `${index * 100}ms` }}
            data-cursor="interactive"
          >
            <Icon type={pillar.type} />
            <h3>{pillar.title}</h3>
            <p>{pillar.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
