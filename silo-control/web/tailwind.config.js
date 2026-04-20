/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      keyframes: {
        'slide-up': {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
      },
      animation: {
        'slide-up': 'slide-up 0.25s ease-out',
      },
      colors: {
        surface: '#FFFFFF',
        surface2: '#F1F5F9',
        accent: '#2563EB',
        accent2: '#3B82F6',
        muted: '#64748B',
        ok: '#DCFCE7',
        warn: '#FEF9C3',
        alarm: '#FEE2E2',
        inactive: '#F1F5F9',
      },
    },
  },
  plugins: [],
}
