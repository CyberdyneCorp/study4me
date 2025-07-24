import type { Config } from 'tailwindcss'

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        'brand-yellow': '#FFF200',
        'brand-blue': '#0050FF',
        'brand-red': '#FF2C2C',
        'brand-pink': '#EC4899',
        'secondary-text': '#222222',
        'border-black': '#000000'
      },
      fontFamily: {
        'mono': ['IBM Plex Mono', 'monospace'],
        'inter': ['Inter', 'sans-serif']
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