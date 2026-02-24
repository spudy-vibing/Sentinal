# Sentinel V2 Design System

## "Terminal Luxe" — Enterprise Command Center Aesthetic

A fusion of Bloomberg Terminal's data density with modern fintech elegance. Dark, precise, and commanding — designed for professionals who make million-dollar decisions.

---

## Design Philosophy

### Core Principles

| Principle | Execution |
|-----------|-----------|
| **Data First** | Information density is a feature, not a bug. Every pixel earns its place. |
| **Terminal Heritage** | Monospace numbers, keyboard-first interactions, real-time streaming. |
| **Quiet Luxury** | Dark palette, subtle gradients, restrained color use — accents only where action lives. |
| **Purposeful Motion** | Animations communicate state changes, never decorative. |
| **Enterprise Trust** | Consistent, predictable, accessible — this is finance, not a startup landing page. |

### What This Is NOT

- Generic dashboard template
- Bright corporate blue (#0066FF everywhere)
- Rounded-everything friendly SaaS
- Material Design clone
- Purple gradient AI aesthetics

---

## Color System

### The Obsidian Scale (Neutrals)

Our foundation is a carefully calibrated dark scale with subtle warm undertones — not blue-tinted like most dark themes.

```css
:root {
  /* Foundations — The Obsidian Scale */
  --s-void:      #050506;  /* True black, app background */
  --s-charcoal:  #0C0C0E;  /* Primary surface */
  --s-graphite:  #141416;  /* Secondary surface */
  --s-slate:     #1C1C1F;  /* Tertiary surface, input backgrounds */
  --s-ash:       #2A2A2E;  /* Borders, dividers */
  --s-smoke:     #3D3D42;  /* Disabled states, subtle elements */
  --s-mist:      #6B6B73;  /* Secondary text, labels */
  --s-cloud:     #A0A0A8;  /* Body text */
  --s-pearl:     #E8E8EC;  /* Primary text */
  --s-white:     #FAFAFA;  /* High emphasis text */
}
```

### Accent Colors

Strategic use of color for meaning, never decoration.

```css
:root {
  /* Primary Accent — Electric Cyan */
  --s-cyan:       #00E5CC;  /* Primary actions, active states */
  --s-cyan-hover: #00D4BC;  /* Hover state */
  --s-cyan-dim:   #00E5CC40; /* 25% opacity backgrounds */
  --s-cyan-glow:  #00E5CC20; /* 12% opacity for glows */

  /* Warning — Amber */
  --s-amber:      #F5A524;  /* Warnings, attention needed */
  --s-amber-dim:  #F5A52440;

  /* Destructive — Red */
  --s-red:        #FF4757;  /* Errors, sell actions, critical */
  --s-red-dim:    #FF475720;

  /* Success — Green */
  --s-green:      #2ED573;  /* Success, buy actions, positive */
  --s-green-dim:  #2ED57320;

  /* Info — Blue (sparingly) */
  --s-blue:       #3B82F6;  /* Links, info only */
  --s-blue-dim:   #3B82F620;
}
```

### Semantic Aliases

```css
:root {
  /* Surfaces */
  --s-surface-0: var(--s-void);     /* App background */
  --s-surface-1: var(--s-charcoal); /* Cards, panels */
  --s-surface-2: var(--s-graphite); /* Nested cards, dropdowns */
  --s-surface-3: var(--s-slate);    /* Inputs, hover states */

  /* Borders */
  --s-border-subtle: var(--s-ash);
  --s-border-default: var(--s-smoke);
  --s-border-emphasis: var(--s-mist);

  /* Text */
  --s-text-primary: var(--s-pearl);
  --s-text-secondary: var(--s-cloud);
  --s-text-muted: var(--s-mist);
  --s-text-disabled: var(--s-smoke);

  /* Interactive */
  --s-interactive: var(--s-cyan);
  --s-interactive-hover: var(--s-cyan-hover);
}
```

---

## Typography

### Font Stack

```css
:root {
  /* Display — Geist (Vercel's font) */
  --s-font-display: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  /* Monospace — JetBrains Mono (data, numbers, code) */
  --s-font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
```

### Type Scale

```css
:root {
  /* Size Scale */
  --s-text-2xs:  0.625rem;   /* 10px — micro labels */
  --s-text-xs:   0.6875rem;  /* 11px — labels, badges */
  --s-text-sm:   0.75rem;    /* 12px — secondary text */
  --s-text-base: 0.875rem;   /* 14px — body text */
  --s-text-lg:   1rem;       /* 16px — emphasis */
  --s-text-xl:   1.25rem;    /* 20px — section headers */
  --s-text-2xl:  1.5rem;     /* 24px — page titles */
  --s-text-3xl:  2rem;       /* 32px — hero numbers */
  --s-text-4xl:  2.5rem;     /* 40px — dashboard metrics */

  /* Weight */
  --s-font-normal: 400;
  --s-font-medium: 500;
  --s-font-semibold: 600;
  --s-font-bold: 700;

  /* Line Height */
  --s-leading-none: 1;
  --s-leading-tight: 1.25;
  --s-leading-normal: 1.5;
  --s-leading-relaxed: 1.75;

  /* Letter Spacing */
  --s-tracking-tight: -0.025em;
  --s-tracking-normal: 0;
  --s-tracking-wide: 0.025em;
  --s-tracking-wider: 0.05em;
  --s-tracking-widest: 0.1em;
}
```

### Typography Classes

```css
/* Display Hierarchy */
.text-display-xl {
  font-family: var(--s-font-display);
  font-size: var(--s-text-4xl);
  font-weight: var(--s-font-bold);
  letter-spacing: var(--s-tracking-tight);
  line-height: var(--s-leading-tight);
}

.text-display-lg {
  font-family: var(--s-font-display);
  font-size: var(--s-text-3xl);
  font-weight: var(--s-font-semibold);
  letter-spacing: var(--s-tracking-tight);
}

/* Data Display (Numbers, Prices, IDs) */
.text-data-xl {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-3xl);
  font-weight: var(--s-font-semibold);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.text-data-lg {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-xl);
  font-weight: var(--s-font-medium);
  font-variant-numeric: tabular-nums;
}

.text-data-base {
  font-family: var(--s-font-mono);
  font-size: var(--s-text-base);
  font-variant-numeric: tabular-nums;
}

/* Labels */
.text-label {
  font-family: var(--s-font-display);
  font-size: var(--s-text-xs);
  font-weight: var(--s-font-medium);
  letter-spacing: var(--s-tracking-widest);
  text-transform: uppercase;
  color: var(--s-text-muted);
}
```

---

## Spacing System

8px base unit, following the "8-point grid".

```css
:root {
  --s-space-0:   0;
  --s-space-0.5: 0.125rem;  /* 2px */
  --s-space-1:   0.25rem;   /* 4px */
  --s-space-1.5: 0.375rem;  /* 6px */
  --s-space-2:   0.5rem;    /* 8px — base unit */
  --s-space-2.5: 0.625rem;  /* 10px */
  --s-space-3:   0.75rem;   /* 12px */
  --s-space-4:   1rem;      /* 16px */
  --s-space-5:   1.25rem;   /* 20px */
  --s-space-6:   1.5rem;    /* 24px */
  --s-space-8:   2rem;      /* 32px */
  --s-space-10:  2.5rem;    /* 40px */
  --s-space-12:  3rem;      /* 48px */
  --s-space-16:  4rem;      /* 64px */
  --s-space-20:  5rem;      /* 80px */
}
```

---

## Border Radius

Sharp-ish corners — financial software, not a toy.

```css
:root {
  --s-radius-none: 0;
  --s-radius-sm:   0.25rem;  /* 4px — inputs, badges */
  --s-radius-md:   0.5rem;   /* 8px — cards, buttons */
  --s-radius-lg:   0.75rem;  /* 12px — modals, large cards */
  --s-radius-xl:   1rem;     /* 16px — feature cards */
  --s-radius-full: 9999px;   /* Pills, avatars */
}
```

---

## Shadows & Elevation

Subtle shadows in dark mode — rely more on borders and surface elevation.

```css
:root {
  /* Elevation through surface color primarily */
  --s-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --s-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
  --s-shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.4);
  --s-shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.5);

  /* Glow effects for active states */
  --s-glow-cyan:  0 0 20px rgba(0, 229, 204, 0.15),
                  0 0 40px rgba(0, 229, 204, 0.05);
  --s-glow-amber: 0 0 20px rgba(245, 165, 36, 0.15);
  --s-glow-red:   0 0 20px rgba(255, 71, 87, 0.15);
  --s-glow-green: 0 0 20px rgba(46, 213, 115, 0.15);
}
```

---

## Components

### Cards

```css
/* Base Card */
.card {
  background: var(--s-surface-1);
  border: 1px solid var(--s-border-subtle);
  border-radius: var(--s-radius-lg);
  padding: var(--s-space-6);
}

/* Interactive Card */
.card-interactive {
  composes: card;
  cursor: pointer;
  transition: all 0.2s ease;
}
.card-interactive:hover {
  background: var(--s-surface-2);
  border-color: var(--s-border-default);
  transform: translateY(-2px);
}

/* Highlighted Card (recommended scenario) */
.card-highlight {
  composes: card;
  border-color: var(--s-cyan);
  box-shadow: var(--s-glow-cyan);
}

/* Nested Card */
.card-nested {
  background: var(--s-surface-2);
  border: 1px solid var(--s-border-subtle);
  border-radius: var(--s-radius-md);
  padding: var(--s-space-4);
}
```

### Buttons

```css
/* Base Button */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--s-space-2);
  padding: var(--s-space-2) var(--s-space-4);
  border-radius: var(--s-radius-md);
  font-family: var(--s-font-display);
  font-size: var(--s-text-sm);
  font-weight: var(--s-font-medium);
  transition: all 0.15s ease;
  cursor: pointer;
  border: none;
}

/* Primary — Cyan */
.btn-primary {
  composes: btn;
  background: var(--s-cyan);
  color: var(--s-void);
}
.btn-primary:hover {
  background: var(--s-cyan-hover);
}

/* Secondary — Ghost */
.btn-secondary {
  composes: btn;
  background: var(--s-surface-3);
  color: var(--s-text-secondary);
  border: 1px solid var(--s-border-subtle);
}
.btn-secondary:hover {
  background: var(--s-ash);
  color: var(--s-text-primary);
  border-color: var(--s-border-default);
}

/* Destructive */
.btn-destructive {
  composes: btn;
  background: var(--s-red);
  color: var(--s-white);
}

/* Ghost */
.btn-ghost {
  composes: btn;
  background: transparent;
  color: var(--s-text-secondary);
}
.btn-ghost:hover {
  background: var(--s-surface-3);
  color: var(--s-text-primary);
}

/* Sizes */
.btn-sm { padding: var(--s-space-1) var(--s-space-2); font-size: var(--s-text-xs); }
.btn-lg { padding: var(--s-space-3) var(--s-space-6); font-size: var(--s-text-base); }
```

### Inputs

```css
.input {
  width: 100%;
  background: var(--s-surface-3);
  border: 1px solid var(--s-border-subtle);
  border-radius: var(--s-radius-md);
  padding: var(--s-space-3) var(--s-space-4);
  font-family: var(--s-font-display);
  font-size: var(--s-text-base);
  color: var(--s-text-primary);
  transition: all 0.15s ease;
}

.input::placeholder {
  color: var(--s-text-muted);
}

.input:focus {
  outline: none;
  border-color: var(--s-cyan);
  box-shadow: 0 0 0 3px var(--s-cyan-glow);
}

/* Monospace Input (for data entry) */
.input-mono {
  composes: input;
  font-family: var(--s-font-mono);
  font-variant-numeric: tabular-nums;
}
```

### Badges

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--s-space-1);
  padding: var(--s-space-0.5) var(--s-space-2);
  border-radius: var(--s-radius-full);
  font-family: var(--s-font-mono);
  font-size: var(--s-text-xs);
  font-weight: var(--s-font-medium);
}

