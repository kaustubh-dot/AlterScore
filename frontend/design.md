# AlterScore — Frontend Design Guidelines

> **Philosophy:** AlterScore is not a fintech app. It is a cognitive laboratory.
> It reads how you think. It watches how you hesitate. It interprets silence.
> The interface must feel like it already knows something about you — precise, clinical, and quietly intelligent.
> No noise. No decoration. Only signal.

---

## 0. Product Essence

AlterScore is an **alternative credit scoring engine** that replaces financial history with behavioral and psychometric signals. It answers one question: *can this person be trusted with money, based on how they think?*

The product has two faces:
1. **The Borrower Experience** — A 27-question psychometric assessment that secretly measures cognitive reflection, risk attitude, honesty, resilience, and social capital. The user does not know they are being scored as they answer.
2. **The Evaluator Dashboard** — A technical command center for loan officers and analysts, showing model performance, fairness audits, feature importance, and drift detection.

Both faces need the same visual DNA but in entirely different registers.

---

## 1. Brand Identity

### 1.1 Core Brand Concept: **"Signal Over Noise"**

AlterScore strips away the noise of traditional finance (bank statements, credit bureaus, loan histories) and listens to pure behavioral signal. The visual language should embody this:

- **Minimalism as precision** — Not empty, but *precise*. Every element earns its place.
- **Dark as depth** — The darkness isn't aesthetic; it's metaphorical. Signal is extracted from the dark.
- **Motion as intelligence** — Animations don't decorate — they *reveal*. They signal that something is being computed, observed, understood.
- **Typography as authority** — Clean, clinical, confident. Like a research paper that happens to be beautiful.

### 1.2 Tone of Voice (Visual)

| Feeling | Not This | But This |
|---|---|---|
| Serious | Heavy, oppressive | Precise, calibrated |
| Intelligent | Complex, cluttered | Sparse, deliberate |
| Trustworthy | Corporate blue | Cold silver + deep indigo |
| Human | Warm, cozy | Present, attentive — clinical warmth |
| Cutting-edge | Gradients everywhere | Micro-animation, surgical interaction |

### 1.3 Visual References (Mood)

Design DNA drawn from:
- **EEG / neural signal visualizations** — waveforms, sine pulses, amplitude traces
- **Scientific instrumentation UI** — oscilloscopes, spectrum analyzers
- **Cinematic UI** (Arrival, Ex Machina, Interstellar) — monospace terminals, sparse glyphs
- **High-end fintech**: Linear, Stripe, Vercel dashboard aesthetics — but darker and more stripped
- **The aesthetic of observation** — something is watching, measuring, processing

---

## 2. Color System

### 2.1 Background Palette (Dark First)

```
--bg-void:      #020409    /* Absolute black-navy — the abyss */
--bg-surface:   #060B14    /* Primary page background */
--bg-elevated:  #0B1221    /* Cards, panels */
--bg-overlay:   #0F1A2E    /* Modals, drawers */
--bg-border:    #111E33    /* Subtle borders */
--bg-muted:     #162035    /* Hover states, subtle highlights */
```

### 2.2 Signal Accent Colors

The primary accent color is **Electric Indigo** — it sits between blue (technical, cold) and violet (depth, intelligence). It is the color of thought becoming electricity.

```
--accent-primary:       #4C6EF5    /* Electric Indigo — primary CTA, active states */
--accent-primary-glow:  #4C6EF520  /* Glow version for ambient light effects */
--accent-secondary:     #7C3AED    /* Deep violet — secondary CTAs, selected states */
--accent-cyan:          #06B6D4    /* Cold cyan — data, numbers, telemetry values */
--accent-emerald:       #10B981    /* Success, high scores, positive signals */
--accent-amber:         #F59E0B    /* Warning, medium risk, attention */
--accent-rose:          #F43F5E    /* Danger, low scores, flags, anomalies */
```

### 2.3 Score Band Colors (Credit Score Visualization)

