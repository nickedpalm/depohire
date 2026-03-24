/**
 * Cloudflare Pages Function: Native Review Submission
 *
 * POST /api/reviews — captures first-party reviews from attorneys.
 * Reviews are stored in D1 and require approval before display.
 */

import type { Env } from '../_types';
import { verifyTurnstile } from '../_auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }

  const { provider_slug, reviewer_name, reviewer_email, rating, comment } = payload;

  if (!provider_slug || !rating || rating < 1 || rating > 5) {
    return new Response(JSON.stringify({ error: 'provider_slug and rating (1-5) are required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }

  // Turnstile verification
  if (env.TURNSTILE_SECRET_KEY) {
    const ip = request.headers.get('CF-Connecting-IP') || '';
    const valid = await verifyTurnstile(payload.turnstile_token || '', env.TURNSTILE_SECRET_KEY, ip);
    if (!valid) {
      return new Response(JSON.stringify({ error: 'Bot verification failed. Please try again.' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }
  }

  try {
    if (!env.LEADS_DB) {
      throw new Error('D1 database not configured');
    }

    await env.LEADS_DB.prepare(
      `INSERT INTO reviews (created_at, provider_slug, reviewer_name, reviewer_email, rating, comment, approved)
       VALUES (?, ?, ?, ?, ?, ?, 0)`
    ).bind(
      new Date().toISOString(),
      provider_slug,
      reviewer_name || '',
      reviewer_email || '',
      rating,
      comment || '',
    ).run();

    return new Response(JSON.stringify({
      status: 'ok',
      message: 'Thank you for your review! It will be published after verification.',
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  } catch (err) {
    console.error('Review submission failed:', err);
    return new Response(JSON.stringify({ error: 'Failed to save review' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }
};

export const onRequestOptions: PagesFunction = async () => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
};
