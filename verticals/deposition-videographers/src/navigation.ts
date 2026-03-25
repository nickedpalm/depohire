import { getPermalink, getBlogPermalink } from './utils/permalinks';
import config from '~/config';

export const headerData = {
  links: [
    {
      text: 'Find Providers',
      href: getPermalink('/search'),
    },
    {
      text: 'Browse by State',
      href: getPermalink('/states/all'),
    },
    {
      text: 'Blog',
      href: getBlogPermalink(),
    },
    {
      text: 'Free Guides',
      href: getPermalink('/guides'),
    },
    {
      text: 'About',
      href: getPermalink('/about'),
    },
  ],
  actions: [
    { text: 'List Your Business', href: getPermalink('/advertise') },
  ],
};

export const footerData = {
  links: [
    {
      title: 'Directory',
      links: [
        { text: 'Search', href: getPermalink('/search') },
        { text: 'Browse States', href: getPermalink('/states/all') },
        { text: 'Statistics', href: getPermalink('/statistics') },
      ],
    },
    {
      title: 'Resources',
      links: [
        { text: 'Blog', href: getBlogPermalink() },
        { text: 'Free Guides', href: getPermalink('/guides') },
        { text: 'Editorial Guidelines', href: getPermalink('/editorial-guidelines') },
      ],
    },
    {
      title: 'For Providers',
      links: [
        { text: 'Advertise', href: getPermalink('/advertise') },
        { text: 'Pricing', href: getPermalink('/pricing') },
      ],
    },
    {
      title: 'Company',
      links: [
        { text: 'About', href: getPermalink('/about') },
        { text: 'Privacy Policy', href: getPermalink('/privacy') },
        { text: 'Terms of Service', href: getPermalink('/terms') },
      ],
    },
  ],
  secondaryLinks: [
    { text: 'Privacy Policy', href: getPermalink('/privacy') },
    { text: 'Editorial Guidelines', href: getPermalink('/editorial-guidelines') },
  ],
  socialLinks: [],
  footNote: `© ${new Date().getFullYear()} ${config.brandName}. All rights reserved.`,
};
