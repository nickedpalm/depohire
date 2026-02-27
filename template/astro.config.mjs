import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

import siteConfig from './src/config.ts';

export default defineConfig({
  site: siteConfig.siteUrl || 'https://example.com',
  integrations: [mdx(), tailwind(), sitemap()],
  output: 'static',
});