```
--score-excellent:  #10B981   /* 750–850: Emerald */
--score-good:       #34D399   /* 650–749: Soft Green */
--score-fair:       #FBBF24   /* 550–649: Amber */
--score-poor:       #F97316   /* 450–549: Orange */
--score-very-poor:  #F43F5E   /* 300–449: Rose */
```

### 2.4 Text Hierarchy

```
--text-primary:    #F1F5F9    /* Almost white — primary body text */
--text-secondary:  #94A3B8    /* Slate-400 — supporting copy */
--text-muted:      #475569    /* Slate-600 — captions, labels, metadata */
--text-ghost:      #1E293B    /* Near-invisible — watermarks, decorative text */
--text-accent:     #818CF8    /* Indigo-400 — highlighted terms, link text */
--text-number:     #7DD3FC    /* Sky blue — all numeric data values */
```

### 2.5 Usage Rule

> **The 90/10 rule**: 90% of every screen should be `--bg-void` to `--bg-elevated`. Accent colors appear in at most 10% of the visual field. When accent appears, it hits hard because it's rare.

---

## 3. Typography System

### 3.1 Font Stack

**Display / Hero**: `"DM Serif Display"` — elegant, intellectual serif for large hero text. Feels like a scientific paper from the future.

**Interface / Body**: `"Inter"` — the gold standard for UI legibility. Variable weight (100–900) allows infinite nuance.

**Monospace / Data**: `"JetBrains Mono"` — for all numerical values, scores, telemetry readings, API responses, code snippets. The "computer is thinking" font.

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

--font-display:  'DM Serif Display', Georgia, serif;
--font-body:     'Inter', -apple-system, sans-serif;
--font-mono:     'JetBrains Mono', 'Fira Code', monospace;
```

### 3.2 Type Scale

```
--text-xs:    0.625rem  / 10px   /* Labels, tags */
--text-sm:    0.75rem   / 12px   /* Captions, metadata */
--text-base:  0.875rem  / 14px   /* Body copy */
--text-md:    1rem      / 16px   /* Emphasized body */
--text-lg:    1.125rem  / 18px   /* Subheadings */
--text-xl:    1.25rem   / 20px   /* Section headers */
--text-2xl:   1.5rem    / 24px   /* Card titles */
--text-3xl:   2rem      / 32px   /* Page titles */
--text-4xl:   2.75rem   / 44px   /* Feature display */
--text-5xl:   3.75rem   / 60px   /* Hero secondary */
--text-6xl:   5rem      / 80px   /* Hero primary */
--text-7xl:   7rem      / 112px  /* Massive statement text */
```

### 3.3 Type Rules

- **Letter-spacing**: Hero text uses `letter-spacing: -0.03em` (tighter) for monumentality. Labels use `letter-spacing: 0.08em` (looser) for scannability.
- **Line-height**: Body copy at `1.7`. Display at `1.1`. Data values at `1.0`.
- **All-caps**: Used **only** for small labels, section identifiers, and status chips — never for body text.
- **Italic**: Used exclusively for the `DM Serif Display` font in the hero section for emphasis contrast.
- **Numbers**: Always `JetBrains Mono`. Never `Inter` for numeric values.

---

## 4. Grid & Spacing System

### 4.1 Grid

- **Max content width**: `1280px` with `auto` side margins
- **Column system**: 12-column grid
- **Gutter**: `24px` (desktop), `16px` (tablet), `12px` (mobile)
- **Section padding**: `120px` top/bottom on desktop, `72px` tablet, `48px` mobile

### 4.2 Spacing Scale (8px base)

```
--space-1:   4px
--space-2:   8px
--space-3:   12px
--space-4:   16px
--space-5:   20px
--space-6:   24px
--space-8:   32px
--space-10:  40px
--space-12:  48px
--space-16:  64px
--space-20:  80px
--space-24:  96px
--space-32:  128px
```

### 4.3 Border Radius

```
--radius-sm:   4px    /* Chips, small tags */
--radius-md:   8px    /* Inputs, small cards */
--radius-lg:   12px   /* Standard cards */
--radius-xl:   16px   /* Large panels */
--radius-2xl:  24px   /* Feature sections */
--radius-full: 9999px /* Pills, avatars */
```

---

## 5. Elevation & Depth System

AlterScore uses **light emission** (not box shadows) to create depth. Elements glow slightly. The darkness of the background makes a faint glow feel significant.

```css
/* Cards — no conventional box shadow. Use border + ambient glow */
--shadow-card:  0 0 0 1px rgba(76, 110, 245, 0.08),
                0 4px 24px rgba(0, 0, 0, 0.5);

