import defaultTheme from 'tailwindcss/defaultTheme';
import plugin from 'tailwindcss/plugin';
import typographyPlugin from '@tailwindcss/typography';

export default {
  content: ['./src/**/*.{astro,html,js,jsx,json,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--aw-color-primary)',
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        secondary: 'var(--aw-color-secondary)',
        accent: 'var(--aw-color-accent)',
        default: 'var(--aw-color-text-default)',
        muted: 'var(--aw-color-text-muted)',
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
