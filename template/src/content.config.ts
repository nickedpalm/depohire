import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: z.string().default('Editorial Team'),
    tags: z.array(z.string()).default([]),
    image: z.string().optional(),
  }),
});

const cities = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/cities' }),
  schema: z.object({
    title: z.string(),
    city: z.string(),
    state: z.string(),
    stateSlug: z.string(),
    slug: z.string(),
    metaDescription: z.string(),
    population: z.number().optional(),
  }),
});

export const collections = { blog, cities };
