import type { Config } from 'tailwindcss'

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        'primary-bg': '#FFF200',
        'accent-blue': '#0050FF',
        'accent-red': '#FF2C2C',
        'secondary-text': '#222222',
        'border-black': '#000000'
      },
      fontFamily: {
        'heading': ['IBM Plex Mono', 'JetBrains Mono', 'Space Mono', 'monospace'],
        'body': ['Inter', 'DM Sans', 'Lexend Deca', 'sans-serif'],
        'code': ['JetBrains Mono', 'monospace']
      },
      borderWidth: {
        '3': '3px',
        '4': '4px'
      },
      borderRadius: {
        'neo': '4px'
      }
    },
  },
  plugins: [],
} satisfies Config