/* Focused input — electric glow */
--shadow-focus: 0 0 0 1px #4C6EF5,
                0 0 16px rgba(76, 110, 245, 0.25);

/* Active/hover state glow */
--shadow-hover: 0 0 0 1px rgba(76, 110, 245, 0.20),
                0 8px 32px rgba(76, 110, 245, 0.12);

/* Score reveal — intense glow based on score band */
--shadow-score-excellent: 0 0 0 1px #10B981, 0 0 48px rgba(16, 185, 129, 0.25);
--shadow-score-good:      0 0 0 1px #34D399, 0 0 48px rgba(52, 211, 153, 0.20);
--shadow-score-fair:      0 0 0 1px #FBBF24, 0 0 48px rgba(251, 191, 36, 0.20);
--shadow-score-poor:      0 0 0 1px #F97316, 0 0 48px rgba(249, 115, 22, 0.20);
--shadow-score-very-poor: 0 0 0 1px #F43F5E, 0 0 48px rgba(244, 63, 94, 0.20);
```

### Glassmorphism (Selective Use)

Used only on overlaid elements (modals, tooltips, floating panels):

```css
.glass {
  background: rgba(11, 18, 33, 0.72);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(76, 110, 245, 0.10);
}
```

---

## 6. The Hero Section

### 6.1 Vision

The hero is the **first impression and the only impression that matters**. It must communicate in 2 seconds: *This is the most sophisticated credit intelligence system you have ever seen.*

It achieves this through:
1. A **cinematic full-viewport animated background** with genuine visual depth
2. A **minimal, devastating headline** — large, precise, and unsettling in the best way
3. **Living data visualizations** — waveforms, neural signal traces, floating numbers
4. A single **primary CTA** — nothing else fights for attention

### 6.2 Hero Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   [ANIMATED BACKGROUND — Full viewport, pointer-reactive]        │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                                                          │  │
│   │                        AlterScore                        │  │
│   │                                                          │  │
│   │         Credit intelligence beyond history.              │  │
│   │                                                          │  │
│   │    ┌────────────────────────────────────┐                │  │
│   │    │ We read how you think. Not what    │                │  │
│   │    │ banks have recorded about you.     │                │  │
│   │    └────────────────────────────────────┘                │  │
│   │                                                          │  │
│   │                 [Begin Assessment →]                     │  │
│   │                                                          │  │
│   │   ─────────────────────────────────────────────          │  │
│   │   27 questions  ·  5 minutes  ·  Instant score          │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 Hero Animated Background — "The Signal Field"

The background is a full-viewport `<canvas>` element rendering a **neural signal visualization** in real-time using vanilla Canvas2D or Three.js:

**What it renders:**
- A dark field (`--bg-void`) with a subtle **radial gradient** emanating from the center (very slight `--accent-primary` glow at the viewport center).
- **Multiple horizontal waveform traces** — 4 to 6 thin lines traversing the screen horizontally. These are sine waves with different frequencies, amplitudes, and phases. They are alive, constantly moving.
  - Color: `rgba(76, 110, 245, 0.25)` to `rgba(76, 110, 245, 0.08)` — different intensities
  - The lines react to mouse position: moving the mouse vertically shifts the amplitude of the nearest trace
- **Floating data glyphs** — sparse, scattered numbers, abbreviated feature names (`CRT`, `NLP`, `locus`, `0.72`, `847`, `Δψ`), and unicode symbols drift very slowly across the background. Opacity: 4%–8%. These are environmental storytelling.
- **Particle field** — 120–180 tiny dots (`radius: 1px`) connected by lines when within `80px` of each other. Very faint (`opacity: 0.12`). They drift slowly, randomly. This is the "invisible network" of behavioral signals.
- **A single bold vertical pulse** — every 4–6 seconds, a bright vertical scan line sweeps from left to right across the full canvas, like a radar sweep. Duration: 1.2 seconds. The line is `2px` wide at peak, with a trailing glow. This signals that something is being scanned/measured.

**Performance notes:**
- Use `requestAnimationFrame` loop
- All rendering on a single `<canvas>` for performance
- Respect `prefers-reduced-motion`: if set, freeze the animation (static snapshot)
- Canvas fills the `#hero` section only, not the full page

