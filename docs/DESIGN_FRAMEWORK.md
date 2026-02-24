# Sentinel Design Framework

## Private Banking Precision

A design language merging Swiss watchmaking precision with the quiet confidence of private wealth management. Every element communicates competence, discretion, and meticulous attention to detail.

---

## Design Philosophy

### Core Principles

1. **Quiet Authority** — Confidence without flashiness. The interface should feel like a senior partner's office: refined, substantial, unhurried.

2. **Precision Over Decoration** — Every pixel earns its place. Ornamentation serves function (hierarchy, state, feedback) or it doesn't exist.

3. **Data as Protagonist** — Numbers, charts, and recommendations take center stage. The UI frames them like a gallery frames art.

4. **Mechanical Elegance** — Animations feel like fine clockwork: smooth, purposeful, inevitable. Nothing bounces or overshoots.

### The Sentinel Aesthetic

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Deep obsidian backgrounds          Champagne accents      │
│   ████████████████████               ░░░░░░░░░░░░░░░░       │
│   #0A0A0B                            #C9A962                │
│                                                             │
│   Hairline borders                   Purposeful whitespace  │
│   ─────────────────────                                     │
│   1px, 0.08 opacity                  32px rhythm minimum    │
│                                                             │
│   Serif authority                    Sans precision         │
│   Cormorant Garamond                 DM Sans                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Color System

### Design Tokens

```css
:root {
  /* ═══════════════════════════════════════════════════════════
     SENTINEL COLOR SYSTEM
     Private Banking Precision
     ═══════════════════════════════════════════════════════════ */

  /* ─── Foundation: Obsidian Scale ─── */
  --s-obsidian-950: #050506;    /* Deepest background */
  --s-obsidian-900: #0A0A0B;    /* Primary background */
  --s-obsidian-850: #0F0F11;    /* Elevated surfaces */
  --s-obsidian-800: #141416;    /* Cards, panels */
  --s-obsidian-700: #1C1C1F;    /* Interactive surfaces */
  --s-obsidian-600: #252528;    /* Hover states */
  --s-obsidian-500: #3A3A3F;    /* Disabled states */
  --s-obsidian-400: #5C5C63;    /* Muted text */
  --s-obsidian-300: #8E8E96;    /* Secondary text */
  --s-obsidian-200: #B8B8BF;    /* Primary text (body) */
  --s-obsidian-100: #E8E8EB;    /* Emphasized text */
  --s-obsidian-50:  #F5F5F7;    /* Headlines, critical data */

  /* ─── Accent: Champagne Gold ─── */
  --s-champagne-900: #3D2F1A;   /* Darkest gold */
  --s-champagne-800: #5A4425;   /* Deep gold */
  --s-champagne-700: #7A5D33;   /* Rich gold */
  --s-champagne-600: #9A7642;   /* Warm gold */
  --s-champagne-500: #C9A962;   /* Primary accent */
  --s-champagne-400: #D4BA7D;   /* Lighter accent */
  --s-champagne-300: #E0CB99;   /* Soft gold */
  --s-champagne-200: #EBD9B5;   /* Pale gold */
  --s-champagne-100: #F5ECD8;   /* Whisper gold */

  /* ─── Semantic: Status Colors ─── */
  /* Positive / Gains */
  --s-positive-900: #0A2E1C;
  --s-positive-700: #166B3E;
  --s-positive-500: #22A55D;    /* Primary positive */
  --s-positive-300: #7DD4A3;
  --s-positive-100: #D4F5E3;

  /* Negative / Losses */
  --s-negative-900: #2E0A0A;
  --s-negative-700: #8B2525;
  --s-negative-500: #D44545;    /* Primary negative */
  --s-negative-300: #EF9A9A;
  --s-negative-100: #FDECEC;

  /* Warning / Caution */
  --s-warning-900: #2E1F0A;
  --s-warning-700: #8B6B25;
  --s-warning-500: #D4A745;     /* Primary warning */
  --s-warning-300: #F0D28A;
  --s-warning-100: #FDF5E0;

  /* Info / Neutral */
  --s-info-900: #0A1A2E;
  --s-info-700: #25558B;
  --s-info-500: #4589D4;        /* Primary info */
  --s-info-300: #9AC4EF;
  --s-info-100: #E0F0FD;

  /* ─── Transparency Layers ─── */
  --s-glass-thick:  rgba(10, 10, 11, 0.95);
  --s-glass-medium: rgba(10, 10, 11, 0.80);
  --s-glass-thin:   rgba(10, 10, 11, 0.60);
  --s-glass-whisper: rgba(10, 10, 11, 0.40);

  --s-glow-champagne: rgba(201, 169, 98, 0.15);
  --s-glow-positive:  rgba(34, 165, 93, 0.15);
  --s-glow-negative:  rgba(212, 69, 69, 0.15);

  /* ─── Borders ─── */
  --s-border-subtle:  rgba(255, 255, 255, 0.06);
  --s-border-default: rgba(255, 255, 255, 0.10);
  --s-border-strong:  rgba(255, 255, 255, 0.16);
  --s-border-accent:  rgba(201, 169, 98, 0.40);
}
```

