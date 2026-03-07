import { getPermalink, getBlogPermalink } from './utils/permalinks';

export const headerData = {
  links: [
    {
      text: 'Search',
      href: getPermalink('/search'),
    },
    {
      text: 'Browse States',
      href: getPermalink('/states/all'),
    },
    {
      text: 'Expert Insights',
      href: getBlogPermalink(),
    },
    {
      text: 'Statistics',
      href: getPermalink('/statistics'),
    },
    {
      text: 'About',
      href: getPermalink('/about'),
    },
    {
      text: 'Advertise',
      href: getPermalink('/advertise'),
    },
  ],
  actions: [
    { text: 'View Pricing', href: getPermalink('/pricing'), variant: 'primary' },
  ]
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
        { text: 'Expert Insights', href: getBlogPermalink() },
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
      ],
    },
  ],
  secondaryLinks: [
    { text: 'Privacy Policy', href: getPermalink('/privacy') },
    { text: 'Editorial Guidelines', href: getPermalink('/editorial-guidelines') },
  ],
  socialLinks: [],
  footNote: '',
};