### 6.4 Hero Headline Typography

```css
.hero-eyebrow {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent-primary);
  opacity: 0.85;
  /* Animate: fade-in + slide-up with 200ms delay */
}

.hero-headline {
  font-family: var(--font-display);
  font-size: clamp(3rem, 6vw, 6.5rem);
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: var(--text-primary);
  /* Animate: each word staggers in with 80ms offset */
}

.hero-headline em {
  font-style: italic;
  color: transparent;
  background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
  -webkit-background-clip: text;
  background-clip: text;
}

.hero-subhead {
  font-family: var(--font-body);
  font-size: var(--text-lg);
  font-weight: 400;
  color: var(--text-secondary);
  max-width: 480px;
  line-height: 1.65;
}
```

**Suggested headline**: `"Credit intelligence beyond history."` with `"intelligence"` as `<em>`.

**Suggested subheadline**: `"We read how you think, how you decide, and how you recover — not what banks have recorded about you."`

### 6.5 Hero Scroll Indicator

A minimal animated chevron at the bottom of the hero section:
- Two downward-pointing `<` lines, slightly offset, pulsing vertically with a `translateY` keyframe animation
- Opacity: `0.35`
- Disappears on scroll past `50px`

---

## 7. Page Structure & Sections (Borrower Journey)

### 7.1 Navigation

**Minimal, transparent top bar** — not a traditional nav. It contains:
- Left: `AlterScore` wordmark (small, monospace style) + a very small signal icon (single waveform SVG)
- Right: Nothing except a subtle `[Dashboard →]` text link for evaluators

The nav has **no background** over the hero (transparent). As the user scrolls past the hero, it gains `backdrop-filter: blur(16px)` + `--bg-elevated` background with `0.85` opacity.

### 7.2 Section: "What We Measure"

After the hero, a section of **three animated feature cards** (horizontal row on desktop, stacked on mobile):

**Card 1: Cognitive Signals**
- Icon: A subtle animated brain wave / EEG trace SVG (looping, very slow)
- Headline: `"How you think"`
- Copy: Numeracy, financial literacy, cognitive reflection, and risk reasoning — measured through carefully crafted questions.
- Accent: `--accent-primary`

**Card 2: Behavioral Telemetry**
- Icon: A timing cursor / chronometer SVG
- Headline: `"How you decide"`
- Copy: Response timing, hesitation patterns, and answer revision rate — captured silently as you answer.
- Accent: `--accent-cyan`

**Card 3: Resilience Profile**
- Icon: A text-pulse / NLP waveform SVG
- Headline: `"How you recover"`
- Copy: A single open text response analyzed locally for agency, sentiment, and problem-solving orientation.
- Accent: `--accent-emerald`

**Card animation**: On scroll into view, each card translates upward `24px` → `0` and fades from `opacity: 0` → `1`. Cards stagger by `120ms`.

### 7.3 Section: "How It Works"

A horizontal **stepper / timeline** showing the borrower journey:

```
[1] Answer the Assessment  →  [2] Signals Are Extracted  →  [3] Get Your Score
     27 questions                 39 behavioral features          300–850 range
     ~5 minutes                  Analyzed locally                With explanation
```

Each step number pulses subtly with a slow `opacity: 0.6 → 1.0` animation on a 2.5-second loop. The arrow between steps has a flowing dash animation (CSS `stroke-dashoffset`).

### 7.4 Section: "Trusted Methodology"

Four stat blocks in a row:
- `1.4B` — Unbanked adults globally
- `39` — Behavioral features analyzed
- `0.76` — Model AUC on held-out test cohort
- `5 min` — Time to your score

