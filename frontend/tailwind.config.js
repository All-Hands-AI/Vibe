/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ✨ Vibecoding Color Palette
        vibe: {
          purple: '#8b5cf6',
          pink: '#ec4899',
          orange: '#f97316',
          blue: '#3b82f6',
          green: '#10b981',
          yellow: '#f59e0b',
          dark: '#0f172a',
          darker: '#020617',
          text: '#e2e8f0',      // Warm text color
          muted: '#94a3b8',     // Warm secondary text
          border: '#475569',    // Warm border color
          accent: '#334155',    // Warm accent background
        },
        // Keep neon for accent colors
        neon: {
          green: '#10b981', // Warmer green for links
          cyan: '#06b6d4',
          pink: '#ec4899',
          purple: '#8b5cf6',
          orange: '#f97316',
          yellow: '#f59e0b',
        },
        // Keep cyber for backward compatibility but with warmer tones
        cyber: {
          dark: '#0f172a',
          darker: '#020617',
          blue: '#3b82f6',
          purple: '#8b5cf6',
          pink: '#ec4899',
          orange: '#f97316',
          text: '#e2e8f0',      // Warm text color
          muted: '#94a3b8',     // Warm secondary text
          border: '#475569',    // Warm border color
          accent: '#334155',    // Warm accent background
        },
        // Keep some original colors for compatibility
        primary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#8b5cf6', // Vibe purple
          400: '#7c3aed',
          500: '#6d28d9',
          600: '#5b21b6',
          700: '#4c1d95',
          800: '#3730a3',
          900: '#312e81',
        },
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        gray: {
          850: '#1a1a1a',
          950: '#0a0a0a',
        }
      },
      fontFamily: {
        // ✨ Vibecoding Monospace Fonts
        mono: [
          'Fira Code',
          'JetBrains Mono',
          'SF Mono',
          'Monaco',
          'Inconsolata',
          'Roboto Mono',
          'Source Code Pro',
          'Menlo',
          'Consolas',
          'DejaVu Sans Mono',
          'monospace'
        ],
        sans: [
          'Fira Code',
          'JetBrains Mono',
          'SF Mono',
          'Monaco',
          'Inconsolata',
          'Roboto Mono',
          'Source Code Pro',
          'Menlo',
          'Consolas',
          'DejaVu Sans Mono',
          'monospace'
        ],
        vibe: [
          'Fira Code',
          'JetBrains Mono',
          'monospace'
        ],
      },
      animation: {
        'pulse-vibe': 'pulse-vibe 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 0.8s infinite',
        'vibe-flow': 'vibe-flow 25s linear infinite',
      },
      keyframes: {
        'pulse-vibe': {
          '0%, 100%': {
            opacity: '1',
            textShadow: '0 0 5px currentColor, 0 0 10px currentColor, 0 0 15px currentColor',
          },
          '50%': {
            opacity: '0.8',
            textShadow: '0 0 2px currentColor, 0 0 5px currentColor, 0 0 8px currentColor',
          },
        },
        'shimmer': {
          '0%': { transform: 'translate(0)', opacity: '0.3' },
          '25%': { transform: 'translate(-1px, -0.5px)', opacity: '0.6' },
          '50%': { transform: 'translate(0)', opacity: '0.3' },
          '75%': { transform: 'translate(1px, 0.5px)', opacity: '0.6' },
          '100%': { transform: 'translate(0)', opacity: '0.3' },
        },
      },
      textShadow: {
        'vibe': '0 0 5px currentColor, 0 0 10px currentColor, 0 0 15px currentColor',
        'vibe-strong': '0 0 5px currentColor, 0 0 10px currentColor, 0 0 15px currentColor, 0 0 20px currentColor',
      },
    },
  },
  plugins: [
    // Add text shadow plugin
    function({ addUtilities }) {
      const newUtilities = {
        '.text-shadow-vibe': {
          textShadow: '0 0 5px currentColor, 0 0 10px currentColor, 0 0 15px currentColor',
        },
        '.text-shadow-vibe-strong': {
          textShadow: '0 0 5px currentColor, 0 0 10px currentColor, 0 0 15px currentColor, 0 0 20px currentColor',
        },
      }
      addUtilities(newUtilities)
    }
  ],
  darkMode: 'class',
}