### Color Usage Guidelines

| Context | Token | Example |
|---------|-------|---------|
| Page background | `--s-obsidian-900` | Main canvas |
| Card background | `--s-obsidian-800` | Recommendation cards |
| Interactive hover | `--s-obsidian-600` | Button hover states |
| Primary text | `--s-obsidian-100` | Headlines, key metrics |
| Secondary text | `--s-obsidian-300` | Labels, descriptions |
| Accent highlight | `--s-champagne-500` | Scores, rankings, CTAs |
| Positive values | `--s-positive-500` | Portfolio gains |
| Negative values | `--s-negative-500` | Portfolio losses |

---

## Typography

### Font Stack

```css
:root {
  /* ─── Type Families ─── */

  /* Display & Headlines: Cormorant Garamond
     Elegant serif with sharp contrast. Conveys authority and heritage. */
  --s-font-display: 'Cormorant Garamond', 'Georgia', serif;

  /* Body & UI: DM Sans
     Geometric precision without coldness. Excellent for data density. */
  --s-font-body: 'DM Sans', 'Helvetica Neue', sans-serif;

  /* Monospace & Data: JetBrains Mono
     Technical precision for numbers, codes, and tickers. */
  --s-font-mono: 'JetBrains Mono', 'SF Mono', monospace;

  /* ─── Type Scale ─── */
  --s-text-xs:   0.75rem;    /* 12px - Labels, metadata */
  --s-text-sm:   0.875rem;   /* 14px - Secondary text */
  --s-text-base: 1rem;       /* 16px - Body text */
  --s-text-lg:   1.125rem;   /* 18px - Emphasized body */
  --s-text-xl:   1.25rem;    /* 20px - Section headers */
  --s-text-2xl:  1.5rem;     /* 24px - Card titles */
  --s-text-3xl:  1.875rem;   /* 30px - Page sections */
  --s-text-4xl:  2.25rem;    /* 36px - Page titles */
  --s-text-5xl:  3rem;       /* 48px - Hero numbers */
  --s-text-6xl:  3.75rem;    /* 60px - Statement pieces */

  /* ─── Line Heights ─── */
  --s-leading-none:    1;
  --s-leading-tight:   1.2;
  --s-leading-snug:    1.35;
  --s-leading-normal:  1.5;
  --s-leading-relaxed: 1.65;

  /* ─── Letter Spacing ─── */
  --s-tracking-tighter: -0.03em;
  --s-tracking-tight:   -0.015em;
  --s-tracking-normal:  0;
  --s-tracking-wide:    0.025em;
  --s-tracking-wider:   0.05em;
  --s-tracking-widest:  0.12em;

  /* ─── Font Weights ─── */
  --s-weight-light:    300;
  --s-weight-regular:  400;
  --s-weight-medium:   500;
  --s-weight-semibold: 600;
  --s-weight-bold:     700;
}
```

### Typography Compositions