Each number should be in `JetBrains Mono`, large (`--text-5xl`), and in `--text-number` (sky blue). They count up from zero when scrolled into view using a vanilla JS counter animation.

### 7.5 Final Hero / CTA Section

Before the footer — a cinematic dark panel:
- Large display text: `"Ready to be seen differently?"`
- Subtext: `"Begin your psychometric assessment. No bank history required."`
- One button: `[Start Your Assessment →]`
- Background: the same waveform canvas as the hero, but at `opacity: 0.4`

---

## 8. Assessment Page Design

### 8.1 Design Philosophy

The assessment must feel like an **intelligent conversation** — not a form. It must feel calm, deliberate, and trustworthy. The user should feel focused, not hurried. But it must also feel precise — like an instrument.

### 8.2 Layout

Full-screen, minimal. No navigation cluttering focus:
- A very thin **progress rail** at the very top of the viewport — a `3px` line that fills left to right as questions are answered. Color: `--accent-primary`.
- Center-aligned content area, max-width `600px`
- A very faint **section indicator** at top: `Section B — Risk & Decisions` in monospace caps
- A question counter in top-right: `Question 4 / 27` in monospace, muted color

### 8.3 Question Card

The question card is the central element. It should feel like it appears from nowhere:

```
┌─────────────────────────────────────────────────────────────┐
│   B-04                                            RISK Q    │  ← monospace label
│                                                             │
│   A bat and a ball together cost ₹110. The bat              │
│   costs ₹100 more than the ball. How much does              │
│   the ball cost?                                            │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │   ₹  ___________                                    │  │  ← numeric input
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   Hint: Take your time — most people get this wrong.        │
│                                                             │
│                                           [Next →]         │
└─────────────────────────────────────────────────────────────┘
```

**Card transition**: When moving to the next question:
- Current card: `translateX(-32px)` + `opacity: 0` over `280ms` (ease-in)
- Next card: starts at `translateX(32px)` + `opacity: 0`, animates to `0, 1` over `320ms` (ease-out)
- Stagger: `40ms` between exit complete and entry start

**Card styling**:
```css
.question-card {
  background: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-xl);
  padding: 40px;
  box-shadow: var(--shadow-card);
  transition: box-shadow 200ms ease;
}

.question-card:hover {
  box-shadow: var(--shadow-hover);
}
```

### 8.4 Input Types

**Number inputs** — clean, monospace, borderless except bottom line:
```css
.input-number {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  color: var(--text-primary);
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--bg-muted);
  outline: none;
  width: 100%;
  padding: 8px 0;
  transition: border-color 200ms;
}
.input-number:focus {
  border-bottom-color: var(--accent-primary);
}
```

**MCQ options** — pill buttons in a vertical list:
```css
.option-pill {
  background: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: 14px 20px;
  cursor: pointer;
  transition: all 180ms ease;
}
.option-pill:hover {
  border-color: rgba(76, 110, 245, 0.4);
  background: var(--bg-muted);
}
.option-pill.selected {
  border-color: var(--accent-primary);
  background: rgba(76, 110, 245, 0.08);
  color: var(--text-primary);
}
```

**Likert scale** — 5 horizontal buttons labeled with the scale descriptors.

**Binary choice** — Two large `option-pill` buttons side by side.

### 8.5 Telemetry Invisibility

The telemetry capture (timing, scrolls, device type) must be completely invisible. No visual indication whatsoever. Users must not feel watched — even though they are being observed.

---

## 9. Processing Screen

After submission, a **full-screen processing animation** plays while the backend scores:

### 9.1 Layout

Center of screen:
```
     Processing your signals...

     ◈ Parsing psychometric responses      ✓  [instantly done]
     ◈ Extracting behavioral telemetry     ✓
     ◈ Running NLP analysis               ✓
     ◈ Computing derived features         [animating...]
     ◈ Applying governance constraints
     ◈ Calibrating score

         Estimated: 3–5 seconds
```

Each step appears sequentially with a `200ms` delay between them. The checkmark `✓` appears with a small scale animation (`0.6 → 1.0`) when each step completes.

