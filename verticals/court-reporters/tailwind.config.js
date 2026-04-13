import defaultTheme from 'tailwindcss/defaultTheme';
import plugin from 'tailwindcss/plugin';
import typographyPlugin from '@tailwindcss/typography';
import { readFileSync } from 'fs';
import { resolve } from 'path';

// Load generated color theme (falls back to blue defaults)
let colors;
try {
  const raw = readFileSync(resolve(process.cwd(), 'colors.json'), 'utf-8');
  colors = JSON.parse(raw);
} catch {
  colors = {
    primary: {
      50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd',
      400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
      800: '#1e40af', 900: '#1e3a8a', 950: '#172554',
    },
    navy: { 800: '#1e3a5f', 900: '#2d2b55', 950: '#1a1a2e' },
    shadow: { r: 37, g: 99, b: 235 },
  };
}

export default {
  content: ['./src/**/*.{astro,html,js,jsx,json,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--aw-color-primary)',
          ...colors.primary,
        },
        navy: colors.navy,
        surface: {
          page: '#f8fafc',
          muted: '#f0f2f5',
        },
        secondary: 'var(--aw-color-secondary)',
        accent: 'var(--aw-color-accent)',
        default: 'var(--aw-color-text-default)',
        muted: 'var(--aw-color-text-muted)',
      },
      borderRadius: {
        'card': '16px',
        'btn': '12px',
        'input': '10px',
        'badge': '8px',
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.06)',
        'card-hover': `0 8px 24px rgba(${colors.shadow.r},${colors.shadow.g},${colors.shadow.b},0.08)`,
        'card-elevated': `0 4px 20px rgba(${colors.shadow.r},${colors.shadow.g},${colors.shadow.b},0.1)`,
      },
      fontFamily: {
        sans: ['var(--aw-font-sans, ui-sans-serif)', ...defaultTheme.fontFamily.sans],
        serif: ['var(--aw-font-serif, ui-serif)', ...defaultTheme.fontFamily.serif],
        heading: ['var(--aw-font-heading, ui-sans-serif)', ...defaultTheme.fontFamily.sans],
      },

      animation: {
        fade: 'fadeInUp 1s both',
      },

      keyframes: {
        fadeInUp: {
          '0%': { opacity: 0, transform: 'translateY(2rem)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            'a': {
              color: theme('colors.primary.600'),
              '&:hover': { color: theme('colors.primary.800') },
            },
            'h2': { marginTop: '1.5em', marginBottom: '0.5em' },
            'h3': { marginTop: '1.25em', marginBottom: '0.4em' },
            'table': { borderCollapse: 'collapse', width: '100%' },
            'thead th': {
              backgroundColor: theme('colors.gray.100'),
              borderBottom: `2px solid ${theme('colors.gray.300')}`,
              padding: '0.75rem 1rem',
              textAlign: 'left',
            },
            'tbody td': {
              borderBottom: `1px solid ${theme('colors.gray.200')}`,
              padding: '0.75rem 1rem',
            },
            'tbody tr:nth-child(even)': {
              backgroundColor: theme('colors.gray.50'),
            },
            'blockquote': {
              fontStyle: 'normal',
              borderLeftColor: theme('colors.gray.300'),
            },
          },
        },
      }),
    },
  },
  plugins: [
    typographyPlugin,
    plugin(({ addVariant }) => {
      addVariant('intersect', '&:not([no-intersect])');
    }),
  ],
  darkMode: 'class',
};