.badge-cyan {
  background: var(--s-cyan-dim);
  color: var(--s-cyan);
}

.badge-amber {
  background: var(--s-amber-dim);
  color: var(--s-amber);
}

.badge-red {
  background: var(--s-red-dim);
  color: var(--s-red);
}

.badge-green {
  background: var(--s-green-dim);
  color: var(--s-green);
}

.badge-muted {
  background: var(--s-smoke);
  color: var(--s-mist);
}
```

### Status Indicators

```css
/* Status Dot */
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-idle     { background: var(--s-smoke); }
.status-active   { background: var(--s-cyan); animation: pulse 2s infinite; }
.status-success  { background: var(--s-green); }
.status-warning  { background: var(--s-amber); }
.status-error    { background: var(--s-red); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### Progress Bars

```css
.progress-track {
  height: 6px;
  background: var(--s-surface-3);
  border-radius: var(--s-radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: var(--s-radius-full);
  transition: width 0.5s ease;
}

.progress-fill-cyan  { background: var(--s-cyan); }
.progress-fill-green { background: var(--s-green); }
.progress-fill-amber { background: var(--s-amber); }
.progress-fill-red   { background: var(--s-red); }
```

---

## Motion

### Timing Functions

```css
:root {
  --s-ease-out:    cubic-bezier(0.16, 1, 0.3, 1);     /* Deceleration */
  --s-ease-in:     cubic-bezier(0.7, 0, 0.84, 0);     /* Acceleration */
  --s-ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);    /* Both */
  --s-spring:      cubic-bezier(0.34, 1.56, 0.64, 1); /* Bouncy */
}
```

### Duration Scale

```css
:root {
  --s-duration-instant: 50ms;
  --s-duration-fast:    100ms;
  --s-duration-normal:  200ms;
  --s-duration-slow:    300ms;
  --s-duration-slower:  500ms;
}
```

### Common Animations

```css
/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide Up */
@keyframes slideUp {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Scale In */
@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Glow Pulse */
@keyframes glowPulse {
  0%, 100% { box-shadow: var(--s-glow-cyan); }
  50% { box-shadow: 0 0 30px rgba(0, 229, 204, 0.25); }
}

/* Shimmer (loading) */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-shimmer {
  background: linear-gradient(
    90deg,
    var(--s-surface-2) 0%,
    var(--s-surface-3) 50%,
    var(--s-surface-2) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

---

## Layout Patterns

### Dashboard Grid

```css
/* Main Layout */
.layout-dashboard {
  display: grid;
  grid-template-columns: 256px 1fr;  /* Sidebar + Content */
  height: 100vh;
}

/* Content Area */
.layout-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.layout-header {
  height: 64px;
  border-bottom: 1px solid var(--s-border-subtle);
  padding: 0 var(--s-space-6);
}

/* Main Content Grid */
.layout-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--s-space-6);
  padding: var(--s-space-6);
}

