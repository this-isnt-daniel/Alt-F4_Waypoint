/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        canvas: 'var(--c-canvas)',
        surface: 'var(--c-surface)',
        raised: 'var(--c-raised)',
        line: 'var(--c-line)',
        hero: {
          DEFAULT: 'var(--c-hero)',
          label: 'var(--c-hero-label)',
          ink: 'var(--c-hero-ink)',
        },
        ink: {
          DEFAULT: 'var(--c-ink)',
          muted: 'var(--c-ink-muted)',
        },
        green: {
          DEFAULT: 'var(--c-green)',
          ink: 'var(--c-green-ink)',
          fill: 'var(--c-green-fill)',
        },
        success: {
          DEFAULT: 'var(--c-success)',
          fill: 'var(--c-success-fill)',
        },
        warning: {
          DEFAULT: 'var(--c-warning)',
          fill: 'var(--c-warning-fill)',
        },
        danger: {
          DEFAULT: 'var(--c-danger)',
          fill: 'var(--c-danger-fill)',
        },
        offline: {
          DEFAULT: 'var(--c-offline)',
          fill: 'var(--c-offline-fill)',
        },
        restriction: {
          DEFAULT: 'var(--c-restriction)',
          fill: 'var(--c-restriction-fill)',
          line: 'var(--c-restriction-line)',
        },
        brand: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
        },
      },
      borderRadius: {
        card: '18px',
        btn: '14px',
        pill: '999px',
      },
      boxShadow: {
        '1': 'var(--shadow-1)',
        '2': 'var(--shadow-2)',
      },
      fontSize: {
        '2xs': '10px',
      },
    },
  },
  plugins: [],
};
