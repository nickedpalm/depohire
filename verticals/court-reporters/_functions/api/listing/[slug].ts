/**
 * GET /api/listing/:slug
 * Public endpoint — returns claimed listing overrides + photos.
 * Used by the static listing page to patch in provider-edited data.
 * No authentication required.
 */
import type { Env } from '../../_types';
import { isAllowedOrigin } from '../../_auth';

export const onRequestGet: PagesFunction<Env> = async ({ params, env, request }) => {
  const slug = params.slug as string;
  const origin = request.headers.get('Origin');
  const domain = env.SITE_DOMAIN;
  const allowed = isAllowedOrigin(origin, domain) || (domain ? `https://${domain}` : '');
  const corsHeaders = {
    'Access-Control-Allow-Origin': allowed,
    'Content-Type': 'application/json',
    'Cache-Control': 'public, max-age=300', // 5 min cache
    'Vary': 'Origin',
  };

  if (!slug) {
    return new Response(JSON.stringify({ claimed: false }), { headers: corsHeaders });
  }

  const claim = await env.LEADS_DB.prepare(
    `SELECT cl.data_json, cl.claimed_at, p.name as provider_name
     FROM claimed_listings cl
     JOIN providers p ON p.id = cl.provider_id
     WHERE cl.listing_slug = ?`
  ).bind(slug).first<{ data_json: string; claimed_at: string; provider_name: string }>();

  if (!claim) {
    return new Response(JSON.stringify({ claimed: false }), { headers: corsHeaders });
  }

  let data: Record<string, any> = {};
  try { data = JSON.parse(claim.data_json || '{}'); } catch {}

  // Get photos
  const photos = await env.LEADS_DB.prepare(
    `SELECT id, r2_key, filename, sort_order FROM provider_photos
     WHERE listing_slug = ? ORDER BY sort_order ASC`
  ).bind(slug).all<{ id: number; r2_key: string; filename: string; sort_order: number }>();

  return new Response(JSON.stringify({
    claimed: true,
    claimed_at: claim.claimed_at,
    data,
    photos: (photos.results || []).map(p => ({
      id: p.id,
      url: `/api/photos/${p.r2_key}`,
      filename: p.filename,
    })),
  }), { headers: corsHeaders });
};

export const onRequestOptions: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin');
  const domain = env.SITE_DOMAIN;
  const allowed = isAllowedOrigin(origin, domain) || (domain ? `https://${domain}` : '');
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': allowed,
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Max-Age': '86400',
      'Vary': 'Origin',
    },
  });
};
