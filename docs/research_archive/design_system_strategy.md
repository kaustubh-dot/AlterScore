# AlterScore: Design System Strategy

This document defines the visual identity, typography system, color tokens, spacing metrics, and accessibility standards for the AlterScore frontend client, ensuring a research-grade, trustworthy interface.

---

## 1. Visual Theme & Color System

AlterScore uses a **dark-mode-first visual language** inspired by scientific terminals and modern financial dashboards. The theme prioritizes legibility, high contrast, and a calm, institutional appearance.

### Core Color Palette

```
[ Background ]          [ Grid Border ]         [ Accent Teal ]         [ Accent Purple ]
  #04050F                 #1E2235                 #30F2D2                 #A78BFF
```

* **Core Backgrounds**:
  * Main Shell Background: `#04050F` (deep dark blue-slate)
  * Panel Backgrounds: `#090B16` or `rgba(255, 255, 255, 0.01)`
* **Accents & Highlights**:
  * Primary Accent: Teal (`#30F2D2` / `rgb(48,242,210)`) — used for positive status, success actions, and active sliders.
  * Secondary Accent: Purple (`#A78BFF` / `rgb(167,139,255)`) — used for baseline comparisons and information tags.
* **Borders & Dividers**:
  * Standard Borders: `#1E2235` or `rgba(255, 255, 255, 0.05)`
  * Interactive Hover Borders: `rgba(48, 242, 210, 0.3)`
* **Semantic Status Indicators**:
  * Success/Excellent: `var(--status-excellent)` — Green (`#30F2D2`)
  * Moderate/Fair: `var(--status-fair)` — Yellow-Orange (`#FFAD33`)
  * Critical/Poor: `var(--status-poor)` — Coral-Red (`#FF4D5E`)

---

## 2. Typography & Scale

The typeface choices reinforce a professional, data-centric interface.

| Font Role | Font Family | CSS Declaration | Character Style |
| :--- | :--- | :--- | :--- |
| **Headers & Titles** | Outfit / Inter | `font-family: 'Outfit', sans-serif;` | Clear geometric letterforms. |
| **Body Copy** | Inter / Roboto | `font-family: 'Inter', sans-serif;` | High readability, neutral stance. |
| **Technical / Metrics** | Roboto Mono | `font-family: 'Roboto Mono', monospace;` | Data values, version numbers, manifest hashes. |

### Type Scale (16px base)
* **h1 (Page Title)**: `2.25rem` (36px) — Bold, tracked slightly tight (`-0.02em`).
* **h2 (Section Title)**: `1.5rem` (24px) — Semibold.
* **h3 (Panel Title)**: `1.125rem` (18px) — Medium.
* **Body**: `0.95rem` (15px) — Regular, line-height `1.6`.
* **Micro-text (Labels)**: `0.75rem` (12px) — Monospace, tracked wide (`0.1em`, uppercase).

---

## 3. Card Elevations & Spacing tokens

* **Spacing Scale**: Mapped to an 8px grid system:
  * `0.25rem` (4px), `0.5rem` (8px), `1.0rem` (16px), `1.5rem` (24px), `2.0rem` (32px), `3.0rem` (48px).
* **Elevation & Transparency**:
  * Instead of heavy shadows, panels use sharp borders (`1px solid var(--border)`) and a subtle background color.
  * Backdrop filter blur (`backdrop-filter: blur(12px)`) is applied to floating components to separate them from the grain background.

---

## 4. Animation Philosophy & Micro-interactions

Animations must be smooth and purposeful, avoiding flashy or distracting effects:
* **GSAP Timings**: Standard sliding transition is `0.55s` using the `power3.out` easing curve.
* **Stagger Effects**: Lists and charts fade in sequentially using small stagger delays (`0.08s` per item) to help the user scan the content naturally.
* **Interactive Hover States**: Buttons and cards transition smoothly (`transition: all 0.2s ease-in-out`). Hovering expands border colors and scales accent highlights to indicate interactivity clearly.
