/**
 * GET /api/provider/analytics?slug=xxx
 *
 * Returns page view counts for a claimed listing.
 * Requires authenticated provider session.
 */

import type { Env } from '../../_types';
import { getProvider, corsHeaders, jsonResponse } from '../../_auth';

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) {
    return jsonResponse({ error: 'Unauthorized' }, 401, origin);
  }

  const url = new URL(request.url);
  const slug = url.searchParams.get('slug');
  if (!slug) {
    return jsonResponse({ error: 'Missing slug' }, 400, origin);
  }

  // Verify provider owns this listing
  const claim = await env.LEADS_DB.prepare(
    `SELECT id FROM claimed_listings WHERE listing_slug = ? AND provider_id = ?`
  ).bind(slug, provider.id).first();
  if (!claim) {
    return jsonResponse({ error: 'Not your listing' }, 403, origin);
  }

  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();

  // Total views (last 30 days)
  const total30 = await env.LEADS_DB.prepare(
    `SELECT COUNT(*) as cnt FROM page_views WHERE listing_slug = ? AND created_at > ?`
  ).bind(slug, thirtyDaysAgo).first<{ cnt: number }>();

  // Views this week
  const total7 = await env.LEADS_DB.prepare(
    `SELECT COUNT(*) as cnt FROM page_views WHERE listing_slug = ? AND created_at > ?`
  ).bind(slug, sevenDaysAgo).first<{ cnt: number }>();

  // Unique visitors (by ip_hash, last 30 days)
  const unique30 = await env.LEADS_DB.prepare(
    `SELECT COUNT(DISTINCT ip_hash) as cnt FROM page_views WHERE listing_slug = ? AND created_at > ? AND ip_hash != ''`
  ).bind(slug, thirtyDaysAgo).first<{ cnt: number }>();

  // Daily views for sparkline (last 12 weeks, grouped by week)
  const weekly = await env.LEADS_DB.prepare(
    `SELECT strftime('%Y-%W', created_at) as week, COUNT(*) as cnt
     FROM page_views WHERE listing_slug = ? AND created_at > ?
     GROUP BY week ORDER BY week`
  ).bind(slug, new Date(now.getTime() - 84 * 24 * 60 * 60 * 1000).toISOString()).all<{ week: string; cnt: number }>();

  // Top referrers
  const referrers = await env.LEADS_DB.prepare(
    `SELECT referrer, COUNT(*) as cnt FROM page_views
     WHERE listing_slug = ? AND created_at > ? AND referrer != ''
     GROUP BY referrer ORDER BY cnt DESC LIMIT 5`
  ).bind(slug, thirtyDaysAgo).all<{ referrer: string; cnt: number }>();

  return jsonResponse({
    views_30d: total30?.cnt || 0,
    views_7d: total7?.cnt || 0,
    unique_visitors_30d: unique30?.cnt || 0,
    weekly_views: weekly?.results || [],
    top_referrers: referrers?.results || [],
  }, 200, origin);
};