```css
/* ═══ DISPLAY: Hero Numbers & Headlines ═══ */
.s-display-hero {
  font-family: var(--s-font-display);
  font-size: var(--s-text-6xl);
  font-weight: var(--s-weight-light);
  line-height: var(--s-leading-none);
  letter-spacing: var(--s-tracking-tight);
  color: var(--s-obsidian-50);
}

.s-display-title {
  font-family: var(--s-font-display);
  font-size: var(--s-text-4xl);
  font-weight: var(--s-weight-regular);
  line-height: var(--s-leading-tight);
  letter-spacing: var(--s-tracking-tight);
  color: var(--s-obsidian-100);
}

/* ═══ HEADINGS: Section & Card Titles ═══ */
.s-heading-section {
  font-family: var(--s-font-body);
  font-size: var(--s-text-xs);
  font-weight: var(--s-weight-semibold);
  line-height: var(--s-leading-none);
  letter-spacing: var(--s-tracking-widest);
  text-transform: uppercase;
  color: var(--s-champagne-500);
}

.s-heading-card {
  font-family: var(--s-font-body);
  font-size: var(--s-text-xl);
  font-weight: var(--s-weight-medium);
  line-height: var(--s-leading-snug);
  letter-spacing: var(--s-tracking-tight);
  color: var(--s-obsidian-100);
}

/* ═══ BODY: Readable Text ═══ */
.s-body-default {
  font-family: var(--s-font-body);
  font-size: var(--s-text-base);
  font-weight: var(--s-weight-regular);
  line-height: var(--s-leading-relaxed);
  color: var(--s-obsidian-200);
}

.s-body-small {
  font-family: var(--s-font-body);
  font-size: var(--s-text-sm);
  font-weight: var(--s-weight-regular);
  line-height: var(--s-leading-normal);
  color: var(--s-obsidian-300);
}

/* ═══ DATA: Numbers & Metrics ═══ */
.s-data-large {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-3xl);
  font-weight: var(--s-weight-medium);
  line-height: var(--s-leading-none);
  letter-spacing: var(--s-tracking-tight);
  font-variant-numeric: tabular-nums;
  color: var(--s-obsidian-50);
}

.s-data-default {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-base);
  font-weight: var(--s-weight-regular);
  line-height: var(--s-leading-normal);
  font-variant-numeric: tabular-nums;
  color: var(--s-obsidian-100);
}

.s-data-ticker {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-sm);
  font-weight: var(--s-weight-semibold);
  letter-spacing: var(--s-tracking-wide);
  color: var(--s-champagne-400);
}
```

---

## Spacing & Layout

### Spacing Scale

```css
:root {
  /* ─── Spacing Scale (4px base) ─── */
  --s-space-0:   0;
  --s-space-px:  1px;
  --s-space-0.5: 0.125rem;  /* 2px */
  --s-space-1:   0.25rem;   /* 4px */
  --s-space-2:   0.5rem;    /* 8px */
  --s-space-3:   0.75rem;   /* 12px */
  --s-space-4:   1rem;      /* 16px */
  --s-space-5:   1.25rem;   /* 20px */
  --s-space-6:   1.5rem;    /* 24px */
  --s-space-8:   2rem;      /* 32px */
  --s-space-10:  2.5rem;    /* 40px */
  --s-space-12:  3rem;      /* 48px */
  --s-space-16:  4rem;      /* 64px */
  --s-space-20:  5rem;      /* 80px */
  --s-space-24:  6rem;      /* 96px */
  --s-space-32:  8rem;      /* 128px */

  /* ─── Component Spacing ─── */
  --s-card-padding: var(--s-space-6);
  --s-card-gap: var(--s-space-4);
  --s-section-gap: var(--s-space-12);
  --s-page-margin: var(--s-space-8);

  /* ─── Border Radius ─── */
  --s-radius-none: 0;
  --s-radius-sm:   0.25rem;  /* 4px - Subtle rounding */
  --s-radius-md:   0.5rem;   /* 8px - Buttons, inputs */
  --s-radius-lg:   0.75rem;  /* 12px - Cards */
  --s-radius-xl:   1rem;     /* 16px - Panels */
  --s-radius-2xl:  1.5rem;   /* 24px - Modals */
  --s-radius-full: 9999px;   /* Pills, avatars */
}
```

### Grid System