The `◈` icon at the active step pulses/rotates slowly.

**Background**: The signal field canvas, running at `0.2` opacity. The screen feels alive.

**Typography**: All monospace. The terminal aesthetic of computation.

---

## 10. Results Page

### 10.1 Score Reveal

The score reveal is the **climax of the entire experience**. It must feel earned, significant, cinematic.

**Animation sequence (4 seconds total):**
1. *(0–0.6s)* Screen is dark. A thin circular ring appears, drawn via `stroke-dashoffset` animation. Ring color matches score band.
2. *(0.6–1.4s)* Inside the ring, a number counts up rapidly from 300 to the actual score. `JetBrains Mono`, `--text-7xl`, color matches score band.
3. *(1.4–2.0s)* The ring glows outward — a radial glow pulse (`box-shadow` expanding) based on score color.
4. *(2.0–3.0s)* The score band label appears below the number: `"GOOD"` / `"EXCELLENT"` / etc. — animated letter by letter.
5. *(3.0–4.0s)* The rest of the page fades in — repayment probability, SHAP explanations, counterfactuals.

```
              ╭─────────────────────────╮
              │                         │
              │          712            │   ← JetBrains Mono, huge, emerald
              │                         │
              │          GOOD           │   ← Inter caps, smaller, animated
              │  ───────────────────    │
              │  82% repayment          │   ← Monospace number + label
              │  probability            │
              ╰─────────────────────────╯
```

### 10.2 SHAP Explanation Panel

Horizontal bar chart of top contributing features, designed as a minimalist table:

```
Feature contribution to your score:

  future_orientation        ████████████████  +18.4%   ↑
  locus_of_control          ████████████      +12.1%   ↑
  CRT_score                 ████████          +8.7%    ↑
  honesty_score             ████████          +8.2%    ↑
  avg_response_time_ms      ████              +4.1%    ↑
  impulsivity_index         ████              -5.3%    ↓
  risk_consistency_flag     ██                -2.8%    ↓
```

Bars are animated: they grow from left to right when the section scrolls into view. Positive bars in `--accent-emerald`, negative bars in `--accent-rose`.

Feature names are in `--font-mono`. Values in `--text-number` color.

### 10.3 Counterfactual "What Could Change" Panel

Cards showing DiCE-generated actionable improvements:

```
┌──────────────────────────────────────────────────────────────┐
│  To move from 712 → 760+, consider:                          │
│                                                              │
│  ● Improve your CRT performance by 1 additional correct      │
│    answer. This alone shifts your score by +12 points.       │
│                                                              │
│  ● Increase your average deliberation time on risk questions │
│    from 2.1s to 4.0s+. This signals more careful reasoning. │
│                                                              │
│  ● Demonstrate stronger future orientation in Section B.     │
└──────────────────────────────────────────────────────────────┘
```

Each suggestion is a subtle card (`--bg-elevated`, thin border) with a left-colored `4px` accent border.

---

## 11. Evaluator Dashboard

### 11.1 Design Approach

The dashboard is a **technical command center**. Different from the borrower flow — no cinematic storytelling here. Just precision, density, and clarity.

- **Sidebar navigation** — fixed, `240px` wide, `--bg-surface` background
- **Main content area** — 12-column grid of analytics panels
- **Dense but not cluttered** — more information per screen than the borrower flow, but still spacious

### 11.2 Dashboard Color Usage

The dashboard makes heavier use of the accent palette since it is data-rich:
- **AUC / performance metrics**: `--accent-emerald` (good performance = green)
- **Fairness flags**: `--accent-amber` for attention, `--accent-rose` for violations
- **Drift indicators**: `--accent-amber` for drift detected, `--accent-cyan` for stable
- **Score distribution**: Gradient from `--score-very-poor` → `--score-excellent`

### 11.3 Panel Design System

Each analytics panel follows the same template:
```css
.dashboard-panel {
  background: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.panel-title {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.panel-value {
  font-family: var(--font-mono);
  font-size: var(--text-3xl);
  color: var(--text-number);
}
```

