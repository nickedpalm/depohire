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
  ],
  actions: [],
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