```css
/* ═══ SENTINEL GRID ═══
   Asymmetric 12-column grid with generous gutters.
   Designed for data density with breathing room. */

.s-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--s-space-6);
  padding: var(--s-page-margin);
  max-width: 1600px;
  margin: 0 auto;
}

/* Span utilities */
.s-col-1  { grid-column: span 1; }
.s-col-2  { grid-column: span 2; }
.s-col-3  { grid-column: span 3; }
.s-col-4  { grid-column: span 4; }
.s-col-5  { grid-column: span 5; }
.s-col-6  { grid-column: span 6; }
.s-col-7  { grid-column: span 7; }
.s-col-8  { grid-column: span 8; }
.s-col-9  { grid-column: span 9; }
.s-col-10 { grid-column: span 10; }
.s-col-11 { grid-column: span 11; }
.s-col-12 { grid-column: span 12; }

/* Golden ratio split: 5-7 or 7-5 */
.s-golden-primary { grid-column: span 7; }
.s-golden-secondary { grid-column: span 5; }
```

---

## Shadows & Elevation

```css
:root {
  /* ─── Elevation System ─── */

  /* Level 0: Flat (default) */
  --s-shadow-none: none;

  /* Level 1: Subtle lift */
  --s-shadow-sm:
    0 1px 2px rgba(0, 0, 0, 0.3),
    0 1px 3px rgba(0, 0, 0, 0.15);

  /* Level 2: Cards & panels */
  --s-shadow-md:
    0 2px 4px rgba(0, 0, 0, 0.25),
    0 4px 12px rgba(0, 0, 0, 0.2);

  /* Level 3: Dropdowns & popovers */
  --s-shadow-lg:
    0 4px 8px rgba(0, 0, 0, 0.3),
    0 8px 24px rgba(0, 0, 0, 0.25);

  /* Level 4: Modals & dialogs */
  --s-shadow-xl:
    0 8px 16px rgba(0, 0, 0, 0.35),
    0 16px 48px rgba(0, 0, 0, 0.3);

  /* Accent Glows */
  --s-glow-gold:
    0 0 20px rgba(201, 169, 98, 0.15),
    0 0 40px rgba(201, 169, 98, 0.08);

  --s-glow-success:
    0 0 20px rgba(34, 165, 93, 0.2),
    0 0 40px rgba(34, 165, 93, 0.1);

  --s-glow-danger:
    0 0 20px rgba(212, 69, 69, 0.2),
    0 0 40px rgba(212, 69, 69, 0.1);

  /* Inner shadows for depth */
  --s-shadow-inset:
    inset 0 1px 2px rgba(0, 0, 0, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.15);
}
```

---

## Motion & Animation

### Animation Philosophy

> "Like the second hand of a Patek Philippe — smooth, inevitable, unhurried."

- **No bouncing or overshooting** — Professional interfaces don't wobble
- **Easing is everything** — Custom cubic-beziers for mechanical precision
- **Staggered reveals** — Orchestrated sequences, not simultaneous chaos
- **Purposeful duration** — Fast enough to feel responsive, slow enough to perceive

### Animation Tokens

```css
:root {
  /* ─── Durations ─── */
  --s-duration-instant: 50ms;
  --s-duration-fast:    150ms;
  --s-duration-normal:  250ms;
  --s-duration-slow:    400ms;
  --s-duration-slower:  600ms;

  /* ─── Easings ─── */
  /* Mechanical: Smooth start and end, like fine machinery */
  --s-ease-mechanical: cubic-bezier(0.4, 0, 0.2, 1);

  /* Enter: Starts slow, ends crisp */
  --s-ease-enter: cubic-bezier(0, 0, 0.2, 1);

  /* Exit: Starts fast, fades out */
  --s-ease-exit: cubic-bezier(0.4, 0, 1, 1);

  /* Subtle: Almost linear with slight cushion */
  --s-ease-subtle: cubic-bezier(0.25, 0.1, 0.25, 1);

  /* ─── Stagger Delays ─── */
  --s-stagger-1: 50ms;
  --s-stagger-2: 100ms;
  --s-stagger-3: 150ms;
  --s-stagger-4: 200ms;
  --s-stagger-5: 250ms;
}
```

### Animation Presets

