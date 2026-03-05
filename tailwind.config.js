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
          50: '#f0f2f8',
          100: '#d9ddef',
          200: '#b3bbe0',
          300: '#8d99d0',
          400: '#6777c1',
          500: '#3a4fa5',
          600: '#2a3a7d',
          700: '#1e2b5e',
          800: '#142044',
          900: '#0f1e44',
          950: '#0a1634',
        },
        secondary: 'var(--aw-color-secondary)',
        accent: {
          DEFAULT: 'var(--aw-color-accent)',
          50: '#edfcfb',
          100: '#d0f7f4',
          200: '#a1efe9',
          300: '#6de5dc',
          400: '#3dd6cc',
          500: '#00a699',
          600: '#008a80',
          700: '#006e66',
          800: '#00534d',
          900: '#003d38',
          950: '#002925',
        },
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
              color: theme('colors.accent.600'),
              '&:hover': { color: theme('colors.accent.800') },
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
