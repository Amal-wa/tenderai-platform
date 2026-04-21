import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0F1C35',
          light: '#162240',
          muted: '#2A3F5E',
        },
        amber: {
          DEFAULT: '#C4962A',
          light: '#d4a93c',
          soft: '#FAF0DC',
        },
        cream: {
          DEFAULT: '#F5F3EE',
          dark: '#EDE9E2',
          border: '#E5E0D8',
        },
        muted: '#6B6560',
        success: { DEFAULT: '#1E7C5A', bg: '#E8F5EF' },
        danger: { DEFAULT: '#B83232', bg: '#FBEAEA' },
        info: { DEFAULT: '#2D52A8', bg: '#E8EEF8' },
      },
      fontFamily: {
        sans: ['var(--font-ibm)', 'IBM Plex Sans', 'sans-serif'],
        heading: ['var(--font-sora)', 'Sora', 'sans-serif'],
        arabic: ['var(--font-arabic)', 'Noto Sans Arabic', 'sans-serif'],
      },
      boxShadow: {
        amber: '0 8px 32px rgba(196,150,42,0.12)',
        card: '0 1px 4px rgba(0,0,0,0.06)',
        'card-hover': '0 16px 40px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
}

export default config