```css
/* ═══ FADE IN ═══ */
@keyframes s-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.s-animate-fade-in {
  animation: s-fade-in var(--s-duration-normal) var(--s-ease-enter) forwards;
}

/* ═══ SLIDE UP (Card reveals) ═══ */
@keyframes s-slide-up {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.s-animate-slide-up {
  animation: s-slide-up var(--s-duration-slow) var(--s-ease-mechanical) forwards;
}

/* ═══ SCALE IN (Modals, popovers) ═══ */
@keyframes s-scale-in {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.s-animate-scale-in {
  animation: s-scale-in var(--s-duration-normal) var(--s-ease-mechanical) forwards;
}

/* ═══ NUMBER TICK (Counter animation) ═══ */
@keyframes s-tick {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

.s-animate-tick {
  animation: s-tick var(--s-duration-fast) var(--s-ease-subtle);
}

/* ═══ PULSE GLOW (Attention) ═══ */
@keyframes s-pulse-glow {
  0%, 100% {
    box-shadow: 0 0 0 0 var(--s-glow-champagne);
  }
  50% {
    box-shadow: 0 0 20px 4px var(--s-glow-champagne);
  }
}

.s-animate-pulse-glow {
  animation: s-pulse-glow 2s var(--s-ease-subtle) infinite;
}

/* ═══ LOADING BAR ═══ */
@keyframes s-loading-bar {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(0%); }
  100% { transform: translateX(100%); }
}

.s-loading-bar {
  overflow: hidden;
  position: relative;
}

.s-loading-bar::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent,
    var(--s-champagne-500),
    transparent
  );
  animation: s-loading-bar 1.5s var(--s-ease-mechanical) infinite;
}

/* ═══ STAGGER CHILDREN ═══ */
.s-stagger-children > *:nth-child(1) { animation-delay: var(--s-stagger-1); }
.s-stagger-children > *:nth-child(2) { animation-delay: var(--s-stagger-2); }
.s-stagger-children > *:nth-child(3) { animation-delay: var(--s-stagger-3); }
.s-stagger-children > *:nth-child(4) { animation-delay: var(--s-stagger-4); }
.s-stagger-children > *:nth-child(5) { animation-delay: var(--s-stagger-5); }
```

---

## Component Patterns

### Recommendation Card

The primary unit of the Canvas UI. Displays a single AI recommendation with utility scores.

```html
<article class="s-card s-card--recommendation" data-rank="1">
  <header class="s-card__header">
    <span class="s-card__rank">01</span>
    <div class="s-card__title-group">
      <h3 class="s-card__title">AMD Substitute Strategy</h3>
      <span class="s-card__subtitle">Correlated replacement for NVDA exposure</span>
    </div>
    <div class="s-card__score">
      <span class="s-card__score-value">69.6</span>
      <span class="s-card__score-label">/ 100</span>
    </div>
  </header>

  <div class="s-card__body">
    <div class="s-card__dimensions">
      <!-- Utility score bars -->
    </div>
    <div class="s-card__details">
      <!-- Trade details -->
    </div>
  </div>

  <footer class="s-card__actions">
    <button class="s-btn s-btn--ghost" data-a2ui-action="what-if">
      What If
    </button>
    <button class="s-btn s-btn--primary" data-a2ui-action="approve">
      Approve
    </button>
  </footer>
</article>
```

```css
.s-card {
  background: var(--s-obsidian-800);
  border: 1px solid var(--s-border-subtle);
  border-radius: var(--s-radius-lg);
  padding: var(--s-card-padding);
  transition:
    border-color var(--s-duration-fast) var(--s-ease-subtle),
    box-shadow var(--s-duration-normal) var(--s-ease-subtle);
}

.s-card:hover {
  border-color: var(--s-border-default);
}

.s-card--recommendation[data-rank="1"] {
  border-color: var(--s-border-accent);
  box-shadow: var(--s-glow-gold);
}

.s-card__header {
  display: flex;
  align-items: flex-start;
  gap: var(--s-space-4);
  margin-bottom: var(--s-space-6);
}

.s-card__rank {
  font-family: var(--s-font-display);
  font-size: var(--s-text-4xl);
  font-weight: var(--s-weight-light);
  line-height: 1;
  color: var(--s-champagne-500);
  opacity: 0.6;
}

.s-card__score {
  margin-left: auto;
  text-align: right;
}

.s-card__score-value {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-3xl);
  font-weight: var(--s-weight-medium);
  color: var(--s-obsidian-50);
}

.s-card__score-label {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-sm);
  color: var(--s-obsidian-400);
}
```

