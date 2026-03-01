/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // SENTINEL V2 — Refined Finance Color System
      colors: {
        // Backgrounds - Dark Terminal Theme (matches CSS variables)
        'bg-primary': '#0A0F1C',
        'bg-secondary': '#121A2F',
        'bg-tertiary': '#1E293B',
        'bg-elevated': '#1E293B',

        // Accent (Neon Blue - tech, precision)
        'accent': {
          DEFAULT: '#3B82F6',
          light: '#60A5FA',
          dim: 'rgba(59, 130, 246, 0.15)',
          glow: 'rgba(59, 130, 246, 0.25)',
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },

        // Status Colors - Vibrant for dark mode
        'success': '#10B981',
        'success-light': 'rgba(16, 185, 129, 0.15)',
        'warning': '#F59E0B',
        'warning-light': 'rgba(245, 158, 11, 0.15)',
        'error': '#EF4444',
        'error-light': 'rgba(239, 68, 68, 0.15)',
        'info': '#0EA5E9',
        'info-light': 'rgba(14, 165, 233, 0.15)',

        // Text - High contrast for dark mode
        'text-primary': '#F8FAFC',
        'text-secondary': '#94A3B8',
        'text-muted': '#64748B',

        // Borders - Dark theme
        'border-subtle': '#1E293B',
        'border-default': '#334155',
        'border-strong': '#475569',
      },

      // Typography
      fontFamily: {
        'sans': ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        'mono': ['JetBrains Mono', 'SF Mono', 'Monaco', 'monospace'],
        'display': ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },

      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.5' }],
        'sm': ['0.875rem', { lineHeight: '1.5' }],
        'base': ['1rem', { lineHeight: '1.6' }],
        'lg': ['1.125rem', { lineHeight: '1.5' }],
        'xl': ['1.25rem', { lineHeight: '1.4' }],
        '2xl': ['1.5rem', { lineHeight: '1.3' }],
        '3xl': ['1.875rem', { lineHeight: '1.25' }],
        '4xl': ['2.25rem', { lineHeight: '1.2' }],
        '5xl': ['3rem', { lineHeight: '1.1' }],
      },

      // Spacing
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },

      // Border Radius
      borderRadius: {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
      },

      // Box Shadow (Professional, subtle)
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'glow': '0 0 20px rgba(30, 64, 175, 0.1)',
        'glow-lg': '0 0 40px rgba(30, 64, 175, 0.15)',
      },

      // Animation
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'slide-down': 'slide-down 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
      },

      keyframes: {
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },

      // Backdrop Blur
      backdropBlur: {
        xs: '2px',
      },

      // Z-index
      zIndex: {
        'modal': '100',
        'overlay': '90',
        'dropdown': '80',
        'sticky': '70',
        'header': '60',
      },
    },
  },
  plugins: [],
}
