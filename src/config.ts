import verticalData from '../vertical.json' with { type: 'json' };

export interface EditorialAuthor {
  name: string;
  title: string;
  bio: string;
  linkedin?: string;
}

export interface SiteConfig {
  name: string;
  slug: string;
  domain: string;
  siteUrl: string;
  tagline: string;
  description: string;
  jobValue: string;
  industry: string;
  primaryKeyword: string;
  secondaryKeywords: string[];
  certifications: string[];
  extraFields: string[];
  cityPagePromptContext: string;
  contactEmail: string;
  editorialAuthor: EditorialAuthor;
  foundedYear: number;
  buildYear: number;
}

const d = verticalData as Record<string, any>;
const editorial = d.editorialAuthor || {};

const config: SiteConfig = {
  name: d.name ?? 'Directory',
  slug: d.slug ?? 'directory',
  domain: d.domain ?? 'example.com',
  siteUrl: d.siteUrl ?? `https://${d.domain ?? 'example.com'}`,
  tagline: d.tagline ?? 'Find professionals near you',
  description: d.description ?? 'A professional directory',
  jobValue: d.jobValue ?? '',
  industry: d.industry ?? '',
  primaryKeyword: d.primaryKeyword ?? '',
  secondaryKeywords: d.secondaryKeywords ?? [],
  certifications: d.certifications ?? [],
  extraFields: d.extraFields ?? [],
  cityPagePromptContext: d.cityPagePromptContext ?? '',
  contactEmail: d.contactEmail ?? `contact@${d.domain ?? 'example.com'}`,
  editorialAuthor: {
    name: editorial.name ?? 'Editorial Team',
    title: editorial.title ?? 'Directory Editor',
    bio: editorial.bio ?? `Expert contributor at ${d.name ?? 'the directory'}.`,
    linkedin: editorial.linkedin,
  },
  foundedYear: d.foundedYear ?? new Date().getFullYear(),
  buildYear: new Date().getFullYear(),
};

export default config;
