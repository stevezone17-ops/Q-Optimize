/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          950: '#06080F',
          900: '#0A0F1D',
          850: '#0E1626',
          800: '#131D32',
          700: '#1B2844',
          600: '#26385E',
        },
        scientific: {
          surface: '#0B101E',
          card: '#10172A',
          border: '#1E293B',
          hover: '#1E2B4A',
          text: '#F1F5F9',
          muted: '#94A3B8',
          accent: '#38BDF8',
          violet: '#8B5CF6',
          gold: '#F59E0B',
          emerald: '#10B981',
          rose: '#F43F5E',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
