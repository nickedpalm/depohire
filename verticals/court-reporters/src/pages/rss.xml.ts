import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import config from '~/config';

export const GET: APIRoute = async () => {
  const posts = (await getCollection('blog'))
    .filter((p) => !p.data.draft)
    .sort((a, b) => (b.data.pubDate?.valueOf() || 0) - (a.data.pubDate?.valueOf() || 0));

  const siteUrl = config.siteUrl || 'https://stenoscout.com';

  const escapeXml = (s: string) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  const items = posts
    .map((post) => {
      const link = `${siteUrl}/blog/${post.slug}/`;
      const pubDate = post.data.pubDate ? new Date(post.data.pubDate).toUTCString() : '';
      return `    <item>
      <title>${escapeXml(post.data.title)}</title>
      <link>${link}</link>
      <guid>${link}</guid>${pubDate ? `\n      <pubDate>${pubDate}</pubDate>` : ''}${post.data.description ? `\n      <description>${escapeXml(post.data.description)}</description>` : ''}
    </item>`;
    })
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escapeXml(config.brandName)} Blog</title>
    <description>${escapeXml(config.description)}</description>
    <link>${siteUrl}</link>
    <atom:link href="${siteUrl}/rss.xml" rel="self" type="application/rss+xml"/>
    <language>en-us</language>
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