### Utility Score Bar

Visualizes each dimension of the utility function.

```html
<div class="s-score-bar">
  <div class="s-score-bar__header">
    <span class="s-score-bar__label">Tax Savings</span>
    <span class="s-score-bar__value">8.2</span>
  </div>
  <div class="s-score-bar__track">
    <div class="s-score-bar__fill" style="--score: 82%;"></div>
  </div>
</div>
```

```css
.s-score-bar {
  --score: 0%;
}

.s-score-bar__header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--s-space-2);
}

.s-score-bar__label {
  font-size: var(--s-text-sm);
  color: var(--s-obsidian-300);
}

.s-score-bar__value {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-sm);
  font-weight: var(--s-weight-medium);
  color: var(--s-obsidian-100);
}

.s-score-bar__track {
  height: 4px;
  background: var(--s-obsidian-700);
  border-radius: var(--s-radius-full);
  overflow: hidden;
}

.s-score-bar__fill {
  height: 100%;
  width: var(--score);
  background: linear-gradient(
    90deg,
    var(--s-champagne-700),
    var(--s-champagne-500)
  );
  border-radius: var(--s-radius-full);
  transition: width var(--s-duration-slow) var(--s-ease-mechanical);
}
```

### Buttons

```css
.s-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--s-space-2);
  padding: var(--s-space-3) var(--s-space-5);
  font-family: var(--s-font-body);
  font-size: var(--s-text-sm);
  font-weight: var(--s-weight-medium);
  letter-spacing: var(--s-tracking-wide);
  border-radius: var(--s-radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition:
    background var(--s-duration-fast) var(--s-ease-subtle),
    border-color var(--s-duration-fast) var(--s-ease-subtle),
    transform var(--s-duration-fast) var(--s-ease-subtle);
}

.s-btn:active {
  transform: scale(0.98);
}

/* Primary: Gold accent */
.s-btn--primary {
  background: var(--s-champagne-500);
  color: var(--s-obsidian-950);
  border-color: var(--s-champagne-500);
}

.s-btn--primary:hover {
  background: var(--s-champagne-400);
  border-color: var(--s-champagne-400);
}

/* Ghost: Subtle outline */
.s-btn--ghost {
  background: transparent;
  color: var(--s-obsidian-200);
  border-color: var(--s-border-default);
}

.s-btn--ghost:hover {
  background: var(--s-obsidian-700);
  border-color: var(--s-border-strong);
}

/* Danger: For destructive actions */
.s-btn--danger {
  background: var(--s-negative-700);
  color: var(--s-obsidian-50);
  border-color: var(--s-negative-700);
}

.s-btn--danger:hover {
  background: var(--s-negative-500);
  border-color: var(--s-negative-500);
}
```

### Slider (Interactive Rebalancing)

```html
<div class="s-slider">
  <label class="s-slider__label">
    <span>Rebalancing Intensity</span>
    <output class="s-slider__output">75%</output>
  </label>
  <input
    type="range"
    class="s-slider__input"
    min="0"
    max="100"
    value="75"
    data-a2ui-action="adjust-intensity"
  >
  <div class="s-slider__ticks">
    <span>Conservative</span>
    <span>Aggressive</span>
  </div>
</div>
```

