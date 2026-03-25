import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

import { defineConfig } from 'astro/config';

import sitemap from '@astrojs/sitemap';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import icon from 'astro-icon';

import { readingTimeRemarkPlugin, responsiveTablesRehypePlugin, lazyImagesRehypePlugin } from './src/utils/frontmatter';
import verticalData from './vertical.json' with { type: 'json' };

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function listingContactsIntegration() {
  return {
    name: 'build-listing-contacts',
    hooks: {
      'astro:build:start': () => {
        console.log('[integration] Generating listing-contacts.json...');
        execSync('npx tsx src/scripts/build-listing-contacts.ts', {
          cwd: __dirname,
          stdio: 'inherit',
        });
      },
    },
  };
}

export default defineConfig({
  site: (verticalData as any).siteUrl || `https://${(verticalData as any).domain || 'localhost'}`,

  output: 'static',

  integrations: [
    listingContactsIntegration(),
    tailwind({
      applyBaseStyles: false,
    }),
    sitemap({
      filter: (page) => !page.includes('/provider/dashboard'),
    }),
    mdx(),
    icon({
      include: {
        tabler: ['*'],
      },
    }),
  ],

  markdown: {
    remarkPlugins: [readingTimeRemarkPlugin],
    rehypePlugins: [responsiveTablesRehypePlugin, lazyImagesRehypePlugin],
  },

  vite: {
    resolve: {
      alias: {
        '~': path.resolve(__dirname, './src'),
      },
    },
  },
});
