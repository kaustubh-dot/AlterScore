import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  LANDING_CHAPTERS,
  LANDING_GLYPH_FIELDS,
  LANDING_SPATIAL_COPY,
} from "../../data/landingChapters.js";
import { useVisualExperience } from "../../context/VisualExperienceContext.jsx";

function getScrollProgress() {
  const max = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
  return Math.min(Math.max(window.scrollY / max, 0), 1);
}

function findActiveChapter(progress) {
  return (
    LANDING_CHAPTERS.find((chapter) => progress >= chapter.range[0] && progress <= chapter.range[1]) ||
    LANDING_CHAPTERS.reduce((nearest, chapter) => {
      const center = (chapter.range[0] + chapter.range[1]) / 2;
      const nearestCenter = (nearest.range[0] + nearest.range[1]) / 2;
      return Math.abs(progress - center) < Math.abs(progress - nearestCenter) ? chapter : nearest;
    }, LANDING_CHAPTERS[0])
  );
}

export default function CinematicLanding() {
  const { setMode, setChapterProgress } = useVisualExperience();
  const [progress, setProgress] = useState(0);
  const [unityStatus, setUnityStatus] = useState("booting");
  const sessionId = useMemo(() => `AS-${Math.floor(Math.random() * 90000 + 10000)}`, []);
  const activeChapter = findActiveChapter(progress);
  const finalReady = progress > 0.78;

  useEffect(() => {
    setMode("landing");
    document.body.classList.add("mode-landing");
    return () => document.body.classList.remove("mode-landing");
  }, [setMode]);

  useEffect(() => {
    let frame = 0;
    let ticking = false;

    function update() {
      ticking = false;
      const nextProgress = getScrollProgress();
      setProgress(nextProgress);
      setChapterProgress(nextProgress);
    }

    function requestUpdate() {
      if (ticking) return;
      ticking = true;
      frame = window.requestAnimationFrame(update);
    }

    update();
    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("scroll", requestUpdate);
      window.removeEventListener("resize", requestUpdate);
      setChapterProgress(0);
    };
  }, [setChapterProgress]);

  useEffect(() => {
    function handleUnityStatus(event) {
      setUnityStatus(event.detail?.status || "ready");
    }

    window.addEventListener("alterscore:unity-status", handleUnityStatus);
    return () => window.removeEventListener("alterscore:unity-status", handleUnityStatus);
  }, []);

  return (
    <main
      className={`sidewave-landing${finalReady ? " is-final" : ""}`}
      style={{ "--landing-progress": progress }}
    >
      {LANDING_CHAPTERS.map((chapter) => (
        <span
          key={`${chapter.id}-anchor`}
          id={chapter.id}
          className="landing-anchor"
          style={{ top: `${chapter.range[0] * 100}%` }}
          aria-hidden="true"
        />
      ))}

      <aside className="sidewave-left-rail" aria-label="Landing chapters">
        <p className="rail-kicker">SIGNAL INDEX</p>
        <ol>
          {LANDING_CHAPTERS.map((chapter) => (
            <li key={chapter.id} className={chapter.id === activeChapter.id ? "is-active" : ""}>
              <a href={`#${chapter.id}`}>
                <span>{chapter.index}</span>
                <strong>{chapter.label}</strong>
              </a>
              <em>{chapter.summary}</em>
            </li>
          ))}
        </ol>
      </aside>

      <div className="sidewave-right-rail" aria-hidden="true">
        <span style={{ transform: `scaleY(${Math.max(progress, 0.015)})` }} />
      </div>

      <div className="sidewave-scroll-cue" aria-hidden="true">
        <span>SCROLL TO DISCOVER</span>
        <i />
      </div>

      <div className="sidewave-session" aria-hidden="true">
        <span>SESSION // {sessionId}</span>
        <span>UNITY // {unityStatus.toUpperCase()}</span>
      </div>

      {LANDING_SPATIAL_COPY.map((copy) => (
        <section key={copy.id} className={`spatial-copy ${copy.className}`}>
          <p>{copy.kicker}</p>
          <h1>{copy.title}</h1>
          <span>{copy.body}</span>
        </section>
      ))}

      {LANDING_GLYPH_FIELDS.map((field) => (
        <div key={field.id} className={`signal-glyph-field ${field.className}`} aria-hidden="true">
          {Array.from({ length: 5 }, (_, index) => (
            <span key={`${field.id}-${index}`}>{field.text}</span>
          ))}
        </div>
      ))}

      <section id="start" className="landing-final-chamber" aria-label="Begin assessment">
        <p>ACCESS</p>
        <h2>A fuller credit signal is ready.</h2>
        <Link className="signal-cta signal-cta--dominant" to="/assessment" data-magnetic>
          <span>Begin assessment</span>
          <i>↗</i>
        </Link>
      </section>

      <div className="landing-scroll-spacer" aria-hidden="true" />
    </main>
  );
}