```css
.s-slider {
  --slider-value: 75%;
}

.s-slider__label {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--s-space-3);
  font-size: var(--s-text-sm);
  color: var(--s-obsidian-200);
}

.s-slider__output {
  font-family: var(--s-font-mono);
  color: var(--s-champagne-500);
}

.s-slider__input {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  background: var(--s-obsidian-700);
  border-radius: var(--s-radius-full);
  outline: none;
}

.s-slider__input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  background: var(--s-champagne-500);
  border-radius: var(--s-radius-full);
  cursor: pointer;
  box-shadow: var(--s-shadow-md);
  transition: transform var(--s-duration-fast) var(--s-ease-subtle);
}

.s-slider__input::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.s-slider__input::-webkit-slider-thumb:active {
  transform: scale(0.95);
}

.s-slider__ticks {
  display: flex;
  justify-content: space-between;
  margin-top: var(--s-space-2);
  font-size: var(--s-text-xs);
  color: var(--s-obsidian-400);
}
```

### Data Badge (Tickers, Status)

```css
.s-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--s-space-1);
  padding: var(--s-space-1) var(--s-space-2);
  font-family: var(--s-font-mono);
  font-size: var(--s-text-xs);
  font-weight: var(--s-weight-medium);
  letter-spacing: var(--s-tracking-wide);
  border-radius: var(--s-radius-sm);
  border: 1px solid;
}

.s-badge--ticker {
  background: var(--s-obsidian-700);
  border-color: var(--s-border-subtle);
  color: var(--s-champagne-400);
}

.s-badge--positive {
  background: var(--s-positive-900);
  border-color: var(--s-positive-700);
  color: var(--s-positive-300);
}

.s-badge--negative {
  background: var(--s-negative-900);
  border-color: var(--s-negative-700);
  color: var(--s-negative-300);
}

.s-badge--warning {
  background: var(--s-warning-900);
  border-color: var(--s-warning-700);
  color: var(--s-warning-300);
}
```

---

## Patterns for Agent-Generated UI

### a2ui-action Attributes

Agents generate interactive elements with `data-a2ui-action` attributes that map to tool calls.

```html
<!-- Approval action -->
<button data-a2ui-action="approve" data-payload='{"scenario_id": "C"}'>
  Approve AMD Strategy
</button>

<!-- What-if analysis -->
<button data-a2ui-action="what-if" data-payload='{"vary": "tax_rate", "range": [0.2, 0.4]}'>
  What If Tax Rate Changes
</button>

<!-- Slider adjustment -->
<input
  type="range"
  data-a2ui-action="adjust"
  data-param="rebalance_intensity"
  data-min="0"
  data-max="100"
>

<!-- Expand/collapse -->
<button data-a2ui-action="toggle" data-target="#details-panel">
  Show Details
</button>
```

### Canvas Template Structure

```html
<!DOCTYPE html>
<html lang="en" data-theme="sentinel-dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sentinel Canvas</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    /* Include design tokens and component styles */
  </style>
</head>
<body class="s-canvas">
  <header class="s-canvas__header">
    <h1 class="s-heading-section">Portfolio Analysis</h1>
    <time class="s-body-small" datetime="2024-03-15T14:32:00Z">
      March 15, 2024 · 2:32 PM EST
    </time>
  </header>

  <main class="s-canvas__body s-grid">
    <section class="s-col-12">
      <h2 class="s-display-title">Recommendations</h2>
    </section>

    <div class="s-col-12 s-stagger-children">
      <!-- Agent-generated recommendation cards -->
    </div>
  </main>

  <footer class="s-canvas__footer">
    <div class="s-canvas__merkle">
      <span class="s-body-small">Merkle Root:</span>
      <code class="s-data-default">a1b2c3d4...</code>
    </div>
  </footer>

  <script>
    // a2ui-action handler
    document.addEventListener('click', (e) => {
      const action = e.target.closest('[data-a2ui-action]');
      if (!action) return;

      const actionType = action.dataset.a2uiAction;
      const payload = JSON.parse(action.dataset.payload || '{}');

      // Send to parent frame or API
      window.parent.postMessage({
        type: 'sentinel-action',
        action: actionType,
        payload
      }, '*');
    });
  </script>
</body>
</html>
```

---

## Responsive Considerations

