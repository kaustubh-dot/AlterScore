/**
 * ScenarioDilemmaCard — Full-card behavioral scenario component.
 *
 * Renders a realistic financial scenario with 3–4 response option cards.
 * Supports a soft optional secondary "Least Like Me" pick after the primary
 * selection is made — secondary pick never blocks progression.
 *
 * Telemetry captured here:
 *   - firstClickTime: ms from card render to first option selection (per scenario)
 *   - optionChanges: incremented each time the primary pick changes
 * These are passed up via onAnswer(optionId, telemetry).
 */

import { useEffect, useRef, useState } from "react";

export default function ScenarioDilemmaCard({ question, selectedId, onAnswer }) {
  const renderTimeRef = useRef(Date.now());
  const [firstClickRecorded, setFirstClickRecorded] = useState(false);
  const [changeCount, setChangeCount] = useState(0);
  const [showLeast, setShowLeast] = useState(false);
  const [leastId, setLeastId] = useState(null);

  // Reset when question changes
  useEffect(() => {
    renderTimeRef.current = Date.now();
    setFirstClickRecorded(false);
    setChangeCount(0);
    setShowLeast(false);
    setLeastId(null);
  }, [question.id]);

  // Show the "Least Like Me" nudge 400ms after a primary pick is made
  useEffect(() => {
    if (!selectedId) return;
    const t = window.setTimeout(() => setShowLeast(true), 400);
    return () => window.clearTimeout(t);
  }, [selectedId]);

  function handlePrimaryPick(optionId) {
    const now = Date.now();
    const firstClickMs = firstClickRecorded ? null : now - renderTimeRef.current;
    if (!firstClickRecorded) setFirstClickRecorded(true);

    const newChangeCount = selectedId && selectedId !== optionId ? changeCount + 1 : changeCount;
    setChangeCount(newChangeCount);

    // If the previously selected least-like option was the same as new primary, clear it
    if (leastId === optionId) setLeastId(null);

    onAnswer(optionId, {
      firstClickMs,
      changeCount: newChangeCount,
      leastId: leastId === optionId ? null : leastId,
    });
  }

  function handleLeastPick(optionId) {
    // Cannot select the same as primary
    if (optionId === selectedId) return;
    const newLeastId = leastId === optionId ? null : optionId; // toggle off if clicked again
    setLeastId(newLeastId);
    onAnswer(selectedId, {
      firstClickMs: null,
      changeCount,
      leastId: newLeastId,
    });
  }

  return (
    <div className="scenario-card">
      <div className="scenario-options">
        {question.options.map((option) => {
          const isPrimary = selectedId === option.id;
          const isLeastSelected = leastId === option.id;
          const isDisabledLeast = showLeast && selectedId === option.id;

          return (
            <button
              key={option.id}
              type="button"
              className={[
                "scenario-option",
                isPrimary ? "scenario-option--primary" : "",
                isLeastSelected ? "scenario-option--least" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => handlePrimaryPick(option.id)}
              aria-pressed={isPrimary}
            >
              <span className="scenario-option__text">{option.text}</span>

              {isPrimary && (
                <span className="scenario-option__badge scenario-option__badge--most">
                  Most like me
                </span>
              )}
              {isLeastSelected && (
                <span className="scenario-option__badge scenario-option__badge--least">
                  Least like me
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Soft secondary pick — optional, never blocks progression */}
      {showLeast && (
        <div className="scenario-least-nudge">
          <p className="scenario-least-nudge__label">
            Optional — which of the remaining feels <em>least</em> like your approach?
          </p>
          <div className="scenario-least-options">
            {question.options
              .filter((opt) => opt.id !== selectedId)
              .map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  className={[
                    "scenario-least-option",
                    leastId === opt.id ? "scenario-least-option--active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => handleLeastPick(opt.id)}
                >
                  {opt.text}
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
