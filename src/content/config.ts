import { z, defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

const metadataDefinition = () =>
  z
    .object({
      title: z.string().optional(),
      ignoreTitleTemplate: z.boolean().optional(),
      canonical: z.string().url().optional(),
      robots: z
        .object({
          index: z.boolean().optional(),
          follow: z.boolean().optional(),
        })
        .optional(),
      description: z.string().optional(),
      openGraph: z
        .object({
          url: z.string().optional(),
          siteName: z.string().optional(),
          images: z
            .array(
              z.object({
                url: z.string(),
                width: z.number().optional(),
                height: z.number().optional(),
              })
            )
            .optional(),
          locale: z.string().optional(),
          type: z.string().optional(),
        })
        .optional(),
      twitter: z
        .object({
          handle: z.string().optional(),
          site: z.string().optional(),
          cardType: z.string().optional(),
        })
        .optional(),
    })
    .optional();

// Blog collection — our schema with AstroWind compat fields
const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    pubDate: z.coerce.date().optional(),
    updatedDate: z.coerce.date().optional(),
    author: z.string().default('Editorial Team'),
    tags: z.array(z.string()).default([]),
    hub: z.string().optional(),
    image: z.string().optional(),
    imageCredit: z.string().optional(),
    // AstroWind compat fields
    category: z.string().optional(),
    draft: z.boolean().optional(),
    metadata: metadataDefinition(),
  }),
});

// City content collection
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
    image: z.string().optional(),
    imageCredit: z.string().optional(),
  }),
});

export const collections = { blog, cities };
