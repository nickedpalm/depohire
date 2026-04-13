import verticalData from '../vertical.json' with { type: 'json' };

export interface EditorialAuthor {
  name: string;
  title: string;
  bio: string;
  linkedin?: string;
}

export interface Pricing {
  featuredMonthlyUsd: number | null;
  featuredAnnualUsd: number | null;
  cityProMonthlyUsd: number | null;
  cityProAnnualUsd: number | null;
}

export interface SiteConfig {
  name: string;
  brandName: string;
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
  // Legacy single-link fields (depohire uses these)
  stripeSponsoredLink: string;
  stripeCityProLink: string;
  // Current 4-link monthly/annual schema
  stripeFeaturedMonthlyLink: string;
  stripeFeaturedAnnualLink: string;
  stripeCityProMonthlyLink: string;
  stripeCityProAnnualLink: string;
  // Stripe resource IDs (for webhooks / admin tooling; not used by template render)
  stripeFeaturedProductId: string;
  stripeCityProProductId: string;
  stripeFeaturedMonthlyPriceId: string;
  stripeFeaturedAnnualPriceId: string;
  stripeCityProMonthlyPriceId: string;
  stripeCityProAnnualPriceId: string;
  // Display pricing (USD amounts shown on pricing/advertise pages)
  pricing: Pricing;
  turnstileSitekey: string;
  turnsiteSitekey: string; // legacy alias; keep until template stops referencing it
  googleAnalyticsId: string;
  editorialAuthor: EditorialAuthor;
  foundedYear: number;
  buildYear: number;
}

const d = verticalData as Record<string, any>;
const editorial = d.editorialAuthor || {};
const pricingData = d.pricing || {};

const config: SiteConfig = {
  name: d.name ?? 'Directory',
  brandName: d.brandName || d.domain?.replace(/\.com$/, '') || 'Directory',
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
  stripeSponsoredLink: d.stripeSponsoredLink ?? '',
  stripeCityProLink: d.stripeCityProLink ?? '',
  stripeFeaturedMonthlyLink: d.stripeFeaturedMonthlyLink ?? '',
  stripeFeaturedAnnualLink: d.stripeFeaturedAnnualLink ?? '',
  stripeCityProMonthlyLink: d.stripeCityProMonthlyLink ?? '',
  stripeCityProAnnualLink: d.stripeCityProAnnualLink ?? '',
  stripeFeaturedProductId: d.stripeFeaturedProductId ?? '',
  stripeCityProProductId: d.stripeCityProProductId ?? '',
  stripeFeaturedMonthlyPriceId: d.stripeFeaturedMonthlyPriceId ?? '',
  stripeFeaturedAnnualPriceId: d.stripeFeaturedAnnualPriceId ?? '',
  stripeCityProMonthlyPriceId: d.stripeCityProMonthlyPriceId ?? '',
  stripeCityProAnnualPriceId: d.stripeCityProAnnualPriceId ?? '',
  pricing: {
    featuredMonthlyUsd: pricingData.featuredMonthlyUsd ?? null,
    featuredAnnualUsd: pricingData.featuredAnnualUsd ?? null,
    cityProMonthlyUsd: pricingData.cityProMonthlyUsd ?? null,
    cityProAnnualUsd: pricingData.cityProAnnualUsd ?? null,
  },
  turnstileSitekey: d.turnstileSitekey ?? d.turnsiteSitekey ?? '',
  turnsiteSitekey: d.turnstileSitekey ?? d.turnsiteSitekey ?? '',
  googleAnalyticsId: d.googleAnalyticsId ?? '',
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
