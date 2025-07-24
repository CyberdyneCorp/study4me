/**
 * tailwind.config.ts - Tailwind CSS configuration for Study4Me
 * 
 * This configuration extends Tailwind CSS with custom design tokens
 * that support the neobrutalism design system used throughout the application.
 * 
 * Design System Features:
 * - High contrast brand colors for visual impact
 * - Thick borders (3px, 4px) for neobrutalism aesthetic
 * - Monospace typography for technical/retro feel
 * - Custom border radius for consistent component styling
 * 
 * Usage:
 * - Colors: Use brand-* classes (bg-brand-yellow, text-brand-blue, etc.)
 * - Typography: font-mono for headings, font-inter for body text
 * - Borders: border-3, border-4 for thick neobrutalism borders
 */

import type { Config } from 'tailwindcss'

export default {
  // Content paths - tells Tailwind which files to scan for class usage
  content: ['./src/**/*.{html,js,svelte,ts}'],
  
  theme: {
    extend: {
      /**
       * Brand Color Palette
       * High contrast colors that create visual impact and accessibility
       * Used consistently across all UI components
       */
      colors: {
        'brand-yellow': '#FFF200',    // Primary background color - bright yellow
        'brand-blue': '#0050FF',      // Primary action color - electric blue
        'brand-red': '#FF2C2C',       // Danger/delete actions - bright red
        'brand-pink': '#EC4899',      // Secondary actions - vibrant pink
        'secondary-text': '#222222',  // Dark gray for readable body text
        'border-black': '#000000'     // Pure black for neobrutalism borders
      },
      
      /**
       * Typography Stack
       * Combination of monospace and sans-serif for neobrutalism aesthetic
       */
      fontFamily: {
        'mono': ['IBM Plex Mono', 'monospace'],  // Headers, buttons, tech elements
        'inter': ['Inter', 'sans-serif']         // Body text, descriptions
      },
      
      /**
       * Border Widths
       * Thick borders are essential for the neobrutalism design
       * Standard Tailwind only goes up to 2px, we need thicker options
       */
      borderWidth: {
        '3': '3px',  // Medium thick borders for secondary elements
        '4': '4px'   // Extra thick borders for primary elements
      },
      
      /**
       * Border Radius
       * Subtle rounding that maintains the sharp neobrutalism feel
       * while adding slight softness for better UX
       */
      borderRadius: {
        'neo': '4px'  // Consistent border radius for neobrutalism components
      }
    },
  },
  
  // No additional plugins needed for our current design system
  plugins: [],
} satisfies Config