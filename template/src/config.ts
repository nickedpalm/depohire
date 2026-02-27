import verticalData from '../vertical.json' with { type: 'json' };

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
}

const config: SiteConfig = {
  name: verticalData.name ?? 'Directory',
  slug: verticalData.slug ?? 'directory',
  domain: verticalData.domain ?? 'example.com',
  siteUrl: verticalData.siteUrl ?? `https://${verticalData.domain ?? 'example.com'}`,
  tagline: verticalData.tagline ?? 'Find professionals near you',
  description: verticalData.description ?? 'A professional directory',
  jobValue: verticalData.jobValue ?? '',
  industry: verticalData.industry ?? '',
  primaryKeyword: verticalData.primaryKeyword ?? '',
  secondaryKeywords: verticalData.secondaryKeywords ?? [],
  certifications: verticalData.certifications ?? [],
  extraFields: verticalData.extraFields ?? [],
  cityPagePromptContext: verticalData.cityPagePromptContext ?? '',
};

export default config;