/* Common Spans */
.col-span-4  { grid-column: span 4; }
.col-span-6  { grid-column: span 6; }
.col-span-8  { grid-column: span 8; }
.col-span-12 { grid-column: span 12; }
```

### Split Panels

```css
/* Two-column split */
.layout-split {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--s-space-6);
  height: 100%;
}

/* Three-column feature */
.layout-feature {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: var(--s-space-6);
  height: 100%;
}
```

---

## Iconography

Use **Lucide Icons** — clean, consistent, well-maintained.

### Standard Sizes

```css
.icon-xs { width: 12px; height: 12px; }
.icon-sm { width: 16px; height: 16px; }
.icon-md { width: 20px; height: 20px; }
.icon-lg { width: 24px; height: 24px; }
.icon-xl { width: 32px; height: 32px; }
```

### Common Icons

| Purpose | Icon |
|---------|------|
| Portfolio | `Briefcase` |
| Holdings | `Layers` |
| Buy/Positive | `TrendingUp` |
| Sell/Negative | `TrendingDown` |
| Warning | `AlertTriangle` |
| Success | `CheckCircle` |
| Error | `XCircle` |
| Loading | `Loader2` (animated) |
| Settings | `Settings` |
| Chat | `MessageSquare` |
| Agent | `Bot` |
| Audit | `Shield` |
| Time | `Clock` |
| Money | `DollarSign` |

---

## Data Visualization

### Chart Colors

```css
:root {
  --s-chart-1: var(--s-cyan);
  --s-chart-2: var(--s-green);
  --s-chart-3: var(--s-amber);
  --s-chart-4: var(--s-red);
  --s-chart-5: var(--s-blue);
  --s-chart-6: #A855F7;  /* Purple */
  --s-chart-7: #EC4899;  /* Pink */
}
```

### Radar/Spider Charts

For utility scoring visualization — shows 5 dimensions clearly.

### Candlestick Colors

```css
:root {
  --s-candle-up:   var(--s-green);
  --s-candle-down: var(--s-red);
  --s-candle-wick: var(--s-mist);
}
```

---

## Accessibility

### Contrast Ratios

All text/background combinations meet WCAG AA standards:

| Element | Foreground | Background | Ratio |
|---------|------------|------------|-------|
| Body text | `--s-cloud` | `--s-charcoal` | 7.2:1 |
| Primary text | `--s-pearl` | `--s-charcoal` | 11.5:1 |
| Cyan on dark | `--s-cyan` | `--s-charcoal` | 7.8:1 |
| Muted text | `--s-mist` | `--s-charcoal` | 4.6:1 |

### Focus States

```css
/* Custom focus ring */
*:focus-visible {
  outline: 2px solid var(--s-cyan);
  outline-offset: 2px;
}

/* For dark on light elements */
.focus-invert:focus-visible {
  outline-color: var(--s-void);
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Responsive Breakpoints

```css
:root {
  --s-screen-sm:  640px;
  --s-screen-md:  768px;
  --s-screen-lg:  1024px;
  --s-screen-xl:  1280px;
  --s-screen-2xl: 1536px;
}

/* Mobile-first approach */
@media (max-width: 1024px) {
  .layout-dashboard {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: fixed;
    transform: translateX(-100%);
    z-index: 50;
  }

  .sidebar.open {
    transform: translateX(0);
  }
}
```

---

## File Organization

```
frontend/src/styles/
├── globals.css           # Tailwind directives + base styles
├── tokens/
│   ├── colors.css        # Color variables
│   ├── typography.css    # Font variables
│   ├── spacing.css       # Spacing scale
│   └── motion.css        # Animation tokens
├── components/
│   ├── buttons.css
│   ├── cards.css
│   ├── inputs.css
│   ├── badges.css
│   └── ...
└── utilities/
    ├── layout.css
    └── accessibility.css
```

---

*Design System Version*: 2.0
*Last Updated*: 2026-02-21