---

## 12. Micro-Animation Library

### 12.1 Core Principles

- **Purpose-driven**: Every animation communicates something. Nothing animates for decoration alone.
- **Brevity**: Most transitions are `180ms`–`320ms`. Nothing drags.
- **Ease curves**: `cubic-bezier(0.4, 0, 0.2, 1)` — Google Material's "Standard" curve — for most transitions. Entrances use `cubic-bezier(0, 0, 0.2, 1)`, exits use `cubic-bezier(0.4, 0, 1, 1)`.
- **Accessibility**: All non-essential motion wrapped in `@media (prefers-reduced-motion: no-preference)`.

### 12.2 Defined Animations

```css
/* Fade Up In — for content entering on scroll */
@keyframes fadeUpIn {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fade-up {
  animation: fadeUpIn 480ms cubic-bezier(0, 0, 0.2, 1) forwards;
}

/* Number Count Up — handled via JS, not CSS */

/* Pulse Glow — for active/score elements */
@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(76, 110, 245, 0.4); }
  50%       { box-shadow: 0 0 0 12px rgba(76, 110, 245, 0); }
}
.animate-pulse-glow {
  animation: pulseGlow 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Score Ring Draw — SVG stroke animation */
@keyframes drawRing {
  from { stroke-dashoffset: 440; }
  to   { stroke-dashoffset: 0; }
}

/* Scan Line — horizontal sweep across the hero canvas */
/* Implemented in Canvas2D, not CSS */

/* Step Tick — checkmark appearing during processing */
@keyframes tickIn {
  from { transform: scale(0.4) rotate(-10deg); opacity: 0; }
  to   { transform: scale(1) rotate(0deg);     opacity: 1; }
}

/* Card Slide In (Question transition) */
@keyframes slideInRight {
  from { opacity: 0; transform: translateX(32px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes slideOutLeft {
  from { opacity: 1; transform: translateX(0); }
  to   { opacity: 0; transform: translateX(-32px); }
}

/* Waveform Trace (Hero canvas) */
/* Pure Canvas2D — sine wave with animated phase offset */

/* Floating Glyph Drift (Hero canvas) */
/* Canvas2D — slow random drift with fade in/out on edges */

/* Bar Grow (SHAP chart) */
@keyframes barGrow {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}
.bar-fill { transform-origin: left; animation: barGrow 600ms cubic-bezier(0, 0, 0.2, 1) forwards; }

/* Button Hover — subtle upward lift */
.btn:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
.btn:active { transform: translateY(0); }
```

### 12.3 Scroll-Triggered Animation

Use `IntersectionObserver` with threshold `0.15` to trigger `.animate-fade-up` on elements entering the viewport. Elements start with `opacity: 0; transform: translateY(24px)` set inline via JS before the observer fires.

Stagger children by adding `animation-delay` in increments of `80ms`.

---

## 13. Button System

### Primary CTA Button

The one big button. Used sparingly.

```css
.btn-primary {
  font-family: var(--font-body);
  font-size: var(--text-md);
  font-weight: 600;
  letter-spacing: 0.01em;
  color: #FFFFFF;
  background: var(--accent-primary);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  padding: 14px 32px;
  cursor: pointer;
  transition: all 180ms cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

/* Shimmer effect on hover */
.btn-primary::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.08) 50%, transparent 60%);
  transform: translateX(-100%);
  transition: transform 400ms ease;
}
.btn-primary:hover::after { transform: translateX(100%); }
.btn-primary:hover { background: #5A7FF7; transform: translateY(-2px); }
```

### Secondary / Ghost Button

```css
.btn-ghost {
  font-family: var(--font-body);
  font-size: var(--text-md);
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: 13px 28px;
  transition: all 180ms ease;
}
.btn-ghost:hover {
  color: var(--text-primary);
  border-color: rgba(76, 110, 245, 0.4);
  background: rgba(76, 110, 245, 0.05);
}
```

---

## 14. Component Reference

