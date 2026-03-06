/**
 * FILE LOCATION: functions/subscribe.ts
 * Cloudflare Pages Function — handles POST /subscribe from all forms
 *
 * Uses Listmonk v6 public subscription form endpoint (/subscription/form)
 * which requires list UUIDs (not numeric IDs) and no authentication.
 *
 * LISTMONK LIST UUIDs (mail.firestick.io):
 *   6  → 1574cfb0-e6d2-4e02-b7db-684b252f7178  DepoHire Newsletter
 *   30 → 1c82963b-310b-4af5-bf89-a7fb96132dd8  DepoHire Leads
 *   31 → 4f72411e-2d6c-4ddb-af06-674b502393d7  DepoHire Blog
 *   33 → b8c38467-94a1-4e6a-aeb4-c14a72bd11a8  DepoHire Provider Interest
 *   34 → c7be263f-1308-4b7a-a65e-594809e728ad  Lead Magnet Downloads
 *
 * CLOUDFLARE PAGES ENV VARS (set per project in Cloudflare dashboard):
 *   LISTMONK_URL  = https://mail.firestick.io
 *
 * SOURCE → LIST UUID ROUTING:
 *   city-quote-form      → 30 (DepoHire Leads)
 *   listing-quote-form   → 30 (DepoHire Leads)
 *   blog-sidebar         → 31 (DepoHire Blog)
 *   exit-intent          → 34 (Lead Magnet Downloads)
 *   provider-signup      → 33 (DepoHire Provider Interest)
 *   advertise-form       → 33 (DepoHire Provider Interest)
 *   default              → 6  (DepoHire Newsletter)
 */

interface Env {
  LISTMONK_URL: string;
}

// Source → list UUID mapping (lists must be type='public' in Listmonk)
const SOURCE_TO_UUID: Record<string, string> = {
  'city-quote-form':    '1c82963b-310b-4af5-bf89-a7fb96132dd8', // list 30
  'listing-quote-form': '1c82963b-310b-4af5-bf89-a7fb96132dd8', // list 30
  'blog-sidebar':       '4f72411e-2d6c-4ddb-af06-674b502393d7', // list 31
  'exit-intent':        'c7be263f-1308-4b7a-a65e-594809e728ad', // list 34
  'provider-signup':    'b8c38467-94a1-4e6a-aeb4-c14a72bd11a8', // list 33
  'advertise-form':     'b8c38467-94a1-4e6a-aeb4-c14a72bd11a8', // list 33
};
const DEFAULT_UUID = '1574cfb0-e6d2-4e02-b7db-684b252f7178'; // list 6 — DepoHire Newsletter

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json',
  };

  try {
    const contentType = request.headers.get('Content-Type') || '';

    let email = '', name = '', source = '';

    if (contentType.includes('application/json')) {
      const body = await request.json() as Record<string, string>;
      email  = body.email  || '';
      name   = body.name   || '';
      source = body.source || '';
    } else {
      // application/x-www-form-urlencoded (from advertise page)
      const formData = await request.formData();
      email  = (formData.get('email')  as string) || '';
      name   = (formData.get('name')   as string) || '';
      source = (formData.get('source') as string) || '';
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(JSON.stringify({ ok: false, error: 'Invalid email' }), { status: 400, headers: cors });
    }

    const base = env.LISTMONK_URL?.replace(/\/$/, '');
    if (!base) {
      console.error('Missing LISTMONK_URL');
      return new Response(JSON.stringify({ ok: false, error: 'Server config error' }), { status: 500, headers: cors });
    }

    const listUUID = SOURCE_TO_UUID[source] ?? DEFAULT_UUID;

    // Use the public /subscription/form endpoint — no auth required in Listmonk v6
    const payload = new URLSearchParams({
      email,
      name: name || email.split('@')[0],
      l: listUUID,
    });

    const res = await fetch(`${base}/subscription/form`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: payload.toString(),
    });

    const responseText = await res.text();

    // Public form returns HTML — check for success/duplicate indicators
    const isAlreadySubscribed = responseText.toLowerCase().includes('already subscribed')
      || responseText.toLowerCase().includes('unsubscribed');
    const isSuccess = res.ok || responseText.toLowerCase().includes('subscribed successfully') || isAlreadySubscribed;

    if (isSuccess) {
      return new Response(JSON.stringify({ ok: true, already: isAlreadySubscribed }), { headers: cors });
    }

    console.error('Listmonk subscription error:', res.status, responseText.slice(0, 200));
    return new Response(JSON.stringify({ ok: false, error: 'Subscription failed' }), { status: 500, headers: cors });

  } catch (err) {
    console.error('Subscribe function error:', err);
    return new Response(JSON.stringify({ ok: false, error: 'Server error' }), { status: 500, headers: cors });
  }
};

export const onRequestOptions: PagesFunction = async () =>
  new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
