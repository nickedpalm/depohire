/**
 * Bridge between our vertical.json config and AstroWind's expected config shapes.
 * Replaces AstroWind's vendor/ integration + config.yaml system.
 */
import config from '~/config';

const brandName = config.brandName;

export const SITE = {
  name: brandName,
  site: config.siteUrl,
  base: '/',
  trailingSlash: true,
  googleSiteVerificationId: '',
};

export const METADATA = {
  title: {
    default: brandName,
    template: `%s | ${brandName}`,
  },
  description: config.description,
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    site_name: brandName,
    type: 'website',
  },
  twitter: {
    cardType: 'summary_large_image',
  },
};

export const I18N = {
  language: 'en',
  textDirection: 'ltr' as const,
};

export const APP_BLOG = {
  isEnabled: true,
  postsPerPage: 12,
  isRelatedPostsEnabled: true,
  list: {
    isEnabled: true,
    pathname: 'blog',
    robots: { index: true, follow: true },
  },
  post: {
    isEnabled: true,
    permalink: 'blog/%slug%',
    robots: { index: true, follow: true },
  },
  category: {
    isEnabled: true,
    pathname: 'blog/category',
    robots: { index: true, follow: true },
  },
  tag: {
    isEnabled: true,
    pathname: 'blog/tag',
    robots: { index: true, follow: true },
  },
};

export const UI = {
  theme: 'light:only' as const,
};

export const ANALYTICS = {
  vendors: {
    googleAnalytics: { id: config.googleAnalyticsId || '', partytown: false },
  },
};
