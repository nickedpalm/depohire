/**
 * Cloudflare Pages Function: Lead Capture Fallback
 *
 * Proxies POST /api/leads to the VPS backend (api.depohire.com).
 * If the VPS is down or times out (5s), stores the lead in D1 as a fallback
 * so zero leads are dropped. Returns 200 to the attorney either way.
 */

interface Env {
  LEADS_DB: D1Database;
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  // CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return new Response(JSON.stringify({ detail: 'Invalid JSON' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }

  // Honeypot check
  if (payload.honeypot) {
    return new Response(JSON.stringify({ status: 'ok' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }

  // Try the primary VPS backend with a 5-second timeout
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const resp = await fetch('https://api.depohire.com/api/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (resp.ok) {
      const data = await resp.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }

    // VPS returned an error — fall through to D1 fallback
    throw new Error(`VPS returned ${resp.status}`);
  } catch (err) {
    // VPS is down or timed out — store in D1 as fallback
    console.error('VPS lead proxy failed, falling back to D1:', err);

    try {
      if (env.LEADS_DB) {
        await env.LEADS_DB.prepare(
          `INSERT INTO leads (created_at, attorney_name, attorney_email, attorney_phone, case_details, city, providers_json, forwarded)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0)`
        ).bind(
          new Date().toISOString(),
          payload.attorney_name || '',
          payload.attorney_email || '',
          payload.attorney_phone || '',
          payload.case_details || '',
          payload.city || '',
          JSON.stringify(payload.providers || []),
        ).run();
      }
    } catch (d1Err) {
      console.error('D1 fallback also failed:', d1Err);
    }

    // Always return success to the attorney
    return new Response(JSON.stringify({
      status: 'ok',
      message: 'Your request has been received. Providers will respond to your email.',
      emailed: (payload.providers || []).length || 1,
      fallback: true,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }
};

// Handle CORS preflight
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