```css
/* ═══ BREAKPOINTS ═══ */
:root {
  --s-breakpoint-sm: 640px;
  --s-breakpoint-md: 768px;
  --s-breakpoint-lg: 1024px;
  --s-breakpoint-xl: 1280px;
  --s-breakpoint-2xl: 1536px;
}

/* Mobile-first: Stack everything */
@media (max-width: 767px) {
  .s-grid {
    grid-template-columns: 1fr;
    gap: var(--s-space-4);
    padding: var(--s-space-4);
  }

  .s-card__header {
    flex-wrap: wrap;
  }

  .s-card__score {
    width: 100%;
    text-align: left;
    margin-top: var(--s-space-4);
    padding-top: var(--s-space-4);
    border-top: 1px solid var(--s-border-subtle);
  }
}

/* Tablet: 2-column where appropriate */
@media (min-width: 768px) and (max-width: 1023px) {
  .s-golden-primary { grid-column: span 6; }
  .s-golden-secondary { grid-column: span 6; }
}

/* Desktop: Full 12-column grid */
@media (min-width: 1024px) {
  /* Default styles apply */
}
```

---

## Accessibility

```css
/* ═══ FOCUS STATES ═══ */
:focus-visible {
  outline: 2px solid var(--s-champagne-500);
  outline-offset: 2px;
}

/* ═══ REDUCED MOTION ═══ */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* ═══ HIGH CONTRAST ═══ */
@media (prefers-contrast: high) {
  :root {
    --s-border-subtle: rgba(255, 255, 255, 0.3);
    --s-border-default: rgba(255, 255, 255, 0.5);
  }
}

/* ═══ SCREEN READER UTILITIES ═══ */
.s-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

---

## Quick Reference: Complete Token List

```css
/* Copy this block to any Canvas HTML for full design system access */

:root {
  /* Colors */
  --s-obsidian-950: #050506;
  --s-obsidian-900: #0A0A0B;
  --s-obsidian-800: #141416;
  --s-obsidian-700: #1C1C1F;
  --s-obsidian-600: #252528;
  --s-obsidian-400: #5C5C63;
  --s-obsidian-300: #8E8E96;
  --s-obsidian-200: #B8B8BF;
  --s-obsidian-100: #E8E8EB;
  --s-obsidian-50: #F5F5F7;

  --s-champagne-500: #C9A962;
  --s-champagne-400: #D4BA7D;

  --s-positive-500: #22A55D;
  --s-negative-500: #D44545;
  --s-warning-500: #D4A745;
  --s-info-500: #4589D4;

  --s-border-subtle: rgba(255, 255, 255, 0.06);
  --s-border-default: rgba(255, 255, 255, 0.10);
  --s-border-accent: rgba(201, 169, 98, 0.40);

  /* Typography */
  --s-font-display: 'Cormorant Garamond', Georgia, serif;
  --s-font-body: 'DM Sans', 'Helvetica Neue', sans-serif;
  --s-font-mono: 'JetBrains Mono', 'SF Mono', monospace;

  /* Spacing */
  --s-space-2: 0.5rem;
  --s-space-4: 1rem;
  --s-space-6: 1.5rem;
  --s-space-8: 2rem;

  /* Radius */
  --s-radius-md: 0.5rem;
  --s-radius-lg: 0.75rem;

  /* Motion */
  --s-duration-fast: 150ms;
  --s-duration-normal: 250ms;
  --s-ease-mechanical: cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Usage by Agents

When generating Canvas UI, agents should:

1. **Import the framework** — Include the token block and Google Fonts link
2. **Use semantic classes** — `.s-card`, `.s-btn`, `.s-score-bar`, etc.
3. **Add a2ui-action attributes** — For interactive elements
4. **Apply stagger animations** — For card reveals
5. **Include Merkle verification** — Footer with chain hash

Example agent output:

```python
CANVAS_TEMPLATE = """
<div class="s-card s-card--recommendation s-animate-slide-up" data-rank="{rank}">
  <header class="s-card__header">
    <span class="s-card__rank">{rank:02d}</span>
    <div class="s-card__title-group">
      <h3 class="s-card__title">{title}</h3>
      <span class="s-card__subtitle">{subtitle}</span>
    </div>
    <div class="s-card__score">
      <span class="s-card__score-value">{score:.1f}</span>
      <span class="s-card__score-label">/ 100</span>
    </div>
  </header>
  <!-- ... -->
</div>
"""
```

---

*Private Banking Precision. Every pixel earns its place.*
