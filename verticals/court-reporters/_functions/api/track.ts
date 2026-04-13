/**
 * GET /api/track?s=<slug>&p=<path>
 *
 * Lightweight page view tracker. Called via 1x1 pixel or sendBeacon.
 * Hashes IP for privacy (no raw IPs stored).
 */

import type { Env } from '../_types';
import { isAllowedOrigin, getSiteConfig } from '../_auth';

async function hashIP(ip: string, salt: string): Promise<string> {
  if (!ip) return '';
  const data = new TextEncoder().encode(ip + salt);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hash)).slice(0, 8).map(b => b.toString(16).padStart(2, '0')).join('');
}

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const slug = url.searchParams.get('s');
  const path = url.searchParams.get('p') || '/';

  if (!slug || !env.LEADS_DB) {
    return new Response('', { status: 204 });
  }

  const ip = request.headers.get('CF-Connecting-IP') || '';
  const ua = request.headers.get('User-Agent') || '';
  const referrer = request.headers.get('Referer') || '';

  // Skip bots
  if (/bot|crawl|spider|slurp|facebookexternalhit|Twitterbot/i.test(ua)) {
    return new Response('', { status: 204 });
  }

  const site = getSiteConfig(env);

  try {
    const ipHash = await hashIP(ip, site.hashSalt);
    await env.LEADS_DB.prepare(
      `INSERT INTO page_views (listing_slug, path, referrer, ip_hash, user_agent, created_at)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(slug, path, referrer.slice(0, 500), ipHash, ua.slice(0, 300), new Date().toISOString()).run();
  } catch (err) {
    console.error('Track insert failed:', err);
  }

  const origin = request.headers.get('Origin');
  const domain = env.SITE_DOMAIN;
  const allowed = isAllowedOrigin(origin, domain) || (domain ? `https://${domain}` : '');
  return new Response('', {
    status: 204,
    headers: {
      'Cache-Control': 'no-store, no-cache',
      'Access-Control-Allow-Origin': allowed,
      'Vary': 'Origin',
    },
  });
};