### Status Chip
```css
.chip {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-weight: 500;
}
.chip-success { background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.25); }
.chip-warning { background: rgba(245, 158, 11, 0.12); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.25); }
.chip-danger  { background: rgba(244, 63, 94, 0.12);  color: #F43F5E; border: 1px solid rgba(244, 63, 94, 0.25); }
.chip-neutral { background: rgba(148, 163, 184, 0.10); color: #94A3B8; border: 1px solid rgba(148, 163, 184, 0.15); }
```

### Divider
```css
.divider {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--bg-border) 20%, var(--bg-border) 80%, transparent 100%);
  margin: 48px 0;
}
```

### Data Value Display
```css
.data-value {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-number);
  line-height: 1;
}
.data-label {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--text-muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-top: 6px;
}
```

---

## 15. Iconography

Use **Lucide React** icons exclusively — thin stroke weight (`strokeWidth: 1.5`), sized at `16px` (UI icons) or `20px` (feature icons). Never fill icons. Never bold icons.

No icon libraries other than Lucide. If a visual concept needs emphasis, use animated SVG, not an icon.

**Hero section icon**: A custom SVG waveform — not from an icon library. Hand-crafted `<polyline>` or `<path>` suggesting an EEG trace.

---

## 16. Responsive Breakpoints

```
--mobile:   375px–767px   (single column, 16px side padding)
--tablet:   768px–1023px  (two columns, 24px side padding)
--desktop:  1024px–1279px (full layout, reduced hero animation performance)
--wide:     1280px+       (full layout, max-width container centered)
```

**Mobile assessment**: The question card occupies the full screen width. Touch targets are minimum `44px × 44px`. The `Next →` button is fixed at the bottom of the screen (iOS-safe area aware).

---

## 17. Footer

Ultra-minimal:
```
AlterScore   ·   Behavioral Credit Intelligence   ·   Valiara Club 2025

[API Docs]    [Backend Health]    [GitHub]
```

One row. Small monospace text. `--text-muted` color. `--bg-surface` background.

---

## 18. Absolutely Prohibited

- ✗ White or light backgrounds (except for a future print/export view)
- ✗ Stock photography or illustrations
- ✗ Gradient text on body copy (display text only)
- ✗ Rounded avatar placeholders or smiley icons
- ✗ Bright "web 2.0" blue `#1a73e8` or similar generic tech colors
- ✗ Animations longer than `600ms` for UI transitions
- ✗ More than 3 typefaces (Display, Body, Mono — that's it)
- ✗ Shadows that look like they come from a light source above (standard box-shadow) — use glows instead
- ✗ Generic loading spinners — always use contextual, purposeful loading states
- ✗ Empty state screens with just "No data" — always explain and offer action
- ✗ Success toast popups that stay longer than `2.5 seconds`

---

## 19. Accessibility Baseline

- **Contrast**: All text meets WCAG AA (`4.5:1` for normal, `3:1` for large). Key measurement: `--text-muted` on `--bg-elevated` = `4.8:1`. ✓
- **Focus states**: Every interactive element has a visible focus ring. Use `outline: 2px solid var(--accent-primary); outline-offset: 3px;` — no `outline: none` without replacement.
- **Motion**: Wrap all non-essential animations in `@media (prefers-reduced-motion: no-preference)`. Static fallback must be beautiful too.
- **ARIA**: Assessment questions use `role="radiogroup"` / `role="radio"` for MCQ. Progress bar has `aria-valuenow`, `aria-valuemin`, `aria-valuemax`.
- **Screen reader**: Score reveal number is announced via `aria-live="polite"` region.

---

## 20. Implementation Priority

**Phase 1** (Core, blocking):
1. Design token CSS variables (`--bg-*`, `--accent-*`, `--text-*`)
2. Font imports and type system
3. Hero section with canvas animation
4. Assessment card component

**Phase 2** (Critical UX):
5. Processing screen
6. Score reveal animation
7. SHAP bar chart
8. Scroll-trigger animation system

**Phase 3** (Polish):
9. Counterfactual panel
10. Evaluator dashboard panels
11. Responsive fixes
12. Micro-interactions on all interactive elements

---

*Design system version: 1.0 | June 2026 | AlterScore Frontend*
